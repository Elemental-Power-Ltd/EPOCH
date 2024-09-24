from abc import ABC, abstractmethod

from app.internal.problem import Problem
from app.internal.result import Result


class Algorithm(ABC):
    @abstractmethod
    def run(self, problem: Problem) -> Result:
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
