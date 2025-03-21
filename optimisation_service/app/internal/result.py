from epoch_simulator import TaskData

from app.models.metrics import _METRICS
from app.models.result import PortfolioSolution, SiteSolution

_DO_NOTHING_SITE = SiteSolution(scenario=TaskData(), metric_values={metric: 0 for metric in _METRICS})


def do_nothing_scenario(site_ids: list[str]) -> PortfolioSolution:
    return PortfolioSolution(
        scenario={site_id: _DO_NOTHING_SITE for site_id in site_ids},
        metric_values={metric: 0 for metric in _METRICS},
    )
