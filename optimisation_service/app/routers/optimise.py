import asyncio
import datetime
import json
import os
import shutil
from pathlib import Path
from uuid import UUID

import httpx
import pandas as pd
from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from ..internal.log import logger
from ..internal.problem import _OBJECTIVES, Problem
from ..internal.result import Result
from .models.core import JSONTask, OptimisationResult, Optimiser, PyTask, SiteData
from .models.database import DatasetIDWithTime
from .models.site_data import FileLoc
from .queue import IQueue

router = APIRouter()


async def post_request(client: httpx.AsyncClient, url: str, json: json):
    try:
        response = await client.post(url=url, json=json)
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Error response {e.response.status_code} while requesting {e.request.url!r}.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


def create_tempdir(sitedatakey: UUID) -> os.PathLike:
    """
    Create temporary folder for site data files.

    Parameters
    ----------
    sitedatakey
        Name of folder.

    Returns
    -------
    temp_dir
        Path to temporary directory.
    """
    temp_dir = Path(".", "app", "data", "temp", str(sitedatakey))
    os.makedirs(temp_dir)
    for file in os.listdir(Path(".", "app", "data", "default")):
        shutil.copy(file, temp_dir)
    return temp_dir


async def fetch_electricity_data(data_id_w_time: DatasetIDWithTime, temp_dir: os.PathLike, client: httpx.AsyncClient) -> None:
    """
    Fetch, process and save electricity load files.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch
    temp_dir
        temp_dir to save files to
    """
    response = await post_request(client=client, url="/get-electricity-load", json=data_id_w_time)
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "FixLoad1", "FixLoad2"])
    df = df.sort_values("HourOfYear")
    df.to_csv(Path(temp_dir, "CSVEload.csv"))


async def fetch_rgen_data(data_id_w_time: DatasetIDWithTime, temp_dir: os.PathLike, client: httpx.AsyncClient) -> None:
    """
    Fetch, process and save renewable generation.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch
    temp_dir
        temp_dir to save files to
    """
    response = await post_request(client=client, url="/get-renewables-generation", json=data_id_w_time)
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "RGen1"])
    df = df.sort_values("HourOfYear")
    df.to_csv(Path(temp_dir, "CSVRGen.csv"))


async def fetch_heat_n_air_data(data_id_w_time: DatasetIDWithTime, temp_dir: os.PathLike, client: httpx.AsyncClient) -> None:
    """
    Fetch, process and save heat load and airtemp files.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch.
    temp_dir
        temp_dir to save files to.
    """
    response = await post_request(client=client, url="/get-heating-load", json=data_id_w_time)
    df = pd.DataFrame.from_dict(response)
    df_heat = df.reindex(columns=["HourOfYear", "Date", "StartTime", "HLoad1"])
    df_air = df.reindex(columns=["HourOfYear", "Date", "StartTime", "Air-temp"])
    df_heat = df_heat.sort_values("HourOfYear")
    df_air = df_air.sort_values("HourOfYear")
    df_heat.to_csv(Path(temp_dir, "CSVHload.csv"))
    df_air.to_csv(Path(temp_dir, "CSVAirtemp.csv"))


async def fetch_ASHP_input_data(data_id_w_time: DatasetIDWithTime, temp_dir: os.PathLike, client: httpx.AsyncClient) -> None:
    """
    Fetch, process and save ASHP input.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch.
    temp_dir
        temp_dir to save files to.
    """
    response = await post_request(client=client, url="/get-ashp-input", json=data_id_w_time)
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=[0, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70])
    df = df.sort_values("0")
    df.to_csv(Path(temp_dir, "CSVASHPinput.csv"))


async def fetch_ASHP_output_data(data_id_w_time: DatasetIDWithTime, temp_dir: os.PathLike, client: httpx.AsyncClient) -> None:
    """
    Fetch, process and save ASHP output.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch.
    temp_dir
        temp_dir to save files to.
    """
    response = await post_request(client=client, url="/get-ashp-output", json=data_id_w_time)
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=[0, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70])
    df = df.sort_values("0")
    df.to_csv(Path(temp_dir, "CSVASHPoutput.csv"))


async def fetch_import_tariff_data(data_id_w_time: DatasetIDWithTime, temp_dir: os.PathLike, client: httpx.AsyncClient) -> None:
    """
    Fetch, process and save import tariff.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch.
    temp_dir
        temp_dir to save files to.
    """
    response = await post_request(client=client, url="/get-import-tariff", json=data_id_w_time)
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "Tariff"])
    df = df.sort_values("HourOfYear")
    df.to_csv(Path(temp_dir, "CSVImporttariff.csv"))


async def fetch_grid_CO2_data(data_id_w_time: DatasetIDWithTime, temp_dir: os.PathLike, client: httpx.AsyncClient) -> None:
    """
    Fetch, process and save grid CO2.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch.
    temp_dir
        temp_dir to save files to.
    """
    response = await post_request(client=client, url="/get-grid-CO2", json=data_id_w_time)
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "Grid CO2e (kg/kWh)"])
    df = df.sort_values("HourOfYear")
    df.to_csv(Path(temp_dir, "CSVGridCO2.csv"))


async def fetch_input_data(site_data_id: UUID):
    """
    Fetch, process and save all necessary data from database.

    Parameters
    ----------
    site_data_id
        UUID to retreive data details from database

    Returns
    -------
    input_dir
        Path to temporary directory containing input data files.
    """
    logger.debug(f"Fetching site data {site_data_id} info.")
    async with httpx.AsyncClient() as client:
        data_ids = await post_request(client=client, url="/get-client-site-data", json={"input_data_ID": site_data_id})
    input_dir = create_tempdir(site_data_id)
    logger.debug(f"Fetching site data {site_data_id}.")
    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_electricity_data(data_ids["electricity_dataset"], input_dir, client),
            fetch_heat_n_air_data(data_ids["gas_dataset"], input_dir, client),
            fetch_rgen_data(data_ids["rgen_dataset"], input_dir, client),
            fetch_ASHP_input_data(data_ids["ashp_input_dataset"], input_dir, client),
            fetch_ASHP_output_data(data_ids["ashp_output_dataset"], input_dir, client),
            fetch_import_tariff_data(data_ids["tariff_dataset"], input_dir, client),
            fetch_grid_CO2_data(data_ids["grid_CO2_dataset"], input_dir, client),
        ]
        await asyncio.gather(*tasks)
    return input_dir


async def get_inputdata_dir(site_data: SiteData) -> os.PathLike:
    """
    Get path to inputdata.
    Either get path to local files or fetch data from database, process it and save to temp dir.

    Returns
    -------
    Path
        Path to inputdata directory.
    """
    if site_data.loc == FileLoc.local:
        assert Path(site_data.path).is_dir(), "Local directory does not exist."
        return site_data.path
    else:
        return await fetch_input_data(site_data.key)


async def preproccess_task(task: JSONTask) -> PyTask:
    """
    Convert json optimisation tasks into corresponding python objects.

    Parameters
    ----------
    task
        Optimisation task to convert

    Returns
    -------
    problem
        Problem.
    optimiser
        Initialised optimiser.
    """
    input_dir = await get_inputdata_dir(task.siteData)
    optimiser = Optimiser[task.optimiser].value(**task.optimiserConfig)
    problem = Problem(
        objectives=task.objectives,
        constraints={},
        parameters=task.searchParameters,
        input_dir=input_dir,
    )
    return PyTask(task_id=task.task_id, problem=problem, optimiser=optimiser, siteData=task.siteData)


async def transmit_results(results):
    await post_request("/put-results", results)


def postprocess_results(task: PyTask, results: Result, completed_at: datetime.datetime) -> list[OptimisationResult]:
    Optimisation_Results = []
    for solutions, objective_values in zip(results.solutions, results.objective_values):
        solutions_dict = task.problem.constant_param()
        for param, value in zip(task.problem.variable_param().keys(), solutions):
            solutions_dict[param] = value
        objective_values_dict = dict(zip(_OBJECTIVES, objective_values))
        OptRes = OptimisationResult(
            task_id=str(task.task_id),
            solution=solutions_dict,
            objective_values=objective_values_dict,
            n_evals=results.n_evals,
            exec_time=results.exec_time,
            completed_at=str(completed_at),
        )
        Optimisation_Results.append(OptRes)

    return Optimisation_Results


async def process_requests(q: IQueue):
    """
    Loop to process tasks in queue.

    Parameters
    ----------
    q
        Queue to process.
    """
    while True:
        logger.info("Awaiting next task from queue.")
        task = await q.get()
        logger.info(f"Optimising {task.task_id}.")
        try:
            results = await task.optimiser.run(task.problem, verbose=False)
            logger.debug(f"Finished optimising {task.task_id}.")
            completed_at = datetime.datetime.now(datetime.UTC)
            logger.debug(f"Postprocessing and encoding results of {task.task_id}.")
            payload = jsonable_encoder(postprocess_results(task, results, completed_at))
            if task.siteData.loc == FileLoc.database:
                logger.debug(f"Transmiting results of {task.task_id} to database.")
                await transmit_results(payload)
                shutil.rmtree(task.problem.input_dir)
            elif task.siteData.loc == FileLoc.local:
                logger.debug(f"Saving results of {task.task_id} to file.")
                with open(Path(task.siteData.path, "results.json"), "w") as f:
                    json.dump(payload, f)
        except Exception:
            logger.error(f"Exception occured, skipping {task.task_id}.", exc_info=True)
            pass
        logger.info(f"Marking {task.task_id} as complete.")
        q.mark_task_done(task)


@router.post("/submit-task/")
async def add_task(request: Request, task: JSONTask):
    """
    Add optimisation task to queue.

    Parameters
    ----------
    Task
        Optimisation task to be added to queue.
    """
    logger.info(f"Received {task.task_id}.")
    q: IQueue = request.app.state.q
    if q.full():
        logger.debug("Queue full.")
        raise HTTPException(status_code=503, detail="Task queue is full.")
    if task.task_id in q.q.keys():
        logger.debug(f"{task.task_id} already in queue.")
        raise HTTPException(status_code=400, detail="Task already in queue.")
    else:
        try:
            logger.debug(f"Preprocessing {task.task_id}.")
            pytask = await preproccess_task(task)
            logger.info(f"Queued {task.task_id}.")
            await q.put(pytask)
            return f"Added {task.task_id} to queue."
        except Exception as e:
            logger.error(f"Exception occured whilst adding {task.task_id} to queue.", exc_info=True)
            raise HTTPException(status_code=400, detail=str(e)) from e
