"""Custom types that we will use across all internal modules.

This is not for external facing types: put those in the `../models/` folder if they're going to be used
as part of an API endpoint.

Use strong typing as much as possible to avoid errors, and add extra types here liberally.
"""

from collections.abc import Mapping
from typing import NewType

import pandas as pd


ParameterDict = dict[str, list[float] | list[int] | float | int]
ConstraintDict = Mapping[str, tuple[None, None] | tuple[float, float] | list[float] | list[int] | list[None]]
HHDataFrame = NewType("HHDataFrame", pd.DataFrame)
DailyDataFrame = NewType("DailyDataFrame", pd.DataFrame)
MonthlyDataFrame = NewType("MonthlyDataFrame", pd.DataFrame)
WeatherDataFrame = NewType("WeatherDataFrame", pd.DataFrame)
