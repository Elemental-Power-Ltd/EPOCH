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

import asyncio
import datetime
import itertools
import json
import logging
import operator
from typing import Any, cast

import numpy as np
import pandas as pd
from app.dependencies import DatabasePoolDep, HttpClientDep
from app.internal.epl_typing import HHDataFrame, NonHHDataFrame, RecordMapping, WeatherDataFrame, db_pool_t
from app.internal.gas_meters import assign_hh_dhw_poisson, fit_bait_and_model, get_poisson_weights, hh_gas_to_monthly
from app.internal.site_manager.bundles import file_self_with_bundle
from app.internal.site_manager.dataset_lists import list_thermal_models
from app.internal.thermal_model import apply_fabric_interventions, building_adjusted_internal_temperature
from app.internal.thermal_model.bait import weather_dataset_to_dataframe
from app.internal.thermal_model.costs import calculate_intervention_costs_params, calculate_THIRD_PARTY_intervention_costs
from app.internal.thermal_model.fitting import simulate_parameters
from app.internal.thermal_model.phpp.interventions import THIRD_PARTY_INTERVENTIONS
from app.internal.thermal_model.phpp.parse_phpp import (
    apply_phpp_intervention,
    phpp_fabric_intervention_cost,
    phpp_total_heat_loss,
)
from app.internal.utils.uuid import uuid7
from app.models.core import DatasetID, DatasetTypeEnum, SiteID, dataset_id_t, site_id_t
from app.models.heating_load import (
    HeatingLoadMetadata,
    HeatingLoadModelEnum,
    HeatingLoadRequest,
    InterventionEnum,
    IsInterventionFeasible,
)
from app.models.weather import BaitAndModelCoefs, WeatherRequest
from app.routers.heating_load.phpp import get_phpp_dataframe_from_database, list_phpp
from app.routers.heating_load.router import api_router
from app.routers.heating_load.thermal_model import get_thermal_model
from app.routers.weather import get_weather
from fastapi import HTTPException


def apply_intervention_count_cost_offset(total_cost: float, interventions: list[Any]) -> float:
    """
    Apply a small offset to the total cost of fabric interventions based on the number of interventions.

    This breaks the symmetry between do-nothing interventions.
    If a site already has triple glazing, the "double glazing" intervention might do nothing and cost nothing.
    In that case, the optimiser will pick it and it'll confuse end user.
    Instead, add a 1p cost per intervention.

    Parameters
    ----------
    total_cost
        Total cost of interventions in £
    interventions
        Interventions you want to try to apply

    Returns
    -------
    float
        A new, slightly higher, total cost
    """
    COST_PER_INTERVENTION = 0.01
    return total_cost + COST_PER_INTERVENTION * len(interventions)


async def get_site_id_for_heating_load(dataset_id: dataset_id_t, pool: db_pool_t) -> site_id_t:
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


async def select_regression_thermal_phpp(params: HeatingLoadRequest, pool: DatabasePoolDep) -> HeatingLoadRequest:
    """
    Select whether the regression mode, the thermal model or a PHPP is best for this site.

    This will first attempt to use a PHPP if one exists.
    Then, if no PHPP exists, but a good quality thermal model does, it'll use that.
    Finally, it will fall back to a genericised regression.

    Parameters
    ----------
    params
        A HeatingLoadRequest with the HeatingLoadModelEnum set to Auto.
        This may be modified as we go along, since we'll need to fill it in for the thermal model or PHPP
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
        structure_id=None,
        surveyed_sizes=params.surveyed_sizes,
        bundle_metadata=params.bundle_metadata,
    )

    # First, check if we've got a good enough PHPP, and if we do, return
    # a request suitable for the PHPP calculation
    available_phpps = await list_phpp(pool=pool, site_id=SiteID(site_id=site_id))
    if available_phpps:
        most_recent = max(available_phpps, key=lambda md: md.created_at)
        return HeatingLoadRequest(
            dataset_id=params.dataset_id,
            start_ts=params.start_ts,
            end_ts=params.end_ts,
            interventions=params.interventions,
            apply_bait=True,
            model_type=HeatingLoadModelEnum.PHPP,
            site_id=site_id,
            structure_id=most_recent.structure_id,
            surveyed_sizes=params.surveyed_sizes,
            savings_fraction=0.0,  # These are specifically overwritten
            bundle_metadata=params.bundle_metadata,  # Make sure we pass the bundle metadata along!
        )

    available_thermal_model_ids = await list_thermal_models(site_id=site_id, pool=pool)

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
        strict=True,
    )
    # This is the quality bar for models in the database; we'll pick the most recent model above this quality threshold
    # if there is one
    R2_THRESH = 0.8
    above_thresh = [item for item in paired if item[0].r2_score is not None and item[0].r2_score > R2_THRESH]

    if not above_thresh:
        all_r2s = [item[0].r2_score for item in paired if item[0].r2_score is not None]
        best_r2 = max(all_r2s) if all_r2s else None
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
        structure_id=most_recent_id,
        surveyed_sizes=params.surveyed_sizes,
        bundle_metadata=params.bundle_metadata,
    )


@api_router.post("/add-feasible-interventions", tags=["phpp", "heating"])
async def add_feasible_interventions(pool: DatabasePoolDep, site_id: SiteID, interventions: list[str]) -> list[list[str]]:
    """
    Add a set of feasible interventions for a given site to the database.

    This overwrites any previous feasible set of interventions.
    It will be used by `generate-all` to generate heating loads.
    Note that there are 2**N interventions generated, so a large list will be slow.

    Parameters
    ----------
    site_id
        ID of the site to add interventions for

    interventions
        Stringified fabric interventions to add to the database,

    Returns
    -------
    list[list[str]]
        List of combinations of all possible fabric interventions that we'll simulate

    Raises
    ------
    HTTPException
        If the interventions aren't valid.
    """
    for item in interventions:
        if item not in THIRD_PARTY_INTERVENTIONS:
            raise HTTPException(422, detail=f"Bad fabric intervention: {item}")

    # Delete the previous feasible interventions to allow us to overwrite these
    await pool.execute("DELETE FROM heating.feasible_interventions WHERE site_id = $1", site_id.site_id)
    await pool.copy_records_to_table(
        table_name="feasible_interventions",
        schema_name="heating",
        columns=["site_id", "intervention_name"],
        records=[(site_id.site_id, intervention) for intervention in interventions],
    )

    return [list(c) for i in range(len(interventions) + 1) for c in itertools.combinations(interventions, i)]


@api_router.post("/list-feasible-interventions", tags=["phpp", "heating", "list"])
async def list_feasible_interventions(pool: DatabasePoolDep, site_id: SiteID) -> list[IsInterventionFeasible]:
    """
    List all the feasible interventions for a given site to the database.

    This lists individual interventions, not all combinations.
    It will be used by `generate-all` to generate heating loads.
    Note that there are 2**N interventions generated, so a large list will be slow.

    Parameters
    ----------
    site_id
        ID of the site to list interventions for

    Returns
    -------
    list[IsInterventionFeasible]
        List of all possible fabric interventions: ones marked True we'll simulate, ones marked False we'll ignore.
    """
    res = await pool.fetchval(
        "SELECT ARRAY_AGG(intervention_name) FROM heating.feasible_interventions WHERE site_id = $1", site_id.site_id
    )
    feasible_interventions = set(res or [])

    # We don't want some of these in our modelling: leave them in there
    # in case someone definitely wants them, but hide them from the list here.
    THIRD_PARTY_interventions = {key for key, value in THIRD_PARTY_INTERVENTIONS.items() if value["u_value"] is not None}
    unfeasible_interventions = THIRD_PARTY_interventions - feasible_interventions

    all_interventions = [IsInterventionFeasible(name=item, is_feasible=True) for item in feasible_interventions] + [
        IsInterventionFeasible(name=item, is_feasible=False) for item in unfeasible_interventions
    ]
    return sorted(all_interventions, key=lambda x: x.name)


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
            # This function will look up if we have a good enough PHPP or thermal model, and create
            # a new heating load request, then all that.
            new_heatload_params = await select_regression_thermal_phpp(params=params, pool=pool)
            logger.info(f"Generating heat load for {new_heatload_params.site_id} with {new_heatload_params.model_type}.")
            return await generate_heating_load(new_heatload_params, pool, http_client)
        case HeatingLoadModelEnum.Regression:
            return await generate_heating_load_regression(params=params, pool=pool, http_client=http_client)
        case HeatingLoadModelEnum.ThermalModel:
            return await generate_thermal_model_heating_load(pool=pool, http_client=http_client, params=params)
        case HeatingLoadModelEnum.PHPP:
            return await generate_heating_load_phpp(pool=pool, http_client=http_client, params=params)


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
            coordinates,
            m.fuel_type
        FROM client_meters.metadata AS m
        LEFT JOIN client_info.site_info AS s
        ON s.site_id = m.site_id WHERE dataset_id = $1
        LIMIT 1""",
        params.dataset_id,
    )

    if fuel_res is None:
        raise HTTPException(400, f"{params.dataset_id} is not a valid gas meter dataset.")

    location, (latitude, longitude), fuel_type = fuel_res
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
    gas_df = pd.DataFrame.from_records(
        cast(RecordMapping, gas_res), columns=["start_ts", "end_ts", "consumption"], index="start_ts"
    )
    gas_df["start_ts"] = gas_df.index
    if gas_df.empty:
        raise HTTPException(
            400,
            f"Got an empty dataset for {location} between {params.start_ts} and {params.end_ts}",
        )

    is_monthly = (gas_df["end_ts"] - gas_df["start_ts"]).mean() > pd.Timedelta(days=7)  # type: ignore
    if is_monthly:
        gas_df = NonHHDataFrame(gas_df)
        gas_df["days"] = (gas_df["end_ts"] - gas_df["start_ts"]).dt.total_seconds() / pd.Timedelta(days=1).total_seconds()
    else:
        gas_df = hh_gas_to_monthly(HHDataFrame(gas_df))

    if gas_df.shape[0] < 3:
        raise HTTPException(400, f"Dataset covered too little time: {gas_df.index.min()} to {gas_df.index.max()}")

    fit_weather_df = weather_dataset_to_dataframe(
        await get_weather(
            WeatherRequest(
                location=location,
                latitude=latitude,
                longitude=longitude,
                start_ts=gas_df["start_ts"].min(),
                end_ts=gas_df["end_ts"].max(),
            ),
            pool=pool,
            http_client=http_client,
        )
    )

    fitted_coefs = await asyncio.to_thread(fit_bait_and_model, gas_df, fit_weather_df, apply_bait=params.apply_bait)
    changed_coefs = apply_fabric_interventions(fitted_coefs, params.interventions, params.savings_fraction)
    forecast_weather_df = weather_dataset_to_dataframe(
        await get_weather(
            WeatherRequest(
                location=location, latitude=latitude, longitude=longitude, start_ts=params.start_ts, end_ts=params.end_ts
            ),
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

    forecast_weather_df["bait"] = await asyncio.to_thread(
        building_adjusted_internal_temperature,
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
    heating_df = await asyncio.to_thread(
        assign_hh_dhw_poisson,
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

    metadata_params = {
        "source_dataset_id": str(params.dataset_id),
        **changed_coefs.model_dump(),
        "generation_method": HeatingLoadModelEnum.Regression,
    }

    if params.surveyed_sizes is not None:
        fabric_cost_total, fabric_cost_breakdown = calculate_THIRD_PARTY_intervention_costs(
            params.surveyed_sizes, interventions=params.interventions
        )
    else:
        fabric_cost_total, fabric_cost_breakdown = None, None

    metadata = HeatingLoadMetadata(
        dataset_id=params.bundle_metadata.dataset_id if params.bundle_metadata is not None else uuid7(),
        site_id=site_id,
        created_at=datetime.datetime.now(datetime.UTC),
        params=json.dumps(metadata_params),
        interventions=params.interventions,
        generation_method=HeatingLoadModelEnum.Regression,
    )

    async with pool.acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO
                heating.metadata (
                    dataset_id,
                    site_id,
                    created_at,
                    params,
                    interventions,
                    fabric_cost_total,
                    fabric_cost_breakdown
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            metadata.dataset_id,
            metadata.site_id,
            metadata.created_at,
            json.dumps(metadata.params),
            metadata.interventions,
            apply_intervention_count_cost_offset(fabric_cost_total, metadata.interventions)
            if fabric_cost_total is not None
            else None,
            json.dumps([item.model_dump(mode="json") for item in fabric_cost_breakdown]) if fabric_cost_breakdown else None,
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
    if params.structure_id is None:
        raise HTTPException(400, "Must have provided a thermal model dataset ID to generate a heating load")
    thermal_model = await get_thermal_model(pool, dataset_id=DatasetID(dataset_id=params.structure_id))

    if params.site_id is None:
        raise HTTPException(400, "Must have provided a site ID for thermal model dataset fitting")
    location_response = await pool.fetchval(
        """SELECT location, coordinates FROM client_info.site_info WHERE site_id = $1 LIMIT 1""",
        params.site_id,
    )
    if location_response is None:
        raise HTTPException(400, f"Could not find a location for {params.site_id}")
    location, (latitude, longitude) = location_response
    weather_records = await get_weather(
        weather_request=WeatherRequest(
            location=location, latitude=latitude, longitude=longitude, start_ts=params.start_ts, end_ts=params.end_ts
        ),
        pool=pool,
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
        seed=params.seed,
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
        params=json.dumps({
            "thermal_model_dataset_id": str(params.structure_id),
            "generation_method": HeatingLoadModelEnum.ThermalModel,
        }),
        interventions=params.interventions,
        generation_method=HeatingLoadModelEnum.ThermalModel,
    )

    fabric_cost_total, fabric_cost_breakdown = calculate_intervention_costs_params(
        thermal_model, interventions=params.interventions
    )
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute(
            """
                INSERT INTO heating.metadata (
                    dataset_id,
                    site_id,
                    created_at,
                    params,
                    interventions,
                    fabric_cost_total,
                    fabric_cost_breakdown
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            metadata.dataset_id,
            metadata.site_id,
            metadata.created_at,
            json.dumps(metadata.params),
            metadata.interventions,
            apply_intervention_count_cost_offset(fabric_cost_total, metadata.interventions),
            json.dumps([item.model_dump(mode="json") for item in fabric_cost_breakdown]) if fabric_cost_breakdown else None,
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
            thermal_bundle_metadata.dataset_id = params.structure_id
            await file_self_with_bundle(conn, bundle_metadata=thermal_bundle_metadata)
    logger = logging.getLogger(__name__)
    logger.info(f"Thermal Model heat load generation {metadata.dataset_id} completed.")
    return metadata


@api_router.post("/generate-phpp-load")
async def generate_heating_load_phpp(
    pool: DatabasePoolDep, http_client: HttpClientDep, params: HeatingLoadRequest
) -> HeatingLoadMetadata:
    """
    Generate a heating load from the PHPP.

    This is actually a regression implementation, but we'll apply fabric savings based on the PHPP peak heat load.

    Parameters
    ----------
    pool
        Database connection pool containing the PHPP data
    http_client
        HTTP Client for requests to VisualCrossing to get weather datas
    params
        request for the heating load including a structure ID (filed under the thermal model dataset ID for nnow)

    Returns
    -------
    HeatingLoadMetadata
        Information about the heating load we just generated
    """
    logger = logging.getLogger(__name__)
    if params.structure_id is None:
        # Note that we don't check if this is a real structure here, just that it was provided.
        # We trust the user to have sent a legitimate request
        raise HTTPException(422, "Need to provide a dataset ID in thermal_model_dataset_id corresponding to a structure.")

    if params.surveyed_sizes is not None:
        logger.warning("Received surveyed sizes for PHPP request which will be ignored")
    if params.site_id is None:
        site_id = await get_site_id_for_heating_load(params.dataset_id, pool)
    else:
        site_id = params.site_id

    new_params = params.model_copy()
    new_params.site_id = site_id

    if params.savings_fraction != 0.0:
        # If we've got a provided savings fraction, we'll override that with our calculations later.
        # For now, return that error noisily so callers know what's happened
        raise HTTPException(
            422, "Provided a nonzero savings fraction to the PHPP generation; must provide 0.0 as we'll overwrite it."
        )

    structure_df, metadata = await get_phpp_dataframe_from_database(pool, params.structure_id)
    peak_hload = phpp_total_heat_loss(
        structure_df=structure_df,
        metadata={
            "air_changes": metadata.air_changes,
            "floor_area": metadata.floor_area,
            "internal_volume": metadata.internal_volume,
        },
    )

    new_structure_df = structure_df.copy()
    air_changes = metadata.air_changes
    for intervention in params.interventions:
        # Repeatedly apply interventions to the same dataframe. This does some unnecessary copying but is cleanest
        new_structure_df = apply_phpp_intervention(new_structure_df, intervention_name=intervention)
        if isinstance(intervention, InterventionEnum):
            intervention = intervention.value

        if "air tightness" in intervention.lower():
            # This is a bodge! Watch out!
            air_changes = max(air_changes * 0.7, min(air_changes, 2.0))

        if "single room heat recovery ventilators" in intervention.lower():
            air_changes = max(air_changes * 0.9, min(air_changes, 2.0))

        if "mechanical ventilation and heat recovery" in intervention.lower():
            air_changes = min(air_changes, 2.0)

        if "tcosy" in intervention.lower():
            air_changes = min(air_changes, 2.0)

    final_peak_hload = phpp_total_heat_loss(
        structure_df=new_structure_df,
        metadata={
            "air_changes": air_changes,
            "floor_area": metadata.floor_area,
            "internal_volume": metadata.internal_volume,
        },
    )

    # Override the existing percentage saving with the new one, which we then send to the regression implementation.
    percentage_saving = 1.0 - (final_peak_hload / peak_hload)  # this might be 1.0 if there were no interventions
    new_params.savings_fraction = percentage_saving

    heating_df, changed_coefs = await generate_heating_load_regression_impl(new_params, pool, http_client)

    metadata_params = {
        "source_dataset_id": str(params.dataset_id),
        "structure_id": str(params.structure_id),
        "generation_method": HeatingLoadModelEnum.PHPP,
        "percentage_saving": percentage_saving,
        **changed_coefs.model_dump(),
    }

    hload_metadata = HeatingLoadMetadata(
        dataset_id=params.bundle_metadata.dataset_id if params.bundle_metadata is not None else uuid7(),
        site_id=site_id,
        created_at=datetime.datetime.now(datetime.UTC),
        params=json.dumps(metadata_params),
        interventions=params.interventions,
        generation_method=HeatingLoadModelEnum.PHPP,
        peak_hload=final_peak_hload / 1000,
    )

    fabric_cost_total, fabric_cost_breakdown = phpp_fabric_intervention_cost(
        structure_df, [item.value if isinstance(item, InterventionEnum) else str(item) for item in params.interventions]
    )
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO
                heating.metadata (
                    dataset_id,
                    site_id,
                    created_at,
                    params,
                    interventions,
                    peak_hload,
                    fabric_cost_total,
                    fabric_cost_breakdown
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            hload_metadata.dataset_id,
            hload_metadata.site_id,
            hload_metadata.created_at,
            json.dumps(hload_metadata.params),
            hload_metadata.interventions,
            # Note that peak heating loads are stored in kW
            final_peak_hload / 1000,
            apply_intervention_count_cost_offset(fabric_cost_total, hload_metadata.interventions),
            json.dumps([item.model_dump(mode="json") for item in fabric_cost_breakdown]) if fabric_cost_breakdown else None,
        )

        await conn.copy_records_to_table(
            schema_name="heating",
            table_name="synthesised",
            columns=["dataset_id", "start_ts", "end_ts", "heating", "dhw", "air_temperature"],
            records=zip(
                itertools.repeat(hload_metadata.dataset_id, len(heating_df.index)),
                heating_df.index,
                heating_df.index + pd.Timedelta(minutes=30),
                heating_df["heating"],
                heating_df["dhw"],
                heating_df["air_temperature"],
                strict=True,
            ),
        )

        if params.bundle_metadata is not None:
            assert params.bundle_metadata.dataset_type == DatasetTypeEnum.HeatingLoad
            await file_self_with_bundle(conn, bundle_metadata=params.bundle_metadata)
            # We also file the PHPP in the database as part of this bundle
            phpp_bundle_metadata = params.bundle_metadata.model_copy()
            phpp_bundle_metadata.dataset_type = DatasetTypeEnum.PHPP
            phpp_bundle_metadata.dataset_id = params.structure_id
            await file_self_with_bundle(conn, bundle_metadata=phpp_bundle_metadata)
    return hload_metadata
