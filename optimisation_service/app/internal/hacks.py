from app.models.constraints import Bounds
from app.models.core import Site
from app.models.metrics import Metric


def extend_config_capex_limits_to_constraints(portfolio: list[Site]) -> None:
    """Extend each sites existing config capex limits into optimisation site constraints.

    Parameters
    ----------
    portfolio
        List of sites to extend their config's capex limits to constraints.

    Returns
    -------
    None
    """
    for site in portfolio:
        site.constraints[Metric.capex] = Bounds(max=site.config.capex_limit)
