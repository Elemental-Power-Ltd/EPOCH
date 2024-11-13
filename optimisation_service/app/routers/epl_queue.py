import asyncio
import datetime
import logging
import shutil
from collections import OrderedDict

from fastapi import APIRouter, HTTPException, Request
from pydantic import UUID4, PositiveInt

from ..models.epl_queue import QueueElem, QueueStatus, task_state
from ..models.tasks import Task

logger = logging.getLogger("default")


class IQueue(asyncio.Queue):
    """
    Inspectable Queue with cancelling of tasks.
    """

    def __init__(self, maxsize: PositiveInt = 1, remove_directory: bool = False) -> None:
        """
        Parameters
        ----------
        maxsize
            Maximum number of tasks to hold in queue.
        remove_directory
            Whether to remove the directory when we're finished with a task.
        """
        logger.info("Initialising Queue.")
        if maxsize <= 0:
            raise ValueError("Queue maxsize must be positive integer.")
        super().__init__(maxsize=0)
        self.q: OrderedDict = OrderedDict()
        self.q_len = maxsize
        self.remove_directory = remove_directory

    async def put(self, task: Task) -> None:
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
        if self.remove_directory:
            shutil.rmtree(task.data_manager.portfolio_dir)
        super().task_done()

    def cancel(self, task_id: UUID4) -> None:
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

    Returns
    -------
    Queue
    """
    time_now = datetime.datetime.now(datetime.UTC)
    return QueueStatus(queue=request.app.state.q.uncancelled(), service_uptime=time_now - request.app.state.start_time)


@router.post("/cancel-task")
async def cancel_task_in_queue(request: Request, task_id: UUID4) -> str:
    """
    Cancels task in queue.
    Can not be used to cancel tasks already running.

    Parameters
    ----------
    task_id
        UUID of task to cancel.
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
    Cancels all tasks in queue.
    """
    logger.info("Clearing queue.")
    for task_id in request.app.state.q.q.keys():
        if request.app.state.q.q[task_id].STATE != task_state.RUNNING:
            request.app.state.q.cancel(task_id)
    return "Queue cleared."
