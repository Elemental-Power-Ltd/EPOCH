import functools
import logging
from os import PathLike

import numpy as np

from app.internal.epoch_utils import Simulator, TaskData, convert_sim_result
from app.models.objectives import Objectives, ObjectiveValues
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
            objective_values: objective values of the portfolio.
        """
        site_scenarios = {}
        objective_values_list = []
        for name in portfolio_scenarios.keys():
            site_scenario = portfolio_scenarios[name]
            sim = self.sims[name]
            result = simulate_scenario(sim, name, site_scenario)
            site_scenarios[name] = SiteSolution(scenario=site_scenario, objective_values=result)
            objective_values_list.append(result)
        objective_values = combine_objective_values(objective_values_list)
        return PortfolioSolution(scenario=site_scenarios, objective_values=objective_values)


@functools.lru_cache(maxsize=100000)
def simulate_scenario(sim: Simulator, site_name: str, site_scenario: TaskData) -> ObjectiveValues:
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
    ObjectiveValues
        Metrics of the simulation.
    """
    res = convert_sim_result(sim.simulate_scenario(site_scenario))
    if any(np.isnan(val) for val in res.values()):
        logger.error(f"Got NaN simulation result {res} for site {site_name} and config {site_scenario}")
    return res


def combine_objective_values(objective_values_list: list[ObjectiveValues]) -> ObjectiveValues:
    """
    Combine a list of objective values into a single list of objective values.
    Most objectives can be summed, but some require more complex functions.

    Parameters
    ----------
    objective_values_list
        List of objective value dictionaries.

    Returns
    -------
    objective_values
        Dictionary of objective values.
    """
    objective_values = ObjectiveValues()

    for objective in [
        Objectives.annualised_cost,
        Objectives.capex,
        Objectives.carbon_balance_scope_1,
        Objectives.carbon_balance_scope_2,
        Objectives.cost_balance,
    ]:
        objective_values[objective] = sum(obj_vals[objective] for obj_vals in objective_values_list)

    if objective_values[Objectives.capex] > 0:
        if objective_values[Objectives.cost_balance] > 0:
            objective_values[Objectives.payback_horizon] = (
                objective_values[Objectives.capex] / objective_values[Objectives.cost_balance]
            )
        else:
            objective_values[Objectives.payback_horizon] = float(np.finfo(np.float32).max)

        if objective_values[Objectives.carbon_balance_scope_1] > 0:
            objective_values[Objectives.carbon_cost] = (
                objective_values[Objectives.capex] / objective_values[Objectives.carbon_balance_scope_1]
            )
        else:
            objective_values[Objectives.carbon_cost] = float(np.finfo(np.float32).max)

    else:
        objective_values[Objectives.payback_horizon] = 0
        objective_values[Objectives.carbon_cost] = 0
    return objective_values
