from pathlib import Path

from epoch_simulator import Simulator

from app.internal.epoch_utils import TaskData

from .conftest import _DATA_PATH


def test_good_taskdata() -> None:
    td = TaskData()
    input_dir = Path(_DATA_PATH, "amcott_house")
    sim = Simulator(inputDir=str(input_dir))
    sim.simulate_scenario(td)
