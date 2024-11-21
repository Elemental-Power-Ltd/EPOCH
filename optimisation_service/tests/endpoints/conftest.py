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
from app.models.core import EndpointResult, Task
from app.models.optimisers import (
    GridSearchHyperParam,
    GridSearchOptimiser,
    OptimiserStr,
)
from app.models.site_data import ASHPResult, SiteDataEntries, SiteMetaData

logger = logging.getLogger("default")


@pytest_asyncio.fixture()
def client() -> Generator[TestClient, None, None]:
    class DataManagerOverride(DataManager):
        def __init__(self) -> None:
            super().__init__()
            self.temp_dir = Path("tests", "data", "temp")

        async def fetch_latest_datasets(self, site_data: SiteMetaData) -> SiteDataEntries:
            return {
                "eload": [],
                "heat": [],
                "ashp_input": ASHPResult(index=[], columns=[], data=[]),
                "ashp_output": ASHPResult(index=[], columns=[], data=[]),
                "import_tariffs": [],
                "grid_co2": [],
                "rgen": [],
            }

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

        async def transmit_results(self, results: list[EndpointResult]) -> None:
            with open(Path(self.temp_dir, f"R_{results[0].task_id}.json"), "w") as f:
                json.dump(jsonable_encoder(results), f)

        async def transmit_task(self, task: Task) -> None:
            return None

    app.dependency_overrides[DataManager] = DataManagerOverride

    with TestClient(app) as client:
        yield client


@pytest.fixture
def default_optimiser() -> GridSearchOptimiser:
    return GridSearchOptimiser(name=OptimiserStr.GridSearch, hyperparameters=GridSearchHyperParam())


@pytest.fixture
def default_task(default_objectives, default_optimiser, default_portfolio) -> Task:
    return Task(
        name="test",
        optimiser=default_optimiser,
        objectives=default_objectives,
        portfolio=default_portfolio,
        client_id="demo",
    )
