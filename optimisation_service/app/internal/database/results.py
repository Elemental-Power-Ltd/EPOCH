import datetime
import logging

import httpx
from fastapi.encoders import jsonable_encoder

from app.internal.epoch_utils import simulation_result_to_pydantic
from app.internal.ga_utils import strip_annotations
from app.internal.uuid7 import uuid7
from app.models.core import (
    OptimisationResultEntry,
    PortfolioOptimisationResult,
    SiteOptimisationResult,
    Task,
    TaskResult,
)
from app.models.result import OptimisationResult

from .utils import _DB_URL

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
                metrics=simulation_result_to_pydantic(portfolio_solution.simulation_result),
                site_results=site_results,
            )
        )

    tasks = TaskResult(task_id=task.task_id, n_evals=results.n_evals, exec_time=results.exec_time, completed_at=completed_at)

    return OptimisationResultEntry(portfolio=portfolios, tasks=tasks)


async def transmit_results(results: OptimisationResultEntry, http_client: httpx.AsyncClient) -> None:
    """
    Transmit optimisation results to database.

    Parameters
    ----------
    results
        List of optimisation results.
    """
    logger.info("Adding results to database.")
    await http_client.post(url=_DB_URL + "/add-optimisation-results", json=jsonable_encoder(results))
