from app.models.constraints import Bounds
from app.models.core import Site
from app.models.metrics import Metric


def extend_config_capex_limits_to_constraints(portfolio: list[Site]) -> None:
    """Convert each sites exisintg config capex limits into optimisation site constraints.

    Parameters
    ----------
    site
        Site to apply convertion to.

    Returns
    -------
    None
    """
    for site in portfolio:
        site.constraints[Metric.capex] = Bounds(max=site.site_range.config.capex_limit)
