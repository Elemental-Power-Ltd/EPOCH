from pathlib import Path

from app.internal.epoch.converters import (
    convert_TaskData_to_pydantic,
    simulation_result_to_metric_dict,
)
from app.models.epoch_types.config import Config
from app.models.metrics import _METRICS
from epoch_simulator import (
    Building,
    DataCentre,
    DomesticHotWater,
    EnergyStorageSystem,
    GasHeater,
    Grid,
    HeatPump,
    Simulator,
    SolarPanel,
    TaskData,
)

from .conftest import _DATA_PATH, load_epoch_data_from_file


def test_convert_sim_result(default_config: Config) -> None:
    td = TaskData()
    td.building = Building()
    td.grid = Grid()
    td.solar_panels = [SolarPanel()]
    td.heat_pump = HeatPump()
    td.data_centre = DataCentre()
    td.domestic_hot_water = DomesticHotWater()
    td.energy_storage_system = EnergyStorageSystem()

    site_name = "amcott_house"
    epoch_data = load_epoch_data_from_file(Path(_DATA_PATH, site_name, "epoch_data.json"))
    sim = Simulator.from_json(epoch_data.model_dump_json(), default_config.model_dump_json())

    sim_result = sim.simulate_scenario(td)

    res = simulation_result_to_metric_dict(sim_result)

    for metric in _METRICS:
        assert metric in res


def test_convert_TaskData_to_pydantic() -> None:
    td = TaskData()
    td.building = Building()
    td.grid = Grid()
    td.solar_panels = [SolarPanel()]
    td.heat_pump = HeatPump()
    td.data_centre = DataCentre()
    td.domestic_hot_water = DomesticHotWater()
    td.energy_storage_system = EnergyStorageSystem()
    td.gas_heater = GasHeater()

    res = convert_TaskData_to_pydantic(td)

    assert hasattr(res, "building")
    assert hasattr(res, "grid")
    assert hasattr(res, "solar_panels")
    assert hasattr(res, "heat_pump")
    assert hasattr(res, "data_centre")
    assert hasattr(res, "domestic_hot_water")
    assert hasattr(res, "energy_storage_system")
    assert hasattr(res, "gas_heater")
