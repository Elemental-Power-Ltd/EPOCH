"""
Heating load generation API endpoints.

This module provides FastAPI endpoints for generating building heating load profiles using
different methodologies:
- Regression-based approach that analyzes historical gas consumption data
- Physics-based thermal modeling

Both methods can simulate the effects of building fabric interventions on heating demand
and generate half-hourly heating and domestic hot water (DHW) load profiles that can be
stored in a database for further analysis.
"""

import datetime
import itertools
import json
import uuid

import numpy as np
import pandas as pd
from fastapi import HTTPException

from ...dependencies import DatabasePoolDep, HttpClientDep
from ...internal.epl_typing import HHDataFrame, MonthlyDataFrame, WeatherDataFrame
from ...internal.gas_meters import assign_hh_dhw_poisson, fit_bait_and_model, get_poisson_weights, hh_gas_to_monthly
from ...internal.thermal_model import apply_fabric_interventions, building_adjusted_internal_temperature
from ...internal.thermal_model.bait import weather_dataset_to_dataframe
from ...internal.thermal_model.fitting import simulate_parameters
from ...models.core import DatasetID, SiteID
from ...models.heating_load import (
    HeatingLoadMetadata,
    HeatingLoadModelEnum,
    HeatingLoadRequest,
)
from ...models.weather import WeatherRequest
from ..client_data import get_location
from ..weather import get_weather
from .router import api_router
from .thermal_model import get_thermal_model


@api_router.post("/generate-heating-load", tags=["generate", "heating"])
async def generate_heating_load(
    params: HeatingLoadRequest,
    pool: DatabasePoolDep,
    http_client: HttpClientDep,
) -> HeatingLoadMetadata:
    """
    Generate a heating load based on the model type specified in an argument.

    Parameters
    ----------
    params
        A HeatingLoadRequest where we switch on the params.model_type
    pool
        Database pool used by the underlying generators
    http_client
        HTTP client with connection pools
    Returns
    -------
    HeatingLoadMetadata
        Metadata about the heating load we just put into the database.
    """
    match params.model_type:
        case HeatingLoadModelEnum.Regression:
            return await generate_heating_load_regression(params=params, pool=pool, http_client=http_client)
        case HeatingLoadModelEnum.ThermalModel:
            return await generate_thermal_model_heating_load(pool=pool, http_client=http_client, params=params)


@api_router.post("/generate-heating-load-regression", tags=["generate", "heating"])
async def generate_heating_load_regression(
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
        "dataset_id": params.final_uuid,
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
                        params,
                        interventions
                        )
                VALUES ($1, $2, $3, $4, $5)""",
                metadata["dataset_id"],
                metadata["site_id"],
                metadata["created_at"],
                metadata["params"],
                metadata["interventions"],
            )

            await conn.copy_records_to_table(
                schema_name="heating",
                table_name="synthesised",
                columns=["dataset_id", "start_ts", "end_ts", "heating", "dhw", "air_temperature"],
                records=zip(
                    itertools.repeat(metadata["dataset_id"], len(heating_df.index)),
                    heating_df.index,
                    heating_df.index + pd.Timedelta(minutes=30),
                    heating_df["heating"],
                    heating_df["dhw"],
                    heating_df["air_temperature"],
                    strict=True,
                ),
            )
    return HeatingLoadMetadata(**metadata)


@api_router.post("/generate-thermal-model-heating-load")
async def generate_thermal_model_heating_load(
    pool: DatabasePoolDep, http_client: HttpClientDep, params: HeatingLoadRequest
) -> HeatingLoadMetadata:
    """
    Generate a heating load using the thermal model.

    Parameters
    ----------
    pool
        Shared database pool for the PostgreSQL database, which should contain weather and thermal models
    http_client
        HTTP Client connection pool for the access to 3rd party APIs
    site_params
        The Site ID you want to model, as well as the start and end timestamps you want a heating load for
    thermal_model_dataset_id
        The thermal model you want to use for this process
    interventions
        The interventions you wish to apply to this site, e.g. Cladding or DoubleGlazing. Defaults to an empty list
        (no interventions).

    Returns
    -------
    DatasetEntry
        ID of the generated thermal model dataset.
    """
    if params.thermal_model_dataset_id is None:
        raise HTTPException(400, "Must have provided a thermal model dataset ID to generat a heating load")
    thermal_model = await get_thermal_model(pool, dataset_id=DatasetID(dataset_id=params.thermal_model_dataset_id))

    async with pool.acquire() as conn:
        if params.site_id is None:
            raise HTTPException(400, "Must have provided a site ID for thermal model dataset fitting")
        location = await get_location(SiteID(site_id=params.site_id), conn)
        weather_records = await get_weather(
            weather_request=WeatherRequest(location=location, start_ts=params.start_ts, end_ts=params.end_ts),
            conn=conn,
            http_client=http_client,
        )
        if weather_records is None:
            raise HTTPException(400, f"Failed to get a weather dataset for {params}.")
        weather_df = pd.DataFrame.from_records([item.model_dump() for item in weather_records], index="timestamp")
        weather_df["timestamp"] = weather_df.index
    elec_df = None
    heating_load_df = simulate_parameters(
        scale_factor=thermal_model.scale_factor,
        ach=thermal_model.ach,
        u_value=thermal_model.u_value,
        boiler_power=thermal_model.boiler_power,
        setpoint=thermal_model.setpoint,
        elec_df=elec_df,
        start_ts=params.start_ts,
        end_ts=params.end_ts,
        weather_df=weather_df,
        interventions=params.interventions,
    )
    # We simulated at a much lower timestep than we want for EPOCH, so
    # regroup it here by adding up the heating demands
    hh_heating_load_df = heating_load_df.resample(pd.Timedelta(minutes=30)).sum(numeric_only=True)
    # ... but we don't want to sum temperatures
    hh_heating_load_df["external_temperatures"] = (
        heating_load_df["external_temperatures"].resample(pd.Timedelta(minutes=30)).mean(numeric_only=True)
    )
    hh_heating_load_df["start_ts"] = hh_heating_load_df.index
    hh_heating_load_df["end_ts"] = hh_heating_load_df.index + pd.Timedelta(minutes=30)

    dataset_id = params.final_uuid
    created_at = datetime.datetime.now(datetime.UTC)

    # TODO (2025-02-02 MHJB): improve DHW load here
    DHW_EVENT_SIZE = 1.0
    poisson_weights = get_poisson_weights(HHDataFrame(hh_heating_load_df)) * thermal_model.dhw_usage
    dhw_load = np.random.default_rng().poisson(poisson_weights) * DHW_EVENT_SIZE
    await pool.execute(
        """
        INSERT INTO heating.metadata
        (dataset_id, site_id, created_at, params, interventions)
        VALUES ($1, $2, $3, $4, $5)""",
        dataset_id,
        params.site_id,
        created_at,
        json.dumps({"thermal_model_dataset_id": str(params.thermal_model_dataset_id)}),
        params.interventions,
    )

    await pool.copy_records_to_table(
        schema_name="heating",
        table_name="synthesised",
        columns=["dataset_id", "start_ts", "end_ts", "heating", "dhw", "air_temperature"],
        records=zip(
            itertools.repeat(dataset_id, len(hh_heating_load_df)),
            hh_heating_load_df.start_ts,
            hh_heating_load_df.end_ts,
            hh_heating_load_df.heating_usage,
            dhw_load,
            hh_heating_load_df.external_temperatures,
            strict=True,
        ),
    )

    return HeatingLoadMetadata(
        dataset_id=dataset_id,
        site_id=params.site_id,
        created_at=created_at,
        params=json.dumps({"thermal_model_dataset_id": str(params.thermal_model_dataset_id)}),
        interventions=params.interventions,
    )
