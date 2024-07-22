from abc import ABC, abstractmethod
from enum import Enum

from .problem import Problem
from .result import Result


class Algorithm(ABC):
    paramstr: str

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
                add = f"{param:.17E}"
                add = add.split("E")[0].rstrip("0").rstrip(".") + "E" + add.split("E")[1]
            else:
                if add.startswith("0."):
                    add = add[1:]
        elif isinstance(param, int):
            add = str(param)
            if len(add) > 5:
                add = f"{param:.0e}"
        elif isinstance(param, Enum):
            add = param.name
        paramstr += "_" + add
    return paramstr
