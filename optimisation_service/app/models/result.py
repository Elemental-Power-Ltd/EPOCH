from dataclasses import dataclass
from datetime import timedelta

from epoch_simulator import TaskData

from app.models.metrics import MetricValues


@dataclass
class SiteSolution:
    scenario: TaskData
    metric_values: MetricValues

    def __hash__(self):
        return hash(self.scenario)


@dataclass
class PortfolioSolution:
    scenario: dict[str, SiteSolution]
    metric_values: MetricValues

    def __hash__(self):
        return hash(tuple(self.scenario.values()))


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
