"""
Endpoints for heating load calculations, including heating:dhw splits.

These generally use a combination of gas meters and external weather to perform regression.
"""

import asyncio
import datetime
import json
import uuid

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from ..dependencies import DatabaseDep, DatabasePoolDep, HttpClientDep
from ..internal.epl_typing import HHDataFrame, MonthlyDataFrame, WeatherDataFrame
from ..internal.gas_meters import assign_hh_dhw_poisson, fit_bait_and_model, get_poisson_weights, hh_gas_to_monthly
from ..internal.heating import apply_fabric_interventions, building_adjusted_internal_temperature
from ..models.core import DatasetIDWithTime, MultipleDatasetIDWithTime, dataset_id_t
from ..models.heating_load import (
    EpochAirTempEntry,
    EpochDHWEntry,
    EpochHeatingEntry,
    FabricIntervention,
    HeatingLoadMetadata,
    HeatingLoadRequest,
    InterventionCostRequest,
    InterventionCostResult,
    InterventionEnum,
)
from ..models.weather import WeatherDatasetEntry, WeatherRequest
from .weather import get_weather

router = APIRouter()


def weather_dataset_to_dataframe(records: list[WeatherDatasetEntry]) -> WeatherDataFrame:
    """
    Convert a set of Weather Dataset Entries to a nice pandas dataframe.

    We re-use the endpoint for getting weather in some of these functions, so
    it's useful to convert out of the network JSON format into something friendly.

    Parameters
    ----------
    records
        The data you get from the `get-weather` endpoint

    Returns
    -------
    WeatherDataFrame
        Nice friendly pandas dataframe with datetime index
    """
    return WeatherDataFrame(
        pd.DataFrame.from_records(
            [item.model_dump() for item in records],
            columns=[
                "timestamp",
                "temp",
                "humidity",
                "solarradiation",
                "windspeed",
                "pressure",
            ],
            index="timestamp",
        )
    )


@router.post("/generate-heating-load", tags=["generate", "heating"])
async def generate_heating_load(
    params: HeatingLoadRequest, pool: DatabasePoolDep, http_client: HttpClientDep
) -> HeatingLoadMetadata:
    """Generate a heating load for this specific site, using regression analysis.

    Given a specific dataset, this will look up the associated site and get some weather data.
    Then, it will use the heating degree days over that time period and regress them against the
    actual gas usage.
    The regression will then provide a measure of domestic hot water and heating load for the building,
    which we can reconstruct into a demand curve (which is different to the heating that was actually provided).

    It might be helpful to have called `get-weather` for this location beforehand to make sure the relevant weather
    is cached in the database (otherwise we can do it here, but it might be inconveniently slow).

    Be aware that this will take a few seconds to complete.

    Parameters
    ----------
    *params*
        Dataset (linked to a site), and timestamps you're interested in.
        This dataset ID is the gas dataset you want to use for the calculation, and shouldn't be confused
        with the returned dataset ID that you'll get at the end of this function.
        The timestamps do not select the timestamps of data that you want, but instead the period of time
        that you want to resample to (e.g. you may request a dataset from 2020 and provide timestamps for 2024, and
        you'll get 2024 data out).

    Returns
    -------
    heating_load_metadata
        Some useful information about the heating load we've inserted into the database.
    """
    async with pool.acquire() as conn:
        res = await conn.fetchrow(
            """
            SELECT
                location,
                s.site_id,
                m.fuel_type
            FROM client_meters.metadata AS m
            LEFT JOIN client_info.site_info AS s
            ON s.site_id = m.site_id WHERE dataset_id = $1
            LIMIT 1""",
            params.dataset_id,
        )

        if res is None:
            raise HTTPException(400, f"{params.dataset_id} is not a valid gas meter dataset.")

        location, site_id, fuel_type = res
        if location is None:
            raise HTTPException(400, f"Did not find a location for dataset {params.dataset_id}.")

        if fuel_type != "gas":
            raise HTTPException(400, f"Dataset ID {params.dataset_id} is for fuel type {fuel_type}, not gas.")
        res = await conn.fetch(
            """
            SELECT
                start_ts,
                end_ts,
                consumption_kwh as consumption
            FROM client_meters.gas_meters
            WHERE dataset_id = $1
            ORDER BY start_ts ASC""",
            params.dataset_id,
        )

    gas_df = pd.DataFrame.from_records(res, columns=["start_ts", "end_ts", "consumption"], index="start_ts")
    gas_df["start_ts"] = gas_df.index
    if gas_df.empty:
        raise HTTPException(
            400,
            f"Got an empty dataset for {location} between {params.start_ts} and {params.end_ts}",
        )

    is_monthly = (gas_df["end_ts"] - gas_df["start_ts"]).mean() > pd.Timedelta(days=7)  # type: ignore
    if is_monthly:
        gas_df = MonthlyDataFrame(gas_df)
        gas_df["days"] = (gas_df["end_ts"] - gas_df["start_ts"]).dt.total_seconds() / pd.Timedelta(days=1).total_seconds()
    else:
        gas_df = hh_gas_to_monthly(HHDataFrame(gas_df))

    if gas_df.shape[0] < 3:
        raise HTTPException(400, f"Dataset covered too little time: {gas_df.index.min()} to {gas_df.index.max()}")
    async with pool.acquire() as conn:
        fit_weather_df = weather_dataset_to_dataframe(
            await get_weather(
                WeatherRequest(location=location, start_ts=gas_df["start_ts"].min(), end_ts=gas_df["end_ts"].max()),
                conn=conn,
                http_client=http_client,
            )
        )

        fitted_coefs = fit_bait_and_model(gas_df, fit_weather_df, apply_bait=params.apply_bait)
        changed_coefs = apply_fabric_interventions(fitted_coefs, params.interventions)
        forecast_weather_df = weather_dataset_to_dataframe(
            await get_weather(
                WeatherRequest(location=location, start_ts=params.start_ts, end_ts=params.end_ts),
                conn=conn,
                http_client=http_client,
            )
        )

    # We do this two step resampling to make sure we don't drop the last 23:30 entry if required
    forecast_weather_df = WeatherDataFrame(
        forecast_weather_df.resample(rule=pd.Timedelta(minutes=30)).mean().interpolate(method="time")
    )
    forecast_weather_df = WeatherDataFrame(
        forecast_weather_df.reindex(
            pd.date_range(params.start_ts, params.end_ts, freq=pd.Timedelta(minutes=30), inclusive="left")
        ).ffill()
    )

    forecast_weather_df["bait"] = building_adjusted_internal_temperature(
        forecast_weather_df,
        changed_coefs.solar_gain,
        changed_coefs.wind_chill,
        humidity_discomfort=changed_coefs.humidity_discomfort,
        smoothing=changed_coefs.smoothing,
    )

    heating_df = HHDataFrame(pd.DataFrame(index=forecast_weather_df.index))
    heating_df["air_temperature"] = forecast_weather_df["temp"]
    heating_df["hdd"] = (
        np.maximum(changed_coefs.threshold - forecast_weather_df["bait"], 0) * pd.Timedelta(minutes=30) / pd.Timedelta(hours=24)
    )

    event_size = 1.0  # Change this for future buildings, assumes each DHW event is exactly 1 kWh in size
    poisson_weights = (
        get_poisson_weights(heating_df, "leisure_centre") * changed_coefs.dhw_kwh * params.dhw_fraction / event_size
    )

    flat_heating_kwh = changed_coefs.dhw_kwh * (1.0 - params.dhw_fraction) * pd.Timedelta(minutes=30) / pd.Timedelta(hours=24)
    heating_df = assign_hh_dhw_poisson(
        heating_df,
        poisson_weights,
        dhw_event_size=event_size,
        hdd_kwh=changed_coefs.heating_kwh,
        flat_heating_kwh=flat_heating_kwh,
    )

    metadata = {
        "dataset_id": uuid.uuid4(),
        "site_id": site_id,
        "created_at": datetime.datetime.now(datetime.UTC),
        "params": json.dumps({"source_dataset_id": str(params.dataset_id), **changed_coefs.model_dump()}),
        "interventions": [item.value for item in params.interventions],
    }
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO
                    heating.metadata (
                        dataset_id,
                        site_id,
                        created_at,
                        params)
                VALUES ($1, $2, $3, $4)""",
                metadata["dataset_id"],
                metadata["site_id"],
                metadata["created_at"],
                metadata["params"],
            )

            await conn.executemany(
                """
                INSERT INTO
                    heating.synthesised (
                        dataset_id,
                        start_ts,
                        end_ts,
                        heating,
                        dhw,
                        air_temperature)
                VALUES ($1, $2, $3, $4, $5, $6)""",
                zip(
                    [metadata["dataset_id"] for _ in heating_df.index],
                    heating_df.index,
                    heating_df.index + pd.Timedelta(minutes=30),
                    heating_df["heating"],
                    heating_df["dhw"],
                    heating_df["air_temperature"],
                    strict=True,
                ),
            )
    return HeatingLoadMetadata(**metadata)


@router.post("/get-intervention-cost", tags=["get", "heating"])
async def get_intervention_cost(params: InterventionCostRequest, conn: DatabaseDep) -> InterventionCostResult:
    """
    Get the costs of interventions for a given site.

    This will only return the interventions that are both stored in the database and are in your request.
    For example, if you request ["Loft", "DoubleGlazing"] and we only have ["Loft"] in the database, you'll
    only get a cost and corresponding total for the loft.

    Parameters
    ----------
    params
        A list of interventions (can be the empty list) that you are interested in for a site, and the site id

    Returns
    -------
    Broken-down costs by intervention type (check that they're all there!), and a total cost for those interventions.
    """
    if not params.interventions:
        return InterventionCostResult(
            breakdown={},
            total=0.0,
        )
    res = await conn.fetch(
        """
        SELECT
            intervention,
            cost
        FROM
            heating.interventions
        WHERE
            site_id = $1
        AND intervention = ANY($2::text[])
        """,
        params.site_id,
        tuple(params.interventions),
    )
    return InterventionCostResult(
        breakdown={InterventionEnum(intervention): float(cost) for intervention, cost in res},
        total=sum(float(cost) for _, cost in res),
    )


@router.post("/get-heating-load", tags=["get", "heating"])
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
        async with db_pool.acquire() as conn:
            res = await conn.fetch(
                """
                SELECT
                    start_ts,
                    heating
                FROM heating.synthesised
                WHERE
                    dataset_id = $1
                    AND $2 <= start_ts
                    AND end_ts <= $3""",
                dataset_id,
                start_ts,
                end_ts,
            )
        heating_df = pd.DataFrame.from_records(res, index="start_ts", columns=["start_ts", "heating"])
        heating_df.index = pd.to_datetime(heating_df.index)
        return heating_df

    async def get_heating_cost(db_pool: DatabasePoolDep, dataset_id: dataset_id_t) -> float:
        async with db_pool.acquire() as conn:
            res = await conn.fetch(
                """
                SELECT SUM(cost) AS total_cost
                FROM heating.interventions
                WHERE site_id = (SELECT site_id FROM heating.metadata WHERE dataset_id = $1)
                AND intervention IN (
                SELECT UNNEST((SELECT interventions FROM heating.metadata WHERE dataset_id = $1))
                )""",
                dataset_id,
            )
            return res[0]["total_cost"] or 0

    async with asyncio.TaskGroup() as tg:
        all_dfs = [
            tg.create_task(
                get_single_dataset(db_pool=pool, start_ts=params.start_ts, end_ts=params.end_ts, dataset_id=dataset_id)
            )
            for dataset_id in params.dataset_id
        ]
        all_costs = [tg.create_task(get_heating_cost(db_pool=pool, dataset_id=dataset_id)) for dataset_id in params.dataset_id]

    return EpochHeatingEntry(
        timestamps=all_dfs[0].result().index.tolist(),
        data=[
            FabricIntervention(cost=cost.result(), reduced_hload=df.result()["heating"].to_list())
            for cost, df in zip(all_costs, all_dfs, strict=False)
        ],
    )


@router.post("/get-dhw-load", tags=["get", "dhw"])
async def get_dhw_load(params: DatasetIDWithTime, conn: DatabasePoolDep) -> EpochDHWEntry:
    """
    Get a previously generated domestic hot water load in an EPOCH friendly format.

    Provided with a given domestic hot water load dataset and timestamps, this will return an EPOCH json.

    Parameters
    ----------
    *params*
        Heating Load dataset ID and timestamps you're interested in (probably a whole year)

    Returns
    -------
    epoch_dhw_entry
        A list of timestamps and a list of DHW values.
    """
    res = await conn.fetch(
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

    return EpochDHWEntry(timestamps=dhw_df.index.tolist(), data=dhw_df["dhw"].to_list())


@router.post("/get-air-temp", tags=["get", "airtemp"])
async def get_air_temp(params: DatasetIDWithTime, conn: DatabasePoolDep) -> EpochAirTempEntry:
    """
    Get a previously generated air temp series in an EPOCH friendly format.

    Provided with a given air temp dataset and timestamps, this will return an EPOCH json.

    Parameters
    ----------
    *params*
        Heating Load dataset ID and timestamps you're interested in (probably a whole year)

    Returns
    -------
    epoch_air_temp_entry
        A list of timestamps and a list of air temp values.
    """
    res = await conn.fetch(
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

    return EpochAirTempEntry(timestamps=dhw_df.index.tolist(), data=dhw_df["air_temperature"].to_list())
