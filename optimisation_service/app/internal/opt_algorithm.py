from abc import ABC, abstractmethod

from .problem import Problem
from .result import Result


class Algorithm(ABC):
    @abstractmethod
    async def run(self, problem: Problem) -> Result:
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
