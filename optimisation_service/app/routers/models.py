from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from os import PathLike
from typing import TypedDict
from uuid import UUID

from ..internal.genetic_algorithm import NSGA2, GeneticAlgorithm
from ..internal.grid_search import GridSearch


class ParamRange(TypedDict):
    min: int | float
    max: int | float
    step: int | float


class FileLoc(Enum):
    database = 0
    local = 1


@dataclass
class SiteData:
    loc = FileLoc
    key = UUID | PathLike


@dataclass
class Task:
    TaskID: UUID
    optimiser: str
    optimiserConfig: dict[str, str | int | float]
    searchParameters: dict[str, ParamRange | int | float]
    objectives: list
    siteData: SiteData


class Optimiser(Enum):
    NSGA2 = NSGA2
    GeneticAlgorithm = GeneticAlgorithm
    GridSearch = GridSearch


class state(Enum):
    QUEUED = 0
    RUNNING = 1
    CANCELLED = 2


@dataclass()
class QueueElem:
    STATE: state
    added_at: datetime


@dataclass()
class QueueStatus:
    queue: dict[UUID, QueueElem]
    service_uptime: float
