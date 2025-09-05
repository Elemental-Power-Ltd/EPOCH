import logging

import httpx
from fastapi.encoders import jsonable_encoder

from app.models.core import Task

from .utils import _DB_URL

logger = logging.getLogger("default")


async def transmit_task(task: Task, http_client: httpx.AsyncClient) -> None:
    """
    Transmit optimisation task to database.

    Parameters
    ----------
    task
        Optimisation task.
    http_client
        Asynchronous HTTP client to use for requests.
    """
    logger.info(f"Adding {task.task_id} to database.")
    portfolio_range, bundle_ids, site_constraints = {}, {}, {}
    for site in task.portfolio:
        site_id = site.site_data.site_id
        portfolio_range[site_id] = site.site_range
        site_constraints[site_id] = site.constraints
        bundle_ids[site_id] = site.site_data.bundle_id
    data = {
        "client_id": task.client_id,
        "task_id": task.task_id,
        "task_name": task.name,
        "objectives": task.objectives,
        "optimiser": task.optimiser,
        "created_at": task.created_at,
        "portfolio_range": portfolio_range,
        "bundle_ids": bundle_ids,
        "portfolio_constraints": task.portfolio_constraints,
        "site_constraints": site_constraints,
    }
    await http_client.post(url=_DB_URL + "/add-optimisation-task", json=jsonable_encoder(data))
