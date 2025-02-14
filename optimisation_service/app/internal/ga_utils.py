import json
import logging
from copy import deepcopy
from enum import Enum
from typing import Any, Never

import numpy as np
import numpy.typing as npt
from pymoo.config import Config  # type: ignore
from pymoo.core.mutation import Mutation  # type: ignore
from pymoo.core.problem import ElementwiseProblem  # type: ignore
from pymoo.core.sampling import Sampling  # type: ignore
from pymoo.operators.repair.bounds_repair import repair_random_init  # type: ignore

from app.internal.epoch_utils import TaskData
from app.internal.heuristics.population_init import generate_building_initial_population
from app.internal.portfolio_simulator import PortfolioSimulator, PortfolioSolution
from app.internal.site_range import count_parameters_to_optimise
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.metrics import Metric, MetricDirection, MetricValues

logger = logging.getLogger("default")

Config.warnings["not_compiled"] = False


class ProblemInstance(ElementwiseProblem):
    """
    Create Pymoo ProblemInstance from OptimiseProblem instance.
    """

    def __init__(self, objectives: list[Metric], constraints: Constraints, portfolio: list[Site]) -> None:
        """
        Define Problem objectives, constraints, parameter search space.

        Parameters
        ----------
        Problem
            Problem to optimise
        """
        self.portfolio = portfolio
        self.site_names = [site.site_data.site_id for site in portfolio]
        self.objectives = objectives
        self.constraints = constraints

        n_obj = len(self.objectives)
        n_ieq_constr = sum(len(bounds) for bounds in self.constraints.values())

        input_dirs = {}
        self.default_parameters: dict[str, dict] = {}
        self.site_ranges: dict[str, dict] = {}
        self.asset_parameters: dict[str, list] = {}
        self.indexes = {}
        num_attr_values = []

        n_var = 0
        for site in portfolio:
            site_range_dict = site.site_range.model_dump(exclude_none=True)
            site_defaults = {}
            site_defaults["config"] = site_range_dict["config"]
            site_range_dict.pop("config")

            site_range: dict[str, dict[str, list[int | float | Enum]]] = {}
            asset_parameters = []

            if "renewables" in site_range_dict.keys():
                site_defaults["renewables"] = {}
                site_range["renewables"] = {}
                if not site_range_dict["renewables"]["COMPONENT_IS_MANDATORY"]:
                    site_defaults["renewables"]["COMPONENT_IS_MANDATORY"] = None
                    site_range["renewables"]["COMPONENT_IS_MANDATORY"] = [0, 1]
                    asset_parameters.append(("renewables", "COMPONENT_IS_MANDATORY"))
                    num_attr_values.append(2)
                site_defaults["renewables"]["yield_scalars"] = []
                for i, attr_values in enumerate(site_range_dict["renewables"]["yield_scalars"]):
                    site_range["renewables"][f"yield_scalars_{i}"] = attr_values
                    asset_parameters.append(("renewables", f"yield_scalars_{i}"))
                    num_attr_values.append(len(attr_values))
                site_range_dict.pop("renewables")

            for asset_name, asset in site_range_dict.items():
                site_range[asset_name] = {}
                site_defaults[asset_name] = {}
                if not asset["COMPONENT_IS_MANDATORY"]:
                    site_defaults[asset_name]["COMPONENT_IS_MANDATORY"] = None
                    site_range[asset_name]["COMPONENT_IS_MANDATORY"] = [0, 1]
                    asset_parameters.append((asset_name, "COMPONENT_IS_MANDATORY"))
                    num_attr_values.append(2)
                asset.pop("COMPONENT_IS_MANDATORY")
                for attr_name, attr_values in asset.items():
                    if len(attr_values) > 1:
                        site_defaults[asset_name][attr_name] = None
                        site_range[asset_name][attr_name] = attr_values
                        asset_parameters.append((asset_name, attr_name))
                        num_attr_values.append(len(attr_values))
                    else:
                        site_defaults[asset_name][attr_name] = attr_values[0]

            site_name = site.site_data.site_id
            self.asset_parameters[site_name] = asset_parameters
            self.default_parameters[site_name] = site_defaults
            self.site_ranges[site_name] = site_range
            # All variables are concatenated into a single list for the GA, this tracks each site's index range in that list
            n_parameters_to_optimise = count_parameters_to_optimise(site.site_range)
            print(n_parameters_to_optimise)
            self.indexes[site_name] = (n_var, n_var + n_parameters_to_optimise)
            n_var += n_parameters_to_optimise

            input_dirs[site_name] = site._input_dir

        self.sim = PortfolioSimulator(input_dirs=input_dirs)

        super().__init__(
            n_var=n_var,
            n_obj=n_obj,
            n_ieq_constr=n_ieq_constr,
            xl=[0] * n_var,
            xu=np.array(num_attr_values) - 1,
        )

    def split_solution(self, x: npt.NDArray) -> dict[str, npt.NDArray]:
        """
        Split a candidate portfolio solution into candidate building solutions.

        Parameters
        ----------
        x
            A candidate portfolio solution (array of parameter values).

        Returns
        -------
        Dictionary of buildings and candidate solutions (array of parameter values).
        """
        return {building_name: x[start:stop] for building_name, (start, stop) in self.indexes.items()}

    def convert_solution(self, x: npt.NDArray, site_name: str) -> TaskData:
        """
        Convert a candidate solution from an array of indeces to a site scenario.

        Parameters
        ----------
        x
            A pymoo compatible site solution (array of indeces).
        site_name
            The name of the building.

        Returns
        -------
        TaskData
            A site scenario.
        """
        site_range = self.site_ranges[site_name]
        site_scenario = deepcopy(self.default_parameters[site_name])
        assets_to_pop = []
        for (asset_name, attr_name), idx in zip(self.asset_parameters[site_name], x):
            if attr_name == "COMPONENT_IS_MANDATORY":
                if site_range[asset_name][attr_name][idx] == 0:
                    assets_to_pop.append(asset_name)
            elif asset_name == "renewables":
                site_scenario[asset_name]["yield_scalars"].append(site_range[asset_name][attr_name][idx])
            else:
                site_scenario[asset_name][attr_name] = site_range[asset_name][attr_name][idx]
        for asset in assets_to_pop:
            site_scenario.pop(asset)
        return TaskData.from_json(json.dumps(site_scenario))

    def simulate_portfolio(self, x: npt.NDArray) -> PortfolioSolution:
        """
        Simulate a candidate portfolio solution.

        Parameters
        ----------
        x
            A candidate portfolio solution (array of parameter values).

        Returns
        -------
        PortfolioSolution
            The evaluated candidate solution.
        """
        x_dict = self.split_solution(x)
        portfolio_pytd = {name: self.convert_solution(x, name) for name, x in x_dict.items()}
        return self.sim.simulate_portfolio(portfolio_pytd)

    def apply_directions(self, metric_values: MetricValues) -> MetricValues:
        """
        Applies metric optimisation direction to metric values.
        Multiplies metric values of metrics that need to be maximised by -1.

        Parameters
        ----------
        metric_values
            Dictionary of metric names and metric values.

        Returns
        -------
        metric_values
            Dictionary of metric names and metric values with directions applied.
        """
        for metric in metric_values.keys():
            metric_values[metric] *= MetricDirection[metric]
        return metric_values

    def calculate_infeasibility(self, metric_values: MetricValues) -> list[float]:
        """
        Calculate the infeasibility of metric values given the problem's portfolio constraints.

        Parameters
        ----------
        metric_values
            Dictionary of metric names and metric values.

        Returns
        -------
        excess
            List of values that indicate by how much the metric values exceed the constraints.
        """
        excess = []
        for metric, bounds in self.constraints.items():
            min_value = bounds.get("min", None)
            max_value = bounds.get("max", None)

            if min_value is not None:
                excess.append(min_value - metric_values[metric])
            if max_value is not None:
                excess.append(metric_values[metric] - max_value)
        return excess

    def _evaluate(self, x: npt.NDArray, out: dict[str, list[float]]) -> None:
        """
        Evaluate a candidate portfolio solution.

        Parameters
        ----------
        x
            A candidate portfolio solution (array of parameter values).
        out
            Dictionary provided by pymoo to store infeasibility scores (G) and objective values (F).

        Returns
        -------
        None
        """
        portfolio_solution = self.simulate_portfolio(x=x)
        out["G"] = self.calculate_infeasibility(portfolio_solution.metric_values)
        selected_results = {metric: portfolio_solution.metric_values[metric] for metric in self.objectives}
        directed_results = self.apply_directions(selected_results)
        out["F"] = list(directed_results.values())


class EstimateBasedSampling(Sampling):
    """
    Generate a population of solutions by estimating some parameter values from data.
    """

    def _do(self, problem: ProblemInstance, n_samples: int, **kwargs):
        site_pops = []
        for site in problem.portfolio:
            site_pops.append(  # noqa: PERF401
                generate_building_initial_population(
                    site_range=site.site_range,
                    input_dir=site._input_dir,
                    pop_size=n_samples,
                )
            )
        portfolio_pop = np.concatenate(site_pops, axis=1)
        return portfolio_pop


class SimpleIntMutation(Mutation):
    """
    Pymoo Mutation Operator which randomly mutates parameter values by a single step in the search space.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def _do(self, problem: ProblemInstance, X: npt.NDArray, **kwargs: Never) -> npt.NDArray:
        X.astype(float)
        prob_var = self.get_prob_var(problem, size=len(X))
        Xp = self.mut_simple_int(X, problem.xl, problem.xu, prob_var)

        return Xp

    @staticmethod
    def mut_simple_int(X: npt.NDArray, xl: npt.NDArray, xu: npt.NDArray, prob: npt.NDArray) -> npt.NDArray:
        """
        Randomly adds or substracts 1 from values in X based.

        Parameters
        ----------
        X
            2D array of values.
        xl
            1D array of lower bounds, one for each column of X.
        xu
            1D array of upper bounds, one for each column of X.
        prob
            1D array of probabilities, one for each row of X.

        Returns
        -------
        Xp
            2D array of values with changed values.
        """
        n, _ = X.shape
        assert len(prob) == n

        Xp = np.full(X.shape, np.inf)
        print(f"xp: {Xp}")
        mut = np.random.random(X.shape) < prob[:, None]
        mut_pos = (np.random.random(mut.shape) < 0.5) * mut
        print(f"mut_pos: {mut_pos}")
        mut_neg = mut * ~mut_pos
        Xp[:, :] = X
        print(f"mut_neg: {mut_neg}")
        Xp += mut_pos.astype(int) + mut_neg.astype(int) * -1

        Xp = repair_random_init(Xp, X, xl, xu)

        return Xp
