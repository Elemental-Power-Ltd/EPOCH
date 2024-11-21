from collections.abc import Mapping
from typing import TypedDict

from app.models.objectives import Objectives


class Bounds(TypedDict):
    min: int | float
    max: int | float


ConstraintDict = Mapping[Objectives, Bounds]
