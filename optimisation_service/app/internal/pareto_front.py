import numpy as np
from paretoset import paretoset  # type: ignore

from app.models.objectives import _OBJECTIVES, Objectives, ObjectivesDirection
from app.models.result import PortfolioSolution


def portfolio_pareto_front(portfolio_solutions: list[PortfolioSolution], objectives: list[Objectives]):
    """
    Find the Pareto-front of a list of portfolio solutions according to a set of objectives.

    Parameters
    ----------
    portfolio_solutions
        List of portfolio solutions.
    objectives
        List of objectives to consider.

    Returns
    -------
    portfolio_solutions
        List of Pareto-front portfolio solutions.
    """
    objective_values = np.array([list(solution.objective_values.values()) for solution in portfolio_solutions])
    objective_mask = [_OBJECTIVES.index(col) for col in objectives]
    objective_values = objective_values[:, objective_mask]

    objective_direct = ["max" if ObjectivesDirection[objective] == -1 else "min" for objective in objectives]
    pareto_efficient = paretoset(costs=objective_values, sense=objective_direct, distinct=True)

    return np.array(portfolio_solutions)[pareto_efficient].tolist()
