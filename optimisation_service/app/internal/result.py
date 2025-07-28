from app.internal.portfolio_simulator import PortfolioSimulator
from app.models.core import Site
from app.models.ga_utils import AnnotatedTaskData
from app.models.result import PortfolioSolution


def get_baseline_portfolio_scenario(portfolio: list[Site]) -> dict[str, AnnotatedTaskData]:
    """
    Fetch the baseline scenario of a portfolio.

    Parameters
    ----------
    portfolio
        Portfolio to fetch baseline scenario from.

    Returns
    -------
    portfolio_scenario
        Dictionnary of site scenarios indexed by site ids.
    """
    portfolio_scenario: dict[str, AnnotatedTaskData] = {}
    for site in portfolio:
        site_id = site.site_data.site_id
        baseline = site._epoch_data.baseline
        portfolio_scenario[site_id] = AnnotatedTaskData.model_validate(baseline.model_dump(exclude_none=True))

    return portfolio_scenario


def get_baseline_portfolio_solution(portfolio: list[Site]) -> PortfolioSolution:
    """
    Fetch the baseline scenario of a portfolio and simulate it.

    Parameters
    ----------
    portfolio
        Portfolio to fetch baseline scenario from.

    Retunrs
    -------
    PortfolioSolution
        Simulated baseline solution.
    """
    epoch_data_dict = {site.site_data.site_id: site._epoch_data for site in portfolio}
    epoch_config_dict = {site.site_data.site_id: site.site_range.config for site in portfolio}
    ps = PortfolioSimulator(epoch_data_dict=epoch_data_dict, epoch_config_dict=epoch_config_dict)

    portfolio_scenarios = get_baseline_portfolio_scenario(portfolio=portfolio)

    return ps.simulate_portfolio(portfolio_scenarios)
