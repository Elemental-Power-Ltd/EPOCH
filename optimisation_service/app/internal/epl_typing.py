from typing import Dict, TypedDict, TypeVar, Union

import numpy as np
import numpy.typing as npt
import pandas as pd

FloatOrArray = TypeVar("FloatOrArray", float, npt.NDArray[np.float64], pd.Series)


class ParamRange(TypedDict):
    min: Union[int, float]
    max: Union[int, float]
    step: Union[int, float]


ParameterDict = Dict[str, Union[list[Union[float, int]], float, int]]
DetailedParameterDict = Dict[str, Union[ParamRange, int, float]]
ConstraintDict = Dict[str, Union[tuple[None, None], tuple[float, float], list[Union[float, int, None]]]]
ObjectiveDict = Dict[str, Union[float, int]]
