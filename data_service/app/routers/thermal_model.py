"""Fitting, database writing, and retrieving endpoints for the thermal model."""

import asyncio
import datetime
import json
import operator
import uuid

import httpx
import pandas as pd
import pydantic
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.encoders import jsonable_encoder

from app.dependencies import DatabasePoolDep, ProcessPoolDep
from app.internal.thermal_model.fitting import fit_to_gas_usage
from app.models.core import DatasetID, DatasetTypeEnum, SiteIDWithTime
from app.models.weather import WeatherRequest
from app.routers.client_data import get_location
from app.routers.meter_data import get_meter_data
from app.routers.site_manager import list_elec_datasets, list_gas_datasets
from app.routers.weather import get_weather

router = APIRouter()


async def file_params_with_db(
    pool: DatabasePoolDep,
    site_id: str,
    task_id: pydantic.UUID4,
    results: dict[str, float],
    datasets: dict[DatasetTypeEnum, pydantic.UUID4],
) -> None:
    """
    Write the parameters for the thermal model to the database.

    Parameters
    ----------
    pool
        Database pool with available connections to write to the database with.
    site_id
        Foreign key, referencing the site you've done this for
    task_id
        The ID of the thermal model task, you should have generated this and handed it back to the user earlier.
    results
        The actual results for the model in the form {physical_param: float value} for the fitted parameters
    datasets
        The underlying datasets used to calculate this model, for reproducibility.

    Returns
    -------
    None
    """
    await pool.execute(
        """INSERT INTO heating.thermal_model VALUES ($1, $2, $3, $4, $5)""",
        task_id,
        datetime.datetime.now(datetime.UTC),
        site_id,
        json.dumps(jsonable_encoder(results)),
        json.dumps(jsonable_encoder(datasets)),
    )


async def thermal_fitting_process_wrapper(
    executor: ProcessPoolDep,
    pool: DatabasePoolDep,
    site_id: str,
    task_id: pydantic.UUID4,
    datasets: dict[DatasetTypeEnum, pydantic.UUID4],
    gas_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    elec_df: pd.DataFrame | None,
) -> None:
    """
    Monitor and join the Thermal Fitting background process.

    This should be handed a given thermal model fitting process which was already started,
    and we'll join it correctly and wait for it to be completed here.
    This should be added as a BackgroundTask so that the endpoints themselves don't wait.

    Parameters
    ----------
    executor
        A ProcessPool to run this task in
    pool
        A database pool to write to at the end
    site_id
        Foreign key, referencing the site you've done this for
    datasets
        The GasMeterData and the ElectricityMeterData you used for this fitting
    gas_df
        Gas meter dataset with start_ts, end_ts and consumption columns
    weather_df
        Weather dataset with solarradiation, temp, start_ts columns
    elec_df
        Electricity usage dataset with start_ts, end_ts and consumption columns (can be None)
    """
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        executor,
        fit_to_gas_usage,
        gas_df,
        weather_df,
        elec_df,
        10,  # n_iter
    )
    await file_params_with_db(pool, site_id, task_id, result, datasets)


@router.post("/get-thermal-model")
async def get_thermal_model(pool: DatabasePoolDep, dataset_id: DatasetID) -> dict[str, float]:
    """
    Get thermal model fitted parameters from the database.

    Parameters
    ----------
    pool
        Connection pool for the database
    dataset_id
        The ID of the thermal model run you want to get data for

    Returns
    -------
    dict[str, float]
        Physical parameters as keys with values as floats, see fit_to_gas_usage for more detail
    """
    res = await pool.fetchval("""SELECT results FROM heating.thermal_model WHERE dataset_id = $1""", dataset_id.dataset_id)
    if res is None:
        raise HTTPException(404, f"Could not find a thermal model for {dataset_id.dataset_id}")
    unpacked = json.loads(res)
    return unpacked


@router.post("/fit-thermal-model")
async def fit_thermal_model_endpoint(
    pool: DatabasePoolDep, process_pool: ProcessPoolDep, bgt: BackgroundTasks, params: SiteIDWithTime
) -> dict[str, pydantic.UUID4]:
    """
    Fit thermal model parameters via a background task.

    This will get the relevant datasets and then spin off the heavy computation into a background task.

    Parameters
    ----------
    pool

    process_pool

    bgt

    params

    Returns
    -------
        The ID that this dataset will eventually get.
    """
    all_gas_datasets = await list_gas_datasets(params, pool)
    if not all_gas_datasets:
        raise HTTPException(400, f"No gas datasets available for `{params.site_id}` to fit to.")
    latest_gas_dataset_id = max(all_gas_datasets, key=operator.attrgetter("created_at")).dataset_id

    all_elec_datasets = await list_elec_datasets(params, pool)
    if not all_elec_datasets:
        raise HTTPException(400, f"No gas datasets available for `{params.site_id}` to fit to.")
    latest_elec_dataset_id = max(all_elec_datasets, key=operator.attrgetter("created_at")).dataset_id

    async with pool.acquire() as conn, httpx.AsyncClient() as client:
        gas_meter_records = await get_meter_data(DatasetID(dataset_id=latest_gas_dataset_id), conn=conn)
        elec_meter_records = await get_meter_data(DatasetID(dataset_id=latest_elec_dataset_id), conn=conn)
        location = await get_location(params, conn=conn)
        weather_records = await get_weather(
            weather_request=WeatherRequest(
                location=location,
                start_ts=min(item.start_ts for item in gas_meter_records),
                end_ts=max(item.end_ts for item in gas_meter_records),
            ),
            conn=conn,
            http_client=client,
        )

    elec_df = pd.DataFrame.from_records([item.model_dump() for item in elec_meter_records])
    gas_df = pd.DataFrame.from_records([item.model_dump() for item in gas_meter_records])
    weather_df = pd.DataFrame.from_records([item.model_dump() for item in weather_records])

    task_id = uuid.uuid4()
    bgt.add_task(
        thermal_fitting_process_wrapper,
        process_pool,
        pool,
        site_id=params.site_id,
        task_id=task_id,
        datasets={
            DatasetTypeEnum.GasMeterData: latest_gas_dataset_id,
            DatasetTypeEnum.ElectricityMeterData: latest_elec_dataset_id,
        },
        gas_df=gas_df,
        weather_df=weather_df,
        elec_df=elec_df,
    )
    return {"task_id": task_id}
