"""Custom types that we will use across all internal modules.

This is not for external facing types: put those in the `../models/` folder if they're going to be used
as part of an API endpoint.

Use strong typing as much as possible to avoid errors, and add extra types here liberally.
"""

import functools
import warnings
from collections.abc import Callable, Mapping
from typing import NewType, ParamSpec, TypeVar

import pandas as pd

P = ParamSpec("P")
R = TypeVar("R")


def mark_unused(func: Callable[P, R]) -> Callable[P, R]:
    """
    Mark a given function as unused.

    This function has deliberately been left in the code for notebook or debugging purposes,
    but should be used more generally.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        warnings.warn(f"Call to an unused function {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


ParameterDict = dict[str, list[float] | list[int] | float | int]
ConstraintDict = Mapping[str, tuple[None, None] | tuple[float, float] | list[float] | list[int] | list[None]]
HHDataFrame = NewType("HHDataFrame", pd.DataFrame)
DailyDataFrame = NewType("DailyDataFrame", pd.DataFrame)
MonthlyDataFrame = NewType("MonthlyDataFrame", pd.DataFrame)
WeatherDataFrame = NewType("WeatherDataFrame", pd.DataFrame)
