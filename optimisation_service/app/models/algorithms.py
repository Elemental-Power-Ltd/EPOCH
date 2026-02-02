from abc import ABC, abstractmethod

from app.models.constraints import Constraints
from app.models.core import Site
from app.models.metrics import Metric
from app.models.result import OptimisationResult


class Algorithm(ABC):
    @abstractmethod
    def run(self, objectives: list[Metric], constraints: Constraints, portfolio: list[Site]) -> OptimisationResult:
        """
        Run optimisation.

        Parameters
        ----------
        objectives
            List of metrics to optimise for.
        portfolio
            List of sites to optimise.
        constraints
            Constraints to apply to metrics.

        Returns
        -------
        OptimisationResult
        """
        pass
