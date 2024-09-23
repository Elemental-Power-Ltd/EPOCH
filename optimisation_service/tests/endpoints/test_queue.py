from collections import OrderedDict

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from app.main import app
from app.routers.models.core import EndpointTask
from app.routers.models.tasks import Task
from app.routers.queue import IQueue, task_state


class TestQueueEndpoint:
    def test_queue_status(self):
        """
        Test /queue-status endpoint.
        """
        with TestClient(app) as client:
            response = client.post("/queue-status")
            assert response.status_code == 200

    @pytest.mark.slow
    def test_cancel_task(self, client: TestClient, endpointtask_factory: EndpointTask):
        """
        Test /cancel-task endpoint.
        """
        task1 = endpointtask_factory()
        task2 = endpointtask_factory()
        _ = client.post("/submit-task", json=jsonable_encoder(task1))
        response2 = client.post("/submit-task", json=jsonable_encoder(task2))
        task2_id = response2.json()["task_id"]
        response = client.post("/cancel-task", params={"task_id": task2_id})
        assert response.status_code == 200

    def test_clear_queue(self, client: TestClient):
        """
        Test /clear-queue endpoint.
        """
        response = client.post("/clear-queue")
        assert response.status_code == 200


class TestQueue:
    def test_init(self):
        """
        Test IQueue class init.
        """
        IQueue(maxsize=5)

    def test_bad_init_maxsize(self):
        """
        Test IQueue class init with bad maxsize arg.
        """
        with pytest.raises(ValueError):
            IQueue(maxsize=-5)

    @pytest.mark.asyncio
    async def test_put(self, task_factory: Task):
        """
        Test IQueue put method.
        """
        q = IQueue()
        await q.put(task_factory())

    @pytest.mark.asyncio
    async def test_get(self, task_factory: Task):
        """
        Test IQueue get method.
        """
        q = IQueue()
        await q.put(task_factory())
        task = await q.get()
        assert isinstance(task, Task)

    @pytest.mark.asyncio
    async def test_mark_task_done(self, task_factory: Task):
        """
        Test Iqueue mark_task_done method.
        """
        q = IQueue()
        task = task_factory()
        await q.put(task)
        assert task.task_id in q.q
        q.mark_task_done(task)
        assert task.task_id not in q.q

    @pytest.mark.asyncio
    async def test_cancel_task(self, task_factory: Task):
        """
        Test IQueue cancel method.
        """
        q = IQueue()
        task = task_factory()
        await q.put(task)
        q.cancel(task.task_id)
        assert q.q[task.task_id].state == task_state.CANCELLED

    @pytest.mark.asyncio
    async def test_uncancelled(self, task_factory: Task):
        """
        Test IQueue uncancelled method.
        """
        q = IQueue()
        task = task_factory()
        assert q.uncancelled() == OrderedDict()
        await q.put(task)
        uncancelled = q.uncancelled()
        assert isinstance(uncancelled, OrderedDict)
        assert task.task_id in uncancelled

    @pytest.mark.asyncio
    async def test_qsize(self, task_factory: Task):
        """
        Test IQueue qsize method.
        """
        q = IQueue()
        assert q.qsize() == 0
        await q.put(task_factory())
        assert q.qsize() == 1
