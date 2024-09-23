"""
Wrappers for Epoch that are more ergonomic for python.
"""

import json
import os
import pathlib
import platform
import subprocess
from typing import Generator

import numpy as np

from .log import logger

try:
    from epoch_simulator import SimulationResult, Simulator, TaskData

    HAS_EPOCH = True
except ImportError as ex:
    logger.warning(f"Failed to import Epoch python bindings due to {ex}")
    HAS_EPOCH = False

    # bodge ourselves some horrible stubs so that
    # we can run tests without EPOCH
    class SimulationResult: ...  # type: ignore

    class TaskData: ...  # type: ignore

    class Simulator:  # type: ignore
        def __init__(self, inputDir: str): ...
        def simulate_scenario(self, task_data: TaskData) -> SimulationResult:
            raise NotImplementedError()


def run_headless(
    project_path: os.PathLike | str,
    input_dir: os.PathLike | str | None = None,
    output_dir: os.PathLike | str | None = None,
    config_dir: os.PathLike | str | None = None,
) -> dict[str, float]:
    """
    Run the headless version of Epoch as a subprocess
    Parameters
    -----------
    project_path
        The path to the root of the Epoch repository
    input_dir
        A directory containing input data for Epoch. Defaults to $project_path$/InputData
    output_dir
         The directory to write the output to. Defaults to ./Data/OutputData
    config_dir
        A directory containing the config file(s) for Epoch. Defaults to $project_path$/Config
    Returns
    -------
        A dictionary containing the best value for each of the five objectives
    """
    if platform.system() == "Windows":
        exe_name = "Epoch.exe"
    else:
        exe_name = "epoch"

    project_path = pathlib.Path(project_path)

    full_path_to_exe = pathlib.Path(exe_name)
    if not full_path_to_exe.is_file():
        suffix = pathlib.Path("install", "headless", "bin")
        full_path_to_exe = project_path / suffix / exe_name
    assert pathlib.Path(full_path_to_exe).exists(), f"Could not find an EPOCH executable at {full_path_to_exe}"

    # input_dir, output_dir and config_dir can all be None
    # in which case we default to the following:
    #   input_dir   - the InputData directory in the Epoch root directory
    #   output_dir  - Data/OutputData within this project
    #   config_dir  - the Config directory in the Epoch root directory

    if input_dir is None:
        input_dir = pathlib.Path(project_path) / "InputData"

    if output_dir is None:
        output_dir = pathlib.Path("Data", "OutputData")

    if config_dir is None:
        config_dir = pathlib.Path(project_path) / "Config"

    input_dir, output_dir, config_dir = pathlib.Path(input_dir), pathlib.Path(output_dir), pathlib.Path(config_dir)
    # check these directories exist
    assert input_dir.is_dir(), f"Could not find {input_dir}"
    assert output_dir.is_dir(), f"Could not find {output_dir}"
    assert config_dir.is_dir(), f"Could not find {config_dir}"

    # check for required files within the directories
    assert (input_dir / "inputParameters.json").is_file(), f"Could not find {input_dir / "inputParameters.json"} is not a file"
    assert (config_dir / "EpochConfig.json").is_file(), f"Could not find {input_dir / "EpochConfig.json"} is not a file"

    result = subprocess.run(
        [str(full_path_to_exe), "--input", str(input_dir), "--output", str(output_dir), "--config", str(config_dir)]
    )

    assert result.returncode == 0

    output_json = output_dir / "outputParameters.json"

    with open(output_json, "r") as f:
        full_output = json.load(f)

    minimal_output = {
        "annualised": full_output["annualised"],
        "scenario_cost_balance": full_output["scenario_cost_balance"],
        "scenario_carbon_balance": full_output["scenario_carbon_balance"],
        "payback_horizon": full_output["payback_horizon"],
        "CAPEX": full_output["CAPEX"],
        "time_taken": full_output["time_taken"],
    }
    return minimal_output


class PyTaskData(TaskData):
    """
    Wrap a TaskData for Python convenience.

    Implements dict-like access, with string keys.
    """

    _VALID_KEYS = [
        "ASHP_HPower",
        "ASHP_HSource",
        "ASHP_HotTemp",
        "ASHP_RadTemp",
        "CAPEX_limit",
        "ESS_capacity",
        "ESS_charge_mode",
        "ESS_charge_power",
        "ESS_discharge_mode",
        "ESS_discharge_power",
        "ESS_start_SoC",
        "EV_flex",
        "Export_headroom",
        "Export_kWh_price",
        "Fixed_load1_scalar",
        "Fixed_load2_scalar",
        "Flex_load_max",
        "GridExport",
        "GridImport",
        "Import_headroom",
        "Min_power_factor",
        "Mop_load_max",
        "OPEX_limit",
        "ScalarHL1",
        "ScalarHYield",
        "ScalarRG1",
        "ScalarRG2",
        "ScalarRG3",
        "ScalarRG4",
        "f22_EV_CP_number",
        "r50_EV_CP_number",
        "s7_EV_CP_number",
        "target_max_concurrency",
        "time_budget_min",
        "timestep_hours",
        "u150_EV_CP_number",
    ]

    _INTEGER_KEYS = {"ESS_charge_mode", "ESS_discharge_mode", "target_max_concurrency"}

    def __init__(self, **kwargs: float | int | np.floating):
        super().__init__()
        for key, value in kwargs.items():
            assert isinstance(value, (float, int, np.floating)), f"Can only set numeric values, got {value}"
            self[key] = value
        self["timestep_hours"] = 1

    def __setitem__(self, key: str, value: float | int | np.float32) -> None:
        if key not in PyTaskData._VALID_KEYS:
            raise KeyError(str(key))

        if key in PyTaskData._INTEGER_KEYS:
            value = int(value)
        else:
            value = np.float32(value)
        self.__setattr__(key, value)

    def __getitem__(self, key: str) -> float | int | np.float32:
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(str(key)) from None

    def keys(self) -> Generator[str, None, None]:
        yield from PyTaskData._VALID_KEYS

    def values(self) -> Generator[float | int | np.float32, None, None]:
        yield from (self[key] for key in self.keys())

    def items(self) -> Generator[tuple[str, float | int | np.float32], None, None]:
        yield from zip(self.keys(), self.values())

    def __iter__(self) -> Generator[str, None, None]:
        yield from self.keys()

    def __contains__(self, item: str) -> bool:
        return item in set(self.keys())

    def __len__(self) -> int:
        return len(list(self.keys()))


class PySimulationResult:
    """
    Wrap a SimulationResult for python convenience.

    Implements a dict-like API for a SimulationResult.
    """

    def __init__(self, res: SimulationResult):
        self.res = res

    def keys(self) -> Generator[str, None, None]:
        yield from [
            "carbon_balance",
            "cost_balance",
            "capex",
            "payback_horizon",
            "annualised_cost",
        ]

    def values(self) -> Generator[float, None, None]:
        yield from (getattr(self.res, key) for key in self.keys())

    def items(self) -> Generator[tuple[str, float], None, None]:
        yield from zip(self.keys(), self.values())

    def __getitem__(self, key: str) -> np.float32:
        return np.float32(getattr(self.res, key))

    def __iter__(self) -> Generator[str, None, None]:
        yield from self.keys()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PySimulationResult):
            return all(self[key] == other[key] for key in self.keys())
        elif isinstance(other, SimulationResult):
            return all(self[key] == getattr(other, key) for key in self.keys())
        return False

    def __repr__(self) -> str:
        return "PySimulationData(" + ",".join(f"{key}={value}" for key, value in self.items()) + ")"
