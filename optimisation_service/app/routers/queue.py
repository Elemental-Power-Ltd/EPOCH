import asyncio
from collections import OrderedDict
from enum import Enum

from fastapi import APIRouter, HTTPException, Request
from pydantic import UUID1

from .optimise import Task


class state(Enum):
    QUEUED = 0
    RUNNING = 1
    CANCELLED = 2


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
        self.q[task.UUID] = state.QUEUED

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
        if self.q[task.UUID] == state.QUEUED:
            self.q[task.UUID] = state.RUNNING
            return task
        elif self.q[task.UUID] == state.CANCELLED:
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
        self.q[UUID] = state.CANCELLED

    def uncancelled(self):
        """
        Ordered dictionary of not cancelled tasks in queue.
        """
        return OrderedDict((key, value) for key, value in self.q.items() if value != state.CANCELLED)

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


@router.post("/queue-status/")
async def get_queue_status(request: Request):
    """
    View tasks in queue.

    Returns
    -------
    Queue
    """
    return request.app.state.q.uncancelled()


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
    if request.app.state.q.q[UUID] == state.QUEUED:
        request.app.state.q.cancel(UUID)
        return "Task cancelled."
    elif UUID not in list(request.app.state.q.q.keys()):
        return HTTPException(status_code=400, detail="Task not found in queue.")
    elif request.app.state.q.q[UUID] == state.RUNNING:
        return HTTPException(status_code=400, detail="Task already running.")
    elif request.app.state.q.q[UUID] == state.CANCELLED:
        return HTTPException(status_code=400, detail="Task already cancelled.")
