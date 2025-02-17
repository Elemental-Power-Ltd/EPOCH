from pathlib import Path

import pytest

from app.internal.epoch_utils import (
    Building,
    Config,
    DataCentre,
    DomesticHotWater,
    EnergyStorageSystem,
    Grid,
    HeatPump,
    Renewables,
    Simulator,
    TaskData,
    convert_sim_result,
    convert_TaskData_to_dictionary,
)
from app.models.metrics import _EPOCH_NATIVE_METRICS, _SERVICE_NATIVE_METRICS

from .conftest import _DATA_PATH


@pytest.mark.requires_epoch
def test_convert_sim_result() -> None:
    td = TaskData()
    td.building = Building()
    td.grid = Grid()
    td.renewables = Renewables()
    td.heat_pump = HeatPump()
    td.data_centre = DataCentre()
    td.domestic_hot_water = DomesticHotWater()
    td.energy_storage_system = EnergyStorageSystem()

    sim = Simulator(inputDir=str(Path(_DATA_PATH, "amcott_house")))

    sim_result = sim.simulate_scenario(td)

    res = convert_sim_result(sim_result)

    for metric in _EPOCH_NATIVE_METRICS:
        assert getattr(sim_result, metric) == res[metric]
    for metric in _SERVICE_NATIVE_METRICS:
        assert metric in res


@pytest.mark.requires_epoch
def test_convert_TaskData_to_dictionary() -> None:
    td = TaskData()
    td.config = Config()
    td.building = Building()
    td.grid = Grid()
    td.renewables = Renewables()
    td.heat_pump = HeatPump()
    td.data_centre = DataCentre()
    td.domestic_hot_water = DomesticHotWater()
    td.energy_storage_system = EnergyStorageSystem()

    res = convert_TaskData_to_dictionary(td)

    assert "config" in res
    assert "building" in res
    assert "grid" in res
    assert "renewables" in res
    assert "heat_pump" in res
    assert "data_centre" in res
    assert "domestic_hot_water" in res
    assert "energy_storage_system" in res
