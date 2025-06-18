from epoch_simulator import Building, GasHeater, Grid, TaskData

from app.internal.portfolio_simulator import PortfolioSimulator
from app.models.core import Site
from app.models.ga_utils import AnnotatedTaskData
from app.models.result import PortfolioSolution


def do_nothing_scenario(portfolio: list[Site]) -> PortfolioSolution:
    epoch_data_dict = {site.site_data.site_id: site._epoch_data for site in portfolio}
    ps = PortfolioSimulator(epoch_data_dict=epoch_data_dict)

    do_nothing_td = TaskData()
    do_nothing_td.building = Building()
    do_nothing_td.grid = Grid()
    do_nothing_td.gas_heater = GasHeater()
    do_nothing_td.gas_heater.maximum_output = 999999
    annotated_nothing_td = AnnotatedTaskData.model_validate_json(do_nothing_td.to_json())

    # TODO: replace with baseline Scenario
    portfolio_scenarios = {site.site_data.site_id: annotated_nothing_td for site in portfolio}

    return ps.simulate_portfolio(portfolio_scenarios)
