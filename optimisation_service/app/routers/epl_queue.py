import datetime
import logging

from fastapi import APIRouter, HTTPException, Request

from app.dependencies import QueueDep
from app.models.database import dataset_id_t
from app.models.epl_queue import QueueStatus, task_state

logger = logging.getLogger("default")


router = APIRouter()


@router.post("/queue-status")
async def get_queue_status(request: Request, queue: QueueDep) -> QueueStatus:
    """
    View tasks in queue.

    Parameters
    ----------
    request
        Internal FastAPI request with queue state
    queue

    Returns
    -------
    QueueStatus
    """
    time_now = datetime.datetime.now(datetime.UTC)
    return QueueStatus(queue=queue.uncancelled(), service_uptime=time_now - request.app.state.start_time)


@router.post("/cancel-task")
async def cancel_task_in_queue(task_id: dataset_id_t, queue: QueueDep) -> str:
    """
    Cancel task in queue.

    Can not be used to cancel tasks already running.

    Parameters
    ----------
    task_id
        UUID of task to cancel.

    Returns
    -------
    str
        Indicative string about what we just did
    """
    if queue.q[task_id].state == task_state.QUEUED:
        queue.cancel(task_id)
        return "Task cancelled."

    if task_id not in list(queue.q.keys()):
        logger.error(f"Task {task_id} not found in queue.")
        raise HTTPException(status_code=400, detail="Task not found in queue.")

    if queue.q[task_id].state == task_state.RUNNING:
        logger.error(f"Task {task_id} already running.")
        raise HTTPException(status_code=400, detail="Task already running.")

    if queue.q[task_id].state == task_state.CANCELLED:
        logger.error(f"Task {task_id} already cancelled.")
        raise HTTPException(status_code=400, detail="Task already cancelled.")

    raise HTTPException(status_code=400, detail=f"Unhandled task state for {task_id}: {queue.q[task_id].state}")


@router.post("/clear-queue")
async def clear_queue(queue: QueueDep) -> str:
    """
    Cancel all tasks in queue.

    Parameters
    ----------
    request
        Internal FastAPI request with queue state

    Returns
    -------
    str
        Indicative string about what we just did
    """
    logger.info("Clearing queue.")
    for task_id in queue.q.keys():
        if queue.q[task_id].state != task_state.RUNNING:
            queue.cancel(task_id)
    return "Queue cleared."
