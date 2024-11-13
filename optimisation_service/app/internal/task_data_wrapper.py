"""
Wrappers for Epoch that are more ergonomic for python.
"""

from collections.abc import Generator

import numpy as np

from app.models.problem import ParametersWORange, ParametersWRange

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
        def simulate_scenario(self, task_data: TaskData, fullReporting: bool = False) -> SimulationResult:
            raise NotImplementedError()


class PyTaskData(TaskData):
    """
    Wrap a TaskData for Python convenience.

    Implements dict-like access, with string keys.
    """

    _VALID_KEYS = frozenset(ParametersWRange + ParametersWORange)

    _INTEGER_KEYS = frozenset(["ESS_charge_mode", "ESS_discharge_mode", "target_max_concurrency"])

    def __init__(self, **kwargs: float | int | np.floating):
        super().__init__()
        for key, value in kwargs.items():
            assert isinstance(value, float | int | np.floating), f"Can only set numeric values, got {value}"
            self[key] = value

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
