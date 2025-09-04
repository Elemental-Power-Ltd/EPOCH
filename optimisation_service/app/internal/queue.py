import asyncio
import datetime
import logging
from collections import OrderedDict

from pydantic import PositiveInt

from app.models.core import Task
from app.models.database import dataset_id_t
from app.models.epl_queue import QueueElem, task_state

logger = logging.getLogger("default")


class IQueue(asyncio.Queue[Task]):
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

    def __getitem__(self, key: dataset_id_t) -> QueueElem:
        """
        Retrieve a queued element by its dataset id.

        Parameters
        ----------
        key
            The dataset id used as the key in the queue.

        Returns
        -------
        QueueElem
            The element associated with the given dataset id.
        """
        return self.q[key]

    def __contains__(self, key: dataset_id_t) -> bool:
        """
        Check if the queue contains an element with the given dataset id.

        Parameters
        ----------
        key
            The dataset identifier to look for in the queue.

        Returns
        -------
        bool
            True if the key is present, False otherwise.
        """
        return key in self.q

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
        logger.info(f"{task.task_id} retrieved from queue.")
        assert self.q[task.task_id].state == task_state.QUEUED or self.q[task.task_id].state == task_state.CANCELLED
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
