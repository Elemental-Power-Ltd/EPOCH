import pathlib

import pytest

from app.internal.epoch_utils import Simulator, TaskData


@pytest.mark.requires_epoch
def test_good_taskdata() -> None:
    td = TaskData()
    input_dir = pathlib.Path(".") / "Epoch" / "InputData"
    sim = Simulator(inputDir=str(input_dir))
    sim.simulate_scenario(td)
