import numpy as np

from app.models.constraints import Bounds, Constraints
from app.models.core import Site
from app.models.metrics import Metric
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


def merge_constraints(constraints_list: list[Constraints]) -> Constraints:
    """
    Merge a list of constraints into a single constraints dict keeping the harshest bounds.

    Parameters
    ----------
    constraints_list
        A list of constraints to merge.

    Returns
    -------
    merged
        The merged constraints.
    """
    merged: Constraints = {}

    for constraints in constraints_list:
        for metric, bounds in constraints.items():
            if metric not in merged:
                merged[metric] = Bounds()  # type: ignore

            if "min" in bounds:
                merged[metric]["min"] = max(bounds["min"], merged[metric].get("min", -float("inf")))

            if "max" in bounds:
                merged[metric]["max"] = min(bounds["max"], merged[metric].get("max", float("inf")))

    return merged


def get_shortfall_constraints(portfolio: list[Site], heat_tolerance: float = 0.01) -> Constraints:
    """
    Get the maximum shortfall constraints for a portfolio.
    Total heat shortfall is bounded above by heat_tolerance percent of the portfolio's total heat load.
    Total electrical shortfall is bounded above by 1 kWh to allow for some floating point issues.

    Parameters
    ----------
    portfolio
        A list of sites to generate shortfall constraints for.
    heat_tolerance
        Percentage of the heat load to bound the total heat shortfall by.

    Returns
    -------
    constraints
        Constraints dict, containing constraints on total_electrical_shortfall and total_heat_shortfall.
    """
    hload = 0.0
    for site in portfolio:
        hload += sum(site._epoch_data.building_hload)
    heat_max = max(heat_tolerance * hload, 1)
    constraints = {Metric.total_electrical_shortfall: Bounds(max=1), Metric.total_heat_shortfall: Bounds(max=heat_max)}
    return constraints


def get_capex_constraints() -> Constraints:
    """
    Get the minimum CAPEX.
    We force CAPEX to be greater than 0, since a scenario with 0 CAPEX is uninteresting to us.

    Returns
    -------
    constraints
        Constraints dict, containing a minimum constraint on CAPEX.
    """
    constraints = {Metric.capex: Bounds(min=float(np.finfo(np.float32).tiny))}
    return constraints


def get_cost_balance_constraints() -> Constraints:
    """
    Get the minimum cost balance.
    We force the cost balance to be positive 0, since a scenario with negative cost balance is uninteresting to us.

    Returns
    -------
    constraints
        Constraints dict, containing a minimum constraint on cost balacance.
    """
    constraints = {Metric.cost_balance: Bounds(min=0)}
    return constraints


def get_default_constraints(portfolio: list[Site]) -> Constraints:
    """
    Get the default constraints that should be applied to an optimisation task.
    These are:
    - Electrical and Heat shortfall upper bounds. We want to make sure that the solutions provided are viable energetically.
    - Cost balance lower bound. We wamt to make sure that the solutions provided are viable economically.
    - CAPEX lower bound. We want to exclude the £0 scenario since it is of no interest.

    Parameters
    ----------
    portfolio
        The portfolio to be optimised.

    Retunrs
    -------
    constraints
        A default constraints dict.
    """
    shortfall_constraints = get_shortfall_constraints(portfolio=portfolio)
    cost_balance_constraints = get_cost_balance_constraints()
    capex_constraints = get_capex_constraints()
    constraints = merge_constraints([shortfall_constraints, cost_balance_constraints, capex_constraints])
    return constraints
