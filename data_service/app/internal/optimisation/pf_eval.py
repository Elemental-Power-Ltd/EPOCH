import numpy as np
import numpy.typing as npt
from paretoset import paretoset  # type: ignore


def InvertedGenDistPlus(ref_pf: npt.NDArray, new_pf: npt.NDArray) -> float:
    """
    Compute average shortest distance between individuals in reference PF to individuals in new PF.
    Distance is set to 0 if new individual is better than any reference individual.

    Parameters
    ----------
    ref_pf
        Pareto Front to use as reference
    new_pf
        Pareto Front to compare
    """
    distances = np.sqrt(
        np.sum(
            np.maximum(new_pf[np.newaxis, :, :] - ref_pf[:, np.newaxis, :], 0) ** 2,
            axis=2,
        )
    )
    min_distances = np.min(distances, axis=1)
    return np.sum(min_distances) / ref_pf.shape[0]


def MaxParetoFrontError(ref_pf: npt.NDArray, new_pf: npt.NDArray) -> float:
    """
    Compute the largest distance between any individual in the new PF and the corresponding closest vector in the reference PF.

    Parameters
    ----------
    ref_pf
        Pareto Front to use as reference
    new_pf
        Pareto Front to compare
    """
    distances = np.sqrt(
        np.sum(
            np.maximum(new_pf[np.newaxis, :, :] - ref_pf[:, np.newaxis, :], 0) ** 2,
            axis=2,
        )
    )
    min_distances = np.min(distances, axis=1)
    return np.max(min_distances)


def MatchingIndividuals(ref_pf: npt.NDArray, new_pf: npt.NDArray) -> int:
    """
    Compute number of individuals in new PF found in reference PF.

    Parameters
    ----------
    ref_pf
        Pareto Front to use as reference
    new_pf
        Pareto Front to compare
    """
    is_matching = [int(np.any(np.all(np.isclose(solution, ref_pf, rtol=0.0, atol=1e-07), axis=1))) for solution in new_pf]
    return np.sum(is_matching)


def NonDominatedIndividuals(ref_pf: npt.NDArray, new_pf: npt.NDArray) -> int:
    """
    Compute number of individuals in new PF non-dominated by reference PF.

    Parameters
    ----------
    ref_pf
        Pareto Front to use as reference
    new_pf
        Pareto Front to compare
    """
    combined = np.concatenate([new_pf, ref_pf])
    non_dom = paretoset(combined)
    nd_new_pf = non_dom[: len(new_pf)]
    return sum(nd_new_pf)


def Spacing(pf: npt.NDArray) -> float:
    """
    Measures how evenly the PF's individuals are distributed along the PF.

    Parameters
    ----------
    pf
        Pareto Front to mesure
    """
    if pf.shape[0] == 1:
        return 0
    distances = np.sqrt(np.sum((pf[:, np.newaxis, :] - pf[np.newaxis, :, :]) ** 2, axis=2))
    id_m = np.identity(distances.shape[0])
    id_m[id_m == 1] = np.inf
    distances += id_m
    min_distances = np.min(distances, axis=0)
    return np.mean(min_distances)


def SingleObjectiveAccuracy(ref_pf: npt.NDArray, new_pf: npt.NDArray) -> list:
    """
    Returns boolean list of single-objectives optimised by new PF with respect to reference PF.

    Parameters
    ----------
    ref_pf
        Pareto Front to use as reference
    new_pf
        Pareto Front to compare
    """
    ref_pf_optimas = np.min(ref_pf, axis=0)
    new_pf_optimas = np.min(new_pf, axis=0)
    return list(new_pf_optimas <= ref_pf_optimas)
