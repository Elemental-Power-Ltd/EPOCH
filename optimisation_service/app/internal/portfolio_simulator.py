import functools
import logging
from os import PathLike

import numpy as np

from app.internal.epoch_utils import PyTaskData, Simulator
from app.models.objectives import _OBJECTIVES, Objectives, ObjectiveValues
from app.models.result import BuildingSolution, PortfolioSolution, convert_sim_result

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

    @functools.lru_cache(maxsize=100000, typed=False)  # noqa: B019
    def simulate_scenario(self, site_name: str, **kwargs) -> ObjectiveValues:
        """
        Simulate scenario wrapper function to leverage caching of simulation results.

        Parameters
        ----------
        site_name
            Name of site to simulate.
        kwargs
            Scenario to Simulate.

        Returns
        -------
        ObjectiveValues
            Metrics of the simulation.
        """
        sim = self.sims[site_name]
        pytd = PyTaskData(**kwargs)
        res = convert_sim_result(sim.simulate_scenario(pytd))
        if any(np.isnan(val) for val in res.values()):
            logger.error(f"Got NaN simulation result {res} for site {site_name} and config {pytd}")
        return res

    def simulate_portfolio(self, portfolio_tasks: dict[str, PyTaskData]) -> PortfolioSolution:
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
        solution = {}
        objective_values_list = []
        for name in portfolio_tasks.keys():
            task = portfolio_tasks[name]
            result = self.simulate_scenario(name, **dict(task.items()))
            solution[name] = BuildingSolution(solution=task, objective_values=result)
            objective_values_list.append(result)
        objective_values = combine_objective_values(objective_values_list)
        return PortfolioSolution(solution=solution, objective_values=objective_values)  # TODO:Solution doesn't require taskdata


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
    combined
        Dictionary of objective values.
    """
    combined = {objective: float(sum(obj_vals[objective] for obj_vals in objective_values_list)) for objective in _OBJECTIVES}
    if combined[Objectives.cost_balance] > 0:
        combined[Objectives.payback_horizon] = combined[Objectives.capex] / combined[Objectives.cost_balance]
    else:
        combined[Objectives.payback_horizon] = np.finfo(np.float32).max
    if combined[Objectives.carbon_balance_scope_1] > 0:
        combined[Objectives.carbon_cost] = combined[Objectives.capex] / (
            combined[Objectives.carbon_balance_scope_1] * 15 / 1000
        )
    else:
        combined[Objectives.carbon_cost] = np.finfo(np.float32).max
    return combined
