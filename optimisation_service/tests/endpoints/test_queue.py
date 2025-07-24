from collections import OrderedDict

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from app.internal.datamanager import DataManager
from app.internal.uuid7 import uuid7
from app.main import app
from app.models.core import Task
from app.routers.epl_queue import IQueue, task_state


class TestQueueEndpoint:
    def test_queue_status(self) -> None:
        """
        Test /queue-status endpoint.
        """
        with TestClient(app) as client:
            response = client.post("/queue-status")
            assert response.status_code == 200, response.text

    @pytest.mark.slow
    def test_cancel_task(self, client: TestClient, default_task: Task) -> None:
        """
        Test /cancel-task endpoint.
        """
        _ = client.post("/submit-portfolio-task", json=jsonable_encoder(default_task))
        default_task.task_id = uuid7()
        _ = client.post("/submit-portfolio-task", json=jsonable_encoder(default_task))
        default_task.task_id = uuid7()
        _ = client.post("/submit-portfolio-task", json=jsonable_encoder(default_task))
        response = client.post("/cancel-task", params={"task_id": str(default_task.task_id)})
        assert response.status_code == 200, response.text

    def test_clear_queue(self, client: TestClient) -> None:
        """
        Test /clear-queue endpoint.
        """
        response = client.post("/clear-queue")
        assert response.status_code == 200, response.text


class TestQueue:
    def test_init(self) -> None:
        """
        Test IQueue class init.
        """
        IQueue(maxsize=5)

    def test_bad_init_maxsize(self) -> None:
        """
        Test IQueue class init with bad maxsize arg.
        """
        with pytest.raises(ValueError):
            IQueue(maxsize=-5)

    @pytest.mark.asyncio
    async def test_put(self, default_task: Task) -> None:
        """
        Test IQueue put method.
        """
        q = IQueue()
        await q.put((default_task, DataManager()))

    @pytest.mark.asyncio
    async def test_get(self, default_task: Task) -> None:
        """
        Test IQueue get method.
        """
        q = IQueue()
        await q.put((default_task, DataManager()))
        task, _ = await q.get()
        assert isinstance(task, Task)

    @pytest.mark.asyncio
    async def test_mark_task_done(self, default_task: Task) -> None:
        """
        Test Iqueue mark_task_done method.
        """
        q = IQueue()
        await q.put((default_task, DataManager()))
        assert default_task.task_id in q.q
        q.mark_task_done(default_task)
        assert default_task.task_id not in q.q

    @pytest.mark.asyncio
    async def test_cancel_task(self, default_task: Task) -> None:
        """
        Test IQueue cancel method.
        """
        q = IQueue()
        await q.put((default_task, DataManager()))
        q.cancel(default_task.task_id)
        assert q.q[default_task.task_id].state == task_state.CANCELLED

    @pytest.mark.asyncio
    async def test_uncancelled(self, default_task: Task) -> None:
        """
        Test IQueue uncancelled method.
        """
        q = IQueue()
        assert q.uncancelled() == OrderedDict()
        await q.put((default_task, DataManager()))
        uncancelled = q.uncancelled()
        assert isinstance(uncancelled, OrderedDict)
        assert default_task.task_id in uncancelled

    @pytest.mark.asyncio
    async def test_qsize(self, default_task: Task) -> None:
        """
        Test IQueue qsize method.
        """
        q = IQueue()
        assert q.qsize() == 0
        await q.put((default_task, DataManager()))
        assert q.qsize() == 1
