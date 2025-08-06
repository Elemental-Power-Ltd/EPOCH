import asyncio
import datetime
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

import httpx
from fastapi import APIRouter, HTTPException, Request

from app.internal.bayesian.bayesian import Bayesian
from app.internal.constraints import apply_default_constraints
from app.internal.datamanager import DataManagerDep
from app.internal.epoch_utils import simulation_result_to_pydantic
from app.internal.ga_utils import strip_annotations
from app.internal.grid_search import GridSearch, get_epoch_path
from app.internal.NSGA2 import NSGA2, SeparatedNSGA2, SeparatedNSGA2xNSGA2
from app.internal.portfolio_simulator import simulate_scenario
from app.internal.site_range import count_parameters_to_optimise
from app.internal.uuid7 import uuid7
from app.models.core import (
    EndpointTask,
    OptimisationResultEntry,
    PortfolioOptimisationResult,
    Site,
    SiteOptimisationResult,
    Task,
    TaskResponse,
    TaskResult,
)
from app.models.result import OptimisationResult
from app.routers.epl_queue import IQueue


class OptimiserFunc(Enum):
    """Mapping of optimiser types to optimiser class."""

    # TODO (2025-08-08 MHJB): should this be a dict instead? feels weird as an enum.
    NSGA2 = NSGA2
    GridSearch = GridSearch
    SeparatedNSGA2xNSGA2 = SeparatedNSGA2xNSGA2
    SeparatedNSGA2 = SeparatedNSGA2
    Bayesian = Bayesian


router = APIRouter()
logger = logging.getLogger("default")


def process_results(task: Task, results: OptimisationResult, completed_at: datetime.datetime) -> OptimisationResultEntry:
    """
    Process the results of a task, creating a portfolio result.

    Parameters
    ----------
    task
        The completed job
    results
        Results of the completed job
    completed_at
        When the job was finished (hopefully recently)

    Returns
    -------
    OptimisationResultEntry
        Format suitable to file in the database as a result with a new UUID
    """
    logger.info(f"Postprocessing results of {task.task_id}.")
    portfolios = []
    for portfolio_solution in results.solutions:
        portfolio_id = uuid7()
        site_results = []
        for site_id, site_solution in portfolio_solution.scenario.items():
            site_results.append(
                SiteOptimisationResult(
                    site_id=site_id,
                    portfolio_id=portfolio_id,
                    scenario=strip_annotations(site_solution.scenario),
                    metrics=simulation_result_to_pydantic(site_solution.simulation_result),
                )
            )
        portfolios.append(
            PortfolioOptimisationResult(
                task_id=task.task_id,
                portfolio_id=portfolio_id,
                # FIXME, type is wrong because PortfolioMetrics and SiteMetrics are different
                metrics=simulation_result_to_pydantic(portfolio_solution.simulation_result),
                site_results=site_results,
            )
        )

    tasks = TaskResult(task_id=task.task_id, n_evals=results.n_evals, exec_time=results.exec_time, completed_at=completed_at)

    return OptimisationResultEntry(portfolio=portfolios, tasks=tasks)


def check_epoch_versions() -> tuple[str | None, str | None]:
    """
    Check the versions of EPOCH's headless exe and EPOCH's python bindings.

    Returns
    -------
    tuple[str | None, str | None]
        Headless version (if available, None otherwise) and pybind version (if available, None otherwise)
    """
    has_headless = False
    has_bindings = False

    try:
        epoch_path = get_epoch_path()
        result = subprocess.run([epoch_path, "--version"], capture_output=True, text=True)
        headless_version = result.stdout.splitlines()[-1]
        has_headless = True
    except Exception as e:
        headless_version = None
        logger.debug(f"Failed to fetch headless version! {e}")

    try:
        import epoch_simulator

        pybind_version = epoch_simulator.__version__  # type: ignore
        has_bindings = True
    except Exception as e:
        pybind_version = None
        logger.debug(f"Failed to fetch epoch_simulator version! {e}")

    if has_headless and has_bindings:
        if pybind_version != headless_version:
            logger.error(f"EPOCH version do not match! Headless: {headless_version}. Pybind: {pybind_version}.")
        else:
            logger.info(f"Using EPOCH version {headless_version}.")

    elif not has_headless and has_bindings:
        logger.warning(f"Failed to fetch headless version! Found epoch_simulator version: {pybind_version}")

    elif has_headless and not has_bindings:
        logger.warning(f"Failed to fetch epoch_simulator version! Found headless version: {headless_version}")

    else:
        logger.warning("Failed to fetch both headless and epoch_simulator!")

    return headless_version, pybind_version


async def process_requests(q: IQueue) -> None:
    """
    Loop to process tasks in queue.

    Parameters
    ----------
    q
        Queue to process.
    """
    logger.info("Initialising worker loop.")
    check_epoch_versions()
    while True:
        logger.info("Awaiting next task from queue.")
        task, data_manager = await q.get()
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
            await data_manager.transmit_results(payload)
        except Exception:
            logger.error(f"Exception occured, skipping {task.task_id}.", exc_info=True)
            pass
        simulate_scenario.cache_clear()
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
    site = Site(name=endpoint_task.site_data.site_id, site_range=endpoint_task.site_range, site_data=endpoint_task.site_data)
    _, pybind_version = check_epoch_versions()
    epp_task = Task(
        name=endpoint_task.name,
        optimiser=endpoint_task.optimiser,
        objectives=endpoint_task.objectives,
        created_at=endpoint_task.created_at,
        portfolio=[site],
        client_id=endpoint_task.client_id,
        portfolio_constraints={},
        epoch_version=pybind_version,
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
    if sum(count_parameters_to_optimise(site.site_range) for site in task.portfolio) < 1:
        logger.warning(f"{task.task_id} has an empty search space.")
        raise HTTPException(
            status_code=400, detail="Task search space is empty. Found no asset values to optimise in site range."
        )
    try:
        await data_manager.fetch_portfolio_data(task)
        task.portfolio, task.portfolio_constraints = apply_default_constraints(
            existing_portfolio=task.portfolio, existing_constraints=task.portfolio_constraints
        )
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
