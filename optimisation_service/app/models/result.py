from dataclasses import dataclass
from datetime import timedelta

from app.internal.epoch_utils import PyTaskData, SimulationResult
from app.models.objectives import _OBJECTIVES, ObjectiveValues


def convert_sim_result(sim_result: SimulationResult) -> ObjectiveValues:
    objective_values = ObjectiveValues()
    for objective in _OBJECTIVES:
        objective_values[objective] = getattr(sim_result, objective)
    return objective_values


@dataclass
class BuildingSolution:
    solution: PyTaskData | dict[str, int | float]
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
