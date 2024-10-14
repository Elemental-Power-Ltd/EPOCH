import glob
import json
import os
import shutil
from collections.abc import Generator
from dataclasses import dataclass
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import Self

import numpy as np

from ..models.problem import (
    ConstraintDict,
    Objectives,
    ParameterDict,
    ParametersWORange,
    ParametersWRange,
    ParamRange,
)
from .task_data_wrapper import PyTaskData

_OBJECTIVES = [objective.value for objective in Objectives]

_OBJECTIVES_DIRECTION = {"carbon_balance": -1, "cost_balance": -1, "capex": 1, "payback_horizon": 1, "annualised_cost": 1}


@dataclass(frozen=True)
class Problem:
    objectives: list[Objectives]
    constraints: ConstraintDict
    parameters: ParameterDict
    input_dir: str | PathLike

    def __post_init__(self) -> None:
        if not len(self.objectives) >= 1:
            raise ValueError("objectives must have at least one objective")
        if not set(self.objectives).issubset(_OBJECTIVES):
            raise ValueError(
                "Invalid objective(s):"
                + str({item.value if isinstance(item, Enum) else str(item) for item in self.objectives} - set(_OBJECTIVES))
            )
        if not set(self.constraints.keys()).issubset(_OBJECTIVES):
            raise ValueError(f"Invalid constraint name(s): {set(self.constraints.keys()) - set(_OBJECTIVES)}")
        for bounds in self.constraints.values():
            if bounds.get("min", -np.inf) > bounds.get("max", np.inf):
                raise ValueError("constraints lower bounds must be smaller or equal to upper bounds.")
        if set(self.parameters.keys()) != set(PyTaskData()._VALID_KEYS):
            param_set = set(self.parameters.keys())
            valid_set = set(PyTaskData()._VALID_KEYS)
            raise ValueError(
                f"Missing or invalid parameter keys. Extra parameters: {param_set - valid_set}."
                f"Missing parameters: {valid_set - param_set}"
            )
        for param_name in ParametersWRange:
            value = self.parameters[param_name]  # type: ignore
            if value["min"] > value["max"]:
                raise ValueError("parameter lower bounds must be smaller or equal to upper bounds.")
            step_is_zero = value["step"] == 0
            min_is_equal_max = value["min"] == value["max"]
            if step_is_zero and not min_is_equal_max:
                raise ValueError(
                    f"Parameter bounds for {param_name} must be equal if stepsize is 0",
                    f"but got {value["min"]} and {value["max"]}",
                )
            if not step_is_zero and min_is_equal_max:
                raise ValueError(
                    f"Stepsize for {param_name} must be equal if bounds are equal,",
                    f"but got {value["min"]} and {value["max"]} with a step of {value["step"]}",
                )

        if self.parameters["Export_kWh_price"] < 1 and self.parameters["Export_kWh_price"] != 0:
            raise ValueError(
                f"Export kWH price of {self.parameters["Export_kWh_price"]} is less than 1p / kWh.",
                " Check that the units are correctly in p / kWh and not £ / kWh.",
            )

    def variable_param(self) -> dict[str, ParamRange]:
        """
        Get parameters which have more than 1 possible value.

        Returns
        -------
        dict
            Dictionary of parameter ranges.
        """
        param_dict = {}
        for param_name in ParametersWRange:
            value = self.parameters[param_name]  # type: ignore
            if (value["step"] != 0) and (value["min"] != value["max"]):
                param_dict[param_name] = value
        return param_dict

    def constant_param(self) -> dict[str, float]:
        """
        Get parameters which have only 1 possible value.

        Returns
        -------
        dict
            Dictionary of parameter values.
        """
        param_dict = {}
        for param_name in ParametersWRange:
            value = self.parameters[param_name]  # type: ignore
            if (value["step"] == 0) and (value["min"] == value["max"]):
                param_dict[param_name] = value["min"]
        for param_name in ParametersWORange:
            param_dict[param_name] = self.parameters[param_name]  # type: ignore
        return param_dict

    def size(self) -> int:
        """
        Get size of parameter search space.
        Calculated by multiplying the number of possible values for each parameter together.

        Returns
        -------
        int
            Size of parameter search space.
        """
        size = 1
        for value in self.variable_param().values():
            n_pos_values = (value["max"] - value["min"]) / value["step"] + 1
            size = int(size * n_pos_values)

        return size

    def split_objectives(self) -> Generator[Self, None, None]:
        """
        Split a problem with multiple objectives (MOO) into multiple single objective (SOO) problems.

        Yield
        -------
        Problem
            Problem instance with single objectives
        """
        for objective in self.objectives:
            yield Problem([objective], self.constraints, self.parameters, self.input_dir)  # type: ignore


def load_problem(name: str, save_dir: str | os.PathLike) -> Problem:
    """
    Loads a problem's objectives, constraints and parameters from the folder under its name in the save directory.

    Parameters
    ----------
    name
        Name of the problem to load
    save_dir
        Path to the problem's directory

    Returns
    -------
    problem instance
    """
    problem_path = Path(save_dir, name)
    assert os.path.isdir(problem_path), "Benchmark does not exist."
    input_dir = Path(problem_path, "InputData")
    assert os.path.isdir(input_dir), "Benchmark does not have an InputData folder."

    with open(Path(problem_path, "objectives.json")) as f:
        objectives = json.load(f)
    with open(Path(problem_path, "constraints.json")) as f:
        constraints = json.load(f)
    with open(Path(problem_path, "parameters.json")) as f:
        parameters = json.load(f)

    return Problem(
        objectives=objectives,
        constraints=constraints,
        parameters=parameters,
        input_dir=input_dir,
    )


def save_problem(problem: Problem, name: str, save_dir: str | os.PathLike, overwrite: bool = False) -> None:
    """
    Saves a problem's objectives, constraints and parameters to json files and copies input data files.
    All are placed into the save directory under name.
    The parameters and input data files are placed in the subdirectory "InputData".

    Parameters
    ----------
    problem
        The problem instance to save
    name
        Name to save problem under
    save_dir
        The directory to place the files
    overwrite
        Whether to overwrite the current save files if they already exist
    """
    assert Path(problem.input_dir).exists(), "Couldn't find problem input directory."

    save_path = Path(save_dir, name)
    if not overwrite:
        assert not os.path.isdir(save_path), "Savefiles already exist under this name."

    Path(save_path).mkdir(parents=False, exist_ok=True)
    Path(save_path, "InputData").mkdir(parents=False, exist_ok=True)
    for file in glob.glob(f"{Path(problem.input_dir)}/*.csv"):
        shutil.copy(file, Path(save_path, "InputData/"))

    with open(Path(save_path, "objectives.json"), "w") as f:
        json.dump(problem.objectives, f)
    with open(Path(save_path, "constraints.json"), "w") as f:
        json.dump(problem.constraints, f)
    with open(Path(save_path, "parameters.json"), "w") as f:
        json.dump(problem.parameters, f)
