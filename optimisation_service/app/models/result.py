import json
from dataclasses import dataclass
from datetime import timedelta

from app.models.ga_utils import AnnotatedTaskData
from app.models.metrics import MetricValues


# TODO (2025-08-08 MHJB): should these be pydantic instead of dataclasses?
@dataclass
class SiteSolution:
    scenario: AnnotatedTaskData
    metric_values: MetricValues

    def __hash__(self):
        json_str = json.dumps(self.scenario.model_dump(), sort_keys=True, default=str)
        return hash(json_str)

    def __eq__(self, other):
        return hash(self) == hash(other)


@dataclass
class PortfolioSolution:
    scenario: dict[str, SiteSolution]
    metric_values: MetricValues

    def __hash__(self):
        return hash(tuple(self.scenario.values()))

    def __eq__(self, other):
        return hash(self) == hash(other)


@dataclass
class OptimisationResult:
    solutions: list[PortfolioSolution]
    n_evals: int
    exec_time: timedelta
    history: list | None = None

    def __post_init__(self) -> None:
        if not self.n_evals > 0:
            raise ValueError("Number of Evaluations must be positive.")
        if not self.exec_time > timedelta(seconds=0):
            raise ValueError("Execution time must be positive.")
