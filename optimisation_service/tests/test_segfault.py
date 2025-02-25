from pathlib import Path

from epoch_simulator import Simulator

from app.internal.datamanager import load_epoch_data_from_file
from app.internal.epoch_utils import TaskData

from .conftest import _DATA_PATH


def test_good_taskdata() -> None:
    td = TaskData()
    site_name = "amcott_house"
    epoch_data = load_epoch_data_from_file(Path(_DATA_PATH, site_name, "epoch_data.json"))
    sim = Simulator.from_json(epoch_data.model_dump_json())
    sim.simulate_scenario(td)
