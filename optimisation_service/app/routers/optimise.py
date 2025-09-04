import asyncio
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

from app.dependencies import HTTPClient, HttpClientDep, QueueDep
from app.internal.bayesian.bayesian import Bayesian
from app.internal.constraints import apply_default_constraints
from app.internal.database.results import process_results, transmit_results
from app.internal.database.site_data import fetch_portfolio_data
from app.internal.database.tasks import transmit_task
from app.internal.NSGA2 import NSGA2, SeparatedNSGA2, SeparatedNSGA2xNSGA2
from app.internal.portfolio_simulator import simulate_scenario
from app.internal.queue import IQueue
from app.internal.site_range import count_parameters_to_optimise
from app.models.core import (
    EndpointTask,
    Site,
    Task,
    TaskResponse,
)


class OptimiserFunc(Enum):
    """Mapping of optimiser types to optimiser class."""

    # TODO (2025-08-08 MHJB): should this be a dict instead? feels weird as an enum.
    NSGA2 = NSGA2
    SeparatedNSGA2xNSGA2 = SeparatedNSGA2xNSGA2
    SeparatedNSGA2 = SeparatedNSGA2
    Bayesian = Bayesian


router = APIRouter()
logger = logging.getLogger("default")


def get_epoch_version() -> str:
    """
    Get the version of the epoch.

    Returns
    -------
        A version string (probably Major.Minor.Patch)

    """
    import epoch_simulator

    return epoch_simulator.__version__  # type: ignore


def check_epoch_version() -> str | None:
    """
    Check that we can get the epoch_simulator's version and log it for information.

    Returns
    -------
    str | None
        The version string of the epoch_simulator (if available, None otherwise)
    """
    try:
        simulator_version = get_epoch_version()
        logger.info(f"Using EPOCH version: {simulator_version}")
    except Exception as e:
        simulator_version = None
        logger.warning(f"Failed to fetch epoch_simulator version! {e}")

    return simulator_version


async def process_requests(queue: IQueue, http_client: HTTPClient) -> None:
    """
    Loop to process tasks in queue.

    Parameters
    ----------
    queue
        Asyncio queue containing oustanding optimisation tasks.
    http_client
        Asynchronous HTTP client to use for requests.
    """
    logger.info("Initialising worker loop.")
    check_epoch_version()
    while True:
        logger.info("Awaiting next task from queue.")
        task = await queue.get()
        try:
            logger.info(f"Optimising {task.task_id}.")
            loop = asyncio.get_event_loop()
            optimiser = OptimiserFunc[task.optimiser.name].value(**dict(task.optimiser.hyperparameters))
            with ThreadPoolExecutor() as executor:
                results = await loop.run_in_executor(
                    executor,
                    lambda: optimiser.run(  # noqa: B023
                        objectives=task.objectives,  # noqa: B023
                        constraints=task.portfolio_constraints,  # noqa: B023
                        portfolio=task.portfolio,  # noqa: B023
                    ),
                )
            logger.info(f"Finished optimising {task.task_id}.")
            completed_at = datetime.datetime.now(datetime.UTC)
            payload = process_results(task, results, completed_at)
            await transmit_results(results=payload, http_client=http_client)
        except Exception:
            logger.error(f"Exception occured, skipping {task.task_id}.", exc_info=True)
            pass
        simulate_scenario.cache_clear()
        queue.mark_task_done(task)


@router.post("/submit-task")
async def submit_task(endpoint_task: EndpointTask, http_client: HttpClientDep, queue: QueueDep) -> TaskResponse:
    """
    Add optimisation task to queue.

    Parameters
    ----------
    endpoint_task
        Site optimisation task to be added to queue.
    http_client
        Asynchronous HTTP client to use for requests.
    queue
        Asyncio queue containing oustanding optimisation tasks.
    """
    site = Site(name=endpoint_task.site_data.site_id, site_range=endpoint_task.site_range, site_data=endpoint_task.site_data)
    simulator_version = get_epoch_version()
    epp_task = Task(
        name=endpoint_task.name,
        optimiser=endpoint_task.optimiser,
        objectives=endpoint_task.objectives,
        created_at=endpoint_task.created_at,
        portfolio=[site],
        client_id=endpoint_task.client_id,
        portfolio_constraints={},
        epoch_version=simulator_version,
    )

    response = await submit_portfolio(task=epp_task, http_client=http_client, queue=queue)
    return response


@router.post("/submit-portfolio-task")
async def submit_portfolio(task: Task, http_client: HttpClientDep, queue: QueueDep) -> TaskResponse:
    """
    Add portfolio optimisation task to queue.

    Parameters
    ----------
    task
        Portfolio optimisation task to be added to queue.
    http_client
        Asynchronous HTTP client to use for requests.
    queue
        Asyncio queue containing oustanding optimisation tasks.
    """
    logger.info(f"Received task - assigned id: {task.task_id}.")

    if queue.full():
        logger.warning("Queue full.")
        raise HTTPException(status_code=503, detail="Task queue is full.")
    if task.task_id in queue.q.keys():
        logger.warning(f"{task.task_id} already in queue.")
        raise HTTPException(status_code=400, detail="Task already in queue.")
    if sum(count_parameters_to_optimise(site.site_range) for site in task.portfolio) < 1:
        logger.warning(f"{task.task_id} has an empty search space.")
        raise HTTPException(
            status_code=400, detail="Task search space is empty. Found no asset values to optimise in site range."
        )
    try:
        await fetch_portfolio_data(task=task, http_client=http_client)
        task.portfolio, task.portfolio_constraints = apply_default_constraints(
            existing_portfolio=task.portfolio, existing_constraints=task.portfolio_constraints
        )
        simulator_version = get_epoch_version()
        task.epoch_version = simulator_version
        save_parameters(task=task)
        await transmit_task(task=task, http_client=http_client)
        await queue.put(task)
        return TaskResponse(task_id=task.task_id)
    except httpx.HTTPStatusError as e:
        logger.warning(f"Failed to add task to database: {e.response.text!s}")
        raise HTTPException(status_code=500, detail=f"Failed to add task to database: {e.response.text!s}") from e
    except Exception as e:
        logger.warning(f"Failed to add task to queue: {type(e)}: {e!s}")
        raise HTTPException(status_code=500, detail=f"Failed to add task to queue: {e!s}") from e


_TEMP_DIR = Path("app", "data", "temp")


def save_parameters(task: Task) -> None:
    """
    Save the parameters of a Task to file for debug.

    Parameters
    ----------
    task
        Task to save parameters for.
    """
    for site in task.portfolio:
        site_temp_dir = Path(_TEMP_DIR, str(task.task_id), site.site_data.site_id)
        site_temp_dir.mkdir(parents=True, exist_ok=True)
        Path(site_temp_dir, "site_range.json").write_text(site.site_range.model_dump_json())
