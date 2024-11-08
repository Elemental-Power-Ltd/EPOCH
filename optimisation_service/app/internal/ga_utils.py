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
from pymoo.operators.sampling.rnd import IntegerRandomSampling  # type: ignore

from app.internal.epoch_utils import PyTaskData
from app.internal.heuristics.population_init import generate_building_initial_population
from app.internal.portfolio_simulator import PortfolioSimulator, PortfolioSolution
from app.internal.problem import PortfolioProblem
from app.models.objectives import ObjectivesDirection, ObjectiveValues

logger = logging.getLogger("default")

Config.warnings["not_compiled"] = False


class ProblemInstance(ElementwiseProblem):
    """
    Create Pymoo ProblemInstance from OptimiseProblem instance.
    """

    def __init__(self, portfolio: PortfolioProblem) -> None:
        """
        Define Problem objectives, constraints, parameter search space.

        Parameters
        ----------
        Problem
            Problem to optimise
        """
        self.buildings = portfolio.buildings
        self.building_names = portfolio.buildings.keys()
        self.objectives = portfolio.objectives
        self.constraints = portfolio.constraints
        n_obj = len(self.objectives)
        n_ieq_constr = sum(len(bounds) for bounds in self.constraints.values())

        input_dirs = {}
        self.constant_params = {}
        self.variable_params = {}
        self.indexes = {}
        lower_bounds = []
        upper_bounds = []
        steps = []

        n_var = 0
        for building_name, building in portfolio.buildings.items():
            variable_params_building = []

            n_var_building = 0
            for key, value in building.variable_param().items():
                variable_params_building.append(key)
                lower_bounds.append(value["min"])
                upper_bounds.append(value["max"])
                steps.append(value["step"])
                n_var_building += 1

            self.indexes[building_name] = (n_var, n_var + n_var_building)
            self.variable_params[building_name] = deepcopy(variable_params_building)
            self.constant_params[building_name] = deepcopy(building.constant_param())
            input_dirs[building_name] = building.input_dir
            n_var += n_var_building

        self.lower_bounds = np.array(lower_bounds)
        self.upper_bounds = np.array(upper_bounds)
        self.steps = np.array(steps)

        self.sim = PortfolioSimulator(input_dirs=input_dirs)

        super().__init__(
            n_var=n_var,
            n_obj=n_obj,
            n_ieq_constr=n_ieq_constr,
            xl=[0] * n_var,
            xu=(self.upper_bounds - self.lower_bounds) / self.steps,
        )

    def scale_solution(self, x: npt.NDArray) -> npt.NDArray:
        """
        Scale from pymoo parameter values to real values.

        Parameters
        ----------
        x
            One or multiple candidate portfolio solution(s) (array of parameter values).

        Returns
        -------
        Scaled candidate portfolio solution(s) (array of parameter values).
        """
        return x * self.steps + self.lower_bounds

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

    def convert_solution(self, x: npt.NDArray, building_name: str) -> PyTaskData:
        """
        Convert a candidate solution from an array of parameter values to a dictionary of parameter names and values.

        Parameters
        ----------
        x
            A candidate building solution (array of parameter values).
        building_name
            The name of the building.

        Returns
        -------
        PyTaskData
            Dictionary of parameter names and values.
        """
        variable_params = dict(zip(self.variable_params[building_name], x))
        all_param = variable_params | deepcopy(self.constant_params[building_name])
        return PyTaskData(**all_param)

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
        x = self.scale_solution(x)
        x_dict = self.split_solution(x)
        portfolio_pytd = {name: self.convert_solution(x, name) for name, x in x_dict.items()}
        return self.sim.simulate_portfolio(portfolio_pytd)

    def apply_directions(self, objective_values: ObjectiveValues) -> ObjectiveValues:
        """
        Applies objective optimisation direction to objective values.
        Multiplies objective values of objectives that need to be maximised by -1.

        Parameters
        ----------
        objective_values
            Dictionary of objective names and objective values.

        Returns
        -------
        objective_values
            Dictionary of objective names and objective values with directions applied.
        """
        for objective in objective_values.keys():
            objective_values[objective] *= ObjectivesDirection[objective]
        return objective_values

    def calculate_infeasibility(self, objective_values: ObjectiveValues) -> list[float]:
        """
        Calculate the infeasibility of objective values given the problem's portfolio constraints.

        Parameters
        ----------
        objective_values
            Dictionary of objective names and objective values.

        Returns
        -------
        excess
            List of values that indicate by how much the objective values exceed the constraints.
        """
        excess = []
        for objective, bounds in self.constraints.items():
            min_value = bounds.get("min", None)
            max_value = bounds.get("max", None)

            if min_value is not None:
                excess.append(min_value - objective_values[objective])
            if max_value is not None:
                excess.append(objective_values[objective] - max_value)
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
        out["G"] = self.calculate_infeasibility(portfolio_solution.objective_values)
        selected_results = {objective: portfolio_solution.objective_values[objective] for objective in self.objectives}
        directed_results = self.apply_directions(selected_results)
        out["F"] = list(directed_results.values())


class EstimateBasedSampling(Sampling):
    """
    Generate a population of solutions by estimating some parameter values from data.
    """

    def _do(self, problem: ProblemInstance, n_samples: int, **kwargs):
        building_pops = []
        for building in problem.buildings.values():
            building_pops.append(  # noqa: PERF401
                generate_building_initial_population(
                    variable_param=building.variable_param(),
                    constant_param=building.constant_param(),
                    input_dir=building.input_dir,
                    pop_size=n_samples,
                )
            )
        portfolio_pop = np.concatenate(building_pops, axis=1)
        return portfolio_pop


class SamplingMethod(Enum):
    RANDOM = IntegerRandomSampling
    ESTIMATE = EstimateBasedSampling


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
