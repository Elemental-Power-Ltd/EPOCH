import logging
from copy import deepcopy
from typing import Any, Never

import numpy as np
import numpy.typing as npt
from pymoo.config import Config  # type: ignore
from pymoo.core.mutation import Mutation  # type: ignore
from pymoo.core.problem import ElementwiseProblem  # type: ignore
from pymoo.core.termination import Termination  # type: ignore
from pymoo.operators.repair.bounds_repair import repair_random_init  # type: ignore
from pymoo.termination.ftol import MultiObjectiveSpaceTermination  # type: ignore
from pymoo.termination.max_eval import MaximumFunctionCallTermination  # type: ignore
from pymoo.termination.max_gen import MaximumGenerationTermination  # type: ignore
from pymoo.termination.robust import RobustTermination  # type: ignore

from app.internal.portfolio_simulator import PortfolioSimulator, PortfolioSolution
from app.internal.problem import PortfolioProblem
from app.internal.task_data_wrapper import PyTaskData
from app.models.algorithms import Algorithm
from app.models.objectives import _OBJECTIVES_DIRECTION, Objectives

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
        self.building_names = portfolio.buildings.keys()
        self.objectives = portfolio.objectives
        self.constraints = portfolio.constraints
        n_obj = len(self.objectives)
        n_ieq_constr = sum(len(bounds) for bounds in self.constraints.values())

        input_dirs = {}
        self.constant_params = {}
        self.variable_params = {}
        self.location = {}
        self.lower_bounds = np.array([])
        self.upper_bounds = np.array([])
        self.steps = np.array([])

        n_var = 0
        for building_name, building in portfolio.buildings.items():
            variable_params_building = []

            n_var_building = 0
            for key, value in building.variable_param().items():
                variable_params_building.append(key)
                self.lower_bounds = np.append(self.lower_bounds, value["min"])
                self.upper_bounds = np.append(self.upper_bounds, value["max"])
                self.steps = np.append(self.steps, value["step"])
                n_var_building += 1

            self.location[building_name] = (n_var, n_var + n_var_building)
            self.variable_params[building_name] = deepcopy(variable_params_building)
            self.constant_params[building_name] = deepcopy(building.constant_param())
            input_dirs[building_name] = building.input_dir
            n_var += n_var_building

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
        return {building_name: x[start:stop] for building_name, (start, stop) in self.location.items()}

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

    def apply_directions(self, objective_values: dict[Objectives, float]) -> dict[Objectives, float]:
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
            objective_values[objective] *= _OBJECTIVES_DIRECTION[objective]
        return objective_values

    def calculate_infeasibility(self, objective_values: dict[Objectives, float]) -> list[float]:
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


class MultiTermination(Termination):
    def __init__(self, tol: float = 1e-6, period: int = 30, n_max_gen: int = 1000, n_max_evals: int = 100000) -> None:
        super().__init__()
        self.f = RobustTermination(MultiObjectiveSpaceTermination(tol, only_feas=True), period)
        self.max_gen = MaximumGenerationTermination(n_max_gen)
        self.max_evals = MaximumFunctionCallTermination(n_max_evals)

        self.criteria = [self.f, self.max_gen, self.max_evals]

    def _update(self, algorithm: Algorithm) -> float:
        f_progress = self.f.update(algorithm)
        max_gen_progess = self.max_gen.update(algorithm)
        max_evals_progress = self.max_evals.update(algorithm)
        p = [f_progress, max_gen_progess, max_evals_progress]
        return max(p)


def mut_simple_int(X: npt.NDArray, xl: npt.NDArray, xu: npt.NDArray, prob: npt.NDArray) -> npt.NDArray:
    """
    Mutate integer variables by 1.
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


class SimpleIntMutation(Mutation):
    """
    Mutate integer variables by 1.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def _do(self, problem: ProblemInstance, X: npt.NDArray, **kwargs: Never) -> npt.NDArray:
        X.astype(float)
        prob_var = self.get_prob_var(problem, size=len(X))
        Xp = mut_simple_int(X, problem.xl, problem.xu, prob_var)

        return Xp
