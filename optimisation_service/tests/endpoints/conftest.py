import datetime
import json
import logging
import os
from collections.abc import Callable, Generator
from pathlib import Path
from uuid import uuid4

import pandas as pd
import pytest
import pytest_asyncio
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from pandas.core.api import DataFrame as DataFrame

from app.internal.datamanager import DataManager
from app.internal.grid_search import GridSearch
from app.internal.problem import Problem
from app.main import app
from app.models.core import EndpointResult, EndpointTask, Objectives, TaskWithUUID
from app.models.optimisers import (
    GABaseHyperParam,
    NSGA2Optmiser,
    OptimiserStr,
)
from app.models.problem import EndpointParameterDict, EndpointParamRange, ParameterDict, ParamRange
from app.models.site_data import ASHPResult, DataDuration, FileLoc, RemoteMetaData, SiteDataEntries, SiteMetaData
from app.models.tasks import Task

logger = logging.getLogger("default")


@pytest_asyncio.fixture()
def client() -> Generator[TestClient, None, None]:
    class DataManagerOverride(DataManager):
        def __init__(self) -> None:
            super().__init__()
            self.temp_dir = Path("tests", "temp")

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
            sample_data_path = Path("tests", "data", "benchmarks", "var-3", "InputData")
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

        async def transmit_task(self, task: TaskWithUUID) -> None:
            return None

    app.dependency_overrides[DataManager] = DataManagerOverride

    with TestClient(app) as client:
        yield client


@pytest.fixture
def endpointtask_factory() -> Callable[[], EndpointTask]:
    def __create_endpointtask() -> EndpointTask:
        optimiser = NSGA2Optmiser(name=OptimiserStr.NSGA2, hyperparameters=GABaseHyperParam())
        search_parameters = EndpointParameterDict(
            ASHP_HPower=EndpointParamRange(min=70, max=70, step=0),
            ASHP_HSource=EndpointParamRange(min=1, max=1, step=0),
            ASHP_HotTemp=EndpointParamRange(min=43, max=43, step=0),
            ASHP_RadTemp=EndpointParamRange(min=70, max=70, step=0),
            ESS_capacity=EndpointParamRange(min=0, max=1000, step=100),
            ESS_charge_mode=EndpointParamRange(min=1, max=1, step=0),
            ESS_charge_power=EndpointParamRange(min=0, max=1000, step=100),
            ESS_discharge_mode=EndpointParamRange(min=1, max=1, step=0),
            ESS_discharge_power=EndpointParamRange(min=0, max=1000, step=100),
            ESS_start_SoC=EndpointParamRange(min=0.5, max=0.5, step=0),
            EV_flex=EndpointParamRange(min=0.5, max=0.5, step=0),
            Export_headroom=EndpointParamRange(min=0, max=0, step=0),
            Fixed_load1_scalar=EndpointParamRange(min=1, max=1, step=0),
            Fixed_load2_scalar=EndpointParamRange(min=3, max=3, step=0),
            Flex_load_max=EndpointParamRange(min=50, max=50, step=0),
            GridExport=EndpointParamRange(min=100, max=100, step=0),
            GridImport=EndpointParamRange(min=140, max=140, step=0),
            Import_headroom=EndpointParamRange(min=0.4, max=0.4, step=0),
            Min_power_factor=EndpointParamRange(min=0.95, max=0.95, step=0),
            Mop_load_max=EndpointParamRange(min=300, max=300, step=0),
            ScalarHL1=EndpointParamRange(min=1, max=1, step=0),
            ScalarHYield=EndpointParamRange(min=0.75, max=0.75, step=0),
            ScalarRG1=EndpointParamRange(min=600, max=600, step=0),
            ScalarRG2=EndpointParamRange(min=75, max=75, step=0),
            ScalarRG3=EndpointParamRange(min=60, max=60, step=0),
            ScalarRG4=EndpointParamRange(min=0, max=0, step=0),
            f22_EV_CP_number=EndpointParamRange(min=3, max=3, step=0),
            r50_EV_CP_number=EndpointParamRange(min=0, max=0, step=0),
            s7_EV_CP_number=EndpointParamRange(min=0, max=0, step=0),
            u150_EV_CP_number=EndpointParamRange(min=0, max=0, step=0),
            DHW_cylinder_volume=EndpointParamRange(min=100, max=100, step=0),
            CAPEX_limit=0,
            Export_kWh_price=5,
            OPEX_limit=0,
            target_max_concurrency=44,
            time_budget_min=5,
            timestep_hours=1,
        )

        objectives = [
            Objectives.carbon_balance,
            Objectives.capex,
            Objectives.annualised_cost,
            Objectives.cost_balance,
            Objectives.payback_horizon,
        ]
        start_ts = datetime.datetime(year=2024, month=1, day=1, hour=0, minute=0, second=0, tzinfo=datetime.UTC)
        duration = DataDuration.year
        site_data = RemoteMetaData(loc=FileLoc.remote, site_id="test", start_ts=start_ts, duration=duration)

        return EndpointTask(
            task_name="test",
            optimiser=optimiser,
            search_parameters=search_parameters,
            objectives=objectives,
            site_data=site_data,
            created_at=datetime.datetime.now(datetime.UTC),
        )

    return __create_endpointtask


@pytest.fixture
def task_factory(tmpdir_factory: pytest.TempdirFactory) -> Callable[[], Task]:
    def __create_task() -> Task:
        task_id = uuid4()
        temp_data_dir = tmpdir_factory.mktemp("tmp")
        temp_data_folder = Path(temp_data_dir, str(task_id))
        os.makedirs(temp_data_folder)
        data_manager = DataManager()
        data_manager.temp_data_dir = temp_data_folder
        data_manager.copy_input_data("./tests/data/benchmarks/var-3/InputData", temp_data_folder)
        problem = Problem(
            objectives=[
                Objectives.carbon_balance,
                Objectives.cost_balance,
                Objectives.capex,
                Objectives.annualised_cost,
                Objectives.payback_horizon,
            ],
            constraints={},
            parameters=ParameterDict(
                ASHP_HPower=ParamRange(min=0, max=1, step=1),
                ASHP_HSource=ParamRange(min=0, max=1, step=1),
                ASHP_HotTemp=ParamRange(min=0, max=1, step=1),
                ASHP_RadTemp=ParamRange(min=0, max=1, step=1),
                ESS_capacity=ParamRange(min=0, max=1, step=1),
                ESS_charge_mode=ParamRange(min=0, max=1, step=1),
                ESS_charge_power=ParamRange(min=0, max=1, step=1),
                ESS_discharge_mode=ParamRange(min=0, max=1, step=1),
                ESS_discharge_power=ParamRange(min=0, max=1, step=1),
                ESS_start_SoC=ParamRange(min=0, max=1, step=1),
                EV_flex=ParamRange(min=0, max=1, step=1),
                Export_headroom=ParamRange(min=0, max=1, step=1),
                Fixed_load1_scalar=ParamRange(min=0, max=1, step=1),
                Fixed_load2_scalar=ParamRange(min=0, max=1, step=1),
                Flex_load_max=ParamRange(min=0, max=1, step=1),
                GridExport=ParamRange(min=0, max=1, step=1),
                GridImport=ParamRange(min=0, max=1, step=1),
                Import_headroom=ParamRange(min=0, max=1, step=1),
                Min_power_factor=ParamRange(min=0, max=1, step=1),
                Mop_load_max=ParamRange(min=0, max=1, step=1),
                ScalarHL1=ParamRange(min=0, max=1, step=1),
                ScalarHYield=ParamRange(min=0, max=1, step=1),
                ScalarRG1=ParamRange(min=0, max=1, step=1),
                ScalarRG2=ParamRange(min=0, max=1, step=1),
                ScalarRG3=ParamRange(min=0, max=1, step=1),
                ScalarRG4=ParamRange(min=0, max=1, step=1),
                f22_EV_CP_number=ParamRange(min=0, max=1, step=1),
                r50_EV_CP_number=ParamRange(min=0, max=1, step=1),
                s7_EV_CP_number=ParamRange(min=0, max=1, step=1),
                u150_EV_CP_number=ParamRange(min=0, max=1, step=1),
                DHW_cylinder_volume=ParamRange(min=100, max=100, step=0),
                CAPEX_limit=0,
                Export_kWh_price=0,
                OPEX_limit=0,
                target_max_concurrency=0,
                time_budget_min=0,
                timestep_hours=0,
            ),
            input_dir=temp_data_folder,
        )

        return Task(task_id=task_id, optimiser=GridSearch(), problem=problem, data_manager=data_manager)

    return __create_task
