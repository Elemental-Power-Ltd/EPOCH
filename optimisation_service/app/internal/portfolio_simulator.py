import functools
import logging
from os import PathLike

import numpy as np

from app.internal.epoch_utils import Simulator, TaskData, convert_sim_result
from app.internal.metrics import calculate_carbon_cost, calculate_payback_horizon
from app.models.metrics import Metric, MetricValues
from app.models.result import PortfolioSolution, SiteSolution

logger = logging.getLogger("default")


class PortfolioSimulator:
    """
    Provides portfolio simulation by initialising multiple EPOCH simulator's.
    """

    def __init__(self, input_dirs: dict[str, PathLike]) -> None:
        """
        Initialise the various EPOCH simulators.

        Parameters
        ----------
        input_dirs
            Dictionary of building names and directories containing input data.

        Returns
        -------
        None
        """
        self.sims = {name: Simulator(inputDir=str(input_dir)) for name, input_dir in input_dirs.items()}

    def simulate_portfolio(self, portfolio_scenarios: dict[str, TaskData]) -> PortfolioSolution:
        """
        Simulate a portfolio.

        Parameters
        ----------
        portfolio_tasks
            Dictionary of building names and task data.

        Returns
        -------
        PortfolioSolution
            solution: dictionary of buildings names and evaluated candidate building solutions.
            metric_values: metric values of the portfolio.
        """
        site_scenarios = {}
        metric_values_list = []
        for name in portfolio_scenarios.keys():
            site_scenario = portfolio_scenarios[name]
            sim = self.sims[name]
            result = simulate_scenario(sim, name, site_scenario)
            site_scenarios[name] = SiteSolution(scenario=site_scenario, metric_values=result)
            metric_values_list.append(result)
        metric_values = combine_metric_values(metric_values_list)
        return PortfolioSolution(scenario=site_scenarios, metric_values=metric_values)


@functools.lru_cache(maxsize=100000)
def simulate_scenario(sim: Simulator, site_name: str, site_scenario: TaskData) -> MetricValues:
    """
    Simulate scenario wrapper function to leverage caching of simulation results.

    Parameters
    ----------
    sim
        Epoch simulator to simulate with.
    site_name
        Name of site to simulate.
    site_scenario
        Scenario to Simulate.

    Returns
    -------
    MetricValues
        Metrics of the simulation.
    """
    res = convert_sim_result(sim.simulate_scenario(site_scenario))
    if any(np.isnan(val) for val in res.values()):
        logger.error(f"Got NaN simulation result {res} for site {site_name} and config {site_scenario}")
    return res


def combine_metric_values(metric_values_list: list[MetricValues]) -> MetricValues:
    """
    Combine a list of metric values into a single list of metric values.
    Most metrics can be summed, but some require more complex functions.

    Parameters
    ----------
    metric_values_list
        List of metric value dictionaries.

    Returns
    -------
    metric_values
        Dictionary of metric values.
    """
    metric_values = MetricValues()

    for metric in [
        Metric.annualised_cost,
        Metric.capex,
        Metric.carbon_balance_scope_1,
        Metric.carbon_balance_scope_2,
        Metric.cost_balance,
    ]:
        metric_values[metric] = sum(obj_vals[metric] for obj_vals in metric_values_list)

    metric_values[Metric.payback_horizon] = calculate_payback_horizon(
        capex=metric_values[Metric.capex], cost_balance=metric_values[Metric.cost_balance]
    )
    metric_values[Metric.carbon_cost] = calculate_carbon_cost(
        capex=metric_values[Metric.capex], carbon_balance_scope_1=metric_values[Metric.carbon_balance_scope_1]
    )
    return metric_values
