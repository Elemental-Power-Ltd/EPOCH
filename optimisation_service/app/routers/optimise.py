import asyncio
import datetime
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

import httpx
from fastapi import APIRouter, HTTPException, Request

from app.internal.datamanager import DataManagerDep
from app.internal.genetic_algorithm import GeneticAlgorithm
from app.internal.grid_search import GridSearch
from app.internal.NSGA2 import NSGA2
from app.models.core import (
    EndpointResult,
    EndpointTask,
    Site,
    Task,
    TaskResponse,
)
from app.models.result import OptimisationResult
from app.routers.epl_queue import IQueue


class OptimiserFunc(Enum):
    NSGA2 = NSGA2
    GeneticAlgorithm = GeneticAlgorithm
    GridSearch = GridSearch


router = APIRouter()
logger = logging.getLogger("default")


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
        task, data_manager = await q.get()
        try:
            logger.info(f"Optimising {task.task_id}.")
            loop = asyncio.get_event_loop()
            optimiser = OptimiserFunc[task.optimiser.name].value(**task.optimiser.hyperparameters.model_dump(mode="python"))
            with ThreadPoolExecutor() as executor:
                results = await loop.run_in_executor(
                    executor,
                    lambda: optimiser.run(objectives=task.objectives, constraints={}, portfolio=task.portfolio),  # noqa: B023
                )
            logger.info(f"Finished optimising {task.task_id}.")
            completed_at = datetime.datetime.now(datetime.UTC)
            payload = process_results(task, results, completed_at)
            await data_manager.transmit_results(payload)
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
    building = Site(
        name=endpoint_task.name, search_parameters=endpoint_task.search_parameters, site_data=endpoint_task.site_data
    )

    epp_task = Task(
        name=endpoint_task.name,
        optimiser=endpoint_task.optimiser,
        objectives=endpoint_task.objectives,
        created_at=endpoint_task.created_at,
        portfolio=[building],
        client_id=endpoint_task.client_id,
    )

    response = await submit_portfolio(request=request, task=epp_task, data_manager=data_manager)
    return response


@router.post("/submit-portfolio-task")
async def submit_portfolio(request: Request, task: Task, data_manager: DataManagerDep) -> TaskResponse:
    """
    Add portfolio optimisation task to queue.

    Parameters
    ----------
    endpoint_portfolio_task
        Portfolio ptimisation task to be added to queue.
    """
    logger.info(f"Received task - assigned id: {task.task_id}.")

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
            data_manager.save_parameters(task)
            await data_manager.transmit_task(task)
            await q.put((task, data_manager))
            return TaskResponse(task_id=task.task_id)
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to add task to database: {e.response.text!s}")
            raise HTTPException(status_code=500, detail=f"Failed to add task to database: {e.response.text!s}") from e
        except Exception as e:
            logger.warning(f"Failed to add task to queue: {type(e)}: {e!s}")
            raise HTTPException(status_code=500, detail=f"Failed to add task to queue: {e!s}") from e
