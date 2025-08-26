"""Custom types that we will use across all internal modules.

This is not for external facing types: put those in the `../models/` folder if they're going to be used
as part of an API endpoint.

Use strong typing as much as possible to avoid errors, and add extra types here liberally.
"""

import functools
import warnings
from collections.abc import Callable, Mapping
from typing import NewType

import asyncpg
import pandas as pd


def mark_unused[R, **KW](func: Callable[KW, R]) -> Callable[KW, R]:
    """
    Mark a given function as unused.

    This function has deliberately been left in the code for notebook or debugging purposes,
    but should be used more generally.
    """

    @functools.wraps(func)
    def wrapper(*args: KW.args, **kwargs: KW.kwargs) -> R:
        warnings.warn(f"Call to an unused function {func.__name__}", stacklevel=2)
        return func(*args, **kwargs)

    return wrapper


type ParameterDict = dict[str, list[float] | list[int] | float | int]
type ConstraintDict = Mapping[str, tuple[None, None] | tuple[float, float] | list[float] | list[int] | list[None]]
HHDataFrame = NewType("HHDataFrame", pd.DataFrame)
DailyDataFrame = NewType("DailyDataFrame", pd.DataFrame)
MonthlyDataFrame = NewType("MonthlyDataFrame", pd.DataFrame)
WeatherDataFrame = NewType("WeatherDataFrame", pd.DataFrame)
SquareHHDataFrame = NewType("SquareHHDataFrame", pd.DataFrame)

type db_pool_t = asyncpg.pool.Pool
type db_conn_t = db_pool_t | asyncpg.Connection | asyncpg.pool.PoolConnectionProxy
type Jsonable = dict[str, Jsonable] | list[Jsonable] | str | int | float | bool | None
