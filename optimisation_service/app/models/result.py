import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from app.models.ga_utils import AnnotatedTaskData
from app.models.metrics import MetricValues
from epoch_simulator import SimulationResult


@dataclass
class SiteSolution:
    scenario: AnnotatedTaskData
    metric_values: MetricValues
    simulation_result: SimulationResult
    is_feasible: bool = True

    def __hash__(self) -> int:
        json_str = json.dumps(self.scenario.model_dump(), sort_keys=True, default=str)
        return hash(json_str)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return hash(self) == hash(other)


@dataclass
class PortfolioSolution:
    scenario: dict[str, SiteSolution]
    metric_values: MetricValues
    simulation_result: SimulationResult
    is_feasible: bool = True

    def __hash__(self) -> int:
        return hash(tuple(self.scenario.values()))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return hash(self) == hash(other)


@dataclass
class OptimisationResult:
    solutions: list[PortfolioSolution]
    n_evals: int
    exec_time: timedelta
    history: list[Any] | None = None

    def __post_init__(self) -> None:
        if not self.n_evals > 0:
            raise ValueError("Number of Evaluations must be positive.")
        if not self.exec_time > timedelta(seconds=0):
            raise ValueError("Execution time must be positive.")
