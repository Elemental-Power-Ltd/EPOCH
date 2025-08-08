import json
from collections.abc import Generator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from pandas.core.api import DataFrame as DataFrame

from app.internal.datamanager import DataManager, load_epoch_data_from_file
from app.main import app
from app.models.core import OptimisationResultEntry, Task
from app.models.optimisers import (
    NSGA2HyperParam,
    NSGA2Optimiser,
    OptimiserStr,
)
from app.models.site_data import LocalMetaData, RemoteMetaData

from ..conftest import _DATA_PATH


@pytest.fixture(scope="session")
def result_tmp_path(tmp_path_factory):
    return tmp_path_factory.mktemp("results")


@pytest_asyncio.fixture()
def client(result_tmp_path: Path) -> Generator[TestClient]:
    class DataManagerOverride(DataManager):
        async def fetch_portfolio_data(self, task: Task) -> None:
            for site in task.portfolio:
                if isinstance(site.site_data, LocalMetaData):
                    site._epoch_data = load_epoch_data_from_file(site.site_data.path)
                elif isinstance(site.site_data, RemoteMetaData):
                    site._epoch_data = load_epoch_data_from_file(Path(_DATA_PATH, site.name))

        async def transmit_results(self, result: OptimisationResultEntry) -> None:
            with open(Path(result_tmp_path, f"{result.tasks.task_id}.json"), "w") as f:
                json.dump(jsonable_encoder(result), f)

        async def transmit_task(self, task: Task) -> None:
            return None

    app.dependency_overrides[DataManager] = DataManagerOverride

    with TestClient(app) as client:
        yield client


@pytest.fixture
def default_optimiser() -> NSGA2Optimiser:
    return NSGA2Optimiser(
        name=OptimiserStr.NSGA2, hyperparameters=NSGA2HyperParam(pop_size=512, n_offsprings=256, n_max_gen=10, period=8)
    )


@pytest.fixture
def default_task(default_objectives, default_optimiser, default_portfolio, default_constraints) -> Task:
    return Task(
        name="test",
        optimiser=default_optimiser,
        objectives=default_objectives,
        portfolio=default_portfolio,
        client_id="demo",
        portfolio_constraints=default_constraints,
        epoch_version="0.0.1",
    )
