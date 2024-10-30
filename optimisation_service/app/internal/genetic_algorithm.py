from datetime import timedelta
from typing import Any

import numpy as np
import numpy.typing as npt
from pymoo.algorithms.soo.nonconvex.ga import GA as Pymoo_GA  # type: ignore
from pymoo.core.termination import Termination  # type: ignore
from pymoo.operators.crossover.pntx import PointCrossover  # type: ignore
from pymoo.operators.mutation.gauss import GaussianMutation  # type: ignore
from pymoo.operators.repair.rounding import RoundingRepair  # type: ignore
from pymoo.operators.sampling.rnd import IntegerRandomSampling  # type: ignore
from pymoo.operators.selection.tournament import TournamentSelection  # type: ignore
from pymoo.optimize import minimize  # type: ignore
from pymoo.termination.ftol import SingleObjectiveSpaceTermination  # type: ignore
from pymoo.termination.max_eval import MaximumFunctionCallTermination  # type: ignore
from pymoo.termination.max_gen import MaximumGenerationTermination  # type: ignore
from pymoo.termination.robust import RobustTermination  # type: ignore

from app.internal.ga_utils import ProblemInstance
from app.internal.pareto_front import portfolio_pareto_front
from app.internal.problem import PortfolioProblem
from app.models.algorithms import Algorithm
from app.models.result import OptimisationResult


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

    def run(self, portfolio: PortfolioProblem) -> OptimisationResult:
        """
        Run GA optimisation.

        Parameters
        ----------
        portfolio
            Portfolio problem instance to optimise.

        Returns
        -------
        OptimisationResult
            solutions: Pareto-front of evaluated candidate portfolio solutions.
            exec_time: Time taken for optimisation process to conclude.
            n_evals: Number of simulation evaluations taken for optimisation process to conclude.
        """
        portfolio_solutions = []
        exec_time, n_evals = 0, 0
        for sub_problem in portfolio.split_objectives():
            pi = ProblemInstance(sub_problem)
            res = minimize(problem=pi, algorithm=self.algorithm, termination=self.termination_criteria)
            portfolio_solutions.append(pi.simulate_portfolio(res.X))

            assert res.exec_time is not None
            exec_time += res.exec_time
            n_evals += res.algorithm.evaluator.n_eval

        exec_timedelta = timedelta(seconds=float(exec_time))
        portfolio_solutions_pf = portfolio_pareto_front(
            portfolio_solutions=portfolio_solutions, objectives=portfolio.objectives
        )

        return OptimisationResult(solutions=portfolio_solutions_pf, exec_time=exec_timedelta, n_evals=n_evals)


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
