import asyncio
import datetime
import logging
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

import httpx
from fastapi import APIRouter, HTTPException, Request

from app.internal.constraints import get_shortfall_constraints
from app.internal.datamanager import DataManagerDep
from app.internal.epoch_utils import convert_TaskData_to_dictionary
from app.internal.grid_search import GridSearch, get_epoch_path
from app.internal.NSGA2 import NSGA2
from app.internal.portfolio_simulator import simulate_scenario
from app.internal.site_range import count_parameters_to_optimise
from app.models.core import (
    EndpointTask,
    OptimisationResultEntry,
    PortfolioMetrics,
    PortfolioOptimisationResult,
    Site,
    SiteMetrics,
    SiteOptimisationResult,
    Task,
    TaskResponse,
    TaskResult,
)
from app.models.metrics import Metric
from app.models.result import OptimisationResult
from app.routers.epl_queue import IQueue


class OptimiserFunc(Enum):
    NSGA2 = NSGA2
    GridSearch = GridSearch


router = APIRouter()
logger = logging.getLogger("default")


def process_results(task: Task, results: OptimisationResult, completed_at: datetime.datetime) -> OptimisationResultEntry:
    logger.info(f"Postprocessing results of {task.task_id}.")
    portfolios = []
    for portfolio_solution in results.solutions:
        portfolio_id = uuid.uuid4()
        site_results = []
        for site_id, site_solution in portfolio_solution.scenario.items():
            site_results.append(
                SiteOptimisationResult(
                    site_id=site_id,
                    portfolio_id=portfolio_id,
                    scenario=convert_TaskData_to_dictionary(site_solution.scenario),
                    metrics=SiteMetrics(
                        carbon_balance_scope_1=site_solution.metric_values[Metric.carbon_balance_scope_1],
                        carbon_balance_scope_2=site_solution.metric_values[Metric.carbon_balance_scope_2],
                        carbon_cost=site_solution.metric_values[Metric.carbon_cost],
                        cost_balance=site_solution.metric_values[Metric.cost_balance],
                        capex=site_solution.metric_values[Metric.capex],
                        payback_horizon=site_solution.metric_values[Metric.payback_horizon],
                        annualised_cost=site_solution.metric_values[Metric.annualised_cost],
                        total_gas_used=site_solution.metric_values[Metric.total_gas_used],
                        total_electricity_imported=site_solution.metric_values[Metric.total_electricity_imported],
                        total_electricity_generated=site_solution.metric_values[Metric.total_electricity_generated],
                        total_electricity_exported=site_solution.metric_values[Metric.total_electricity_exported],
                        total_electrical_shortfall=site_solution.metric_values[Metric.total_electrical_shortfall],
                        total_heat_shortfall=site_solution.metric_values[Metric.total_heat_shortfall],
                        total_gas_import_cost=site_solution.metric_values[Metric.total_gas_import_cost],
                        total_electricity_import_cost=site_solution.metric_values[Metric.total_electricity_import_cost],
                        total_electricity_export_gain=site_solution.metric_values[Metric.total_electricity_export_gain],
                    ),
                )
            )
        portfolios.append(
            PortfolioOptimisationResult(
                task_id=task.task_id,
                portfolio_id=portfolio_id,
                metrics=PortfolioMetrics(
                    carbon_balance_scope_1=portfolio_solution.metric_values[Metric.carbon_balance_scope_1],
                    carbon_balance_scope_2=portfolio_solution.metric_values[Metric.carbon_balance_scope_2],
                    carbon_cost=portfolio_solution.metric_values[Metric.carbon_cost],
                    cost_balance=portfolio_solution.metric_values[Metric.cost_balance],
                    capex=portfolio_solution.metric_values[Metric.capex],
                    payback_horizon=portfolio_solution.metric_values[Metric.payback_horizon],
                    annualised_cost=portfolio_solution.metric_values[Metric.annualised_cost],
                    total_gas_used=portfolio_solution.metric_values[Metric.total_gas_used],
                    total_electricity_imported=portfolio_solution.metric_values[Metric.total_electricity_imported],
                    total_electricity_generated=portfolio_solution.metric_values[Metric.total_electricity_generated],
                    total_electricity_exported=portfolio_solution.metric_values[Metric.total_electricity_exported],
                    total_electrical_shortfall=portfolio_solution.metric_values[Metric.total_electrical_shortfall],
                    total_heat_shortfall=portfolio_solution.metric_values[Metric.total_heat_shortfall],
                    total_gas_import_cost=portfolio_solution.metric_values[Metric.total_gas_import_cost],
                    total_electricity_import_cost=portfolio_solution.metric_values[Metric.total_electricity_import_cost],
                    total_electricity_export_gain=portfolio_solution.metric_values[Metric.total_electricity_export_gain],
                ),
                site_results=site_results,
            )
        )

    tasks = TaskResult(task_id=task.task_id, n_evals=results.n_evals, exec_time=results.exec_time, completed_at=completed_at)

    return OptimisationResultEntry(portfolio=portfolios, tasks=tasks)


def check_epoch_versions():
    """
    Checks the versions of EPOCH's headless exe and EPOCH's python bindings.
    """
    has_headless = False
    has_bindings = False

    try:
        epoch_path = get_epoch_path()
        result = subprocess.run([epoch_path, "--version"], capture_output=True, text=True)
        headless_version = result.stdout.splitlines()[-1]
        has_headless = True
    except Exception as e:
        logger.debug(f"Failed to fetch headless version! {e}")

    try:
        import epoch_simulator

        pybind_version = epoch_simulator.__version__  # type: ignore
        has_bindings = True
    except Exception as e:
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
            optimiser = OptimiserFunc[task.optimiser.name].value(**task.optimiser.hyperparameters.model_dump(mode="python"))
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

    epp_task = Task(
        name=endpoint_task.name,
        optimiser=endpoint_task.optimiser,
        objectives=endpoint_task.objectives,
        created_at=endpoint_task.created_at,
        portfolio=[site],
        client_id=endpoint_task.client_id,
        portfolio_constraints={},
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
        task.portfolio_constraints = task.portfolio_constraints | get_shortfall_constraints(task.portfolio)
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
