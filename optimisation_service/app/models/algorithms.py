from abc import ABC, abstractmethod

from app.internal.problem import PortfolioProblem
from app.models.result import OptimisationResult


class Algorithm(ABC):
    @abstractmethod
    def run(self, problem: PortfolioProblem) -> OptimisationResult:
        """
        Run optimisation.

        Parameters
        ----------
        problem
            Problem instance to optimise.

        Returns
        -------
        Result
        """
        pass
