import copy
import functools
import logging
from typing import Any

import numpy as np

from app.internal.epoch.converters import simulation_result_to_metric_dict
from app.models.epoch_types.config import Config as PydanticConfig
from app.models.ga_utils import AnnotatedTaskData
from app.models.result import PortfolioSolution, SiteSolution
from app.models.site_data import EpochSiteData
from epoch_simulator import SimulationResult, Simulator, TaskData, aggregate_site_results

logger = logging.getLogger("default")


class PortfolioSimulator:
    """Provides portfolio simulation by initialising multiple EPOCH simulators."""

    def __init__(self, epoch_data_dict: dict[str, EpochSiteData], epoch_config_dict: dict[str, PydanticConfig]) -> None:
        """
        Initialise the various EPOCH simulators.

        Parameters
        ----------
        epoch_data_dict
            Dictionary of Epoch ingestable datasets. One for each site in the portfolio.
        epoch_config_dict
            Dictionary of Epoch configurations. One for each site in the portfolio.

        Returns
        -------
        None
        """
        # store these even though they can be enormous so that
        # we can re-create the simulators if needed.
        self.epoch_data_dict = epoch_data_dict
        self.epoch_config_dict = epoch_config_dict
        self.sims = {
            name: Simulator.from_json(epoch_data.model_dump_json(), epoch_config_dict[name].model_dump_json())
            for name, epoch_data in epoch_data_dict.items()
        }

    def __copy__(self) -> "PortfolioSimulator":
        """
        Shallow copy this Portfolio Simulator, sharing simulators.

        Simulator objects aren't pickleable (the default way of copying), so for this
        shallowcopy we will simply add references to the old simulators.

        Parameters
        ----------
        self
            The object we want to copy

        Returns
        -------
        Self
            Brand new portfolio simulator exactly the same as this one with shared dicts and simulators.
        """
        other = PortfolioSimulator(epoch_data_dict=self.epoch_data_dict, epoch_config_dict=self.epoch_config_dict)
        other.sims = self.sims
        return other

    def __deepcopy__(self, memo: dict[int, Any] | None) -> "PortfolioSimulator":
        """
        Deepcopy this Portfolio Simulator, making sure to re-create any simulators.

        Simulator objects aren't pickleable (the default way of copying), so for this
        deepcopy we will simply re-construct a new PortfolioSimulator with new Simulator
        objects within it, making sure that we copy the dictionaries.

        Parameters
        ----------
        self
            The object we want to copy
        memo
            Mystery black box parameter from the copy.deepcopy library function
            (it's a dict of id: value mappings to break loops)

        Returns
        -------
        Self
            Brand new portfolio simulator exactly the same as this one.
        """
        return PortfolioSimulator(
            epoch_data_dict=copy.deepcopy(self.epoch_data_dict), epoch_config_dict=copy.deepcopy(self.epoch_config_dict)
        )

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
        results = []
        for name in portfolio_scenarios:
            annotated_task = portfolio_scenarios[name]
            site_scenario = TaskData.from_json(annotated_task.model_dump_json(exclude_none=True))
            sim = self.sims[name]
            sim_result = simulate_scenario(sim, name, site_scenario)
            metrics = simulation_result_to_metric_dict(sim_result)
            if any(np.isnan(val) for val in metrics.values()):
                logger.error(f"Got NaN simulation result {metrics} for site {name} and config {site_scenario}")

            site_scenarios[name] = SiteSolution(scenario=annotated_task, metric_values=metrics, simulation_result=sim_result)
            results.append(sim_result)

        portfolio_result = aggregate_site_results(results)
        portfolio_metrics = simulation_result_to_metric_dict(portfolio_result)
        return PortfolioSolution(scenario=site_scenarios, metric_values=portfolio_metrics, simulation_result=portfolio_result)


@functools.lru_cache(maxsize=100000)
def simulate_scenario(sim: Simulator, site_name: str, site_scenario: TaskData) -> SimulationResult:
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
    SimulationResult
        The python bindings for the C++ SimulationResult.
    """
    return sim.simulate_scenario(site_scenario)
