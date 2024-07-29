import asyncio
import datetime
import os
import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from uuid import UUID

import aiohttp
import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from ..internal.opt_algorithm import Algorithm
from ..internal.problem import Problem, convert_objectives, convert_parameters
from ..internal.result import Result
from .models import FileLoc, Optimiser, SiteData, Task
from .queue import IQueue

router = APIRouter()


# def transmit(problem: Problem, results: Result, completed_at: datetime.UTC):
#     df_objective_values = pd.DataFrame(data=results.objective_values, columns=problem.objectives.keys())
#     df_solutions = pd.DataFrame(data=results.solutions, columns=problem.variable_param().keys())
#     constant_param = problem.constant_param()
#     constant_param_values = np.repeat([list(problem.constant_param().values())], results.solutions.shape[0], axis=0)
#     df_constants = pd.DataFrame(data=constant_param_values, columns=constant_param.keys())

#     records[problem.name] = pd.concat([df_objective_values, df_solutions, df_constants], axis=1).to_json(orient="records")


async def convert_task(task: Task) -> tuple[Problem, Algorithm, os.PathLike]:
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
        name=str(task.TaskID),
        objectives=convert_objectives(task.objectives),
        constraints={
            "annualised_cost": [None, None],
            "capex": [None, None],
            "carbon_balance": [None, None],
            "cost_balance": [None, None],
            "payback_horizon": [None, None],
        },
        parameters=convert_parameters(task.searchParameters),
        input_dir=input_dir,
    )
    return problem, optimiser, input_dir


async def post_request(url, data):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            response_data = await response.json()
            return response_data


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


async def fps_elec(data_id: UUID, temp_dir: os.PathLike) -> None:
    """
    Fetch, process and save electricity load files.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch
    temp_dir
        temp_dir to save files to
    """
    response = await post_request(url="/get-meter-data", data={"dataset_id": data_id})
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "FixLoad1", "FixLoad2"])
    df = df.sort_values("HourOfYear")
    df.to_csv(Path(temp_dir, "CSVEload.csv"))


async def fps_rgen(data_id: UUID, temp_dir: os.PathLike) -> None:
    """
    Fetch, process and save renewable generation.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch
    temp_dir
        temp_dir to save files to
    """
    response = await post_request(url="/get-rgen", data={"dataset_id": data_id})
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "RGen1"])
    df = df.sort_values("HourOfYear")
    df.to_csv(Path(temp_dir, "CSVRGen.csv"))


async def fps_heat_n_air(data_id: UUID, temp_dir: os.PathLike) -> None:
    """
    Fetch, process and save heat load and airtemp files.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch.
    temp_dir
        temp_dir to save files to.
    """
    response = await post_request(url="/get-heating-load", data={"dataset_id": data_id})
    df = pd.DataFrame.from_dict(response)
    df_heat = df.reindex(columns=["HourOfYear", "Date", "StartTime", "HLoad1"])
    df_air = df.reindex(columns=["HourOfYear", "Date", "StartTime", "Air-temp"])
    df_heat = df_heat.sort_values("HourOfYear")
    df_air = df_air.sort_values("HourOfYear")
    df_heat.to_csv(Path(temp_dir, "CSVHload.csv"))
    df_air.to_csv(Path(temp_dir, "CSVAirtemp.csv"))


async def fps_ASHP_input(data_id: UUID, temp_dir: os.PathLike) -> None:
    """
    Fetch, process and save ASHP input.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch.
    temp_dir
        temp_dir to save files to.
    """
    response = await post_request(url="/get-ashp-input", data={"dataset_id": data_id})
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=[0, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70])
    df = df.sort_values("0")
    df.to_csv(Path(temp_dir, "CSVASHPinput.csv"))


async def fps_ASHP_output(data_id: UUID, temp_dir: os.PathLike) -> None:
    """
    Fetch, process and save ASHP output.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch.
    temp_dir
        temp_dir to save files to.
    """
    response = await post_request(url="/get-ashp-output", data={"dataset_id": data_id})
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=[0, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70])
    df = df.sort_values("0")
    df.to_csv(Path(temp_dir, "CSVASHPoutput.csv"))


async def fps_import_tariff(data_id: UUID, temp_dir: os.PathLike) -> None:
    """
    Fetch, process and save import tariff.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch.
    temp_dir
        temp_dir to save files to.
    """
    response = await post_request(url="/get-import-tariff", data={"dataset_id": data_id})
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "Tariff"])
    df = df.sort_values("HourOfYear")
    df.to_csv(Path(temp_dir, "CSVImporttariff.csv"))


async def fps_grid_CO2(data_id: UUID, temp_dir: os.PathLike) -> None:
    """
    Fetch, process and save grid CO2.

    Parameters
    ----------
    data_id
        UUID of dataset to fetch.
    temp_dir
        temp_dir to save files to.
    """
    response = await post_request(url="/get-grid-CO2", data={"dataset_id": data_id})
    df = pd.DataFrame.from_dict(response)
    df = df.reindex(columns=["HourOfYear", "Date", "StartTime", "Grid CO2e (kg/kWh)"])
    df = df.sort_values("HourOfYear")
    df.to_csv(Path(temp_dir, "CSVGridCO2.csv"))


async def fps_inputdata(site_data_id: UUID):
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
    data_ids = await post_request(url="/get-client-site-data", data={"input_data_ID": site_data_id})
    input_dir = create_tempdir(site_data_id)
    elec = fps_elec(data_ids["electricity_dataset"], input_dir)
    heat = fps_heat_n_air(data_ids["gas_dataset"], input_dir)
    rgen = fps_rgen(data_ids["rgen_dataset"], input_dir)
    ashp_input = fps_ASHP_input(data_ids["ashp_input_dataset"], input_dir)
    ashp_output = fps_ASHP_output(data_ids["ashp_output_dataset"], input_dir)
    import_tariff = fps_import_tariff(data_ids["tariff_dataset"], input_dir)
    grid_CO2 = fps_grid_CO2(data_ids["grid_CO2_dataset"], input_dir)
    await asyncio.gather(elec, heat, rgen, ashp_input, ashp_output, import_tariff, grid_CO2)
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
        return site_data.path
    else:
        return await fps_inputdata(site_data.key)


def optimise(problem: Problem, optimiser: Algorithm) -> tuple[Result, datetime.datetime]:
    """
    Apply optimisation algorithm to problem.

    Parameters
    ----------
    problem
        Problem to optimise.
    optimiser
        Optimiser to solve problem.

    Returns
    -------
    Result
        Optimisation results.
    completed_at
        Completion time of optimiser.
    """
    return optimiser.run(problem), datetime.datetime.now(datetime.UTC)


async def process_requests(q: IQueue, pool: ProcessPoolExecutor):
    """
    Loop to process tasks in queue.

    Parameters
    ----------
    q
        Queue to process.
    pool
        Process Pool Executor to run tasks.
    """
    while True:
        task = await q.get()
        loop = asyncio.get_running_loop()
        problem, optimiser, input_dir = await convert_task(task)
        results, completed_at = await loop.run_in_executor(pool, optimise, *(problem, optimiser))
        # transmit(problem, results, completed_at)
        if task.site["type"] == FileLoc.database:
            shutil.rmtree(input_dir)
        q.mark_task_done(task)


@router.post("/submit-task/")
async def add_task(request: Request, task: Task):
    """
    Add optimisation task to queue.

    Parameters
    ----------
    Task
        Optimisation task to be added to queue.
    """
    q: IQueue = request.app.state.q
    if q.full():
        raise HTTPException(status_code=503, detail="Task queue is full.")
    else:
        await q.put(task)
        return "Added task to queue."
