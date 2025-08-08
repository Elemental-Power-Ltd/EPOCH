import asyncio
import datetime
import logging
from collections import OrderedDict

from fastapi import APIRouter, HTTPException, Request
from pydantic import PositiveInt

from app.models.core import Task
from app.models.database import dataset_id_t
from app.models.epl_queue import QueueElem, QueueStatus, TaskWDataManager, task_state

logger = logging.getLogger("default")


class IQueue(asyncio.Queue[TaskWDataManager]):
    """Inspectable Queue with cancelling of tasks."""

    def __init__(self, maxsize: PositiveInt = 1) -> None:
        """
        Create the queue.

        Parameters
        ----------
        maxsize
            Maximum number of tasks to hold in queue.
        """
        logger.info("Initialising Queue.")
        if maxsize <= 0:
            raise ValueError("Queue maxsize must be positive integer.")
        super().__init__(maxsize=0)
        self.q: OrderedDict[dataset_id_t, QueueElem] = OrderedDict()
        self.q_len = maxsize

    async def put(self, task_w_datamanager: TaskWDataManager) -> None:
        """
        Add task in queue.

        Parameters
        ----------
        task_w_datamanager
            Task to add in queue with associated data manager
        """
        task, _ = task_w_datamanager
        logger.info(f"Queued {task.task_id}.")
        await super().put(task_w_datamanager)
        self.q[task.task_id] = QueueElem(state=task_state.QUEUED, added_at=datetime.datetime.now(datetime.UTC))

    async def get(self) -> TaskWDataManager:
        """
        Get next task from queue.

        Skips cancelled tasks.
        Waits if queue is empty.

        Returns
        -------
        task
            Next task in queue with associated data manager
        """
        task, data_manager = await super().get()
        logger.info(f"{task.task_id} retrieved from queue.")
        assert self.q[task.task_id].state == task_state.QUEUED or self.q[task.task_id].state == task_state.CANCELLED
        if self.q[task.task_id].state == task_state.QUEUED:
            self.q[task.task_id].state = task_state.RUNNING
            return task, data_manager
        else:
            self.mark_task_done(task)
            return await self.get()

    def mark_task_done(self, task: Task) -> None:
        """
        Mark task as done.

        Parameters
        ----------
        task
            Task to mark as done
        """
        logger.info(f"Marking as done {task.task_id}.")
        del self.q[task.task_id]
        super().task_done()

    def cancel(self, task_id: dataset_id_t) -> None:
        """
        Cancel a task in queue.

        Parameters
        ----------
        task_id
            UUID of task to cancel
        """
        logger.info(f"Cancelling {task_id}.")
        assert self.q[task_id].state != task_state.RUNNING, "Task already running."
        self.q[task_id].state = task_state.CANCELLED

    def uncancelled(self) -> OrderedDict[dataset_id_t, QueueElem]:
        """
        Ordered dictionary of not cancelled tasks in queue.

        Returns
        -------
        OrderedDict
            All jobs in their current order to be processed
        """
        return OrderedDict((key, value) for key, value in self.q.items() if value.state != task_state.CANCELLED)

    def qsize(self) -> int:
        """
        Get the number of not cancelled tasks in queue.

        Returns
        -------
        int
            number of uncancelled jobs
        """
        return len(self.uncancelled())

    def full(self) -> bool:
        """
        Check if queue is full.

        Returns
        -------
        boolean
            True if full, False otherwise.
        """
        return self.qsize() >= self.q_len


router = APIRouter()


@router.post("/queue-status")
async def get_queue_status(request: Request) -> QueueStatus:
    """
    View tasks in queue.

    Parameters
    ----------
    request
        Internal FastAPI request with queue state

    Returns
    -------
    QueueStatus
    """
    time_now = datetime.datetime.now(datetime.UTC)
    return QueueStatus(queue=request.app.state.q.uncancelled(), service_uptime=time_now - request.app.state.start_time)


@router.post("/cancel-task")
async def cancel_task_in_queue(request: Request, task_id: dataset_id_t) -> str:
    """
    Cancel task in queue.

    Can not be used to cancel tasks already running.

    Parameters
    ----------
    request
        Internal FastAPI request with queue state
    task_id
        UUID of task to cancel.

    Returns
    -------
    str
        Indicative string about what we just did
    """
    if request.app.state.q.q[task_id].state == task_state.QUEUED:
        request.app.state.q.cancel(task_id)
        return "Task cancelled."

    if task_id not in list(request.app.state.q.q.keys()):
        logger.error(f"Task {task_id} not found in queue.")
        raise HTTPException(status_code=400, detail="Task not found in queue.")

    if request.app.state.q.q[task_id].state == task_state.RUNNING:
        logger.error(f"Task {task_id} already running.")
        raise HTTPException(status_code=400, detail="Task already running.")

    if request.app.state.q.q[task_id].state == task_state.CANCELLED:
        logger.error(f"Task {task_id} already cancelled.")
        raise HTTPException(status_code=400, detail="Task already cancelled.")

    raise HTTPException(status_code=400, detail=f"Unhandled task state for {task_id}: {request.app.state.q.q[task_id].state}")


@router.post("/clear-queue")
async def clear_queue(request: Request) -> str:
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
    for task_id in request.app.state.q.q.keys():
        if request.app.state.q.q[task_id].STATE != task_state.RUNNING:
            request.app.state.q.cancel(task_id)
    return "Queue cleared."
