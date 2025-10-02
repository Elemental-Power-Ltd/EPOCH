from app.models.constraints import Bounds, Constraints
from app.models.core import Site
from app.models.database import site_id_t
from app.models.metrics import Metric, MetricValues
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

                if min_value is not None and min_value > metric_values[metric]:
                    within_constraints = False
                    break
                if max_value is not None and max_value < metric_values[metric]:
                    within_constraints = False
                    break
            mask.append(within_constraints)

        return mask

    return [True] * len(solutions)


def are_metrics_in_constraints(constraints: Constraints, metric_values: MetricValues) -> bool:
    """
    Check whether a set of metrics values are within consrtaints or not.

    Parameters
    ----------
    constraints
        Dictionary of constraints to check against.
    metric_values
        Metric values to check.

    Returns
    -------
        Boolean mindicating if the metrics values are within consrtaints or not.
    """
    for metric, bounds in constraints.items():
        min_value = bounds.get("min", None)
        max_value = bounds.get("max", None)

        if min_value is not None and min_value > metric_values[metric]:
            return False
        if max_value is not None and max_value < metric_values[metric]:
            return False

    return True


def update_feasibility(
    site_constraints_dict: dict[site_id_t, Constraints], constraints: Constraints, portfolio_solution: PortfolioSolution
) -> PortfolioSolution:
    """
    Update the feasibility measures of a portfolio solution and it's site solutions.

    Parameters
    ----------
    portfolio
        Portfolio of sites.
    constraints
        Dictionary of constraints to check against.
    portfolio_solution
        Portfolio solution to update.

    Returns
    -------
    portfolio_solution
        Portfolio solution with updated feasibility measure.
    """
    for site_id, site_constraints in site_constraints_dict.items():
        site_metrics = portfolio_solution.scenario[site_id].metric_values
        site_is_feasible = are_metrics_in_constraints(constraints=site_constraints, metric_values=site_metrics)
        portfolio_solution.scenario[site_id].is_feasible = site_is_feasible

    all_sites_feasible = all(portfolio_solution.scenario[site_id].is_feasible for site_id in site_constraints_dict)

    portfolio_solution.is_feasible = all_sites_feasible and are_metrics_in_constraints(
        constraints=constraints, metric_values=portfolio_solution.metric_values
    )

    return portfolio_solution


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
                merged[metric] = Bounds()

            if "min" in bounds:
                merged[metric]["min"] = max(bounds["min"], merged[metric].get("min", -float("inf")))

            if "max" in bounds:
                merged[metric]["max"] = min(bounds["max"], merged[metric].get("max", float("inf")))

    return merged


def get_shortfall_constraints(site: Site, heat_tolerance: float = 0.01, dhw_tolerance: float | None = None) -> Constraints:
    """
    Get the maximum shortfall constraints for a site.

    Total heat shortfall is bounded above by heat_tolerance percent of the site's central heating load.
    The total DHW shortfall is separated from the central heating shortfall.
    Total electrical shortfall is bounded above by 1 kWh to allow for some floating point issues.
    We also constrain the total shortfall across both heat metrics as an edge case.

    Parameters
    ----------
    site
        A site to generate shortfall constraints for.
    heat_tolerance
        Percentage of the heat load to bound the central heating shortfall by.
    dhw_tolerance
        Percentage of the DHW load to bound the DHW shorfall by. If default, use the same as the heat tolerance.

    Returns
    -------
    constraints
        Constraints dict, containing constraints on total_electrical_shortfall and total_heat_shortfall.
    """
    if dhw_tolerance is None:
        dhw_tolerance = heat_tolerance

    hload = sum(site._epoch_data.building_hload)
    dhw_load = sum(site._epoch_data.dhw_demand)

    # Clip these to always forgive 1 kWh of shortfall in case of floating point errors
    # or other minor weirdness.
    ch_max = max(heat_tolerance * hload, 1.0)
    dhw_max = max(dhw_tolerance * dhw_load, 1.0)

    constraints = {
        Metric.total_electrical_shortfall: Bounds(max=1),
        Metric.total_ch_shortfall: Bounds(max=ch_max),
        Metric.total_dhw_shortfall: Bounds(max=dhw_max),
        # We keep the total heat shortfall just in case it's useful elsewhere!
        Metric.total_heat_shortfall: Bounds(max=ch_max + dhw_max),
        Metric.peak_hload_shortfall: Bounds(max=0),
    }
    return constraints


def apply_default_constraints(
    existing_portfolio: list[Site], existing_constraints: Constraints
) -> tuple[list[Site], Constraints]:
    """
    Apply default constraints to existing portfolio and site constraints.

    These are:
    - Electrical shortfall upper bounds on the sites.
    - Central heating shortfall upper bounds
    - Domestic hot water upper bounds
    We want to make sure that the solutions provided are viable energetically.

    Parameters
    ----------
    existing_portfolio
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
    for site in existing_portfolio:
        shortfall_constraints = get_shortfall_constraints(site=site)
        exsiting_site_constraints = site.constraints
        site.constraints = merge_constraints([exsiting_site_constraints, shortfall_constraints])
        portfolio.append(site)

    return portfolio, existing_constraints
