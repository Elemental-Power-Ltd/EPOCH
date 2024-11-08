import json
import logging
import os
import pathlib
import platform
import shutil
import subprocess
import tempfile
import time
from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from paretoset import paretoset  # type: ignore

from ..models.algorithms import Algorithm
from ..models.problem import EndpointParameterDict, OldParameterDict, ParameterDict, ParametersWORange, ParametersWRange
from .problem import _OBJECTIVES, _OBJECTIVES_DIRECTION, Problem
from .result import Result

logger = logging.getLogger("default")

_EPOCH_CONFIG = {"optimiser": {"leagueTableCapacity": 1, "produceExhaustiveOutput": True}}


def convert_param(parameters: ParameterDict | EndpointParameterDict | dict[str, Any]) -> OldParameterDict:
    """
    Converts dictionary of parameters from dict of dicts to dict of lists.
    ex: {"param1":{"min":0, "max":10, "step":1}, "param2":123} -> {"param1":[0, 10, 1], "param2":123}

    Parameters
    ----------
    parameters
        Dictionary of parameters with values in the format {"min":min, "max":max, "step":step} or int or float.

    Returns
    -------
    ParameterDict
        Dictionary of parameters with values in the format [min, max, step] or int or float.
    """
    if isinstance(parameters, EndpointParameterDict):
        parameters = parameters.model_dump()
    new_dict = {}
    for param_name in ParametersWRange:
        value = parameters[param_name]  # type: ignore
        new_dict[param_name] = [value["min"], value["max"], value["step"]]
    for param_name in ParametersWORange:
        new_dict[param_name] = parameters[param_name]  # type: ignore
    return new_dict


class GridSearch(Algorithm):
    """
    Optimise a multi-objective EPOCH problem using grid search.
    """

    def __init__(
        self,
        keep_degenerate: bool = False,
    ) -> None:
        """
        Define grid search parameters.

        Parameters
        ----------
        keep_degenerate
            Whether or not to keep degenerate solutions in solutions
        """
        self.keep_degenerate = keep_degenerate

    def run(self, problem: Problem) -> Result:
        """
        Run grid search optimisation.

        Parameters
        ----------
        problem
            Problem instance to optimise.

        Returns
        -------
        solutions
            Optimal solutions.
        objective_values
            objective_values of optimal solutions.
        """
        temp_dir = tempfile.TemporaryDirectory()

        output_dir = Path(temp_dir.name, "tmp_outputs")
        os.makedirs(output_dir, exist_ok=True)

        config_dir = Path(temp_dir.name, "Config")
        Path(temp_dir.name, "Config").mkdir(parents=False, exist_ok=False)

        with open(Path(config_dir, "EpochConfig.json"), "w") as f:
            json.dump(_EPOCH_CONFIG, f)

        with open(Path(problem.input_dir, "inputParameters.json"), "w") as f:
            json.dump(convert_param(problem.parameters), f)

        t0 = time.perf_counter()
        run_headless(
            config_dir=str(config_dir),
            input_dir=str(problem.input_dir),
            output_dir=str(output_dir),
        )
        exec_time = timedelta(seconds=(time.perf_counter() - t0))

        os.remove(Path(problem.input_dir, "inputParameters.json"))

        variable_param = list(problem.variable_param().keys())
        usecols = [item.value if isinstance(item, Enum) else str(item) for item in _OBJECTIVES + variable_param]

        df_res = pd.read_csv(Path(output_dir, "ExhaustiveResults.csv"), encoding="cp1252", dtype=np.float32, usecols=usecols)

        for constraint, bounds in problem.constraints.items():
            df_res = df_res[df_res[constraint] >= bounds.get("min", -np.inf)]
            df_res = df_res[df_res[constraint] <= bounds.get("max", -np.inf)]

        solutions = df_res[variable_param].to_numpy()
        obj_direct = ["max" if _OBJECTIVES_DIRECTION[objective] == -1 else "min" for objective in problem.objectives]
        pareto_efficient = paretoset(df_res[problem.objectives].to_numpy(), obj_direct, distinct=not self.keep_degenerate)
        solutions = solutions[pareto_efficient]
        objective_values = df_res[_OBJECTIVES].to_numpy()[pareto_efficient]

        temp_dir.cleanup()

        return Result(solutions=solutions, objective_values=objective_values, exec_time=exec_time, n_evals=problem.size())


def run_headless(
    input_dir: os.PathLike | str,
    output_dir: os.PathLike | str,
    config_dir: os.PathLike | str,
) -> dict[str, float]:
    """
    Run the headless version of Epoch as a subprocess

    Parameters
    ----------
    input_dir
        A directory containing input data for Epoch.
    output_dir
         The directory to write the output to.
    config_dir
        A directory containing the config file(s) for Epoch.

    Returns
    -------
        A dictionary containing the best value for each of the five objectives
    """
    logger.debug("Running run_headless.")

    epoch_path = get_epoch_path()

    input_dir, output_dir, config_dir = pathlib.Path(input_dir), pathlib.Path(output_dir), pathlib.Path(config_dir)
    # check these directories exist
    assert input_dir.is_dir(), f"Could not find {input_dir}"
    assert output_dir.is_dir(), f"Could not find {output_dir}"
    assert config_dir.is_dir(), f"Could not find {config_dir}"

    # check for required files within the directories
    assert (input_dir / "inputParameters.json").is_file(), f"Could not find {input_dir / "inputParameters.json"} is not a file"
    assert (config_dir / "EpochConfig.json").is_file(), f"Could not find {input_dir / "EpochConfig.json"} is not a file"

    result = subprocess.run([
        epoch_path,
        "--input",
        str(input_dir),
        "--output",
        str(output_dir),
        "--config",
        str(config_dir),
    ])

    assert result.returncode == 0, result

    output_json = output_dir / "outputParameters.json"

    with open(output_json) as f:
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


def get_epoch_path() -> str:
    """
    Find the Epoch executable

    This tries a number of options in the following order:
    1. Epoch is in the system PATH
    2. There is a release build of Epoch within the EPOCH_DIRECTORY path
    3. There is a debug build of Epoch within the EPOCH_DIRECTORY path

    Returns
    -------
        A valid path to supply to subprocess.run
    """

    # When using Docker, we expect to find Epoch in the PATH
    system_path_epoch = shutil.which("Epoch")
    if system_path_epoch:
        logger.debug(f"Found Epoch in the PATH - {system_path_epoch}")
        return "Epoch"

    # Epoch is not in the system PATH, try looking in the build folder of EPOCH_DIR
    epoch_dir = str(os.environ.get("EPOCH_DIR", "./Epoch"))

    if platform.system() == "Windows":
        # Windows places Release and Debug builds in separate folders
        # We prioritise Release builds (we currently only support RelWithDebInfo and Debug)
        exe_name = "Epoch.exe"

        suffixes = [
            pathlib.Path("build", "headless", "epoch_main", "RelWithDebInfo"),
            pathlib.Path("build", "headless", "epoch_main", "Debug")
        ]
    else:
        # Linux places the executable in build/epoch_main
        exe_name = "Epoch"

        suffixes = [
            pathlib.Path("build", "epoch_main")
        ]

    project_path = pathlib.Path(epoch_dir)

    for suffix in suffixes:
        full_path_to_exe = project_path / suffix / exe_name
        if os.path.isfile(full_path_to_exe):
            logger.debug(f"Found Epoch at {full_path_to_exe}")
            return str(full_path_to_exe)

    raise FileNotFoundError("Failed to find Epoch executable")
