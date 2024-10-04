import logging
from copy import deepcopy
from datetime import timedelta
from typing import Any, Never

import numpy as np
import numpy.typing as npt
from paretoset import paretoset  # type: ignore
from pymoo.algorithms.moo.nsga2 import NSGA2 as Pymoo_NSGA2  # type: ignore
from pymoo.algorithms.soo.nonconvex.ga import GA as Pymoo_GA  # type: ignore
from pymoo.config import Config  # type: ignore
from pymoo.core.mutation import Mutation  # type: ignore
from pymoo.core.problem import ElementwiseProblem  # type: ignore
from pymoo.core.termination import Termination  # type: ignore
from pymoo.operators.crossover.pntx import PointCrossover  # type: ignore
from pymoo.operators.mutation.gauss import GaussianMutation  # type: ignore
from pymoo.operators.repair.bounds_repair import repair_random_init  # type: ignore
from pymoo.operators.repair.rounding import RoundingRepair  # type: ignore
from pymoo.operators.sampling.rnd import IntegerRandomSampling  # type: ignore
from pymoo.operators.selection.tournament import TournamentSelection  # type: ignore
from pymoo.optimize import minimize  # type: ignore
from pymoo.termination.ftol import MultiObjectiveSpaceTermination, SingleObjectiveSpaceTermination  # type: ignore
from pymoo.termination.max_eval import MaximumFunctionCallTermination  # type: ignore
from pymoo.termination.max_gen import MaximumGenerationTermination  # type: ignore
from pymoo.termination.robust import RobustTermination  # type: ignore

from ..models.algorithms import Algorithm
from .problem import _OBJECTIVES, _OBJECTIVES_DIRECTION, Problem
from .result import Result
from .task_data_wrapper import PySimulationResult, PyTaskData, Simulator

logger = logging.getLogger("default")

Config.warnings["not_compiled"] = False

logger = logging.getLogger("default")


class NSGA2(Algorithm):
    """
    Optimise a multi-objective EPOCH problem using NSGA-II.
    """

    def __init__(
        self,
        pop_size: int = 128,
        n_offsprings: int | None = None,
        prob_crossover: float = 0.9,
        n_crossover: int = 1,
        prob_mutation: float = 0.9,
        std_scaler: float = 0.2,
        tol: float = 1e-14,
        period: int | None = 25,
        n_max_gen: int = int(1e14),
        n_max_evals: int = int(1e14),
    ) -> None:
        """
        Define GA hyperparameters.

        Parameters
        ----------
        pop_size
            population size of GA
        n_offsprings
            number of offspring to generate at each generation, defaults to pop_size
        prob_crossover
            probability of applying crossover between two parents
        n_crossover
            number of points to use in crossover
        prob_mutation
            probability of applying mutation to each child
        std_scaler
            Scales standard deviation of nomral distribution from which is sampled new parameter values during mutation.
            Base value of std is parameter range
        tol
            Value for tolerance of improvement between current and past fitness, terminates if below
        period
            Number of passed fitness values to include in delta calculation, max delta is selected.
            Defaults to n_max_gen if set to None.
        n_max_gen
            Max number of generations before termination
        n_max_evals
            Max number of evaluations of EPOCH before termination
        """
        if n_offsprings is None:
            n_offsprings = pop_size

        self.algorithm = Pymoo_NSGA2(
            pop_size=pop_size,
            n_offsprings=n_offsprings,
            sampling=IntegerRandomSampling(),
            crossover=PointCrossover(prob=prob_crossover, n_points=n_crossover, repair=RoundingRepair()),
            mutation=GaussianMutation(prob=prob_mutation, sigma=std_scaler, vtype=float, repair=RoundingRepair()),
            eliminate_duplicates=True,
        )

        if period is None:
            period = n_max_gen

        self.termination_criteria = MultiTermination(tol, period, n_max_gen, n_max_evals)

    def run(self, problem: Problem) -> Result:
        """
        Run NSGA optimisation.

        Parameters
        ----------
        problem
            Problem instance to optimise.

        Returns
        -------
        solution
            Optimal solutions.
        fitness
            Objective values of optimal solutions.
        """
        pi = ProblemInstance(problem)

        pareto_front = minimize(problem=pi, algorithm=self.algorithm, termination=self.termination_criteria)
        # To facilitate the algorithm, the problem parameter values are scaled, with ranges from 0 to n and a stepsize of 1.
        # Hence, resutls need to be scaled back to valid values.
        solutions = pi.scale_solutions(pareto_front.X)
        # Moreover, the optimiser only maintains track of optimised objectives.
        # Hence, each solution in the pareto front is reevaluated to gather missing objective values.
        objective_values = []
        objective_values_for_pf = []
        for sol in solutions:
            simresult = pi.simulate(sol)
            objective_values.append([simresult[objective] for objective in _OBJECTIVES])
            objective_values_for_pf.append([simresult[objective] for objective in problem.objectives])
        objective_values_arr = np.asarray(objective_values)
        objective_values_for_pf_arr = np.asarray(objective_values_for_pf)

        n_evals = pareto_front.algorithm.evaluator.n_eval
        exec_time = timedelta(seconds=pareto_front.exec_time)

        obj_direct = ["max" if _OBJECTIVES_DIRECTION[objective] == -1 else "min" for objective in problem.objectives]
        pareto_efficient = paretoset(objective_values_for_pf_arr, obj_direct, distinct=True)
        solutions = solutions[pareto_efficient]
        objective_values_arr = objective_values_arr[pareto_efficient]

        return Result(solutions=solutions, objective_values=objective_values_arr, exec_time=exec_time, n_evals=n_evals)


class GeneticAlgorithm(Algorithm):
    """
    Optimise one or multiple uni-objective EPOCH problem(s) using a genetic algorithm.
    """

    def __init__(
        self,
        pop_size: int = 128,
        n_offsprings: int | None = None,
        k_tournament: int = 2,
        prob_crossover: float = 0.9,
        n_crossover: int = 1,
        prob_mutation: float = 0.9,
        std_scaler: float = 0.2,
        tol: float = 1e-14,
        period: int = 25,
        n_max_gen: int = int(1e14),
        n_max_evals: int = int(1e14),
    ):
        """
        Define GA hyperparameters.

        Parameters
        ----------
        pop_size
            population size of GA
        n_offsprings
            number of offspring to generate at each generation, defaults to pop_size
        k_tournament
            number of parents taking part in selection tournament
        prob_crossover
            probability of applying crossover between two parents
        n_crossover
            number of points to use in crossover
        prob_mutation
            probability of applying mutation to each child
        std_scaler
            Scales standard deviation of nomral distribution from which is sampled new parameter values during mutation.
            Base value of std is parameter range
        tol
            Value for tolerance of improvement between current and past fitness, terminates if below
        period
            Number of passed fitness values to include in delta calculation, max delta is selected.
            Defaults to n_max_gen if set to None.
        n_max_gen
            Max number of generations before termination
        n_max_evals
            Max number of evaluations of EPOCH before termination
        """
        if n_offsprings is None:
            n_offsprings = pop_size // 2

        self.algorithm = Pymoo_GA(
            pop_size=pop_size,
            n_offsprings=n_offsprings,
            sampling=IntegerRandomSampling(),
            selection=TournamentSelection(pressure=k_tournament, func_comp=comp_by_cv_and_fitness),
            crossover=PointCrossover(prob=prob_crossover, n_points=n_crossover, repair=RoundingRepair()),
            mutation=GaussianMutation(prob=prob_mutation, sigma=std_scaler, vtype=float, repair=RoundingRepair()),
            eliminate_duplicates=True,
        )

        self.termination_criteria = SingleTermination(tol, period, n_max_gen, n_max_evals)

    def run(self, problem: Problem) -> Result:
        """
        Run GA optimisation.

        Parameters
        ----------
        problem
            Problem instance to optimise.

        Returns
        -------
        solution
            Optimal solutions.
        fitness
            Objective values of optimal solutions.
        """
        objective_values, solutions = [], []
        exec_time, n_evals = 0, 0
        for sub_problem in problem.split_objectives():
            pi = ProblemInstance(sub_problem)
            single_solution = minimize(problem=pi, algorithm=self.algorithm, termination=self.termination_criteria)
            # To facilitate the algorithm, the problem parameter values are scaled, with ranges from 0 to n and a stepsize of 1.
            # Hence, resutls need to be scaled back to valid values.
            x = pi.scale_solutions(single_solution.X)
            # Moreover, the optimiser only maintains track of optimised objectives.
            # Hence, each solution in the pareto front is reevaluated to gather missing objective values.
            solutions.append(x)
            simresult = pi.simulate(x)
            objective_values.append([simresult[objective] for objective in _OBJECTIVES])

            assert single_solution.exec_time is not None
            exec_time += single_solution.exec_time
            n_evals += single_solution.algorithm.evaluator.n_eval

        exec_timedelta = timedelta(seconds=float(exec_time))
        objective_values_arr, solutions_arr = np.asarray(objective_values), np.asarray(solutions)

        obj_direct = ["max" if _OBJECTIVES_DIRECTION[objective] == -1 else "min" for objective in problem.objectives]
        pareto_efficient = paretoset(objective_values_arr, obj_direct, distinct=True)
        solutions_arr = solutions_arr[pareto_efficient]
        objective_values_arr = objective_values_arr[pareto_efficient]

        return Result(solutions=solutions_arr, objective_values=objective_values_arr, exec_time=exec_timedelta, n_evals=n_evals)


class ProblemInstance(ElementwiseProblem):
    """
    Create Pymoo ProblemInstance from OptimiseProblem instance.
    """

    def __init__(self, problem: Problem) -> None:
        """
        Define Problem objectives, constraints, parameter search space.

        Parameters
        ----------
        Problem
            Problem to optimise
        """
        n_obj = len(problem.objectives)
        self.constant_param = deepcopy(problem.constant_param())
        self.sim = Simulator(inputDir=str(problem.input_dir))  # epoch_simulator doesn't accept windows paths
        self.objectives = problem.objectives
        self.constraints = problem.constraints

        n_ieq_constr = sum(len(bounds) for bounds in self.constraints.values())

        self.v_params, self.lb, ub, self.step = [], np.array([]), np.array([]), np.array([])
        n_var = 0
        for key, value in problem.variable_param().items():
            self.v_params.append(key)
            self.lb = np.append(self.lb, value["min"])
            ub = np.append(ub, value["max"])
            self.step = np.append(self.step, value["step"])
            n_var += 1

        super().__init__(n_var=n_var, n_obj=n_obj, n_ieq_constr=n_ieq_constr, xl=[0] * n_var, xu=(ub - self.lb) / self.step)

    def scale_solutions(self, x: npt.NDArray) -> npt.NDArray:
        return x * self.step + self.lb

    def simulate(self, x: npt.NDArray) -> PySimulationResult:
        variable_param = dict(zip(self.v_params, x))
        all_param = variable_param | deepcopy(self.constant_param)
        pytd = PyTaskData(**all_param)
        res = PySimulationResult(self.sim.simulate_scenario(pytd))
        if any(np.isnan(val) for val in res.values()):
            logger.error(f"Got NaN simulation result {res} for config: {pytd}")
        return res

    def _evaluate(self, x: npt.NDArray, out: dict[str, list[np.floating]]) -> None:
        fractional_parts, _ = np.modf(x)
        if np.any(fractional_parts != 0):
            logger.warning(f"Solution contains decimal values: {x}")
        x = self.scale_solutions(x)
        fractional_parts, _ = np.modf(x)
        if np.any(fractional_parts != 0):
            logger.warning(f"Scaled solution contains decimal values: {x}")
        result = self.simulate(x)

        out["F"] = [result[objective] * _OBJECTIVES_DIRECTION[objective] for objective in self.objectives]
        if np.isnan(out["F"]).any():
            logger.warning(f"nan in objective values for sol: {x}")

        out["G"] = []
        for constraint, bounds in self.constraints.items():
            min_value = bounds.get("min", None)
            max_value = bounds.get("max", None)

            if min_value is not None:
                out["G"].append(min_value - result[constraint])
            if max_value is not None:
                out["G"].append(result[constraint] - max_value)


class SingleTermination(Termination):
    def __init__(self, tol: float = 1e-6, period: int = 30, n_max_gen: int = 1000, n_max_evals: int = 100000) -> None:
        super().__init__()
        self.f = RobustTermination(SingleObjectiveSpaceTermination(tol, only_feas=True), period)
        self.max_gen = MaximumGenerationTermination(n_max_gen)
        self.max_evals = MaximumFunctionCallTermination(n_max_evals)

        self.criteria = [self.f, self.max_gen, self.max_evals]

    def _update(self, algorithm: Algorithm) -> float:
        p = [criterion.update(algorithm) for criterion in self.criteria]
        return max(p)


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


def comp_by_cv_and_fitness(pop: Any, P: npt.NDArray, **kwargs: Any) -> npt.NDArray[np.integer]:
    """
    Perform tournament selection

    Parameters
    ----------
    pop
        Pymoo population
    P
        Candidates in tournanemt
    kwargs
        ???

    Returns
    -------
    Parents from tournament selection
    """
    S = np.full(P.shape[0], np.nan)
    rng = np.random.default_rng()

    for i in range(P.shape[0]):
        candidates = P[i, :]
        feasible = [candidate for candidate in candidates if pop[candidate].CV <= 0.0]
        if len(feasible) > 0:
            candidates_fitnesses = [pop[candidate].F for candidate in feasible]
            minimum = min(candidates_fitnesses)
            best_candidates = [candidate for candidate in feasible if pop[candidate].F == minimum]
            S[i] = rng.choice(best_candidates)
        else:
            candidates_fitnesses = [pop[candidate].CV for candidate in feasible]
            minimum = min(candidates_fitnesses)
            best_candidates = [candidate for candidate in feasible if pop[candidate].CV == minimum]
            S[i] = rng.choice(best_candidates)

    return S[:, np.newaxis].astype(int)


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
