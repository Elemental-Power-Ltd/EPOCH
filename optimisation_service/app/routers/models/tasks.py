from dataclasses import dataclass

from pydantic import UUID4

from app.internal.models.algorithms import Algorithm
from app.internal.problem import Problem
from app.routers.utils.datamanager import DataManager


@dataclass
class Task:
    task_id: UUID4
    optimiser: Algorithm
    problem: Problem
    data_manager: DataManager
