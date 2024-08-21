import os
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.internal.models.algorithms import Optimiser
from app.routers.models.core import EndpointTask
from app.routers.optimise import convert_task
from app.routers.utils.datamanager import DataManager


def test_submit_task(client: TestClient, endpointtask_factory: EndpointTask):
    """
    Test /submit-task endpoint.
    """
    task = endpointtask_factory()
    response = client.post("/submit-task", json=task)
    assert response.status_code == 200, response.text
    while task["task_id"] in client.post("/queue-status").json()["queue"]:
        time.sleep(0.1)
    assert os.path.isfile(Path(Path("tests", "temp"), f"R_{task["task_id"]}.json"))


class TestConvertTask:
    def test_convert_task(self, endpointtask_factory: EndpointTask):
        endpointtask = endpointtask_factory()
        data_manager = DataManager()
        task = convert_task(endpointtask, data_manager)
        assert task.task_id == endpointtask["task_id"]
        assert isinstance(task.optimiser, Optimiser[endpointtask.optimiser.name])
        assert task.data_manager == data_manager
