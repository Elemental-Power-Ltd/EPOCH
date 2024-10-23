from dataclasses import dataclass
from datetime import timedelta

from app.internal.task_data_wrapper import PyTaskData
from app.models.objectives import Objectives

ObjectiveValues = dict[Objectives, int | float]


@dataclass
class BuildingSolution:
    solution: PyTaskData
    objective_values: ObjectiveValues


@dataclass
class PortfolioSolution:
    solution: dict[str, BuildingSolution]
    objective_values: ObjectiveValues


@dataclass
class OptimisationResult:
    solutions: list[PortfolioSolution]
    n_evals: int
    exec_time: timedelta

    def __post_init__(self) -> None:
        if not self.n_evals > 0:
            raise ValueError("Number of Evaluations must be positive.")
        if not self.exec_time > timedelta(seconds=0):
            raise ValueError("Execution time must be positive.")
