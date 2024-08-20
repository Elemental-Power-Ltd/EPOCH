import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.routers.models.core import EndpointTask


@pytest.mark.asyncio
def test_submit_task(client: TestClient, endpointtask_factory: EndpointTask):
    task = endpointtask_factory()
    response = client.post("/submit-task", json=task)
    assert response.status_code == 200, response.text
    assert os.path.isfile(Path(Path("tests", "temp"), f"{task["task_id"]}.csv"))
