from abc import ABC, abstractmethod
from enum import Enum
from hashlib import sha256

from .problem import Problem
from .result import Result


class Algorithm(ABC):
    paramstr: str

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


def alg_param_to_hash(*args: float | int | Enum) -> str:
    """
    Converts algorithm arguments into a string.

    Parameters
    ----------
    args
        list of arguments.

    Returns
    -------
    str
        sha256 hash of arguments.
    """
    items = sorted(args.items())
    param_str_list = [f"{key}={value}" for key, value in items]
    param_str = "__".join(param_str_list)
    return sha256(param_str.encode("utf-8")).hexdigest()
