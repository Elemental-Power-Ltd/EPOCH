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
import logging
import operator
from typing import cast

import numpy as np
import pandas as pd
from fastapi import HTTPException

from ...dependencies import DatabasePoolDep, HttpClientDep
from ...internal.epl_typing import HHDataFrame, MonthlyDataFrame, WeatherDataFrame
from ...internal.gas_meters import assign_hh_dhw_poisson, fit_bait_and_model, get_poisson_weights, hh_gas_to_monthly
from ...internal.site_manager import list_thermal_models
from ...internal.site_manager.bundles import file_self_with_bundle
from ...internal.thermal_model import apply_fabric_interventions, building_adjusted_internal_temperature
from ...internal.thermal_model.bait import weather_dataset_to_dataframe
from ...internal.thermal_model.costs import calculate_THIRD_PARTY_intervention_costs
from ...internal.thermal_model.fitting import simulate_parameters
from ...models.core import DatasetID, DatasetTypeEnum, SiteID, dataset_id_t, site_id_t
from ...internal.utils.uuid import uuid7
from ...models.heating_load import HeatingLoadMetadata, HeatingLoadModelEnum, HeatingLoadRequest
from ...models.weather import BaitAndModelCoefs, WeatherRequest
from ..client_data import get_location
from ..weather import get_weather
from .router import api_router
from .thermal_model import get_thermal_model


async def get_site_id_for_heating_load(dataset_id: dataset_id_t, pool: DatabasePoolDep) -> site_id_t:
    """
    Get the site ID associated with a given gas meter dataset.

    Parameters
    ----------
    dataset_id
        Gas meter dataset to look up
    pool
        Database to look up in

    Returns
    -------
    site_id_t
        Site ID associated with those meter readings

    Raises
    ------
    ValueError
        If site ID not found or is None
    """
    site_id = await pool.fetchval(
        "SELECT site_id FROM client_meters.metadata WHERE dataset_id = $1 LIMIT 1",
        dataset_id,
    )
    if site_id is None:
        raise ValueError(f"Could not find a site ID for {dataset_id}")
    return cast(site_id_t, site_id)


async def select_regression_or_thermal(params: HeatingLoadRequest, pool: DatabasePoolDep) -> HeatingLoadRequest:
    """
    Select whether the regression mode or the thermal model is best for this site.

    This will attempt to use the thermal model if there is a model stored in the database above a given quality
    threshold, or fall back to regression mode otherwise.

    Parameters
    ----------
    params
        A HeatingLoadRequest with the HeatingLoadModelEnum set to Auto.
        This may be modified as we go along, since we'll need to fill it in for the thermal model
    pool
        Connection pool to a database, potentially with thermal models in.

    Returns
    -------
    HeatingLoadRequest
        The new request which we should send to generate a heating load, filled with sensible defaults.
    """
    logger = logging.getLogger(__name__)
    if params.site_id is None:
        # Old versions of the HeatingLoadRequest only needed a dataset ID for the source gas data,
        # and not the site ID.
        # If we got no site ID, look it up here.
        site_id = await get_site_id_for_heating_load(params.dataset_id, pool)
    else:
        site_id = params.site_id

    # This function is structured slightly backwards, as it's cleaner than using a try... except
    # We'll perform a number of processing steps to find if we have any thermal models, but
    # if we don't, we'll return this Regression request via a series of early exits
    # Future refactoring for the logic appreciated if you think it needs tidying.
    default_regression_request = HeatingLoadRequest(
        dataset_id=params.dataset_id,
        start_ts=params.start_ts,
        end_ts=params.end_ts,
        interventions=params.interventions,
        apply_bait=True,
        model_type=HeatingLoadModelEnum.Regression,
        site_id=site_id,
        thermal_model_dataset_id=None,
        surveyed_sizes=params.surveyed_sizes,
        bundle_metadata=params.bundle_metadata,
    )

    available_thermal_model_ids = await list_thermal_models(site_id=SiteID(site_id=site_id), pool=pool)

    if not available_thermal_model_ids:
        logger.debug("Using regression instead of thermal as we didn't get any thermal model metadata.")
        return default_regression_request

    all_thermal_models = [
        await get_thermal_model(pool, dataset_id=DatasetID(dataset_id=item.dataset_id)) for item in available_thermal_model_ids
    ]

    if not all_thermal_models:
        logger.debug("Using regression instead of thermal as we didn't get any thermal models with valid parameters.")
        return default_regression_request

    paired = zip(
        all_thermal_models,
        (item.created_at for item in available_thermal_model_ids),
        (item.dataset_id for item in available_thermal_model_ids),
        strict=False,
    )
    # This is the quality bar for models in the database; we'll pick the most recent model above this quality threshold
    # if there is one
    R2_THRESH = 0.8
    above_thresh = [item for item in paired if item[0].r2_score is not None and item[0].r2_score > R2_THRESH]

    if not above_thresh:
        all_r2s = [item[0].r2_score for item in paired if item[0].r2_score is not None]
        if all_r2s:
            best_r2 = max(all_r2s)
        else:
            best_r2 = None
        logger.debug(
            "Using regression instead of thermal as we didn't get a thermal model above the threshold.",
            extra={"best_r2": best_r2},
        )
        return default_regression_request

    # Get the entry with the maximum created_at timestamp.
    most_recent_id = max(above_thresh, key=operator.itemgetter(1))[2]
    return HeatingLoadRequest(
        dataset_id=params.dataset_id,
        start_ts=params.start_ts,
        end_ts=params.end_ts,
        interventions=params.interventions,
        model_type=HeatingLoadModelEnum.ThermalModel,
        site_id=site_id,
        thermal_model_dataset_id=most_recent_id,
        surveyed_sizes=params.surveyed_sizes,
        bundle_metadata=params.bundle_metadata,
    )


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
    logger = logging.getLogger(__name__)
    match params.model_type:
        case HeatingLoadModelEnum.Auto:
            # This function will look up if we have a good enough thermal model, and create
            # a new heating load request, then all that.
            new_heatload_params = await select_regression_or_thermal(params=params, pool=pool)
            logger.info(f"Generating heat load for {new_heatload_params.site_id} with {new_heatload_params.model_type}.")
            return await generate_heating_load(new_heatload_params, pool, http_client)
        case HeatingLoadModelEnum.Regression:
            return await generate_heating_load_regression(params=params, pool=pool, http_client=http_client)
        case HeatingLoadModelEnum.ThermalModel:
            return await generate_thermal_model_heating_load(pool=pool, http_client=http_client, params=params)


async def generate_heating_load_regression_impl(
    params: HeatingLoadRequest, pool: DatabasePoolDep, http_client: HttpClientDep
) -> tuple[HHDataFrame, BaitAndModelCoefs]:
    """
    Generate a heating load by regression.

    Parameters
    ----------
    params
        Heating load request including fabric interventions and savings
    pool
        Database connection pool to grab gas meter data from
    http_client
        HTTP connection pool to get weather data

    Returns
    -------
    HHDataFrame, BaitAndModelCoefs
        The half hourly heating load data and the associated parameters from the regression.
    """
    fuel_res = await pool.fetchrow(
        """
        SELECT
            location,
            m.fuel_type
        FROM client_meters.metadata AS m
        LEFT JOIN client_info.site_info AS s
        ON s.site_id = m.site_id WHERE dataset_id = $1
        LIMIT 1""",
        params.dataset_id,
    )

    if fuel_res is None:
        raise HTTPException(400, f"{params.dataset_id} is not a valid gas meter dataset.")

    location, fuel_type = fuel_res
    if location is None:
        raise HTTPException(400, f"Did not find a location for dataset {params.dataset_id}.")

    if fuel_type != "gas":
        raise HTTPException(400, f"Dataset ID {params.dataset_id} is for fuel type {fuel_type}, not gas.")
    gas_res = await pool.fetch(
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
    gas_df = pd.DataFrame.from_records(gas_res, columns=["start_ts", "end_ts", "consumption"], index="start_ts")
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
        changed_coefs = apply_fabric_interventions(fitted_coefs, params.interventions, params.savings_fraction)
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
    return heating_df, changed_coefs


@api_router.post("/generate-heating-load-regression", tags=["generate", "heating"])
async def generate_heating_load_regression(
    params: HeatingLoadRequest, pool: DatabasePoolDep, http_client: HttpClientDep
) -> HeatingLoadMetadata:
    """
    Generate a heating load for this specific site, using regression analysis.

    Given a specific dataset, this will look up the associated site and get some weather data.
    Then, it will use the heating degree days over that time period and regress them against the
    actual gas usage.
    The regression will then provide a measure of domestic hot water and heating load for the building,
    which we can reconstruct into a demand curve (which is different to the heating that was actually provided).

    It might be helpful to have called `get-weather` for this location beforehand to make sure the relevant weather
    is cached in the database (otherwise we can do it here, but it might be inconveniently slow).

    Be aware that this will take a few seconds to complete.

    If you've surveyed the site, this will estimate the costs and savings due to your proposed fabric interventions.

    Parameters
    ----------
    params
        Dataset (linked to a site), and timestamps you're interested in.
        This dataset ID is the gas dataset you want to use for the calculation, and shouldn't be confused
        with the returned dataset ID that you'll get at the end of this function.
        The timestamps do not select the timestamps of data that you want, but instead the period of time
        that you want to resample to (e.g. you may request a dataset from 2020 and provide timestamps for 2024, and
        you'll get 2024 data out).
    pool
        Database connection pool to the DB that you'll read / write from
    http_client
        HTTP connection pool for weather data requests
    surveyed_sizes
        Surveyed sizes of the building used to calculate costs.

    Returns
    -------
    heating_load_metadata
        Some useful information about the heating load we've inserted into the database.
    """
    if params.site_id is None:
        site_id = await get_site_id_for_heating_load(params.dataset_id, pool)
    else:
        site_id = params.site_id

    heating_df, changed_coefs = await generate_heating_load_regression_impl(params, pool, http_client)

    metadata_params = {"source_dataset_id": str(params.dataset_id), **changed_coefs.model_dump()}
    if params.surveyed_sizes is not None:
        cost = calculate_THIRD_PARTY_intervention_costs(params.surveyed_sizes, interventions=params.interventions)
        metadata_params["cost"] = cost

    metadata = HeatingLoadMetadata(
        dataset_id=params.bundle_metadata.dataset_id if params.bundle_metadata is not None else uuid7(),
        site_id=site_id,
        created_at=datetime.datetime.now(datetime.UTC),
        params=json.dumps(metadata_params),
        interventions=params.interventions,
    )

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
                metadata.dataset_id,
                metadata.site_id,
                metadata.created_at,
                json.dumps(metadata.params),
                metadata.interventions,
            )

            await conn.copy_records_to_table(
                schema_name="heating",
                table_name="synthesised",
                columns=["dataset_id", "start_ts", "end_ts", "heating", "dhw", "air_temperature"],
                records=zip(
                    itertools.repeat(metadata.dataset_id, len(heating_df.index)),
                    heating_df.index,
                    heating_df.index + pd.Timedelta(minutes=30),
                    heating_df["heating"],
                    heating_df["dhw"],
                    heating_df["air_temperature"],
                    strict=True,
                ),
            )
            if params.bundle_metadata is not None:
                await file_self_with_bundle(conn, bundle_metadata=params.bundle_metadata)
    logger = logging.getLogger(__name__)
    logger.info(f"Regression heat load generation {metadata.dataset_id} completed.")
    return metadata


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
        raise HTTPException(400, "Must have provided a thermal model dataset ID to generate a heating load")
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
        dhw_usage=thermal_model.dhw_usage,
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

    metadata = HeatingLoadMetadata(
        dataset_id=params.bundle_metadata.dataset_id if params.bundle_metadata is not None else uuid7(),
        site_id=params.site_id,
        created_at=datetime.datetime.now(datetime.UTC),
        params=json.dumps({"thermal_model_dataset_id": str(params.thermal_model_dataset_id)}),
        interventions=params.interventions,
    )

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO heating.metadata
                (dataset_id, site_id, created_at, params, interventions)
                VALUES ($1, $2, $3, $4, $5)""",
                metadata.dataset_id,
                metadata.site_id,
                metadata.created_at,
                json.dumps(metadata.params),
                metadata.interventions,
            )

            await conn.copy_records_to_table(
                schema_name="heating",
                table_name="synthesised",
                columns=["dataset_id", "start_ts", "end_ts", "heating", "dhw", "air_temperature"],
                records=zip(
                    itertools.repeat(metadata.dataset_id, len(hh_heating_load_df)),
                    hh_heating_load_df.start_ts,
                    hh_heating_load_df.end_ts,
                    hh_heating_load_df.heating_usage,
                    hh_heating_load_df.dhw,
                    hh_heating_load_df.external_temperatures,
                    strict=True,
                ),
            )
            if params.bundle_metadata is not None:
                await file_self_with_bundle(conn, bundle_metadata=params.bundle_metadata)

                # We also file the thermal model in the database as part of this bundle
                thermal_bundle_metadata = params.bundle_metadata.model_copy()
                thermal_bundle_metadata.dataset_type = DatasetTypeEnum.ThermalModel
                thermal_bundle_metadata.dataset_id = params.thermal_model_dataset_id
                await file_self_with_bundle(conn, bundle_metadata=thermal_bundle_metadata)
    logger = logging.getLogger(__name__)
    logger.info(f"Thermal Model heat load generation {metadata.dataset_id} completed.")
    return metadata
