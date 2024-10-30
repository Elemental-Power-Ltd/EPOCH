from datetime import timedelta

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2 as Pymoo_NSGA2  # type: ignore
from pymoo.operators.crossover.pntx import PointCrossover  # type: ignore
from pymoo.operators.mutation.gauss import GaussianMutation  # type: ignore
from pymoo.operators.repair.rounding import RoundingRepair  # type: ignore
from pymoo.operators.sampling.rnd import IntegerRandomSampling  # type: ignore
from pymoo.optimize import minimize  # type: ignore

from app.internal.ga_utils import MultiTermination, ProblemInstance
from app.internal.pareto_front import portfolio_pareto_front
from app.internal.problem import PortfolioProblem
from app.models.algorithms import Algorithm
from app.models.result import OptimisationResult


class NSGA2(Algorithm):
    """
    Optimise a multi-objective EPOCH problem using NSGA-II.
    """

    def __init__(
        self,
        pop_size: int = 2048,
        n_offsprings: int | None = None,
        prob_crossover: float = 0.9,
        n_crossover: int = 1,
        prob_mutation: float = 0.9,
        std_scaler: float = 0.2,
        tol: float = 1e-14,
        period: int | None = 5,
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
            n_offsprings = int(pop_size * (3 / 4))

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

    def run(self, portfolio: PortfolioProblem) -> OptimisationResult:
        """
        Run NSGA optimisation.

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
        pi = ProblemInstance(portfolio)
        res = minimize(problem=pi, algorithm=self.algorithm, termination=self.termination_criteria)
        n_evals = res.algorithm.evaluator.n_eval
        exec_time = timedelta(seconds=res.exec_time)
        non_dom_sol = res.X
        if non_dom_sol.ndim == 1:
            non_dom_sol = np.expand_dims(non_dom_sol, axis=0)
        portfolio_solutions = [pi.simulate_portfolio(sol) for sol in non_dom_sol]
        portfolio_solutions_pf = portfolio_pareto_front(
            portfolio_solutions=portfolio_solutions, objectives=portfolio.objectives
        )

        return OptimisationResult(solutions=portfolio_solutions_pf, exec_time=exec_time, n_evals=n_evals)
