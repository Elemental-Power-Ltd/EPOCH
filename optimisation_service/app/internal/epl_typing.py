from typing import Mapping, TypedDict, TypeVar, Union

import numpy as np
import numpy.typing as npt
import pandas as pd

FloatOrArray = TypeVar("FloatOrArray", float, npt.NDArray[np.float64], pd.Series)


class ParamRange(TypedDict):
    min: Union[int, float]
    max: Union[int, float]
    step: Union[int, float]


ParameterDict = Mapping[str, Union[list[Union[float, int]], float, int]]
DetailedParameterDict = Mapping[str, Union[ParamRange, int, float]]
ConstraintDict = Mapping[str, Union[tuple[None, None], tuple[float, float], list[Union[float, int, None]]]]
ObjectiveDict = Mapping[str, Union[float, int]]
