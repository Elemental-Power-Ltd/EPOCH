from typing import Mapping, TypedDict, TypeVar

import numpy as np
import numpy.typing as npt
import pandas as pd

FloatOrArray = TypeVar("FloatOrArray", float, npt.NDArray[np.float64], pd.Series)


class ParamRange(TypedDict):
    min: int | float
    max: int | float
    step: int | float


OldParameterDict = Mapping[str, list[int | float] | tuple[int | float] | int | float]
ParameterDict = Mapping[str, ParamRange | int | float]
ConstraintDict = Mapping[str, tuple[None, None] | tuple[float, float] | list[float | int | None]]
ObjectiveDict = Mapping[str, float | int]
