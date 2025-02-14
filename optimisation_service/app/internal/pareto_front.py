import numpy as np
from paretoset import paretoset  # type: ignore

from app.models.metrics import Metric, MetricDirection
from app.models.result import PortfolioSolution


def portfolio_pareto_front(portfolio_solutions: list[PortfolioSolution], objectives: list[Metric]) -> list[PortfolioSolution]:
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
    objective_values = np.array(
        [[solution.metric_values[objective] for objective in objectives] for solution in portfolio_solutions]
    )
    objective_direct = ["max" if MetricDirection[objective] == -1 else "min" for objective in objectives]
    pareto_efficient = paretoset(costs=objective_values, sense=objective_direct, distinct=True)

    return np.array(portfolio_solutions)[pareto_efficient].tolist()
