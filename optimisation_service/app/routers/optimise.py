import asyncio
import datetime
import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import UUID4

from app.internal.problem import Building, PortfolioProblem
from app.models.result import OptimisationResult

from ..internal.datamanager import DataManager, DataManagerDep
from ..internal.grid_search import convert_param
from ..internal.problem import ParameterDict
from ..models.core import (
    EndpointBuilding,
    EndpointPortfolioTask,
    EndpointResult,
    EndpointTask,
    TaskResponse,
    TaskWithUUID,
)
from ..models.optimisers import OptimiserFunc
from ..models.tasks import Task
from .epl_queue import IQueue

router = APIRouter()
logger = logging.getLogger("default")


def convert_task(task: TaskWithUUID, data_manager: DataManager) -> Task:
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
    optimiser_func = OptimiserFunc[task.optimiser.name].value
    optimiser = optimiser_func(**task.optimiser.hyperparameters.model_dump(mode="python"))

    buildings = {}
    for building in task.buildings:
        building_dir = data_manager.building_dirs[building.name]
        # Write out the parameters for debug purposes; EPOCH doesn't actually use them.
        with open(building_dir / "inputParameters.json", "w") as fi:
            json.dump(convert_param(building.search_parameters), fi)

        buildings[building.name] = Building(
            parameters=ParameterDict(**building.search_parameters.model_dump()), input_dir=building_dir
        )

    problem = PortfolioProblem(objectives=task.objectives, constraints={}, buildings=buildings)
    return Task(task_id=task.task_id, problem=problem, optimiser=optimiser, data_manager=data_manager)


def process_results(task: Task, results: OptimisationResult, completed_at: datetime.datetime) -> list[EndpointResult]:
    logger.info(f"Postprocessing results of {task.task_id}.")
    Optimisation_Results = []
    for portfolio_solution in results.solutions:
        portfolio_id = uuid.uuid4()
        for site_id, building_solution in portfolio_solution.solution.items():
            OptRes = EndpointResult(
                task_id=task.task_id,
                site_id=site_id,
                portfolio_id=portfolio_id,
                result_id=uuid.uuid4(),  # generate a uuid to refer back to later
                solution=dict(building_solution.solution.items()),  # type: ignore
                objective_values=building_solution.objective_values,  # type: ignore
                n_evals=results.n_evals,
                exec_time=results.exec_time,
                completed_at=completed_at,
            )
            Optimisation_Results.append(OptRes)
        OptRes = EndpointResult(
            task_id=task.task_id,
            site_id=None,
            portfolio_id=portfolio_id,
            result_id=uuid.uuid4(),  # generate a uuid to refer back to later
            solution=None,  # type: ignore
            objective_values=portfolio_solution.objective_values,  # type: ignore
            n_evals=results.n_evals,
            exec_time=results.exec_time,
            completed_at=completed_at,
        )
        Optimisation_Results.append(OptRes)
    return Optimisation_Results


async def process_requests(q: IQueue) -> None:
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
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                results = await loop.run_in_executor(executor, lambda: task.optimiser.run(task.problem))  # noqa: B023
            logger.info(f"Finished optimising {task.task_id}.")
            completed_at = datetime.datetime.now(datetime.UTC)
            payload = process_results(task, results, completed_at)
            await task.data_manager.transmit_results(payload)
        except Exception:
            logger.error(f"Exception occured, skipping {task.task_id}.", exc_info=True)
            pass
        q.mark_task_done(task)


@router.post("/submit-task")
async def submit_task(request: Request, endpoint_task: EndpointTask, data_manager: DataManagerDep) -> TaskResponse:
    """
    Add optimisation task to queue.

    Parameters
    ----------
    Task
        Optimisation task to be added to queue.
    """
    building = EndpointBuilding(
        name=endpoint_task.name, search_parameters=endpoint_task.search_parameters, site_data=endpoint_task.site_data
    )

    epp_task = EndpointPortfolioTask(
        name=endpoint_task.name,
        optimiser=endpoint_task.optimiser,
        objectives=endpoint_task.objectives,
        created_at=endpoint_task.created_at,
        buildings=[building],
        client_id=endpoint_task.client_id,
    )

    response = await submit_portfolio(request=request, endpoint_portfolio_task=epp_task, data_manager=data_manager)
    return response


@router.post("/submit-portfolio-task")
async def submit_portfolio(
    request: Request, endpoint_portfolio_task: EndpointPortfolioTask, data_manager: DataManagerDep
) -> TaskResponse:
    """
    Add portfolio optimisation task to queue.

    Parameters
    ----------
    endpoint_portfolio_task
        Portfolio ptimisation task to be added to queue.
    """
    task_id: UUID4 = uuid.uuid4()
    logger.info(f"Received task - assigning id: {task_id}.")
    task = TaskWithUUID(**endpoint_portfolio_task.model_dump(), task_id=task_id)

    q: IQueue = request.app.state.q
    if q.full():
        logger.warning("Queue full.")
        raise HTTPException(status_code=503, detail="Task queue is full.")
    if task.task_id in q.q.keys():
        logger.warning(f"{task.task_id} already in queue.")
        raise HTTPException(status_code=400, detail="Task already in queue.")
    else:
        try:
            await data_manager.fetch_portfolio_data(task)
            pytask = convert_task(task, data_manager)
            await data_manager.transmit_task(task)
            await q.put(pytask)
            return TaskResponse(task_id=task.task_id)
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to add task to database: {e.response.text!s}")
            raise HTTPException(status_code=500, detail=f"Failed to add task to database: {e.response.text!s}") from e
        except Exception as e:
            logger.warning(f"Failed to add task to queue: {type(e)}: {e!s}")
            raise HTTPException(status_code=500, detail=f"Failed to add task to queue: {e!s}") from e
