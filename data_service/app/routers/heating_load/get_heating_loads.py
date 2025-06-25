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

import pandas as pd

from ...dependencies import DatabasePoolDep
from ...models.core import DatasetID, DatasetIDWithTime, MultipleDatasetIDWithTime, dataset_id_t
from ...models.heating_load import EpochAirTempEntry, EpochDHWEntry, EpochHeatingEntry, FabricIntervention
from .costs import get_heating_cost_thermal_model
from .router import api_router
from .thermal_model import get_thermal_model


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
        res = await pool.fetch(
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
        heating_df = pd.DataFrame.from_records(res, index="start_ts", columns=["start_ts", "heating"])
        heating_df.index = pd.to_datetime(heating_df.index)
        return heating_df

    async def get_heating_cost(db_pool: DatabasePoolDep, dataset_id: dataset_id_t) -> float:
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
        cost in GBP of associated interventions
        """
        metadata = await db_pool.fetchrow(
            """SELECT params, interventions FROM heating.metadata WHERE dataset_id = $1""", dataset_id
        )
        if metadata is not None and "cost" in metadata["params"]:
            # If we've pre-calculated the cost, simply return that
            return float(metadata["params"]["cost"])
        if metadata is not None and "thermal_model_dataset_id" in metadata["params"]:
            # If we have a thermal model, get the heating cost based off the calculated areas.
            if isinstance(metadata["params"], str):
                # This is horrible, but the params section could legitimately have been passed as a string
                # so try to read it as JSON
                thermal_model_dataset_id = json.loads(metadata["params"])["thermal_model_dataset_id"]
            else:
                thermal_model_dataset_id = metadata["params"]["thermal_model_dataset_id"]
            model = await get_thermal_model(dataset_id=DatasetID(dataset_id=thermal_model_dataset_id), pool=pool)
            return await get_heating_cost_thermal_model(model, interventions=metadata["interventions"], pool=db_pool)
        else:
            # However, if we don't have a thermal model then we have no idea of the size,
            # so look the generic cost up in the DB.
            res = await db_pool.fetchval(
                """
                SELECT
                    SUM(cost)
                FROM heating.metadata AS m
                JOIN heating.interventions AS i
                ON
                    i.site_id = m.site_id AND i.intervention = ANY(m.interventions)
                WHERE dataset_id = $1""",
                dataset_id,
            )
            if res is None:
                return 0.0
        return float(res)

    async with asyncio.TaskGroup() as tg:
        all_dfs = [
            tg.create_task(
                get_single_dataset(db_pool=pool, start_ts=params.start_ts, end_ts=params.end_ts, dataset_id=dataset_id)
            )
            for dataset_id in params.dataset_id
        ]
        all_costs = [tg.create_task(get_heating_cost(db_pool=pool, dataset_id=dataset_id)) for dataset_id in params.dataset_id]

    return EpochHeatingEntry(
        timestamps=all_dfs[0].result().index.to_list(),
        data=[
            FabricIntervention(cost=cost.result(), reduced_hload=df.result()["heating"].to_list())
            for cost, df in zip(all_costs, all_dfs, strict=False)
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
    dhw_df = pd.DataFrame.from_records(res, index="start_ts", columns=["start_ts", "end_ts", "dhw"])

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
    dhw_df = pd.DataFrame.from_records(res, index="start_ts", columns=["start_ts", "end_ts", "air_temperature"])

    return EpochAirTempEntry(timestamps=dhw_df.index.to_list(), data=dhw_df["air_temperature"].to_list())
