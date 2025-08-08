from itertools import islice, product
from typing import cast

import numpy as np
from paretoset import paretoset  # type: ignore

from app.internal.portfolio_simulator import combine_metric_values
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
    objective_values = np.array([
        [solution.metric_values[objective] for objective in objectives] for solution in portfolio_solutions
    ])
    objective_direct = ["max" if MetricDirection[objective] == -1 else "min" for objective in objectives]
    pareto_efficient = paretoset(costs=objective_values, sense=objective_direct, distinct=True)

    return cast(list[PortfolioSolution], np.array(portfolio_solutions)[pareto_efficient].tolist())


def merge_and_optimise_two_portfolio_solution_lists(
    list1: list[PortfolioSolution],
    list2: list[PortfolioSolution],
    objectives: list[Metric],
    capex_limit: float | None = None,
    batch_size: int = 1000000,
) -> list[PortfolioSolution]:
    """
    Merge two lists of portfolio solutions into a single list of portfolio solutions that is pareto-optimal.

    Achieved by taking the product of both lists and optimising them in batches of batch_size,
    whilst maintaining a pareto-optimal list of solutions.
    A capex_limit can be set to remove out-of-bound solutions before the optimisation step.

    Parameters
    ----------
    list1
        List of portfolio solutions.
    list2
        List of portfolio solutions.
    objectives
        List of objectives to use in optimisation.
    capex_limit
        Set an upper constraint on the CAPEX of the merged solutions.
        Can help improve the performance of the optimisation step by reducing the number of candidates to analyse.
    batch_size
        Number of solutions to optimise at the same time.
        Large batch_size may cause memory errors.
        Small batch_size will take longer to compute.

    Returns
    -------
    list[PortfolioSolution]
        New pareto front of solutions
    """
    combinations = product(list1, list2)
    if len(list1) == 1 or len(list2) == 1:
        return [
            PortfolioSolution(
                scenario=sol1.scenario | sol2.scenario,
                metric_values=combine_metric_values([sol1.metric_values, sol2.metric_values]),
            )
            for sol1, sol2 in list(combinations)
        ]
    pf: list[PortfolioSolution] = []
    while subset := list(islice(combinations, batch_size)):
        if capex_limit is not None:
            subset_combined = [
                PortfolioSolution(
                    scenario=sol1.scenario | sol2.scenario,
                    metric_values=combine_metric_values([sol1.metric_values, sol2.metric_values]),
                )
                for sol1, sol2 in subset
                if sol1.metric_values[Metric.capex] + sol2.metric_values[Metric.capex] <= capex_limit
            ]
        else:
            subset_combined = [
                PortfolioSolution(
                    scenario=sol1.scenario | sol2.scenario,
                    metric_values=combine_metric_values([sol1.metric_values, sol2.metric_values]),
                )
                for sol1, sol2 in subset
            ]

        pf = portfolio_pareto_front(portfolio_solutions=pf + subset_combined, objectives=objectives)

    return pf
