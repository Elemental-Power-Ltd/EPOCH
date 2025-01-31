from dataclasses import dataclass
from datetime import timedelta

from app.internal.epoch_utils import TaskData
from app.models.objectives import ObjectiveValues


@dataclass
class SiteSolution:
    scenario: TaskData
    objective_values: ObjectiveValues


@dataclass
class PortfolioSolution:
    scenario: dict[str, SiteSolution]
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
