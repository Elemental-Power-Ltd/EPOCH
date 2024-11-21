from abc import ABC, abstractmethod

from app.models.constraints import ConstraintDict
from app.models.core import Site
from app.models.objectives import Objectives
from app.models.result import OptimisationResult


class Algorithm(ABC):
    @abstractmethod
    def run(self, objectives: list[Objectives], constraints: ConstraintDict, portfolio: list[Site]) -> OptimisationResult:
        """
        Run optimisation.

        Parameters
        ----------
        objectives
            List of metrics to optimise for.
        portfolio
            List of buidlings to find optimise scenarios.
        constraints
            Constraints to apply to metrics.

        Returns
        -------
        OptimisationResult
        """
        pass
