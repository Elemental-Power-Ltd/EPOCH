from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from os import PathLike
from typing import Optional
from uuid import UUID

from pydantic import AwareDatetime, BaseModel

from ..internal.epl_typing import ParameterDict
from ..internal.genetic_algorithm import NSGA2, GeneticAlgorithm
from ..internal.grid_search import GridSearch
from ..internal.opt_algorithm import Algorithm
from ..internal.problem import Problem


class FileLoc(Enum):
    database = 0
    local = 1


class SiteData(BaseModel):
    loc: FileLoc
    path: Optional[PathLike] = None
    key: Optional[UUID] = None


class JSONTask(BaseModel):
    TaskID: UUID
    optimiser: str
    optimiserConfig: dict[str, str | int | float]
    searchParameters: ParameterDict
    objectives: list
    siteData: SiteData


@dataclass
class PyTask:
    TaskID: UUID
    optimiser: Algorithm
    problem: Problem
    siteData: SiteData


class Optimiser(Enum):
    NSGA2 = NSGA2
    GeneticAlgorithm = GeneticAlgorithm
    GridSearch = GridSearch


class state(Enum):
    QUEUED = 0
    RUNNING = 1
    CANCELLED = 2


@dataclass
class QueueElem:
    STATE: state
    added_at: datetime


@dataclass
class QueueStatus:
    queue: dict[UUID, QueueElem]
    service_uptime: float


class DatasetIDWithTime(BaseModel):
    dataset_id: UUID
    start_ts: AwareDatetime
    end_ts: AwareDatetime
