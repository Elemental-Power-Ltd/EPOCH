from epoch_simulator import TaskData

from app.internal.portfolio_simulator import PortfolioSimulator
from app.models.core import Site
from app.models.result import PortfolioSolution


def do_nothing_scenario(portfolio: list[Site]) -> PortfolioSolution:
    epoch_data_dict = {site.site_data.site_id: site._epoch_data for site in portfolio}
    ps = PortfolioSimulator(epoch_data_dict=epoch_data_dict)

    portfolio_scenarios = {site.site_data.site_id: TaskData() for site in portfolio}  # TODO: replace with baseline Scenario

    return ps.simulate_portfolio(portfolio_scenarios)
