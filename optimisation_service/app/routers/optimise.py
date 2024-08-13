import asyncio
import datetime
import logging
import os
import shutil
from pathlib import Path
from uuid import UUID

import httpx
import pandas as pd
from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from ..internal.models.algorithms import Optimiser
from ..internal.models.problem import ParameterDict
from ..internal.problem import _OBJECTIVES, Problem
from ..internal.result import Result
from .models.core import EndpointResult, EndpointTask, ObjectiveValues, OptimisationSolution, Task
from .models.database import DatasetIDWithTime
from .models.site_data import FileLoc, SiteData
from .queue import IQueue

router = APIRouter()
logger = logging.getLogger("default")
database_url = os.environ.get("DB_API_URL", "http://localhost:8000")


async def post_request(client: httpx.AsyncClient, url: str, data: dict):
    try:
        response = await client.post(url=url, json=data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Error response {e.response.status_code} while requesting {e.request.url!r}: {e.response.text}.")
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error while requesting {e.request.url!r}: {str(e)}", exc_info=True)
        raise


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
    response = await post_request(client=client, url=f"{database_url}/get-electricity-load", data=data_id_w_time)
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "FixLoad1"])
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
    response = await post_request(client=client, url=f"{database_url}/get-renewables-generation", data=data_id_w_time)
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
    response = await post_request(client=client, url=f"{database_url}/get-heating-load", data=data_id_w_time)
    df = pd.DataFrame.from_dict(response)
    df_heat = df.reindex(columns=["HourOfYear", "Date", "StartTime", "HLoad1"])
    df_air = df.reindex(columns=["HourOfYear", "Date", "StartTime", "AirTemp"])
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
    response = await post_request(client=client, url=f"{database_url}/get-ashp-input", data=data_id_w_time)
    df = pd.DataFrame.from_dict(response, orient="tight")
    df = df.reindex(columns=[0, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70])
    df = df.sort_values("temperature")
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
    response = await post_request(client=client, url=f"{database_url}/get-ashp-output", data=data_id_w_time)
    df = pd.DataFrame.from_dict(response, orient="tight")
    df = df.reindex(columns=[25, 30, 35, 40, 45, 50, 55, 60, 65, 70])
    df = df.sort_values("temperature")
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
    response = await post_request(client=client, url=f"{database_url}/get-import-tariff", data=data_id_w_time)
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
    response = await post_request(client=client, url=f"{database_url}/get-grid-CO2", data=data_id_w_time)
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "GridCO2"])
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
    logger.debug(f"Fetching site data info {site_data_id}.")
    async with httpx.AsyncClient() as client:
        data_ids = await post_request(
            client=client, url=f"{database_url}/get-client-site-data", data={"input_data_ID": site_data_id}
        )
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
        logger.info(f"Fetching site data from {site_data.path}.")
        assert Path(site_data.path).is_dir(), "Local directory does not exist."
        return site_data.path
    else:
        logger.info(f"Fetching site data from database {site_data.key}.")
        return await fetch_input_data(site_data.key)


async def convert_task(task: EndpointTask, input_dir: str | os.PathLike) -> Task:
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
    logger.info(f"Converting {task.task_id}.")
    optimiser = Optimiser[task.optimiser.name].value(**task.optimiser.hyperparameters.model_dump(mode="python"))
    search_parameters: ParameterDict = task.search_parameters.model_dump(mode="python")
    problem = Problem(
        objectives=task.objectives,
        constraints={},
        parameters=search_parameters,
        input_dir=input_dir,
    )
    return Task(task_id=task.task_id, problem=problem, optimiser=optimiser, siteData=task.site_data)


async def transmit_results(results: list[EndpointResult]):
    logger.info("Adding results to database.")
    async with httpx.AsyncClient() as client:
        await post_request(client=client, url=f"{database_url}/add-optimisation-results", data=jsonable_encoder(results))


async def transmit_task(task: EndpointTask):
    logger.info(f"Adding {task.task_id} to database.")
    async with httpx.AsyncClient() as client:
        await post_request(client=client, url=f"{database_url}/add-optimisation-task", data=jsonable_encoder(task))


def postprocess_results(task: Task, results: Result, completed_at: datetime.datetime) -> list[EndpointResult]:
    logger.info(f"Postprocessing results of {task.task_id}.")
    Optimisation_Results = []
    for solutions, objective_values in zip(results.solutions, results.objective_values):
        solution_dict = task.problem.constant_param() | dict(zip(task.problem.variable_param().keys(), solutions))
        solution: OptimisationSolution = solution_dict
        objective_values: ObjectiveValues = dict(zip(_OBJECTIVES, objective_values))
        OptRes = EndpointResult(
            task_id=str(task.task_id),
            solution=solution,
            objective_values=objective_values,
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
    logger.info("Initialising worker loop.")
    while True:
        logger.info("Awaiting next task from queue.")
        task = await q.get()
        try:
            logger.info(f"Optimising {task.task_id}.")
            results = await task.optimiser.run(task.problem)
            logger.info(f"Finished optimising {task.task_id}.")
            completed_at = datetime.datetime.now(datetime.UTC)
            payload = postprocess_results(task, results, completed_at)
            if task.siteData.loc == FileLoc.database:
                await transmit_results(payload)
                shutil.rmtree(task.problem.input_dir)
            elif task.siteData.loc == FileLoc.local:
                await transmit_results(payload)
        except Exception:
            logger.error(f"Exception occured, skipping {task.task_id}.", exc_info=True)
            pass
        q.mark_task_done(task)


@router.post("/submit-task/")
async def add_task(request: Request, task: EndpointTask):
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
        logger.info("Queue full.")
        raise HTTPException(status_code=503, detail="Task queue is full.")
    if task.task_id in q.q.keys():
        logger.info(f"{task.task_id} already in queue.")
        raise HTTPException(status_code=400, detail="Task already in queue.")
    else:
        try:
            input_dir = await get_inputdata_dir(task.site_data)
            pytask = await convert_task(task, input_dir)
            await transmit_task(task)
            await q.put(pytask)
            return f"Added {task.task_id} to queue and database."
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"Failed to add task to database: {str(e.response.text)}") from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add task to queue: {str(e)}") from e
