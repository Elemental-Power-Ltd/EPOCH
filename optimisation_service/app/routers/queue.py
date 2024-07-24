import asyncio
import datetime
import time
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum

from fastapi import APIRouter, HTTPException, Request
from pydantic import UUID1

from .optimise import Task


class state(Enum):
    QUEUED = 0
    RUNNING = 1
    CANCELLED = 2


@dataclass()
class QueueElem:
    STATE: state
    added_at: datetime.datetime


@dataclass()
class QueueStatus:
    queue: dict[UUID1, QueueElem]
    service_uptime: float


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
        super().__init__(maxsize=0)
        self.q = OrderedDict()
        self.q_len = maxsize

    async def put(self, task: Task):
        """
        Add task in queue.

        Parameters
        ----------
        task
            Task to add in queue.
        """
        await super().put(task)
        self.q[task.UUID] = QueueElem(state.QUEUED, datetime.datetime.now(datetime.UTC))

    async def get(self):
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
        if self.q[task.UUID].STATE == state.QUEUED:
            self.q[task.UUID].STATE = state.RUNNING
            return task
        elif self.q[task.UUID].STATE == state.CANCELLED:
            del self.q[task.UUID]
            return await self.get()

    def task_done(self, task: Task) -> None:
        """
        Mark task as done.

        Parameters
        ----------
        task
            Task to mark as done
        """
        del self.q[task.UUID]
        super().task_done()

    def cancel(self, UUID: UUID1):
        """
        Cancel a task in queue.

        Parameters
        ----------
        UUID
            UUID of task to cancel
        """
        assert self.q[UUID].STATE != state.RUNNING, "Task already running."
        self.q[UUID].STATE = state.CANCELLED

    def uncancelled(self):
        """
        Ordered dictionary of not cancelled tasks in queue.
        """
        return OrderedDict((key, value) for key, value in self.q.items() if value.STATE != state.CANCELLED)

    def qsize(self):
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
    return QueueStatus(request.app.state.q.uncancelled(), time.time() - request.app.state.start_time)


@router.post("/cancel-task/")
async def cancel_task_in_queue(request: Request, UUID: UUID1):
    """
    Cancels task in queue.
    Can not be used to cancel tasks already running.

    Parameters
    ----------
    UUID
        UUID of task to cancel.
    """
    if request.app.state.q.q[UUID].STATE == state.QUEUED:
        request.app.state.q.cancel(UUID)
        return "Task cancelled."
    elif UUID not in list(request.app.state.q.q.keys()):
        return HTTPException(status_code=400, detail="Task not found in queue.")
    elif request.app.state.q.q[UUID].STATE == state.RUNNING:
        return HTTPException(status_code=400, detail="Task already running.")
    elif request.app.state.q.q[UUID].STATE == state.CANCELLED:
        return HTTPException(status_code=400, detail="Task already cancelled.")


@router.post("/clear-queue/")
async def clear_queue(request: Request):
    """
    Cancels all tasks in queue.
    """
    for UUID in request.app.state.q.q.keys():
        if request.app.state.q.q[UUID].STATE != state.RUNNING:
            request.app.state.q.cancel(UUID)
