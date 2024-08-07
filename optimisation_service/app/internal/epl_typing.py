from typing import Mapping, TypedDict, TypeVar

import numpy as np
import numpy.typing as npt
import pandas as pd

FloatOrArray = TypeVar("FloatOrArray", float, npt.NDArray[np.float64], pd.Series)


class Bounds(TypedDict):
    min: int | float | None = None
    max: int | float | None = None


OldParameterDict = Mapping[str, list[int | float] | tuple[int | float] | int | float]
ConstraintDict = Mapping[str, Bounds]
