from itertools import islice, product, starmap
from typing import cast

import numpy as np
from paretoset import paretoset  # type: ignore

from app.internal.epoch.converters import simulation_result_to_metric_dict
from app.models.metrics import Metric, MetricDirection
from app.models.result import PortfolioSolution
from epoch_simulator import aggregate_site_results


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
    feasible_portfolio_solutions = [
        portfolio_solution for portfolio_solution in portfolio_solutions if portfolio_solution.is_feasible
    ]
    if len(feasible_portfolio_solutions) > 0:
        portfolio_solutions = feasible_portfolio_solutions
    objective_values = np.array([
        [solution.metric_values[objective] for objective in objectives] for solution in portfolio_solutions
    ])
    objective_direct = ["max" if MetricDirection[objective] == -1 else "min" for objective in objectives]
    pareto_efficient = paretoset(costs=objective_values, sense=objective_direct, distinct=True)

    return cast(list[PortfolioSolution], np.array(portfolio_solutions)[pareto_efficient].tolist())


def _merge_solutions(sol1: PortfolioSolution, sol2: PortfolioSolution) -> PortfolioSolution:
    """
    Merge two Portfolio Solutions into one.

    Parameters
    ----------
    sol1
        The first PortfolioSolution to merge.
    sol2
        The second PortfolioSolution to merge.

    Returns
    -------
    PortfolioSolution
        The combined PortfolioSolution.
    """
    sol1_site_results = [site.simulation_result for site in sol1.scenario.values()]
    sol2_site_results = [site.simulation_result for site in sol2.scenario.values()]
    all_sites = sol1_site_results + sol2_site_results

    combined_result = aggregate_site_results(all_sites)

    is_feasible = sol1.is_feasible and sol2.is_feasible

    return PortfolioSolution(
        scenario=sol1.scenario | sol2.scenario,
        simulation_result=combined_result,
        metric_values=simulation_result_to_metric_dict(combined_result),
        is_feasible=is_feasible,
    )


def merge_list_of_portfolio_solutions(portfolio_solutions: list[PortfolioSolution]) -> PortfolioSolution:
    """
    Merge two Portfolio Solutions into one.

    Parameters
    ----------
    sol1
        The first PortfolioSolution to merge.
    sol2
        The second PortfolioSolution to merge.

    Returns
    -------
    PortfolioSolution
        The combined PortfolioSolution.
    """
    all_sites = [site.simulation_result for solution in portfolio_solutions for site in solution.scenario.values()]

    combined_result = aggregate_site_results(all_sites)

    is_feasible = all(solution.is_feasible for solution in portfolio_solutions)

    return PortfolioSolution(
        scenario={k: v for d in portfolio_solutions for k, v in d.scenario.items()},
        simulation_result=combined_result,
        metric_values=simulation_result_to_metric_dict(combined_result),
        is_feasible=is_feasible,
    )


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
        return list(starmap(_merge_solutions, list(combinations)))
    pf: list[PortfolioSolution] = []
    while subset := list(islice(combinations, batch_size)):
        if capex_limit is not None:
            subset_combined = [
                _merge_solutions(sol1, sol2)
                for sol1, sol2 in subset
                if sol1.metric_values[Metric.capex] + sol2.metric_values[Metric.capex] <= capex_limit
            ]
        else:
            subset_combined = list(starmap(_merge_solutions, subset))

        pf = portfolio_pareto_front(portfolio_solutions=pf + subset_combined, objectives=objectives)

    return pf
