import asyncio
import datetime
import logging
from collections import OrderedDict
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from .models.core import Task
from .models.queue import QueueElem, QueueStatus, task_state

logger = logging.getLogger("default")


class IQueue(asyncio.Queue):
    """
    Inspectable Queue with cancelling of tasks.
    """

    def __init__(self, maxsize: int = 0) -> None:
        """
        Parameters
        ----------
        maxsize
            Maximum number of tasks to hold in queue.
        """
        logger.info("Initalisaing Queue.")
        super().__init__(maxsize=0)
        self.q: OrderedDict = OrderedDict()
        self.q_len = maxsize

    async def put(self, task: Task):
        """
        Add task in queue.

        Parameters
        ----------
        task
            Task to add in queue.
        """
        logger.info(f"Queued {task.task_id}.")
        await super().put(task)
        self.q[task.task_id] = QueueElem(state=task_state.QUEUED, added_at=datetime.datetime.now(datetime.UTC))

    async def get(self) -> Task:
        """
        Get next task from queue.
        Skips cancelled tasks.
        Waits if queue is empty.

        Returns
        -------
        task
            Next task in queue.
        """
        task = await super().get()
        assert self.q[task.task_id].state == task_state.QUEUED or self.q[task.task_id].STATE == task_state.CANCELLED
        if self.q[task.task_id].state == task_state.QUEUED:
            self.q[task.task_id].state = task_state.RUNNING
            return task
        elif self.q[task.task_id].state == task_state.CANCELLED:
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

    def cancel(self, task_id: UUID):
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

    def uncancelled(self) -> OrderedDict:
        """
        Ordered dictionary of not cancelled tasks in queue.
        """
        return OrderedDict((key, value) for key, value in self.q.items() if value.state != task_state.CANCELLED)

    def qsize(self) -> int:
        """
        Number of not cancelled tasks in queue.
        """
        return len(self.uncancelled())

    def full(self):
        """
        Check if queue is full.

        Returns
        -------
        boolean
            True if full, False otherwise.
        """
        if self.qsize() >= self.q_len:
            return True
        else:
            return False


router = APIRouter()


@router.post("/queue-status/", response_model=QueueStatus)
async def get_queue_status(request: Request):
    """
    View tasks in queue.

    Returns
    -------
    Queue
    """
    time_now = datetime.datetime.now(datetime.UTC)
    return QueueStatus(queue=request.app.state.q.uncancelled(), service_uptime=request.app.state.start_time - time_now)


@router.post("/cancel-task/")
async def cancel_task_in_queue(request: Request, task_id: UUID):
    """
    Cancels task in queue.
    Can not be used to cancel tasks already running.

    Parameters
    ----------
    task_id
        UUID of task to cancel.
    """
    logger.debug(f"Cancelling task {task_id}.")
    if request.app.state.q.q[task_id].state == task_state.QUEUED:
        request.app.state.q.cancel(task_id)
        logger.info(f"Cancelled task {task_id}.")
        return "Task cancelled."
    elif task_id not in list(request.app.state.q.q.keys()):
        logger.error(f"Task {task_id} not found in queue.")
        return HTTPException(status_code=400, detail="Task not found in queue.")
    elif request.app.state.q.q[task_id].state == task_state.RUNNING:
        logger.error(f"Task {task_id} already running.")
        return HTTPException(status_code=400, detail="Task already running.")
    elif request.app.state.q.q[task_id].state == task_state.CANCELLED:
        logger.error(f"Task {task_id} already cancelled.")
        return HTTPException(status_code=400, detail="Task already cancelled.")


@router.post("/clear-queue/")
async def clear_queue(request: Request):
    """
    Cancels all tasks in queue.
    """
    logger.info("Clearing queue.")
    for task_id in request.app.state.q.q.keys():
        if request.app.state.q.q[task_id].STATE != task_state.RUNNING:
            request.app.state.q.cancel(task_id)
