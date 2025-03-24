from app.models.constraints import Constraints
from app.models.result import PortfolioSolution


def count_constraints(constraints: Constraints) -> int:
    """
    Count the number of individual upper or lower bounds placed on metric values as optimisation constraints.

    Parameters
    ----------
    constraints
        Dictionary of constraints to analyse.

    Returns
    -------
    n_constraints
        Number of individuals constraints found.
    """
    n_constraints = 0
    for bounds in constraints.values():
        min_value = bounds.get("min", None)
        max_value = bounds.get("max", None)
        if min_value is not None:
            n_constraints += 1
        if max_value is not None:
            n_constraints += 1
    return n_constraints


def is_in_constraints(constraints: Constraints, solutions: list[PortfolioSolution]) -> list[bool]:
    """
    Informs which PortfolioSolutions are within the metric constraints.

    Parameters
    ----------
    constraints
        Dictionary of constraints to check against.
    solutions
        List of PortfolioSolutions to check.

    Returns
    -------
    mask
        Boolean mask indicating if each solution is within the constratins or not.
    """
    if len(constraints) > 0:
        mask = []
        for solution in solutions:
            within_constraints = True
            metric_values = solution.metric_values
            for metric, bounds in constraints.items():
                min_value = bounds.get("min", None)
                max_value = bounds.get("max", None)

                if min_value is not None and min_value >= metric_values[metric]:
                    within_constraints = False
                    break
                if max_value is not None and max_value <= metric_values[metric]:
                    within_constraints = False
                    break
            mask.append(within_constraints)

        return mask

    return [True] * len(solutions)
