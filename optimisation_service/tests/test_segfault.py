from pathlib import Path

import pytest

from app.internal.epoch_utils import Simulator, TaskData

from .conftest import _DATA_PATH


@pytest.mark.requires_epoch
def test_good_taskdata() -> None:
    td = TaskData()
    input_dir = Path(_DATA_PATH, "amcott_house")
    sim = Simulator(inputDir=str(input_dir))
    sim.simulate_scenario(td)
