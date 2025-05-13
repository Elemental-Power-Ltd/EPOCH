# from collections.abc import Mapping
from typing import NotRequired, TypedDict

from app.models.metrics import Metric


class Bounds(TypedDict):
    min: NotRequired[int | float]
    max: NotRequired[int | float]


Constraints = dict[Metric, Bounds]
