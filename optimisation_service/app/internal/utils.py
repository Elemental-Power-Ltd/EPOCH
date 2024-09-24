import typing
from typing import Any, Never

import numpy as np
import numpy.typing as npt
from pymoo.core.mutation import Mutation  # type: ignore
from pymoo.operators.repair.bounds_repair import repair_random_init  # type: ignore

from ..internal.genetic_algorithm import ProblemInstance


def typename(x: typing.Any) -> str:
    """
    Get a string representation of the name of a class.

    Parameters
    ----------
    x
        Any python object

    Returns
    -------
        String of the name, e.g. typename(1) == "int"
    """
    return type(x).__name__


def mut_simple_int(X: npt.NDArray, xl: npt.NDArray, xu: npt.NDArray, prob: npt.NDArray) -> npt.NDArray:
    """
    Mutate integer variables by 1.
    """
    n, _ = X.shape
    assert len(prob) == n

    Xp = np.full(X.shape, np.inf)
    mut = np.random.random(X.shape) < prob[:, None]
    mut_pos = (np.random.random(mut.shape) < 0.5) * mut
    mut_neg = -(mut * ~mut_pos)
    Xp[:, :] = X
    Xp += mut_pos + mut_neg

    Xp = repair_random_init(Xp, X, xl, xu)

    return Xp


class SimpleIntMutation(Mutation):
    """
    Mutate integer variables by 1.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def _do(self, problem: ProblemInstance, X: npt.NDArray, **kwargs: Never) -> npt.NDArray:
        X.astype(float)
        prob_var = self.get_prob_var(problem, size=len(X))
        Xp = mut_simple_int(X, problem.xl, problem.xu, prob_var)

        return Xp
