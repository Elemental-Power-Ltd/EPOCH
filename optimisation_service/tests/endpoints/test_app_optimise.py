import datetime
import os
import time
from pathlib import Path

from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from app.models.core import Task
from app.models.result import OptimisationResult
from app.models.site_range import (
    BatteryModeEnum,
    Building,
    Config,
    DomesticHotWater,
    EnergyStorageSystem,
    Grid,
    HeatPump,
    HeatSourceEnum,
    Renewables,
    SiteRange,
)
from app.routers.optimise import process_results


class TestSubmitPortfolioTask:
    def test_good_task(self, client: TestClient, result_tmp_path: Path, default_task: Task) -> None:
        """
        Test /submit-portfolio-task endpoint.
        """
        response = client.post("/submit-portfolio-task", json=jsonable_encoder(default_task))
        assert response.status_code == 200, response.text
        while str(default_task.task_id) in client.post("/queue-status").json()["queue"]:
            time.sleep(1)
        assert os.path.isfile(Path(result_tmp_path, f"{default_task.task_id}.json"))

    def test_empty_search_space(self, client: TestClient, default_task: Task) -> None:
        """
        Test /submit-portfolio-task endpoint.
        """
        building = Building(
            COMPONENT_IS_MANDATORY=True, scalar_heat_load=[1], scalar_electrical_load=[1], fabric_intervention_index=[0]
        )
        domestic_hot_water = DomesticHotWater(COMPONENT_IS_MANDATORY=True, cylinder_volume=[100])
        energy_storage_system = EnergyStorageSystem(
            COMPONENT_IS_MANDATORY=True,
            capacity=[100],
            charge_power=[100],
            discharge_power=[100],
            battery_mode=[BatteryModeEnum.CONSUME],
            initial_charge=[0],
        )
        grid = Grid(
            COMPONENT_IS_MANDATORY=True,
            export_headroom=[0.5],
            grid_export=[60],
            grid_import=[60],
            import_headroom=[0.5],
            min_power_factor=[1],
            tariff_index=[0],
        )
        heat_pump = HeatPump(
            COMPONENT_IS_MANDATORY=True, heat_power=[100], heat_source=[HeatSourceEnum.AMBIENT_AIR], send_temp=[70]
        )
        renewables = Renewables(COMPONENT_IS_MANDATORY=True, yield_scalars=[[100]])
        config = Config(capex_limit=99999999999)

        empty_site_range = SiteRange(
            building=building,
            domestic_hot_water=domestic_hot_water,
            energy_storage_system=energy_storage_system,
            grid=grid,
            heat_pump=heat_pump,
            renewables=renewables,
            config=config,
        )

        for site in default_task.portfolio:
            site.site_range = empty_site_range

        response = client.post("/submit-portfolio-task", json=jsonable_encoder(default_task))
        assert response.status_code == 400, response.text


def test_process_results(default_task: Task, default_optimisation_result: OptimisationResult) -> None:
    """
    Test result processing.
    """
    completed_at = datetime.datetime.now(datetime.UTC)
    result_entry = process_results(default_task, default_optimisation_result, completed_at)
    assert len(result_entry.portfolio) >= 1
