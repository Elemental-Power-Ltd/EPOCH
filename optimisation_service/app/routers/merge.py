"""Endpoints to merge existing results."""

import datetime
import logging

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.dependencies import HTTPClient, HttpClientDep
from app.internal.database.results import process_results, transmit_results
from app.internal.database.site_data import get_bundle_timestamps, get_bundled_data, site_data_entries_to_epoch_site_data
from app.internal.database.utils import _DB_URL
from app.internal.epoch import get_epoch_version
from app.internal.portfolio_simulator import PortfolioSimulator
from app.internal.uuid7 import uuid7
from app.models.database import bundle_id_t, dataset_id_t, site_id_t
from app.models.epoch_types.site_range_type import Config, SiteRange
from app.models.ga_utils import AnnotatedTaskData
from app.models.result import OptimisationResult, PortfolioSolution

logger = logging.getLogger("default")

router = APIRouter()


class SiteInfo(BaseModel):
    """Site level information required to merge site scenairos into portfolio scenarios."""

    site_id: site_id_t
    bundle_id: bundle_id_t
    config: Config
    scenarios: list[AnnotatedTaskData]


class PortfolioMergeRequest(BaseModel):
    """Information required to merge site scenairos into portfolio scenarios."""

    sites: list[SiteInfo]
    client_id: str
    task_name: str


@router.post("/merge-site-scenarios")
async def merge_site_scenarios_into_portfolios_and_transmit(
    merge_request: PortfolioMergeRequest, http_client: HttpClientDep
) -> dataset_id_t:
    """
    Merge lists of site scenarios into a list of portfolio scenarios.

    We re-evaluate each portfolio to caculate portfolio level metrics.
    This requires bundle_ids for epoch data and configs.

    Parameters
    ----------
    site_scenario_lists
        Dictionnary of site_ids to lists of site scenarios.
        All lists should be of same length.
    bundle_ids
        Dictionnary of site_ids to bundle_ids.
    configs
        Dictionnary of site_ids to configs.
        Must be site_range configs, not task_data configs.

    Retunrs
    -------
    task_id
        The task_id of the newly generated results.
    """
    bundle_ids = {site.site_id: site.bundle_id for site in merge_request.sites}
    portfolio_solutions = await merge_site_scenarios_into_portfolios(
        site_scenario_lists={site.site_id: site.scenarios for site in merge_request.sites},
        bundle_ids=bundle_ids,
        configs={site.site_id: site.config for site in merge_request.sites},
        http_client=http_client,
    )

    portfolio_range = {site.site_id: SiteRange(config=site.config) for site in merge_request.sites}

    task_id = uuid7()

    logger.info(f"Adding merge request {task_id} to database.")
    data = {
        "client_id": merge_request.client_id,
        "task_name": merge_request.task_name,
        "task_id": task_id,
        "bundle_ids": bundle_ids,
        "epoch_version": get_epoch_version(),
        "created_at": datetime.datetime.now(datetime.UTC),
        "portfolio_range": portfolio_range,
        "optimiser": {"name": "NSGA2", "hyperparameters": None},
        "objectives": [],
        "portfolio_constraints": None,
        "site_constraints": {site.site_id: {} for site in merge_request.sites},
    }
    response = await http_client.post(url=_DB_URL + "/add-optimisation-task", json=jsonable_encoder(data))

    assert response.is_success, response.text

    results = OptimisationResult(
        solutions=portfolio_solutions, exec_time=datetime.timedelta(seconds=1), n_evals=len(portfolio_solutions)
    )

    completed_at = datetime.datetime.now(datetime.UTC)
    payload = process_results(task_id=task_id, results=results, completed_at=completed_at)
    await transmit_results(results=payload, http_client=http_client)

    return task_id


async def merge_site_scenarios_into_portfolios(
    site_scenario_lists: dict[site_id_t, list[AnnotatedTaskData]],
    bundle_ids: dict[site_id_t, bundle_id_t],
    configs: dict[site_id_t, Config],
    http_client: HTTPClient,
) -> list[PortfolioSolution]:
    """
    Merge lists of site scenarios into a list of portfolio scenarios.

    We re-evaluate each portfolio to caculate portfolio level metrics.
    This requires bundle_ids for epoch data and configs.

    Parameters
    ----------
    site_scenario_lists
        Dictionnary of site_ids to lists of site scenarios.
        All lists should be of same length.
    bundle_ids
        Dictionnary of site_ids to bundle_ids.
    configs
        Dictionnary of site_ids to configs.
    http_client
        Asynchronous HTTP client to use for requests.

    Retunrs
    -------
    portfolio_solutions
        List of portfolio solutions.
    """
    if site_scenario_lists.keys() != bundle_ids.keys() != configs.keys():
        raise ValueError("Mismatch in input indexes!")
    if len({len(v) for v in site_scenario_lists.values()}) != 1:
        raise ValueError("Can not merge site scenarios into portfolios. Not all site scenario lists have the same length!")

    epoch_data_dict = {}
    for site_id, bundle_id in bundle_ids.items():
        site_data_entries = await get_bundled_data(bundle_id=bundle_id, http_client=http_client)
        start_ts, end_ts = await get_bundle_timestamps(bundle_id=bundle_id, http_client=http_client)
        epoch_data = site_data_entries_to_epoch_site_data(site_data_entries, start_ts, end_ts)
        epoch_data_dict[site_id] = epoch_data

    ps = PortfolioSimulator(epoch_data_dict=epoch_data_dict, epoch_config_dict=configs)

    portfolio_solutions = []
    for site_scenarios in zip(*site_scenario_lists.values(), strict=False):
        portfolio_scenario = dict(zip(site_scenario_lists.keys(), site_scenarios, strict=False))
        portfolio_solution = ps.simulate_portfolio(portfolio_scenario)
        portfolio_solutions.append(portfolio_solution)

    return portfolio_solutions
