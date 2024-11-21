import datetime
import os
import time
from pathlib import Path

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from app.models.core import Task
from app.models.result import OptimisationResult
from app.routers.optimise import process_results


@pytest.mark.requires_epoch
def test_submit_portfolio_task(client: TestClient, default_task: Task) -> None:
    """
    Test /submit-portfolio-task endpoint.
    """
    response = client.post("/submit-portfolio-task", json=jsonable_encoder(default_task))
    assert response.status_code == 200, response.text
    while str(default_task.task_id) in client.post("/queue-status").json()["queue"]:
        time.sleep(1)
    assert os.path.isfile(Path("tests", "data", "temp", f"R_{default_task.task_id}.json"))


def test_process_results(default_task: Task, dummy_optimisation_result: OptimisationResult) -> None:
    """
    Test result processing.
    """
    completed_at = datetime.datetime.now(datetime.UTC)
    results_list = process_results(default_task, dummy_optimisation_result, completed_at)
    assert len(results_list) >= 1
