import functools
import logging

import numpy as np
from epoch_simulator import Simulator, TaskData

from app.internal.epoch_utils import convert_sim_result
from app.internal.metrics import calculate_carbon_cost, calculate_payback_horizon
from app.models.ga_utils import AnnotatedTaskData
from app.models.metrics import _SUMMABLE_METRICS, Metric, MetricValues
from app.models.result import PortfolioSolution, SiteSolution
from app.models.site_data import EpochSiteData

logger = logging.getLogger("default")


class PortfolioSimulator:
    """
    Provides portfolio simulation by initialising multiple EPOCH simulator's.
    """

    def __init__(self, epoch_data_dict: dict[str, EpochSiteData]) -> None:
        """
        Initialise the various EPOCH simulators.

        Parameters
        ----------
        epoch_data_dict
            Dictionary of Epoch ingestable datasets. One for each site in the portfolio.

        Returns
        -------
        None
        """
        self.sims = {name: Simulator.from_json(epoch_data.model_dump_json()) for name, epoch_data in epoch_data_dict.items()}

    def simulate_portfolio(self, portfolio_scenarios: dict[str, AnnotatedTaskData]) -> PortfolioSolution:
        """
        Simulate a portfolio.

        Parameters
        ----------
        portfolio_scenarios
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
            annotated_task = portfolio_scenarios[name]
            site_scenario = TaskData.from_json(annotated_task.model_dump_json(exclude_none=True))
            sim = self.sims[name]
            result = simulate_scenario(sim, name, site_scenario)
            site_scenarios[name] = SiteSolution(scenario=annotated_task, metric_values=result)
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

    # start by finding the metrics that all entries have in common
    # we can only combine a metric if it is present in every entry
    common_metrics = set.intersection(*(set(mv.keys()) for mv in metric_values_list))

    combined_metric_values = MetricValues()

    for metric in _SUMMABLE_METRICS:
        if metric in common_metrics:
            combined_metric_values[metric] = sum(obj_vals[metric] for obj_vals in metric_values_list)

    if Metric.capex in combined_metric_values and Metric.cost_balance in combined_metric_values:
        combined_metric_values[Metric.payback_horizon] = calculate_payback_horizon(
            capex=combined_metric_values[Metric.capex], cost_balance=combined_metric_values[Metric.cost_balance]
        )

    if Metric.capex in combined_metric_values and Metric.carbon_balance_scope_1 in combined_metric_values:
        combined_metric_values[Metric.carbon_cost] = calculate_carbon_cost(
            capex=combined_metric_values[Metric.capex],
            carbon_balance_scope_1=combined_metric_values[Metric.carbon_balance_scope_1],
        )

    if Metric.carbon_balance_scope_1 in combined_metric_values and Metric.carbon_balance_scope_2 in combined_metric_values:
        combined_metric_values[Metric.carbon_balance_total] = (
            combined_metric_values[Metric.carbon_balance_scope_1] + combined_metric_values[Metric.carbon_balance_scope_2]
        )

    return combined_metric_values
