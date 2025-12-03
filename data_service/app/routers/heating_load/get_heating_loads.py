"""
Heating data retrieval API endpoints.

This module provides FastAPI endpoints for retrieving previously generated
heating-related data in formats compatible with the EPOCH energy modeling system:
- Space heating loads with associated intervention costs
- Domestic hot water (DHW) consumption profiles
- Air temperature time series
"""

import asyncio
import datetime
import json
import logging
from typing import cast

import pandas as pd

from app.dependencies import DatabasePoolDep
from app.internal.epl_typing import RecordMapping
from app.internal.thermal_model.costs import calculate_intervention_costs_params
from app.models.core import DatasetID, DatasetIDWithTime, MultipleDatasetIDWithTime, dataset_id_t
from app.models.heating_load import EpochAirTempEntry, EpochDHWEntry, EpochHeatingEntry, FabricCostBreakdown, FabricIntervention
from app.routers.heating_load.router import api_router
from app.routers.heating_load.thermal_model import get_thermal_model


@api_router.post("/get-heating-load", tags=["get", "heating"])
async def get_heating_load(params: MultipleDatasetIDWithTime, pool: DatabasePoolDep) -> EpochHeatingEntry:
    """
    Get a previously generated heating load in an EPOCH friendly format.

    Provided with a given heating load dataset (not the dataset of gas data!) and timestamps,
    this will return an EPOCH json.
    Currently just supplies one heating load, but will be extended in future to provide many.

    Parameters
    ----------
    *params*
        Heating Load dataset ID (not a gas dataset ID!) and timestamps you're interested in (probably a whole year)

    Returns
    -------
    epoch_heating_entries
        JSON with HLoad1 and DHWLoad1, oriented by records.
    """

    async def get_single_dataset(
        db_pool: DatabasePoolDep, start_ts: datetime.datetime, end_ts: datetime.datetime, dataset_id: dataset_id_t
    ) -> pd.DataFrame:
        """
        Get a single heating load dataset from the DB.

        A single heating load dataset is uniquely identified by a UUID, and doesn't include DHW.

        Parameters
        ----------
        db_pool
            Database pool containing the heating load dataset
        start_ts
            Earliest part of this dataset to select
        end_ts
            Latest part of thtis dataset to select
        dataset_id
            The specific ID of the single dataset you want.

        Returns
        -------
        pd.DataFrame
            Heating load of start_ts and heating in kWh
        """
        res = await db_pool.fetch(
            """
            SELECT
                start_ts,
                heating
            FROM heating.synthesised
            WHERE
                dataset_id = $1
                AND $2 <= start_ts
                AND end_ts <= $3
            ORDER BY
                start_ts""",
            dataset_id,
            start_ts,
            end_ts,
        )
        heating_df = pd.DataFrame.from_records(cast(RecordMapping, res), index="start_ts", columns=["start_ts", "heating"])
        heating_df.index = pd.to_datetime(heating_df.index)
        return heating_df

    async def get_heating_cost(db_pool: DatabasePoolDep, dataset_id: dataset_id_t) -> tuple[float, list[FabricCostBreakdown]]:
        """
        Get the cost associated with a given heating load.

        This is generally due to fabric interventions.
        We'll try to look up the cost in the database first, and if we can't find it then estimate from a thermal model.
        If we can't find that, return a generic cost.

        Parameters
        ----------
        db_pool
            Database connection pool to DB containing heating loads
        dataset_id
            ID of the heating load you want to look up a cost for

        Returns
        -------
        float
            cost in GBP of associated interventions
        """
        logger = logging.getLogger(__name__)
        metadata = await db_pool.fetchrow(
            """SELECT
                params,
                interventions,
                fabric_cost_total,
                fabric_cost_breakdown
            FROM heating.metadata WHERE dataset_id = $1
            LIMIT 1""",
            dataset_id,
        )

        if (
            metadata is not None
            and metadata.get("fabric_cost_total") is not None
            and metadata.get("fabric_cost_breakdown") is not None
        ):
            # This is the happy path, we got the cost and the breakdown we wanted
            return metadata["fabric_cost_total"], [
                FabricCostBreakdown.model_validate(item) for item in json.loads(metadata["fabric_cost_breakdown"])
            ]

        if (
            metadata is not None
            and metadata.get("fabric_cost_total") is not None
            and metadata.get("fabric_cost_breakdown") is None
            and metadata["fabric_cost_total"] >= 0.01
        ):
            logger.warning(
                f"Did get a total cost but not a fabric cost breakdown for {dataset_id}."
                " Returning just the total and no breakdown."
            )
            # We've store the total cost correctly, but not the breakdown, so just give the total back.
            return metadata["fabric_cost_total"], []

        if metadata is not None and "thermal_model_dataset_id" in metadata["params"]:
            logger.warning(
                f"Got a thermal model dataset_id for {dataset_id} but no pre-calculated breakdown."
                " Returning a newly calculated breakdown."
            )
            # If we have a thermal model, get the heating cost based off the calculated areas.
            # We should store the cost in the metadata anyway, but this is the case where we didn't get it.
            thermal_model_dataset_id = (
                json.loads(metadata["params"])["thermal_model_dataset_id"]
                if isinstance(metadata["params"], str)
                else metadata["params"]["thermal_model_dataset_id"]
            )
            thermal_model = await get_thermal_model(dataset_id=DatasetID(dataset_id=thermal_model_dataset_id), pool=pool)
            return calculate_intervention_costs_params(thermal_model, interventions=metadata["interventions"])
        # However, if we don't have a thermal model then we have no idea of the size,
        # so look the generic cost up in the DB.
        # Note that this drops unknown interventions!
        logger.warning(f"Didn't get a stored cost for {dataset_id} or thermal model; returning a database estimate.")
        res = await db_pool.fetch(
            """
                SELECT
                    intervention,
                    cost
                FROM heating.metadata AS m
                JOIN heating.interventions AS i
                ON
                    i.site_id = m.site_id AND i.intervention = ANY(m.interventions)
                WHERE dataset_id = $1""",
            dataset_id,
        )
        if not res:
            return 0.0, []

        return sum(float(item["cost"]) for item in res), [
            FabricCostBreakdown(name=item["intervention"], area=None, cost=float(item["cost"])) for item in res
        ]

    async with asyncio.TaskGroup() as tg:
        # TODO (2025-08-04 MHJB): this is a classic N+1 query pattern; we should look all of these up
        # in a single query and separate them out on our site.
        all_dfs = {
            dataset_id: tg.create_task(
                get_single_dataset(db_pool=pool, start_ts=params.start_ts, end_ts=params.end_ts, dataset_id=dataset_id)
            )
            for dataset_id in params.dataset_id
        }
        all_costs = {
            dataset_id: tg.create_task(get_heating_cost(db_pool=pool, dataset_id=dataset_id))
            for dataset_id in params.dataset_id
        }
        peak_hload_resp = tg.create_task(
            pool.fetch(
                """
                SELECT dataset_id, peak_hload
                FROM heating.metadata
                WHERE dataset_id = ANY($1::UUID[])""",
                params.dataset_id,
            )
        )

    all_peak_hloads = {dataset_id: peak_hload for dataset_id, peak_hload in peak_hload_resp.result()}  # noqa: C416
    # Do this ordering by dataset ID to make sure that the costs remain associated with the relevant heating load,
    # otherwise we'll get them scrambled in the order that the tasks completed.
    return EpochHeatingEntry(
        timestamps=all_dfs[params.dataset_id[0]].result().index.to_list(),
        data=[
            FabricIntervention(
                cost=all_costs[dataset_id].result()[0],
                reduced_hload=all_dfs[dataset_id].result()["heating"].to_list(),
                peak_hload=all_peak_hloads.get(dataset_id, 0.0) if all_peak_hloads.get(dataset_id) is not None else 0.0,
                cost_breakdown=all_costs[dataset_id].result()[1],
            )
            for dataset_id in params.dataset_id
        ],
    )


@api_router.post("/get-dhw-load", tags=["get", "dhw"])
async def get_dhw_load(params: DatasetIDWithTime, pool: DatabasePoolDep) -> EpochDHWEntry:
    """
    Get a previously generated domestic hot water load in an EPOCH friendly format.

    Provided with a given domestic hot water load dataset and timestamps, this will return an EPOCH json.

    Parameters
    ----------
    params
        Heating Load dataset ID and timestamps you're interested in (probably a whole year)

    Returns
    -------
    epoch_dhw_entry
        A list of timestamps and a list of DHW values.
    """
    res = await pool.fetch(
        """
        SELECT
            start_ts,
            end_ts,
            dhw
        FROM heating.synthesised
        WHERE dataset_id = $1
        AND $2 <= start_ts
        AND end_ts <= $3
        ORDER BY start_ts ASC""",
        params.dataset_id,
        params.start_ts,
        params.end_ts,
    )
    dhw_df = pd.DataFrame.from_records(cast(RecordMapping, res), index="start_ts", columns=["start_ts", "end_ts", "dhw"])

    return EpochDHWEntry(timestamps=dhw_df.index.to_list(), data=dhw_df["dhw"].to_list())


@api_router.post("/get-air-temp", tags=["get", "airtemp"])
async def get_air_temp(params: DatasetIDWithTime, pool: DatabasePoolDep) -> EpochAirTempEntry:
    """
    Get a previously generated air temp series in an EPOCH friendly format.

    Provided with a given air temp dataset and timestamps, this will return an EPOCH json.

    Parameters
    ----------
    params
        Heating Load dataset ID and timestamps you're interested in (probably a whole year)

    Returns
    -------
    epoch_air_temp_entry
        A list of timestamps and a list of air temp values.
    """
    res = await pool.fetch(
        """
        SELECT
            start_ts,
            end_ts,
            air_temperature
        FROM heating.synthesised
        WHERE dataset_id = $1
        AND $2 <= start_ts
        AND end_ts <= $3
        ORDER BY start_ts ASC""",
        params.dataset_id,
        params.start_ts,
        params.end_ts,
    )
    dhw_df = pd.DataFrame.from_records(
        cast(RecordMapping, res), index="start_ts", columns=["start_ts", "end_ts", "air_temperature"]
    )

    return EpochAirTempEntry(timestamps=dhw_df.index.to_list(), data=dhw_df["air_temperature"].to_list())
