import datetime
import os
import time
import uuid
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from app.internal.datamanager import DataManager
from app.internal.result import Result
from app.models.core import EndpointTask, TaskWithUUID
from app.models.optimisers import OptimiserFunc
from app.models.tasks import Task
from app.routers.optimise import convert_task, process_results


@pytest.mark.requires_epoch
def test_submit_task(client: TestClient, endpointtask_factory: Callable[[], EndpointTask]) -> None:
    """
    Test /submit-task endpoint.
    """
    task = endpointtask_factory()
    response = client.post("/submit-task", json=jsonable_encoder(task))
    assert response.status_code == 200, response.text
    task_id = response.json()["task_id"]
    while task_id in client.post("/queue-status").json()["queue"]:
        time.sleep(0.1)
    assert os.path.isfile(Path(Path("tests", "temp"), f"R_{task_id}.json"))


def test_convert_task(endpointtask_factory: Callable[[], EndpointTask]) -> None:
    """
    Test task convertion.
    """
    endpointtask = endpointtask_factory()
    task_id = uuid.uuid4()
    endpointtask = TaskWithUUID(**endpointtask.model_dump(), task_id=task_id)
    data_manager = DataManager()
    data_manager.temp_data_dir = Path("")
    task = convert_task(endpointtask, data_manager)
    assert task.task_id == task_id
    assert isinstance(task.optimiser, OptimiserFunc[endpointtask.optimiser.name].value)
    assert task.data_manager == data_manager


def test_process_results(task_factory: Callable[[], Task]) -> None:
    """
    Test result processing.
    """
    task = task_factory()
    parameters = task.problem.variable_param()
    solution = []
    for param_range in parameters.values():
        min_v = param_range["min"]
        max_v = param_range["max"]
        step = param_range["step"]
        poss_values = np.arange(min_v, max_v + step, step)
        rand_param = np.random.choice(poss_values)
        solution.append(rand_param)
    results = Result(
        solutions=np.array([solution]),
        objective_values=np.array([[0, 0, 0, 0, 0]]),
        n_evals=1,
        exec_time=datetime.timedelta(seconds=1),
    )
    completed_at = datetime.datetime.now(datetime.UTC)
    results_list = process_results(task, results, completed_at)
    assert len(results_list) == 1
