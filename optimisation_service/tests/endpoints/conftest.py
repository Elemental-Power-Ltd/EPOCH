import asyncio
import datetime
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Generator
from uuid import uuid4

import pandas as pd
import pytest
import pytest_asyncio
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from pandas.core.api import DataFrame as DataFrame
from pydantic import UUID4

from app.internal.grid_search import GridSearch
from app.internal.models.problem import ParameterDict
from app.internal.problem import Problem
from app.main import app
from app.routers.models.core import EndpointResult, EndpointTask, Objectives
from app.routers.models.database import DatasetIDWithTime
from app.routers.models.optimisers import (
    GABaseHyperParam,
    NSGA2Optmiser,
)
from app.routers.models.problem import EndpointParameterDict, EndpointParamRange
from app.routers.models.site_data import FileLoc, SiteData
from app.routers.models.tasks import Task
from app.routers.utils.datamanager import DataManager

logger = logging.getLogger("default")


@pytest_asyncio.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    class DataManagerOverride:
        def __init__(self) -> None:
            self.temp_dir = Path("tests", "temp")
            self.input_data_files = [
                "CSVEload.csv",
                "CSVHload.csv",
                "CSVAirtemp.csv",
                "CSVRGen.csv",
                "CSVASHPinput.csv",
                "CSVASHPoutput.csv",
                "CSVImporttariff.csv",
                "CSVGridCO2.csv",
            ]

        def copy_input_data(self, source: str | os.PathLike, destination: str | os.PathLike) -> None:
            """
            Copies input data files from source to destination folder.

            Parameters
            ----------
            source
                Folder to copy files from.
            destination
                Folder to copy files to.
            """
            logger.debug(f"Copying local data files from {source} to {destination}.")
            for file in self.input_data_files:
                shutil.copy(Path(source, file), Path(destination, file))

        async def process_site_data(self, site_data: SiteData, task_id: UUID4) -> os.PathLike:
            """
            Process task site data.
            Either copy local files to temp dir or fetch and process data from database and save to temp dir.

            Parameters
            ----------
            site_data
                Description of data.
            """
            logger.debug(f"Processing site data for {task_id}.")
            self.temp_data_dir = Path(self.temp_dir, str(task_id))
            logger.debug(f"Creating temporary directory {self.temp_data_dir}.")
            os.makedirs(self.temp_data_dir)
            if site_data.loc == FileLoc.local:
                self.copy_input_data(site_data.path, self.temp_data_dir)
            else:
                site_data_info = await self.fetch_site_data_info(site_data.key)
                dfs = await self.fetch_all_input_data(site_data_info)
                for name, df in dfs.items():
                    df.to_csv(Path(self.temp_data_dir, f"CSV{name}.csv"))

        async def transmit_results(self, results: list[EndpointResult]) -> None:
            with open(Path(self.temp_dir, f"R_{results[0].task_id}.json"), "w") as f:
                json.dump(jsonable_encoder(results), f)
            return None

        async def transmit_task(self, task: EndpointTask) -> None:
            with open(Path(self.temp_dir, f"T_{task.task_id}.json"), "w") as f:
                json.dump(jsonable_encoder(task), f)
            return None

        async def fetch_site_data_info(self, site_data_id: UUID4) -> None:
            logger.debug(f"Fetching site data info {site_data_id}.")
            _ = site_data_id
            return None

        async def fetch_all_input_data(self, site_data_ids: dict[str, DatasetIDWithTime]) -> dict[str, DataFrame]:
            logger.debug("Fetching all input data.")
            _ = site_data_ids
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
            }
            return site_data

    app.dependency_overrides[DataManager] = DataManagerOverride

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def endpointtask_factory():
    def __create_endpointtask() -> EndpointTask:
        optimiser = NSGA2Optmiser(name="NSGA2", hyperparameters=GABaseHyperParam())
        search_parameters = EndpointParameterDict(
            ASHP_HPower=EndpointParamRange(min=0, max=1, step=1),
            ASHP_HSource=EndpointParamRange(min=0, max=1, step=1),
            ASHP_HotTemp=EndpointParamRange(min=0, max=1, step=1),
            ASHP_RadTemp=EndpointParamRange(min=0, max=1, step=1),
            ESS_capacity=EndpointParamRange(min=0, max=1, step=1),
            ESS_charge_mode=EndpointParamRange(min=0, max=1, step=1),
            ESS_charge_power=EndpointParamRange(min=0, max=1, step=1),
            ESS_discharge_mode=EndpointParamRange(min=0, max=1, step=1),
            ESS_discharge_power=EndpointParamRange(min=0, max=1, step=1),
            ESS_start_SoC=EndpointParamRange(min=0, max=1, step=1),
            EV_flex=EndpointParamRange(min=0, max=1, step=1),
            Export_headroom=EndpointParamRange(min=0, max=1, step=1),
            Fixed_load1_scalar=EndpointParamRange(min=0, max=1, step=1),
            Fixed_load2_scalar=EndpointParamRange(min=0, max=1, step=1),
            Flex_load_max=EndpointParamRange(min=0, max=1, step=1),
            GridExport=EndpointParamRange(min=0, max=1, step=1),
            GridImport=EndpointParamRange(min=0, max=1, step=1),
            Import_headroom=EndpointParamRange(min=0, max=1, step=1),
            Min_power_factor=EndpointParamRange(min=0, max=1, step=1),
            Mop_load_max=EndpointParamRange(min=0, max=1, step=1),
            ScalarHL1=EndpointParamRange(min=0, max=1, step=1),
            ScalarHYield=EndpointParamRange(min=0, max=1, step=1),
            ScalarRG1=EndpointParamRange(min=0, max=1, step=1),
            ScalarRG2=EndpointParamRange(min=0, max=1, step=1),
            ScalarRG3=EndpointParamRange(min=0, max=1, step=1),
            ScalarRG4=EndpointParamRange(min=0, max=1, step=1),
            f22_EV_CP_number=EndpointParamRange(min=0, max=1, step=1),
            r50_EV_CP_number=EndpointParamRange(min=0, max=1, step=1),
            s7_EV_CP_number=EndpointParamRange(min=0, max=1, step=1),
            u150_EV_CP_number=EndpointParamRange(min=0, max=1, step=1),
            CAPEX_limit=0,
            Export_kWh_price=0,
            OPEX_limit=0,
            target_max_concurrency=0,
            time_budget_min=0,
            timestep_hours=0,
        )

        objectives = [
            Objectives.carbon_balance,
            Objectives.capex,
            Objectives.annualised_cost,
            Objectives.cost_balance,
            Objectives.payback_horizon,
        ]
        site_data = SiteData(loc=FileLoc.remote, key=uuid4())

        return jsonable_encoder(
            EndpointTask(
                task_id=uuid4(),
                task_name="test",
                optimiser=optimiser,
                search_parameters=search_parameters,
                objectives=objectives,
                site_data=site_data,
                created_at=datetime.datetime.now(datetime.UTC),
            )
        )

    return __create_endpointtask


@pytest.fixture(scope="function")
def task_factory(tmpdir_factory: pytest.TempdirFactory):
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
                "carbon_balance",
                "cost_balance",
                "capex",
                "payback_horizon",
                "annualised_cost",
            ],
            constraints={},
            parameters=ParameterDict(
                ASHP_HPower=EndpointParamRange(min=0, max=1, step=1),
                ASHP_HSource=EndpointParamRange(min=0, max=1, step=1),
                ASHP_HotTemp=EndpointParamRange(min=0, max=1, step=1),
                ASHP_RadTemp=EndpointParamRange(min=0, max=1, step=1),
                ESS_capacity=EndpointParamRange(min=0, max=1, step=1),
                ESS_charge_mode=EndpointParamRange(min=0, max=1, step=1),
                ESS_charge_power=EndpointParamRange(min=0, max=1, step=1),
                ESS_discharge_mode=EndpointParamRange(min=0, max=1, step=1),
                ESS_discharge_power=EndpointParamRange(min=0, max=1, step=1),
                ESS_start_SoC=EndpointParamRange(min=0, max=1, step=1),
                EV_flex=EndpointParamRange(min=0, max=1, step=1),
                Export_headroom=EndpointParamRange(min=0, max=1, step=1),
                Fixed_load1_scalar=EndpointParamRange(min=0, max=1, step=1),
                Fixed_load2_scalar=EndpointParamRange(min=0, max=1, step=1),
                Flex_load_max=EndpointParamRange(min=0, max=1, step=1),
                GridExport=EndpointParamRange(min=0, max=1, step=1),
                GridImport=EndpointParamRange(min=0, max=1, step=1),
                Import_headroom=EndpointParamRange(min=0, max=1, step=1),
                Min_power_factor=EndpointParamRange(min=0, max=1, step=1),
                Mop_load_max=EndpointParamRange(min=0, max=1, step=1),
                ScalarHL1=EndpointParamRange(min=0, max=1, step=1),
                ScalarHYield=EndpointParamRange(min=0, max=1, step=1),
                ScalarRG1=EndpointParamRange(min=0, max=1, step=1),
                ScalarRG2=EndpointParamRange(min=0, max=1, step=1),
                ScalarRG3=EndpointParamRange(min=0, max=1, step=1),
                ScalarRG4=EndpointParamRange(min=0, max=1, step=1),
                f22_EV_CP_number=EndpointParamRange(min=0, max=1, step=1),
                r50_EV_CP_number=EndpointParamRange(min=0, max=1, step=1),
                s7_EV_CP_number=EndpointParamRange(min=0, max=1, step=1),
                u150_EV_CP_number=EndpointParamRange(min=0, max=1, step=1),
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


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()
