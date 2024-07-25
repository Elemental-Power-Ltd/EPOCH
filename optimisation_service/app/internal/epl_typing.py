from typing import Mapping, TypeVar

import numpy as np
import numpy.typing as npt
import pandas as pd

FloatOrArray = TypeVar("FloatOrArray", float, npt.NDArray[np.float64], pd.Series)

ParameterDict = dict[str, list[float] | list[int] | float | int]
ConstraintDict = Mapping[str, tuple[None, None] | tuple[float, float] | list[float] | list[int] | list[None]]
ObjectiveDict = dict[str, float | int]
