from epoch_simulator import Building, GasHeater, Grid, TaskData

from app.internal.portfolio_simulator import PortfolioSimulator
from app.models.core import Site
from app.models.result import PortfolioSolution


def do_nothing_scenario(portfolio: list[Site]) -> PortfolioSolution:
    epoch_data_dict = {site.site_data.site_id: site._epoch_data for site in portfolio}
    ps = PortfolioSimulator(epoch_data_dict=epoch_data_dict)

    do_nothing_td = TaskData()
    do_nothing_td.building = Building()
    do_nothing_td.grid = Grid()
    do_nothing_td.gas_heater = GasHeater()
    do_nothing_td.gas_heater.maximum_output = 999999

    portfolio_scenarios = {site.site_data.site_id: do_nothing_td for site in portfolio}  # TODO: replace with baseline Scenario

    return ps.simulate_portfolio(portfolio_scenarios)
