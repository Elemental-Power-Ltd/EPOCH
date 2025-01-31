from dataclasses import dataclass
from datetime import timedelta

<<<<<<< HEAD
import numpy as np

from app.internal.epoch_utils import SimulationResult, TaskData
from app.models.objectives import _OBJECTIVES, Objectives, ObjectiveValues


def convert_sim_result(sim_result: SimulationResult) -> ObjectiveValues:
    objective_values = ObjectiveValues()
    for objective in _OBJECTIVES:
        if objective == Objectives.carbon_cost:
            if sim_result.carbon_balance_scope_1 > 0:
                objective_values[Objectives.carbon_cost] = sim_result.capex / (sim_result.carbon_balance_scope_1 * 15 / 1000)
            else:
                objective_values[Objectives.carbon_cost] = np.finfo(np.float32).max
        else:
            objective_values[objective] = getattr(sim_result, objective)
    return objective_values
=======
from app.internal.epoch_utils import TaskData
from app.models.objectives import ObjectiveValues
>>>>>>> 8ac6f7d5594df344b18d6aad2289ecaa89634e79


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
