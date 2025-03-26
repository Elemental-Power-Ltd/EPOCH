from epoch_simulator import TaskData

from app.models.metrics import _METRICS
from app.models.result import PortfolioSolution, SiteSolution

_DO_NOTHING_SITE = SiteSolution(scenario=TaskData(), metric_values=dict.fromkeys(_METRICS, 0))


def do_nothing_scenario(site_ids: list[str]) -> PortfolioSolution:
    return PortfolioSolution(
        scenario=dict.fromkeys(site_ids, _DO_NOTHING_SITE),
        metric_values=dict.fromkeys(_METRICS, 0),
    )
