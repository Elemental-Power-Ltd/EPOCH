import glob
import json
import os
import shutil
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Generator, Self

from .epl_typing import ConstraintDict, OldParameterDict, ParameterDict, ParamRange
from .task_data_wrapper import PyTaskData

_OBJECTIVES = [
    "carbon_balance",
    "cost_balance",
    "capex",
    "payback_horizon",
    "annualised_cost",
]

_OBJECTIVES_DIRECTION = {"carbon_balance": -1, "cost_balance": -1, "capex": 1, "payback_horizon": 1, "annualised_cost": 1}


@dataclass(frozen=True)
class Problem:
    name: str
    objectives: list[str]
    constraints: ConstraintDict
    parameters: ParameterDict
    input_dir: str | PathLike

    def __post_init__(self) -> None:
        if not len(self.objectives) >= 1:
            raise ValueError("objectives must have at least one objective")
        if not set(self.objectives).issubset(_OBJECTIVES):
            raise ValueError(f"Invalid objective: {set(self.objectives) - set(_OBJECTIVES)}")
        if set(self.constraints.keys()) != set(_OBJECTIVES):
            raise ValueError(f"constraints must contain values for all of {_OBJECTIVES}.")
        for bounds in self.constraints.values():
            if bounds[0] is not None and bounds[1] is not None:
                if bounds[0] > bounds[1]:
                    raise ValueError("constraints lower bounds must be smaller or equal to upper bounds.")
        if set(self.parameters.keys()) != set(PyTaskData()._VALID_KEYS):
            param_set = set(self.parameters.keys())
            valid_set = set(PyTaskData()._VALID_KEYS)
            raise ValueError(
                f"Missing or invalid parameter keys. Extra parameters: {param_set - valid_set}."
                f"Missing parameters: {valid_set - param_set}"
            )
        for value in self.parameters.values():
            if isinstance(value, dict):
                if value["min"] > value["max"]:
                    raise ValueError("parameter lower bounds must be smaller or equal to upper bounds.")
                if ((value["step"] == 0) & (value["min"] != value["max"])) or (
                    (value["step"] != 0) & (value["min"] == value["max"])
                ):
                    raise ValueError("parameter bounds must be equal if stepsize is 0.")

    def variable_param(self) -> dict[str, ParamRange]:
        param_dict = {}
        for key, value in self.parameters.items():
            if isinstance(value, dict):
                if (value["step"] != 0) & (value["min"] != value["max"]):
                    param_dict[key] = value
        return param_dict

    def constant_param(self) -> dict[str, float]:
        param_dict = {}
        for key, value in self.parameters.items():
            if isinstance(value, dict):
                if (value["step"] == 0) & (value["min"] == value["max"]):
                    param_dict[key] = value["min"]
            else:
                param_dict[key] = value
        return param_dict

    def size(self) -> int:
        size = 1
        for value in self.variable_param().values():
            n_pos_values = (value["max"] - value["min"]) / value["step"] + 1
            size = int(size * n_pos_values)

        return size

    def split_objectives(self) -> Generator[Self, None, None]:
        for objective in self.objectives:
            yield Problem(self.name, [objective], self.constraints, self.parameters, self.input_dir)  # type: ignore


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

    with open(Path(problem_path, "objectives.txt"), "r") as f:
        objectives = [line.rstrip("\n") for line in f]
    with open(Path(problem_path, "constraints.json")) as f:
        constraints = json.load(f)
    with open(Path(problem_path, "parameters.json")) as f:
        parameters = json.load(f)

    return Problem(
        name=name,
        objectives=objectives,
        constraints=constraints,
        parameters=parameters,
        input_dir=input_dir,
    )


def save_problem(problem: Problem, save_dir: str | os.PathLike, overwrite: bool = False) -> None:
    """
    Saves a problem's objectives, constraints and parameters to json files and copies input data files.
    All are placed into the save directory under the problem name.
    The parameters and input data files are placed in the subdirectory "InputData".

    Parameters
    ----------
    problem
        The problem instance to save
    save_dir
        The directory to place the files
    overwrite
        Whether to overwrite the current save files if they already exist
    """
    assert Path(problem.input_dir).exists(), "Couldn't find problem input directory."

    save_path = Path(save_dir, problem.name)
    if not overwrite:
        assert not os.path.isdir(save_path), "Problem savefiles already exist."

    Path(save_path).mkdir(parents=False, exist_ok=True)
    Path(save_path, "InputData").mkdir(parents=False, exist_ok=True)
    for file in glob.glob(f"{Path(problem.input_dir)}/*.csv"):
        shutil.copy(file, Path(save_path, "InputData/"))

    with open(Path(save_path, "objectives.txt"), "w") as f:
        for s in problem.objectives:
            f.write(s + "\n")
    with open(Path(save_path, "constraints.json"), "w") as f:
        json.dump(problem.constraints, f)
    with open(Path(save_path, "parameters.json"), "w") as f:
        json.dump(problem.parameters, f)


def convert_param(parameters: ParameterDict) -> OldParameterDict:
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
    new_dict = {}
    for key, value in parameters.items():
        if isinstance(value, dict):
            new_dict[key] = [value["min"], value["max"], value["step"]]
        elif isinstance(value, int | float):
            new_dict[key] = value
    return new_dict
