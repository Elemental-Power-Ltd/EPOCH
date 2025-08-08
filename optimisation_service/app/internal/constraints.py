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


def get_shortfall_constraints(site: Site, heat_tolerance: float = 0.01) -> Constraints:
    """
    Get the maximum shortfall constraints for a site.

    Total heat shortfall is bounded above by heat_tolerance percent of the site's heat load.
    Total electrical shortfall is bounded above by 1 kWh to allow for some floating point issues.

    Parameters
    ----------
    site
        A site to generate shortfall constraints for.
    heat_tolerance
        Percentage of the heat load to bound the total heat shortfall by.

    Returns
    -------
    constraints
        Constraints dict, containing constraints on total_electrical_shortfall and total_heat_shortfall.
    """
    hload = sum(site._epoch_data.building_hload)
    heat_max = max(heat_tolerance * hload, 1)
    constraints = {Metric.total_electrical_shortfall: Bounds(max=1), Metric.total_heat_shortfall: Bounds(max=heat_max)}
    return constraints


def apply_default_constraints(
    exsiting_portfolio: list[Site], existing_constraints: Constraints
) -> tuple[list[Site], Constraints]:
    """
    Apply default constraints to existing portfolio and site constraints.

    These are:
    - Electrical and Heat shortfall upper bounds on the sites.
      We want to make sure that the solutions provided are viable energetically.

    Parameters
    ----------
    exsiting_portfolio
        The associated portfolio.
    existing_constraints
        The existing portfolio constraints.

    Returns
    -------
    portfolio
        The existing associated portfolio with default site constraints applied to it.
    constraints
        The existing portfolio constraints with default constraints applied to them.
    """
    portfolio = []
    for site in exsiting_portfolio:
        shortfall_constraints = get_shortfall_constraints(site=site)
        exsiting_site_constraints = site.constraints
        site.constraints = merge_constraints([exsiting_site_constraints, shortfall_constraints])
        portfolio.append(site)

    return portfolio, existing_constraints
