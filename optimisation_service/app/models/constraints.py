from collections.abc import Mapping
from typing import NotRequired, TypedDict

from app.models.objectives import Objectives


class Bounds(TypedDict):
    min: NotRequired[int | float]
    max: NotRequired[int | float]


Constraints = Mapping[Objectives, Bounds]
