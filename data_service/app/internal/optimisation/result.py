import os
import pickle as pkl
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

import numpy.typing as npt


class BenchmarkScoring(TypedDict):
    ExecTimeRatio: float
    NumEvalRatio: float
    InvertedGenDistPlus: float
    MaxParetoFrontError: float
    NumMatchingRatio: float
    NumNonDominatedRatio: float
    SpacingRatio: float
    SOOSuccess: dict[str, bool]
    SOOAccuracy: float


@dataclass(frozen=True)
class Result:
    solutions: npt.NDArray
    fitnesses: npt.NDArray
    n_evals: int
    exec_time: float

    def __post_init__(self) -> None:
        if not self.solutions.ndim == 2:
            raise ValueError("solutions must be 2D numpy arrays.")
        if not self.fitnesses.ndim == 2:
            raise ValueError("Solutions must be 2D numpy arrays.")
        if not self.solutions.shape[0] == self.fitnesses.shape[0]:
            raise ValueError("Solutions and Fitnesses must have the same shape.")
        if not self.n_evals > 0:
            raise ValueError("Number of Evaluations must be positive.")
        if not self.exec_time > 0:
            raise ValueError("Execution time must be positive.")


def save_optimisation_results(results: Result, save_dir: str | os.PathLike) -> None:
    """
    Save a Result instance to a directory.

    Parameters
    ----------
    results
        Result instance to save
    save_dir
        Directory to save to
    """
    Path(save_dir).mkdir(parents=False, exist_ok=True)
    with open(Path(save_dir, "optimisation_results.pkl"), "wb") as f:
        pkl.dump(results, f)


def load_optimisation_results(save_dir: str | os.PathLike) -> Result:
    """
    Load a Result instance from a directory.

    Parameters
    ----------
    save_dir
        Directory to save to

    Returns
    -------
    Result instance
    """
    with open(Path(save_dir, "optimisation_results.pkl"), "rb") as f:
        results = pkl.load(f)
    return results
