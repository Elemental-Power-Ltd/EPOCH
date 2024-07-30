from abc import ABC, abstractmethod
from collections.abc import Awaitable
from enum import Enum

from .problem import Problem
from .result import Result


class Algorithm(ABC):
    paramstr: str

    @abstractmethod
    async def run(self, problem: Problem, verbose: bool) -> Awaitable[Result]:
        """
        Run optimisation.

        Parameters
        ----------

        problem
            Problem instance to optimise.
        verbose
            Whether the algorithm should print output in this run or not.

        Returns
        -------
        Result
        """
        pass


def alg_param_to_string(*args: float | int | Enum) -> str:
    """
    Converts algorithm arguments into a string.

    Parameters
    ----------
    args
        list of arguments

    Returns
    -------
    string of arguments
    """
    paramstr = ""
    for param in args:
        if isinstance(param, float):
            add = str(param)
            if len(add) > 5:
                add = "{0:.17E}".format(param)
                add = add.split("E")[0].rstrip("0").rstrip(".") + "E" + add.split("E")[1]
            else:
                if add.startswith("0."):
                    add = add[1:]
        elif isinstance(param, int):
            add = str(param)
            if len(add) > 5:
                add = "{:.0e}".format(param)
        elif isinstance(param, Enum):
            add = param.name
        paramstr += "_" + add
    return paramstr
