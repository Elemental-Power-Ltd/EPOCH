from app.models.constraints import Bounds, Constraints
from app.models.core import Site
from app.models.metrics import Metric


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
    hload = 0
    for site in portfolio:
        hload += sum(site._epoch_data.building_hload)
    heat_max = max(heat_tolerance * hload, 1)
    constraints = {Metric.total_electrical_shortfall: Bounds(max=1), Metric.total_heat_shortfall: Bounds(max=heat_max)}
    return constraints
