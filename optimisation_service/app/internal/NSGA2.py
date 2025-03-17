from datetime import timedelta

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2 as Pymoo_NSGA2  # type: ignore
from pymoo.core.initialization import Initialization
from pymoo.core.population import Population
from pymoo.core.termination import Termination  # type: ignore
from pymoo.operators.crossover.pntx import PointCrossover  # type: ignore
from pymoo.operators.mutation.gauss import GaussianMutation  # type: ignore
from pymoo.operators.sampling.rnd import IntegerRandomSampling  # type: ignore
from pymoo.optimize import minimize  # type: ignore
from pymoo.termination.ftol import MultiObjectiveSpaceTermination  # type: ignore
from pymoo.termination.max_eval import MaximumFunctionCallTermination  # type: ignore
from pymoo.termination.max_gen import MaximumGenerationTermination  # type: ignore
from pymoo.termination.robust import RobustTermination  # type: ignore
from pymoo.util.misc import at_least_2d_array

from app.internal.constraints import is_in_constraints
from app.internal.ga_utils import EstimateBasedSampling, ProblemInstance, RoundingAndDegenerateRepair
from app.internal.pareto_front import merge_and_optimise_two_portfolio_solution_lists, portfolio_pareto_front
from app.internal.portfolio_simulator import simulate_scenario
from app.models.algorithms import Algorithm
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.ga_utils import SamplingMethod
from app.models.metrics import Metric
from app.models.result import OptimisationResult, PortfolioSolution


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
        n_max_gen
            Max number of generations before termination
        n_max_evals
            Max number of evaluations of EPOCH before termination
        """
        if n_offsprings is None:
            n_offsprings = int(pop_size * (3 / 4))

        if sampling == SamplingMethod.ESTIMATE:
            sampling_cls = EstimateBasedSampling
        elif sampling == SamplingMethod.RANDOM:
            sampling_cls = IntegerRandomSampling
        self.sampling = sampling_cls()

        self.algorithm = Pymoo_NSGA2(
            pop_size=pop_size,
            n_offsprings=n_offsprings,
            sampling=self.sampling,
            crossover=PointCrossover(prob=prob_crossover, n_points=n_crossover, repair=RoundingAndDegenerateRepair()),
            mutation=GaussianMutation(prob=prob_mutation, sigma=std_scaler, vtype=float, repair=RoundingAndDegenerateRepair()),
            eliminate_duplicates=True,
            repair=RoundingAndDegenerateRepair(),
        )

        if period is None:
            period = n_max_gen

        self.termination_criteria = MultiTermination(tol, period, n_max_gen, n_max_evals)

    def _load_existing_solutions(self, solutions: list[PortfolioSolution], problem: ProblemInstance):
        """
        Load existing solutions to the optimisation problem into the population.
        Can only be run once before run.
        Should not be used directly, favour using existing_solutions variable in run function.

        Parameters
        ----------
        solutions
            PortfolioSolutions to load into the population
        problem
            Optimisation problem instance. Used to convert PortfolioSolutions into Choromosomes.

        Returns
        -------
        None
        """
        population = []
        for solution in solutions:
            individual = [
                problem.convert_site_scenario_to_chromosome(solution.scenario[site_name].scenario, site_name)
                for site_name in problem.site_names
            ]
            population.append(np.concatenate(individual))
        population_arr = Population.new(X=at_least_2d_array(np.array(population)))

        pop_size = self.algorithm.pop_size
        rng = np.random.default_rng()
        if len(population_arr) > pop_size:
            population_arr = rng.choice(population_arr, pop_size, replace=False)
        elif len(population_arr) < pop_size:
            sampled_pop = self.sampling(problem, pop_size - len(population_arr))
            population_arr = np.concatenate([population_arr, sampled_pop])

        population_arr = population_arr.view(Population)

        self.algorithm.initialization = Initialization(
            population_arr, self.algorithm.initialization.repair, self.algorithm.initialization.eliminate_duplicates
        )

    def run(
        self,
        objectives: list[Metric],
        constraints: Constraints,
        portfolio: list[Site],
        existing_solutions: list[PortfolioSolution] | None = None,
    ) -> OptimisationResult:
        """
        Run NSGA optimisation.

        Parameters
        ----------
        objectives
            Objectives to optimise.
        constraints
            Constraints on the metrics to apply.
        portfolio
            Portfolio of sites to optimise.
        existing_solutions
            Existing solutions to the problem to initialise the optimisation with.

        Returns
        -------
        OptimisationResult
            solutions: Pareto-front of evaluated candidate portfolio solutions.
            exec_time: Time taken for optimisation process to conclude.
            n_evals: Number of simulation evaluations taken for optimisation process to conclude.
        """
        pi = ProblemInstance(objectives, constraints, portfolio)
        if existing_solutions is not None:
            self._load_existing_solutions(existing_solutions, pi)
        res = minimize(problem=pi, algorithm=self.algorithm, termination=self.termination_criteria, verbose=True)
        simulate_scenario.cache_clear()
        n_evals = res.algorithm.evaluator.n_eval
        exec_time = max(timedelta(seconds=res.exec_time), timedelta(seconds=1))
        non_dom_sol = res.X
        if non_dom_sol.ndim == 1:
            non_dom_sol = np.expand_dims(non_dom_sol, axis=0)
        portfolio_solutions = [pi.simulate_portfolio(sol) for sol in non_dom_sol]
        portfolio_solutions_pf = portfolio_pareto_front(portfolio_solutions=portfolio_solutions, objectives=objectives)

        return OptimisationResult(solutions=portfolio_solutions_pf, exec_time=exec_time, n_evals=n_evals)


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


class SeperatedNSGA2(Algorithm):
    def __init__(
        self,
        pop_size=2048,
        sampling=SamplingMethod.RANDOM,
        n_offsprings=None,
        prob_crossover=0.9,
        n_crossover=1,
        prob_mutation=0.9,
        std_scaler=0.2,
        tol=1e-14,
        period=5,
        n_max_gen=100000000000000,
        n_max_evals=100000000000000,
    ):
        self.alg = NSGA2(
            pop_size,
            sampling,
            n_offsprings,
            prob_crossover,
            n_crossover,
            prob_mutation,
            std_scaler,
            tol,
            period,
            n_max_gen,
            n_max_evals,
        )

    def run(self, objectives, constraints, portfolio, existing_solutions=None):
        capex_limit = constraints[Metric.capex]["max"]
        sub_solutions: list[list[PortfolioSolution]] = []
        for i, site in enumerate(portfolio):
            print(f"Optimising portfolio {i+1} at max CAPEX £{capex_limit}.")
            res = self.alg.run(objectives=objectives, constraints={Metric.capex: {"max": capex_limit}}, portfolio=[site])
            sub_solutions.append(res.solutions)

        combined_solutions = sub_solutions[0]
        for sub_solution in sub_solutions[1:]:
            combined_solutions = merge_and_optimise_two_portfolio_solution_lists(
                combined_solutions, sub_solution, objectives, capex_limit
            )

        mask = is_in_constraints(constraints, combined_solutions)
        combined_solutions = np.array(combined_solutions)[mask].tolist()

        return combined_solutions
