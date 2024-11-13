from dataclasses import dataclass

from pydantic import UUID4

from app.internal.problem import PortfolioProblem

from ..internal.datamanager import DataManager
from .algorithms import Algorithm


@dataclass
class Task:
    task_id: UUID4
    optimiser: Algorithm
    problem: PortfolioProblem
    data_manager: DataManager
