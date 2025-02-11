import asyncio
import datetime
import operator
from multiprocessing import Process

import httpx
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, HTTPException, Response

from app.dependencies import DatabasePoolDep, ProcessPoolDep
from app.internal.thermal_model.fitting import fit_to_gas_usage
from app.models.core import SiteIDWithTime
from app.routers.client_data import get_location
from app.routers.meter_data import get_meter_data
from app.routers.site_manager import list_elec_datasets, list_gas_datasets

router = APIRouter()


async def fit_thermal_model_background(site_id: str, start_ts: datetime.datetime, end_ts: datetime.datetime):
    fit_to_gas_usage(gas_df, weather_df, elec_df)


async def monitor_thermal_fitting_process(
    executor: ProcessPoolDep, gas_df: pd.DataFrame, weather_df: pd.DataFrame, elec_df: pd.DataFrame
) -> None:
    """
    Monitor and join the Thermal Fitting background process.

    This should be handed a given thermal model fitting process which was already started,
    and we'll join it correctly and wait for it to be completed here.
    This should be added as a BackgroundTask so that the endpoints themselves don't wait.

    Parameters
    ----------
    p
        A multiprocessing.Process that you've already started, running `fit_thermal_model`
    """
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, fit_to_gas_usage, [gas_df, weather_df, elec_df])


@router.post("/fit-thermal-model")
async def fit_thermal_model_endpoint(pool: DatabasePoolDep, process_pool: ProcessPoolDep, params: SiteIDWithTime) -> Response:
    """
    Fit thermal model parameters via a background task.
    """
    all_gas_datasets = await list_gas_datasets(params.site_id, pool)
    if not all_gas_datasets:
        raise HTTPException(400, f"No gas datasets available for `{params.site_id}` to fit to.")
    latest_gas_dataset_id = max(all_gas_datasets, key=operator.attrgetter("created_at")).dataset_id

    all_elec_datasets = await list_elec_datasets(params.site_id, pool)
    if not all_elec_datasets:
        raise HTTPException(400, f"No gas datasets available for `{params.site_id}` to fit to.")
    latest_elec_dataset_id = max(all_elec_datasets, key=operator.attrgetter("created_at")).dataset_id

    async with pool.acquire() as conn, httpx.AsyncClient() as client:
        gas_meter_records = await get_meter_data(latest_gas_dataset_id, conn=conn)
        elec_meter_records = await get_meter_data(latest_elec_dataset_id, conn=conn)
        location = await get_location(params.site_id, conn=conn)
        # weather_records = await get_weather(
        #    weather_request=WeatherRequest(
        #        location=location,
        #        start_ts=min(item.start_ts for item in gas_meter_records),
        #        end_ts=max(item.end_ts for item in gas_meter_records),
        #    ),
        #    conn=conn,
        #    http_client=client,
        # )
    print(elec_meter_records)
    elec_df = pd.DataFrame.from_dict(elec_meter_records)
    gas_df = pd.DataFrame.from_dict(gas_meter_records, orient="records")
    # weather_df = pd.DataFrame.from_dict(weather_records)
    print(gas_df.head())
    print(elec_df.head())
    p = Process(target=fit_thermal_model_background, args=[params.site_id, params.start_ts, params.end_ts])
    p.start()
    bgt = BackgroundTasks.add_task(monitor_thermal_fitting_process, p)
    return Response(content="Thermal model fitting task successfully queued", background=bgt)
