from dataclasses import dataclass

from pydantic import UUID4

from ...internal.opt_algorithm import Algorithm
from ...internal.problem import Problem
from ..utils.datamanager import DataManager


@dataclass
class Task:
    task_id: UUID4
    optimiser: Algorithm
    problem: Problem
    data_manager: DataManager
