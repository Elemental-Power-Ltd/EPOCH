"""
Wrappers for Epoch that are more ergonomic for python.
"""

from collections.abc import Generator

import numpy as np

from app.models.parameters import ParametersWORange, ParametersWRange

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


class PyTaskData(TaskData):
    """
    Wrap a TaskData for Python convenience.

    Implements dict-like access, with string keys.
    """

    _VALID_KEYS = frozenset(ParametersWRange + ParametersWORange)

    _INTEGER_KEYS = frozenset(["ESS_charge_mode", "ESS_discharge_mode", "target_max_concurrency"])

    def __init__(self, **kwargs: float | int | np.floating | np.integer):
        super().__init__()
        for key, value in kwargs.items():
            assert isinstance(value, float | int | np.floating | np.integer), f"Can only set numeric values, got {value}"
            self[key] = value

    def __setitem__(self, key: str, value: float | int | np.floating | np.integer) -> None:
        if key not in PyTaskData._VALID_KEYS:
            raise KeyError(str(key))

        if key in PyTaskData._INTEGER_KEYS:
            value = int(value)
        else:
            value = np.float32(value)
        self.__setattr__(key, value)

    def __getitem__(self, key: str) -> float | int | np.floating | np.integer:
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(str(key)) from None

    def keys(self) -> Generator[str, None, None]:
        yield from PyTaskData._VALID_KEYS

    def values(self) -> Generator[float | int | np.floating | np.integer, None, None]:
        yield from (self[key] for key in self.keys())

    def items(self) -> Generator[tuple[str, float | int | np.floating | np.integer], None, None]:
        yield from zip(self.keys(), self.values())

    def __iter__(self) -> Generator[str, None, None]:
        yield from self.keys()

    def __contains__(self, item: str) -> bool:
        return item in set(self.keys())

    def __len__(self) -> int:
        return len(list(self.keys()))
