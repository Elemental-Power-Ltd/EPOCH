"""
Endpoints for heating load calculations, including heating:dhw splits.

These generally use a combination of gas meters and external weather to perform regression.
"""

import datetime
import json
import logging
import uuid
from enum import Enum
from typing import cast

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from ..dependencies import DatabasePoolDep, HttpClientDep
from ..internal.epl_typing import HHDataFrame, MonthlyDataFrame, RecordMapping, WeatherDataFrame
from ..internal.gas_meters import assign_hh_dhw_poisson, fit_bait_and_model, get_poisson_weights, hh_gas_to_monthly
from ..internal.heating import apply_fabric_interventions, building_adjusted_internal_temperature
from ..models.heating_load import (
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
    logger = logging.getLogger(__name__)

    res = await pool.fetchrow(
        """
        SELECT
            location,
            s.site_id,
            m.reading_type,
            m.fuel_type
        FROM client_meters.metadata AS m
        LEFT JOIN client_info.site_info AS s
        ON s.site_id = m.site_id WHERE dataset_id = $1
        LIMIT 1""",
        params.dataset_id,
    )

    if res is None:
        raise HTTPException(400, f"{params.dataset_id} is not a valid gas meter dataset.")

    location, site_id, reading_type, fuel_type = res
    if location is None:
        raise HTTPException(400, f"Did not find a location for dataset {params.dataset_id}.")

    if fuel_type != "gas":
        raise HTTPException(400, f"Dataset ID {params.dataset_id} is for fuel type {fuel_type}, not gas.")
    res = await pool.fetch(
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

    gas_df = pd.DataFrame.from_records(
        cast(RecordMapping, res), columns=["start_ts", "end_ts", "consumption"], index="start_ts"
    )
    gas_df["start_ts"] = gas_df.index
    if gas_df.empty:
        raise HTTPException(
            400,
            f"Got an empty dataset for {location} between {params.start_ts} and {params.end_ts}",
        )
    if reading_type == "halfhourly":
        logger.info(f"Got reading type {reading_type} for {params.dataset_id} in {location} so resampling.")
        gas_df = hh_gas_to_monthly(HHDataFrame(gas_df))
    elif reading_type in {"automatic", "manual"}:
        logger.info(f"Got reading type {reading_type} for {params.dataset_id} in {location}.")
        gas_df = MonthlyDataFrame(gas_df)
        gas_df["days"] = (gas_df["end_ts"] - gas_df["start_ts"]).dt.total_seconds() / pd.Timedelta(days=1).total_seconds()
    else:
        raise HTTPException(400, f"Unknown reading type {reading_type} for this dataset.")

    if gas_df.shape[0] < 3:
        raise HTTPException(400, f"Dataset covered too little time: {gas_df.index.min()} to {gas_df.index.max()}")

    fit_weather_df = weather_dataset_to_dataframe(
        await get_weather(
            WeatherRequest(location=location, start_ts=gas_df["start_ts"].min(), end_ts=gas_df["end_ts"].max()),
            pool=pool,
            http_client=http_client,
        )
    )

    fitted_coefs = fit_bait_and_model(gas_df, fit_weather_df, apply_bait=params.apply_bait)
    changed_coefs = apply_fabric_interventions(fitted_coefs, params.interventions)
    forecast_weather_df = weather_dataset_to_dataframe(
        await get_weather(
            WeatherRequest(location=location, start_ts=params.start_ts, end_ts=params.end_ts),
            pool=pool,
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
        "interventions": [item.value if isinstance(item, Enum) else str(item) for item in params.interventions],
    }
    async with pool.acquire() as conn, conn.transaction():
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
async def get_intervention_cost(params: InterventionCostRequest, pool: DatabasePoolDep) -> InterventionCostResult:
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
    res = await pool.fetch(
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
