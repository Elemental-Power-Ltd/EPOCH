from pathlib import Path

from epoch_simulator import (
    Building,
    Config,
    DataCentre,
    DomesticHotWater,
    EnergyStorageSystem,
    GasHeater,
    Grid,
    HeatPump,
    Renewables,
    Simulator,
    TaskData,
)

from app.internal.datamanager import load_epoch_data_from_file
from app.internal.epoch_utils import (
    convert_sim_result,
    convert_TaskData_to_pydantic,
)
from app.models.metrics import _METRICS

from .conftest import _DATA_PATH


def test_convert_sim_result() -> None:
    td = TaskData()
    td.building = Building()
    td.grid = Grid()
    td.renewables = Renewables()
    td.heat_pump = HeatPump()
    td.data_centre = DataCentre()
    td.domestic_hot_water = DomesticHotWater()
    td.energy_storage_system = EnergyStorageSystem()

    site_name = "amcott_house"
    epoch_data = load_epoch_data_from_file(Path(_DATA_PATH, site_name, "epoch_data.json"))
    sim = Simulator.from_json(epoch_data.model_dump_json())

    sim_result = sim.simulate_scenario(td)

    res = convert_sim_result(sim_result)

    for metric in _METRICS:
        assert metric in res


def test_convert_TaskData_to_pydantic() -> None:
    td = TaskData()
    td.config = Config()
    td.building = Building()
    td.grid = Grid()
    td.renewables = Renewables()
    td.heat_pump = HeatPump()
    td.data_centre = DataCentre()
    td.domestic_hot_water = DomesticHotWater()
    td.energy_storage_system = EnergyStorageSystem()
    td.gas_heater = GasHeater()

    res = convert_TaskData_to_pydantic(td)

    assert hasattr(res, "config")
    assert hasattr(res, "building")
    assert hasattr(res, "grid")
    assert hasattr(res, "renewables")
    assert hasattr(res, "heat_pump")
    assert hasattr(res, "data_centre")
    assert hasattr(res, "domestic_hot_water")
    assert hasattr(res, "energy_storage_system")
    assert hasattr(res, "gas_heater")
