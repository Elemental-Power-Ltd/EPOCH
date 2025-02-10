import json
import logging
from collections.abc import Generator
from pathlib import Path

import pandas as pd
import pytest
import pytest_asyncio
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from pandas.core.api import DataFrame as DataFrame

from app.internal.datamanager import DataManager
from app.main import app
from app.models.core import OptimisationResultEntry, Task
from app.models.optimisers import (
    NSGA2HyperParam,
    NSGA2Optmiser,
    OptimiserStr,
)
from app.models.site_data import SiteDataEntries

logger = logging.getLogger("default")


@pytest_asyncio.fixture()
def client() -> Generator[TestClient, None, None]:
    class DataManagerOverride(DataManager):
        def __init__(self) -> None:
            super().__init__()
            self.temp_dir = Path("tests", "data", "temp")

        def transform_all_input_data(self, site_data_entries: SiteDataEntries) -> dict[str, DataFrame]:
            sample_data_path = Path("tests", "data", "input_data")
            site_data = {
                "Eload": pd.read_csv(Path(sample_data_path, "CSVEload.csv")),
                "Hload": pd.read_csv(Path(sample_data_path, "CSVHload.csv")),
                "Airtemp": pd.read_csv(Path(sample_data_path, "CSVAirtemp.csv")),
                "RGen": pd.read_csv(Path(sample_data_path, "CSVRGen.csv")),
                "ASHPinput": pd.read_csv(Path(sample_data_path, "CSVASHPinput.csv")),
                "ASHPoutput": pd.read_csv(Path(sample_data_path, "CSVASHPoutput.csv")),
                "Importtariff": pd.read_csv(Path(sample_data_path, "CSVImporttariff.csv")),
                "GridCO2": pd.read_csv(Path(sample_data_path, "CSVGridCO2.csv")),
                "DHWdemand": pd.read_csv(Path(sample_data_path, "CSVDHWdemand.csv")),
            }
            return site_data

        async def transmit_results(self, result: OptimisationResultEntry) -> None:
            with open(Path(self.temp_dir, f"R_{result.tasks[0].task_id}.json"), "w") as f:
                json.dump(jsonable_encoder(result), f)

        async def transmit_task(self, task: Task) -> None:
            return None

    app.dependency_overrides[DataManager] = DataManagerOverride

    with TestClient(app) as client:
        yield client


@pytest.fixture
def default_optimiser() -> NSGA2Optmiser:
    return NSGA2Optmiser(name=OptimiserStr.NSGA2, hyperparameters=NSGA2HyperParam(pop_size=4096, n_offsprings=2048, period=2))


@pytest.fixture
def default_task(default_objectives, default_optimiser, default_portfolio, default_constraints) -> Task:
    return Task(
        name="test",
        optimiser=default_optimiser,
        objectives=default_objectives,
        portfolio=default_portfolio,
        client_id="demo",
        portfolio_constraints=default_constraints,
    )
