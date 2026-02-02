import datetime
import logging

from app.dependencies import HTTPClient
from app.internal.epoch.converters import simulation_result_to_pydantic
from app.internal.ga_utils import strip_annotations
from app.internal.uuid7 import uuid7
from app.models.core import (
    OptimisationResultEntry,
    PortfolioOptimisationResult,
    SiteOptimisationResult,
    TaskResult,
)
from app.models.database import dataset_id_t
from app.models.result import OptimisationResult
from app.models.simulate import LegacyResultReproConfig, NewResultReproConfig, result_repro_config_t
from fastapi.encoders import jsonable_encoder

from .utils import _DB_URL

logger = logging.getLogger("default")


def process_results(
    task_id: dataset_id_t, results: OptimisationResult, completed_at: datetime.datetime
) -> OptimisationResultEntry:
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
    logger.info(f"Postprocessing results of {task_id}.")
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
                    is_feasible=site_solution.is_feasible,
                )
            )
        portfolios.append(
            PortfolioOptimisationResult(
                task_id=task_id,
                portfolio_id=portfolio_id,
                metrics=simulation_result_to_pydantic(portfolio_solution.simulation_result),
                site_results=site_results,
                is_feasible=portfolio_solution.is_feasible,
            )
        )

    tasks = TaskResult(task_id=task_id, n_evals=results.n_evals, exec_time=results.exec_time, completed_at=completed_at)

    return OptimisationResultEntry(portfolio=portfolios, tasks=tasks)


async def transmit_results(results: OptimisationResultEntry, http_client: HTTPClient) -> None:
    """
    Transmit optimisation results to database.

    Parameters
    ----------
    results
        List of optimisation results.
    http_client
        Asynchronous HTTP client to use for requests.
    """
    logger.info("Adding results to database.")
    await http_client.post(url=_DB_URL + "/add-optimisation-results", json=jsonable_encoder(results))


async def get_result_configuration(portfolio_id: dataset_id_t, http_client: HTTPClient) -> result_repro_config_t:
    """
    Get the configuration that was used to generate a portfolio result that is stored in the database.

    Parameters
    ----------
    portfolio_id
        UUID associated with a portfolio optimisation result.
    http_client
        Asynchronous HTTP client to use for requests.

    Returns
    -------
    ResultReproConfig
        Portfolio configuration
    """
    response = await http_client.post(url=_DB_URL + "/get-result-configuration", json={"result_id": str(portfolio_id)})
    data = response.json()
    logger.info(f"Got result configuration: {data}")
    if "site_data" in data:
        return LegacyResultReproConfig.model_validate(data)
    return NewResultReproConfig.model_validate(data)
