import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

from app.dependencies import HttpClientDep, QueueDep
from app.internal.constraints import apply_default_constraints
from app.internal.database.site_data import fetch_portfolio_data
from app.internal.database.tasks import transmit_task
from app.internal.hacks import extend_config_capex_limits_to_constraints
from app.internal.site_range import count_parameters_to_optimise
from app.models.core import (
    Task,
    TaskResponse,
)

router = APIRouter()
logger = logging.getLogger("default")


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
    if task.task_id in queue:
        logger.warning(f"{task.task_id} already in queue.")
        raise HTTPException(status_code=400, detail="Task already in queue.")
    if sum(count_parameters_to_optimise(site.site_range) for site in task.portfolio) < 1:
        logger.warning(f"{task.task_id} has an empty search space.")
        raise HTTPException(
            status_code=400, detail="Task search space is empty. Found no asset values to optimise in site range."
        )
    try:
        extend_config_capex_limits_to_constraints(portfolio=task.portfolio)
        await fetch_portfolio_data(task=task, http_client=http_client)
        task.portfolio, task.portfolio_constraints = apply_default_constraints(
            existing_portfolio=task.portfolio, existing_constraints=task.portfolio_constraints
        )
        save_parameters(task=task)
        await transmit_task(task=task, http_client=http_client)
        await queue.put(task)
        return TaskResponse(task_id=task.task_id)
    except httpx.HTTPStatusError as e:
        logger.warning(f"Failed to add task to database: {e.response.text!s}")
        raise HTTPException(status_code=500, detail=f"Failed to add task to database: {e.response.text!s}") from e
    except Exception as e:
        logger.warning(f"Failed to add task to queue: {type(e).__name__}: {e!s}")
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
