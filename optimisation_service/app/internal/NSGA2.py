from datetime import timedelta

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2 as Pymoo_NSGA2  # type: ignore
from pymoo.core.crossover import Crossover  # type: ignore
from pymoo.core.mutation import Mutation  # type: ignore
from pymoo.core.repair import Repair  # type: ignore
from pymoo.core.sampling import Sampling  # type: ignore
from pymoo.core.termination import Termination  # type: ignore
from pymoo.operators.crossover.pntx import PointCrossover  # type: ignore
from pymoo.operators.mutation.gauss import GaussianMutation  # type: ignore
from pymoo.operators.sampling.rnd import IntegerRandomSampling  # type: ignore
from pymoo.optimize import minimize  # type: ignore
from pymoo.termination.cv import ConstraintViolationTermination  # type: ignore
from pymoo.termination.ftol import MultiObjectiveSpaceTermination  # type: ignore
from pymoo.termination.max_eval import MaximumFunctionCallTermination  # type: ignore
from pymoo.termination.max_gen import MaximumGenerationTermination  # type: ignore
from pymoo.termination.robust import RobustTermination  # type: ignore

from app.internal.ga_utils import EstimateBasedSampling, ProblemInstance, RoundingAndDegenerateRepair
from app.internal.pareto_front import portfolio_pareto_front
from app.internal.portfolio_simulator import simulate_scenario
from app.internal.result import do_nothing_scenario
from app.models.algorithms import Algorithm
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.ga_utils import SamplingMethod
from app.models.metrics import Metric
from app.models.result import OptimisationResult


class CustomPymooNSGA2(Pymoo_NSGA2):
    def __init__(
        self,
        pop_size: int,
        n_offsprings: int,
        sampling: Sampling,
        crossover: Crossover,
        mutation: Mutation,
        eliminate_duplicates: bool,
        repair: Repair,
        return_least_infeasible: bool,
        pop_size_incr_scaler: float = 0.1,
        pop_size_incr_threshold: float = 0.9,
        **kwargs,
    ):
        assert pop_size_incr_scaler >= 0.0, "pop_size_incr_scaler must be greater or equal to 1."
        assert pop_size_incr_threshold > 0.0, "pop_size_incr_threshold must be greater than 1."
        assert pop_size_incr_threshold <= 1.0, "pop_size_incr_threshold must be smaller or equal to 1."
        self.pop_size_incr_scaler = pop_size_incr_scaler
        self.pop_size_incr_threshold = pop_size_incr_threshold
        super().__init__(
            pop_size=pop_size,
            n_offsprings=n_offsprings,
            sampling=sampling,
            crossover=crossover,
            mutation=mutation,
            eliminate_duplicates=eliminate_duplicates,
            repair=repair,
            return_least_infeasible=return_least_infeasible,
            **kwargs,
        )

    def _advance(self, infills=None, **kwargs):
        if self.pop_size_incr_scaler > 0.0:
            # if the current pareto front is larger than pop_size_incr_threshold percent of the pop size
            # increases pop size by pop_size_incr_scaler percent
            if len(self.opt) >= self.pop_size * self.pop_size_incr_threshold:
                self.pop_size = int((1 + self.pop_size_incr_scaler) * self.pop_size)
                self.n_offsprings = int((1 + self.pop_size_incr_scaler) * self.n_offsprings)
        return super()._advance(infills, **kwargs)


class NSGA2(Algorithm):
    """
    Optimise a multi-objective EPOCH problem using NSGA-II.
    """

    def __init__(
        self,
        pop_size: int = 2048,
        sampling: SamplingMethod = SamplingMethod.RANDOM,
        n_offsprings: int | None = None,
        prob_crossover: float = 0.9,
        n_crossover: int = 1,
        prob_mutation: float = 0.9,
        std_scaler: float = 0.2,
        tol: float = 1e-14,
        period: int | None = 5,
        n_max_gen: int = int(1e14),
        n_max_evals: int = int(1e14),
        cv_tol: float = 1e-14,
        cv_period: int = int(1e14),
        pop_size_incr_scaler: float = 0.0,
        pop_size_incr_threshold: float = 1.0,
        return_least_infeasible: bool = True,
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
            probability of applying mutation to each child (not probability of mutating a parameter!)
        std_scaler
            Scales standard deviation of nomral distribution from which is sampled new parameter values during mutation.
            Base value of std is parameter range
        tol
            Value for tolerance of improvement between current and past fitness, terminates if below
        period
            Number of passed fitness values to include in delta calculation, max delta is selected.
            Defaults to n_max_gen if set to None.
        cv_tol
            Tolerance of improvement between current and past constraint violations, terminates if below.
        cv_period
            Number of generations to include in constraint violation improvement calculation.
        n_max_gen
            Max number of generations before termination
        n_max_evals
            Max number of evaluations of EPOCH before termination
        pop_size_incr_scaler
            Scaler value to increase the pop_size and n_offsprings by for the next generation when the number of
            optimal scenarios surpasses pop_size_incr_threshold percent of the pop_size.
        pop_size_incr_threshold
            Percent of the pop_size to set as the threshold to increase the pop_size.
        return_least_infeasible
            If true, returns the most feasible solution if all solution are infeasible.
        """
        if n_offsprings is None:
            n_offsprings = int(pop_size * (3 / 4))

        if sampling == SamplingMethod.ESTIMATE:
            sampling_cls = EstimateBasedSampling
        elif sampling == SamplingMethod.RANDOM:
            sampling_cls = IntegerRandomSampling

        self.algorithm = CustomPymooNSGA2(
            pop_size=pop_size,
            n_offsprings=n_offsprings,
            sampling=sampling_cls(),
            crossover=PointCrossover(prob=prob_crossover, n_points=n_crossover, repair=RoundingAndDegenerateRepair()),
            mutation=GaussianMutation(prob=prob_mutation, sigma=std_scaler, vtype=float, repair=RoundingAndDegenerateRepair()),
            eliminate_duplicates=True,
            repair=RoundingAndDegenerateRepair(),
            return_least_infeasible=return_least_infeasible,
            pop_size_incr_scaler=pop_size_incr_scaler,
            pop_size_incr_threshold=pop_size_incr_threshold,
        )

        if period is None:
            period = n_max_gen

        self.termination_criteria = MultiTermination(tol, period, n_max_gen, n_max_evals, cv_tol, cv_period)

    def run(self, objectives: list[Metric], constraints: Constraints, portfolio: list[Site]) -> OptimisationResult:
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
        pi = ProblemInstance(objectives, constraints, portfolio)
        res = minimize(problem=pi, algorithm=self.algorithm, termination=self.termination_criteria, verbose=True)
        simulate_scenario.cache_clear()
        n_evals = res.algorithm.evaluator.n_eval
        exec_time = timedelta(seconds=res.exec_time)
        non_dom_sol = res.X
        if non_dom_sol is None:
            portfolio_solutions_pf = [do_nothing_scenario(pi.site_names)]
        else:
            if non_dom_sol.ndim == 1:
                non_dom_sol = np.expand_dims(non_dom_sol, axis=0)
            portfolio_solutions = [pi.simulate_portfolio(sol) for sol in non_dom_sol]
            portfolio_solutions_pf = portfolio_pareto_front(portfolio_solutions=portfolio_solutions, objectives=objectives)

        return OptimisationResult(solutions=portfolio_solutions_pf, exec_time=exec_time, n_evals=n_evals)


class MultiTermination(Termination):
    def __init__(
        self,
        tol: float = 1e-6,
        period: int = 30,
        n_max_gen: int = 1000,
        n_max_evals: int = 100000,
        cv_tol: float = 1e-6,
        cv_period: int = 30,
    ) -> None:
        super().__init__()
        self.f = RobustTermination(MultiObjectiveSpaceTermination(tol, only_feas=True), period)
        self.max_gen = MaximumGenerationTermination(n_max_gen)
        self.max_evals = MaximumFunctionCallTermination(n_max_evals)
        self.cv = RobustTermination(ConstraintViolationTermination(cv_tol, terminate_when_feasible=False), cv_period)

        self.criteria = [self.f, self.max_gen, self.max_evals, self.cv]

    def _update(self, algorithm: Algorithm) -> float:
        f_progress = self.f.update(algorithm)
        max_gen_progess = self.max_gen.update(algorithm)
        max_evals_progress = self.max_evals.update(algorithm)
        cv_progress = self.cv.update(algorithm)
        p = [f_progress, max_gen_progess, max_evals_progress, cv_progress]
        return max(p)
