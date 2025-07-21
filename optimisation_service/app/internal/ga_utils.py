import logging
from copy import deepcopy
from typing import Any, Never, cast

import numpy as np
import numpy.typing as npt
from pymoo.config import Config  # type: ignore
from pymoo.core.mutation import Mutation  # type: ignore
from pymoo.core.problem import ElementwiseProblem  # type: ignore
from pymoo.core.repair import Repair  # type: ignore
from pymoo.core.sampling import Sampling  # type: ignore
from pymoo.operators.repair.bounds_repair import repair_random_init  # type: ignore

from app.internal.heuristics.population_init import generate_site_scenarios_from_heuristics
from app.internal.portfolio_simulator import PortfolioSimulator, PortfolioSolution
from app.internal.site_range import FIXED_PARAMETERS, REPEAT_COMPONENTS, count_parameters_to_optimise
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.epoch_types import TaskDataPydantic
from app.models.ga_utils import AnnotatedTaskData, AssetParameter, ParsedAsset, asset_t, value_t
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
        for site in portfolio:
            n_ieq_constr += sum(len(bounds) for bounds in site.constraints.values())

        epoch_data_dict = {}
        epoch_config_dict = {}

        self.default_parameters: dict[str, dict] = {}
        self.site_ranges: dict[str, dict] = {}
        self.asset_parameters: dict[str, list[AssetParameter]] = {}
        self.indexes = {}
        num_attr_values = []

        n_var = 0
        for site in portfolio:
            site_range_dict = site.site_range.model_dump(exclude_none=True)
            site_defaults = {}
            site_defaults["config"] = site_range_dict["config"]
            site_range_dict.pop("config")

            # we use a generic typed dict here as mypy can't tell whether a component type is asset_t or list[asset_t]
            # without heavy use of typing.cast
            site_range: dict[str, Any] = {}

            asset_parameters: list[AssetParameter] = []

            for asset_name, asset in site_range_dict.items():
                if asset_name in REPEAT_COMPONENTS:
                    site_range[asset_name] = []
                    site_defaults[asset_name] = []

                    for i, sub_asset in enumerate(asset):
                        parsed_asset = self.split_asset_into_default_and_range(sub_asset)

                        site_defaults[asset_name].append(parsed_asset.fixed)
                        site_range[asset_name].append(parsed_asset.ranged)
                        num_attr_values.extend(parsed_asset.num_values)

                        for attr_name in parsed_asset.ranged.keys():
                            asset_parameters.append(  # noqa: PERF401
                                AssetParameter(asset_name=asset_name, attr_name=attr_name, repeat_index=i)
                            )
                else:
                    # singleton component
                    parsed_asset = self.split_asset_into_default_and_range(asset)

                    site_defaults[asset_name] = parsed_asset.fixed
                    site_range[asset_name] = parsed_asset.ranged
                    num_attr_values.extend(parsed_asset.num_values)

                    # add the asset,attribute pairings to asset_parameters
                    for attr_name in parsed_asset.ranged.keys():
                        asset_parameters.append(AssetParameter(asset_name=asset_name, attr_name=attr_name))  # noqa: PERF401

            site_name = site.site_data.site_id
            self.asset_parameters[site_name] = asset_parameters
            self.default_parameters[site_name] = site_defaults
            self.site_ranges[site_name] = site_range
            # All variables are concatenated into a single list for the GA, this tracks each site's index range in that list
            n_parameters_to_optimise = count_parameters_to_optimise(site.site_range)
            self.indexes[site_name] = (n_var, n_var + n_parameters_to_optimise)
            n_var += n_parameters_to_optimise

            epoch_data_dict[site_name] = site._epoch_data
            epoch_config_dict[site_name] = site.site_range.config

        self.sim = PortfolioSimulator(epoch_data_dict, epoch_config_dict)

        super().__init__(
            n_var=n_var,
            n_obj=n_obj,
            n_ieq_constr=n_ieq_constr,
            xl=[0] * n_var,
            xu=np.array(num_attr_values) - 1,
        )

    def split_asset_into_default_and_range(self, asset: asset_t) -> ParsedAsset:
        """
        Parse an asset to separate the attributes that are fixed from the attributes that vary.

        Parameters
        ----------
        asset
            an individual component

        Returns
        -------
        A ParsedAsset, separated into fixed and ranged parts

        """
        parsed_asset = ParsedAsset()

        if not asset["COMPONENT_IS_MANDATORY"]:
            parsed_asset.fixed["COMPONENT_IS_MANDATORY"] = None
            parsed_asset.ranged["COMPONENT_IS_MANDATORY"] = [0, 1]
            parsed_asset.num_values.append(2)
        asset.pop("COMPONENT_IS_MANDATORY")
        for attr_name, attr_value in asset.items():
            # fixed parameters go straight into the defaults
            if attr_name in FIXED_PARAMETERS:
                # cast; hint to mypy that this is not a list
                attr_value = cast(value_t, attr_value)
                parsed_asset.fixed[attr_name] = attr_value
            else:
                # cast; hint to mypy that this is a list
                attr_value = cast(list[value_t], attr_value)
                # lists with a single value also go straight into defaults
                if len(attr_value) == 1:
                    parsed_asset.fixed[attr_name] = attr_value[0]
                # if we have multiple values, put it into the asset_range
                else:
                    parsed_asset.fixed[attr_name] = None
                    parsed_asset.ranged[attr_name] = attr_value
                    parsed_asset.num_values.append(len(attr_value))

        return parsed_asset

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

    def convert_chromosome_to_site_scenario(self, x: npt.NDArray, site_name: str) -> AnnotatedTaskData:
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
            A site scenario, annotated with tracking info for repeat components
        """
        site_range = self.site_ranges[site_name]
        site_scenario = deepcopy(self.default_parameters[site_name])

        singleton_assets_to_pop: list[str] = []
        repeat_assets_to_pop: list[tuple[str, int]] = []

        for param, idx in zip(self.asset_parameters[site_name], x):
            if param.attr_name == "COMPONENT_IS_MANDATORY":
                if param.repeat_index is None:
                    if site_range[param.asset_name][param.attr_name][idx] == 0:
                        # this singleton asset should not be in this solution
                        singleton_assets_to_pop.append(param.asset_name)
                else:
                    if site_range[param.asset_name][param.repeat_index][param.attr_name][idx] == 0:
                        # this repeat asset should not be in this solution
                        repeat_assets_to_pop.append((param.asset_name, param.repeat_index))

            elif param.repeat_index is None:
                # this is an attribute for a singleton component
                site_scenario[param.asset_name][param.attr_name] = site_range[param.asset_name][param.attr_name][idx]
            else:
                # this is an attribute for a repeat component
                repeat_attr = site_range[param.asset_name][param.repeat_index][param.attr_name][idx]
                site_scenario[param.asset_name][param.repeat_index][param.attr_name] = repeat_attr

        # remove any singleton assets that are turned off in this solution
        for asset_name in singleton_assets_to_pop:
            site_scenario.pop(asset_name)

        # annotate the repeat components, so that we can re-associate them correctly after removing components below
        for asset_name in REPEAT_COMPONENTS:
            if asset_name in site_scenario:
                for i in range(len(site_scenario[asset_name])):
                    site_scenario[asset_name][i]["index_tracker"] = i

        # remove any repeat assets that are turned off in this solution
        # (we start by sorting the list by descending index to ensure we never shift the order)
        repeat_assets_to_pop.sort(key=lambda name_index: name_index[1], reverse=True)
        for asset_name, repeat_index in repeat_assets_to_pop:
            site_scenario[asset_name].pop(repeat_index)

        return AnnotatedTaskData.model_validate(site_scenario)

    def convert_site_scenario_to_chromosome(self, site_scenario: AnnotatedTaskData, site_name: str) -> npt.NDArray:
        """
        Convert a candidate solution from a site scenario to an array of indeces.

        Parameters
        ----------
        TaskData
            A site scenario.
        site_name
            The name of the building.

        Returns
        -------
        x
            A pymoo compatible site solution (array of indeces).
        """
        td_dict = site_scenario.model_dump(exclude_none=True)
        site_range = self.site_ranges[site_name]
        x = []
        for param in self.asset_parameters[site_name]:
            if param.repeat_index is None:
                # singleton component
                if param.asset_name not in td_dict:
                    x.append(0)
                elif param.attr_name == "COMPONENT_IS_MANDATORY":
                    x.append(1)
                else:
                    value = td_dict[param.asset_name][param.attr_name]
                    x.append(site_range[param.asset_name][param.attr_name].index(value))
            else:
                # repeat component
                if param.asset_name not in td_dict:
                    # we have none of this repeat component
                    x.append(0)
                elif not any(rc["index_tracker"] == param.repeat_index for rc in td_dict[param.asset_name]):
                    # this instance of the repeat component is not present
                    x.append(0)
                elif param.attr_name == "COMPONENT_IS_MANDATORY":
                    x.append(1)
                else:
                    # we know this instance is present, find it and read from the appropriate index in SiteRange
                    repeat_instance = next(rc for rc in td_dict[param.asset_name] if rc["index_tracker"] == param.repeat_index)
                    value = repeat_instance[param.attr_name]
                    x.append(site_range[param.asset_name][param.repeat_index][param.attr_name].index(value))

        return np.array(x)

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
        portfolio_pytd = {name: self.convert_chromosome_to_site_scenario(x, name) for name, x in x_dict.items()}
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

    def calculate_infeasibility(self, portfolio_solution: PortfolioSolution) -> list[float]:
        """
        Calculate the infeasibility of a portfolio solution given the problem's portfolio constraints.

        Parameters
        ----------
        portfolio_solution
            The portfolio solution to evaluate.

        Returns
        -------
        excess
            List of values that indicate by how much the metric values exceed the constraints.
        """
        # evaluate portfolio level constraints first
        excess = evaluate_excess(portfolio_solution.metric_values, constraints=self.constraints)

        # evaluate site constraints
        for site in self.portfolio:
            metric_values = portfolio_solution.scenario[site.site_data.site_id].metric_values
            excess.extend(evaluate_excess(metric_values=metric_values, constraints=site.constraints))

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
        out["G"] = self.calculate_infeasibility(portfolio_solution)
        selected_results = {metric: portfolio_solution.metric_values[metric] for metric in self.objectives}
        directed_results = self.apply_directions(selected_results)
        out["F"] = list(directed_results.values())


def evaluate_excess(metric_values: MetricValues, constraints: Constraints) -> list[float]:
    """
    Measures by how much the metric values exceed the constraints.
    Returns a list of floats, one for each constraint.

    Parameters
    ----------
    metric_values
        The metric values to evaluate.
    constraints
        The constraints to evaluate against.

    Returns
    -------
    excess
        List of floats indicating how close we are to the constraints.
        A positive float indicates that the metric has exceeded the minimum or maximum bound.
        A negative float indicates that the metric is within the minimum or maximum bound.
    """
    excess = []
    for metric, bounds in constraints.items():
        if "min" in bounds:
            excess.append(bounds["min"] - metric_values[metric])
        if "max" in bounds:
            excess.append(metric_values[metric] - bounds["max"])

    return excess


class EstimateBasedSampling(Sampling):
    """
    Generate a population of solutions by estimating some parameter values from data.
    """

    def _do(self, problem: ProblemInstance, n_samples: int, **kwargs):
        site_pops = []
        for site in problem.portfolio:
            site_name = site.site_data.site_id
            site_scenarios = generate_site_scenarios_from_heuristics(
                site_range=site.site_range,
                epoch_data=site._epoch_data,
                pop_size=n_samples,
            )
            site_pops.append([
                problem.convert_site_scenario_to_chromosome(site_scenario, site_name) for site_scenario in site_scenarios
            ])
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
        mut = np.random.random(X.shape) < prob[:, None]
        mut_pos = (np.random.random(mut.shape) < 0.5) * mut
        mut_neg = mut * ~mut_pos
        Xp[:, :] = X
        Xp += mut_pos.astype(int) + mut_neg.astype(int) * -1

        Xp = repair_random_init(Xp, X, xl, xu)

        return Xp


class RoundingAndDegenerateRepair(Repair):
    """
    Function to repair pymoo chromosomes.
    Floats are rounded to the nearest integer.
    Components that have been disabled in the solution have all their other asset values set to the smallest value.
    This is to reduce the number of degenerate solutions.
    """

    def __init__(self, **kwargs) -> None:
        """

        Returns
        -------
        object
        """
        super().__init__(**kwargs)

    def _do(self, problem: ProblemInstance, X, **kwargs):
        """
        Forces all degenrate solutions cause by optional components to have the same default values.

        For example:
        Imagine we would like to optimise a site with a single optional heat pump component with three sizes: [10, 20, 30].
        The pymoo representation of the porblem would be [x, y], where x is a bool if the heat pump is installed or not,
        and y is an index to the size list.
        Then there are 6 possible chromosomes: [0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2].
        However, [0, 0], [0, 1] and [0, 2] all represent the same solution, i.e. no heat pump is intsalled.
        Hence, [0, 1] and [0, 2] are modified to [0, 0], [0, 0] such that all three solutions have the same chromosome.
        """
        X = np.around(X).astype(int)

        toggle_columns_dict = {}
        curr_asset_toggled: tuple[str, int | None] = "", None
        curr_toggle_idx = None
        i = 0
        for site_name in problem.site_names:
            for param in problem.asset_parameters[site_name]:
                if param.attr_name == "COMPONENT_IS_MANDATORY":
                    toggle_columns = []
                    curr_asset_toggled = param.asset_name, param.repeat_index
                    curr_toggle_idx = i
                elif (param.asset_name, param.repeat_index) == curr_asset_toggled:
                    toggle_columns.append(i)
                    toggle_columns_dict[curr_toggle_idx] = toggle_columns
                i += 1

        for key_col, affected_cols in toggle_columns_dict.items():
            mask = X[:, key_col] == 0  # Find rows where the key column is zero
            X[np.ix_(mask, affected_cols)] = 0

        return X


def strip_annotations(annotated_task: AnnotatedTaskData) -> TaskDataPydantic:
    """
    Remove annotations from a TaskData
    Parameters
    ----------
    annotated_task
        a TaskData that may contain annotations on repeat components

    Returns
    -------
    A pydantic TaskData with no annotations.

    """
    return TaskDataPydantic.model_validate(annotated_task)
