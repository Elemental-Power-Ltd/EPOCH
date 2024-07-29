from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from os import PathLike
from typing import Optional
from uuid import UUID

from ..internal.epl_typing import DetailedParameterDict
from ..internal.genetic_algorithm import NSGA2, GeneticAlgorithm
from ..internal.grid_search import GridSearch


class FileLoc(Enum):
    database = 0
    local = 1


@dataclass
class SiteData:
    loc: FileLoc
    path: Optional[PathLike] = None
    key: Optional[UUID] = None


@dataclass
class Task:
    TaskID: UUID
    optimiser: str
    optimiserConfig: dict[str, str | int | float]
    searchParameters: DetailedParameterDict
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
