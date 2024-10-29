from collections.abc import Generator
from dataclasses import dataclass
from enum import Enum
from os import PathLike
from typing import Self

import numpy as np

from app.internal.task_data_wrapper import PyTaskData
from app.models.constraints import ConstraintDict
from app.models.objectives import _OBJECTIVES, Objectives
from app.models.parameters import (
    ParameterDict,
    ParametersWORange,
    ParametersWRange,
    ParamRange,
)


@dataclass(frozen=True)
class Building:
    parameters: ParameterDict
    input_dir: PathLike

    def __post_init__(self) -> None:
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

        if self.parameters["ASHP_HSource"]["step"] != 0:
            raise ValueError(
                "Scanning over ASHP_HSource parameters for a site without a hot room.",
                " Set ASHP_HSource['min'] == ASHP_HSource['max'] == 1.",
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


@dataclass()
class PortfolioProblem:
    objectives: list[Objectives]
    constraints: ConstraintDict
    buildings: dict[str, Building]

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

    def split_objectives(self) -> Generator[Self, None, None]:
        """
        Split a problem with multiple objectives (MOO) into multiple single objective (SOO) problems.

        Yield
        -------
        Problem
            Problem instance with single objectives
        """
        for objective in self.objectives:
            yield PortfolioProblem([objective], self.constraints, self.buildings)  # type: ignore
