from datetime import UTC, datetime, timedelta

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2 as Pymoo_NSGA2  # type: ignore
from pymoo.core.crossover import Crossover  # type: ignore
from pymoo.core.initialization import Initialization  # type: ignore
from pymoo.core.mutation import Mutation  # type: ignore
from pymoo.core.population import Population  # type: ignore
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
from pymoo.util.misc import at_least_2d_array  # type: ignore

from app.internal.constraints import is_in_constraints
from app.internal.ga_utils import EstimateBasedSampling, ProblemInstance, RoundingAndDegenerateRepair
from app.internal.pareto_front import merge_and_optimise_two_portfolio_solution_lists, portfolio_pareto_front
from app.internal.portfolio_simulator import simulate_scenario
from app.internal.result import get_baseline_portfolio_solution
from app.models.algorithms import Algorithm
from app.models.constraints import Bounds, Constraints
from app.models.core import Site
from app.models.ga_utils import SamplingMethod
from app.models.metrics import Metric
from app.models.optimisers import NSGA2HyperParam
from app.models.result import OptimisationResult, PortfolioSolution


class CustomPymooNSGA2(Pymoo_NSGA2):
    """Extend the PymooNSGA2 code with some utility for our purposes."""

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
        pop_size_incr_scalar: float = 0.1,
        pop_size_incr_threshold: float = 0.9,
        **kwargs,
    ):
        """
        Initialise a Pymoo NSGA2 algorithm with a customised loop.

        This is capable of automatically increasing the population size at
        each generation dependent on the proportion of optimal scenarios in the population.

        Parameters
        ----------
        pop_size
            Initial population size.
        n_offsprings
            Number of offspring to generate at each generation.
            If the number of offspring is smaller than the population size,
            then the following popluation will be constituted of the newly generated offspring
            as well as (pop_size - n_offsprings) individuals from the current population.
            If the number of offpsring is greater than the population size,
            then the following popluation will be constituted of pop_size newly generated offspring.
        sampling
            Sampling method to generate the initial population with.
        crossover
            Crossover method to generate new offspring at each generation.
        mutation
            Mutation method to generate new offspring at each generation.
        eliminate_duplicates
            Boolean indicating if duplicates should be eliminated from the population or not.
        repair
            Repair method to ensure correctness of new offspring.
        return_least_infeasible
            Boolean indicating if the least feasible individual should be returned or not if no feasible solution is found.
        pop_size_incr_scalar
            Scalar value to increase the pop_size and n_offsprings by for the next generation when the number of
            optimal scenarios surpasses pop_size_incr_threshold percent of the pop_size.
        pop_size_incr_threshold
            Percent of the pop_size to set as the threshold to increase the pop_size.
        """
        assert pop_size_incr_scalar >= 0.0, "pop_size_incr_scaler must be greater or equal to 1."
        assert pop_size_incr_threshold > 0.0, "pop_size_incr_threshold must be greater than 0."
        assert pop_size_incr_threshold <= 1.0, "pop_size_incr_threshold must be smaller or equal to 1."
        self.pop_size_incr_scalar = pop_size_incr_scalar
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
        """
        Extend the _advance function to enable automatic population size increase.

        The function is called at each generation.

        Parameters
        ----------
        infills
            Passed to Pymoo_NSGA2
        kwargs
            Forwarded to the Pymoo_NSGA2

        Returns
        -------
            ?
        """
        if self.pop_size_incr_scalar > 0.0:
            # if the current pareto front is larger than pop_size_incr_threshold percent of the pop size
            # increases pop size by pop_size_incr_scalar percent.
            # the population is limited to 10k individuals.
            if len(self.opt) >= self.pop_size * self.pop_size_incr_threshold:  # type: ignore
                self.pop_size = min(self.pop_size + max(1, int(self.pop_size_incr_scalar * self.pop_size)), 10000)  # type: ignore
                self.n_offsprings = min(self.n_offsprings + max(1, int(self.pop_size_incr_scalar * self.n_offsprings)), 10000)  # type: ignore
        return super()._advance(infills, **kwargs)


class NSGA2(Algorithm):
    """Optimise a multi-objective EPOCH problem using NSGA-II."""

    def __init__(
        self,
        pop_size: int = 256,
        sampling: SamplingMethod = SamplingMethod.RANDOM,
        n_offsprings: int | None = 128,
        prob_crossover: float = 0.2,
        n_crossover: int = 2,
        prob_mutation: float = 0.8,
        std_scaler: float = 1.0,
        tol: float = 1e-14,
        period: int | None = 5,
        n_max_gen: int = 1000,
        n_max_evals: int = int(1e14),
        cv_tol: float = 0.001,
        cv_period: int = 100,
        pop_size_incr_scalar: float = 0.0,
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
            Scales standard deviation of normal distribution from which is sampled new parameter values during mutation.
            Base value of std is parameter range.
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
        pop_size_incr_scalar
            Scalar value to increase the pop_size and n_offsprings by for the next generation when the number of
            optimal scenarios surpasses pop_size_incr_threshold percent of the pop_size.
        pop_size_incr_threshold
            Percent of the pop_size to set as the threshold to increase the pop_size.
        return_least_infeasible
            If true, returns the most feasible solution if all solution are infeasible.
        """
        if n_offsprings is None:
            n_offsprings = int(pop_size / 2)

        if sampling == SamplingMethod.ESTIMATE:
            sampling_cls = EstimateBasedSampling
        elif sampling == SamplingMethod.RANDOM:
            sampling_cls = IntegerRandomSampling
        self.sampling = sampling_cls()

        self.algorithm = CustomPymooNSGA2(
            pop_size=pop_size,
            n_offsprings=n_offsprings,
            sampling=self.sampling,
            crossover=PointCrossover(prob=prob_crossover, n_points=n_crossover, repair=RoundingAndDegenerateRepair()),
            mutation=GaussianMutation(prob=prob_mutation, sigma=std_scaler, repair=RoundingAndDegenerateRepair()),
            eliminate_duplicates=True,
            repair=RoundingAndDegenerateRepair(),
            return_least_infeasible=return_least_infeasible,
            pop_size_incr_scalar=pop_size_incr_scalar,
            pop_size_incr_threshold=pop_size_incr_threshold,
        )

        if period is None:
            period = n_max_gen

        self.termination_criteria = MultiTermination(tol, period, n_max_gen, n_max_evals, cv_tol, cv_period)

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
        save_history: bool = False,
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
        save_history
            Whether to save the history (creates a list of NSGA2 objects in the return value)

        Returns
        -------
        OptimisationResult
            solutions: Pareto-front of evaluated candidate portfolio solutions.
            exec_time: Time taken for optimisation process to conclude.
            n_evals: Number of simulation evaluations taken for optimisation process to conclude.
        """
        pi = ProblemInstance(objectives, constraints, portfolio)
        if existing_solutions is not None and len(existing_solutions) > 0:
            self._load_existing_solutions(existing_solutions, pi)
        res = minimize(problem=pi, algorithm=self.algorithm, termination=self.termination_criteria, save_history=save_history)
        simulate_scenario.cache_clear()
        n_evals = res.algorithm.evaluator.n_eval
        exec_time = max(timedelta(seconds=res.exec_time), timedelta(seconds=1))
        non_dom_sol = res.X
        if non_dom_sol is None or len(non_dom_sol) == 0:
            portfolio_solutions_pf = [get_baseline_portfolio_solution(portfolio)]
        else:
            if non_dom_sol.ndim == 1:
                non_dom_sol = np.expand_dims(non_dom_sol, axis=0)
            portfolio_scenarios = [
                pi.convert_portfolio_chromosome_to_portfolio_scenario(chromosome) for chromosome in non_dom_sol
            ]
            portfolio_solutions = [pi.sim.simulate_portfolio(portfolio_scenario) for portfolio_scenario in portfolio_scenarios]
            portfolio_solutions_pf = portfolio_pareto_front(portfolio_solutions=portfolio_solutions, objectives=objectives)

        return OptimisationResult(
            solutions=portfolio_solutions_pf,
            exec_time=exec_time,
            n_evals=n_evals,
            history=res.history if save_history else None,
        )


class MultiTermination(Termination):
    """Combination of multiple termination criteria: robust, maximum generation, maximum func calls, constrint violation."""

    def __init__(
        self,
        tol: float = 1e-6,
        period: int = 30,
        n_max_gen: int = 1000,
        n_max_evals: int = 100000,
        cv_tol: float = 1e-6,
        cv_period: int = 30,
    ) -> None:
        """
        Create the multi termination criterion.

        Parameters
        ----------
        tol
            Tolerance for the Robust criterion
        period
            Memory length for the Robust criterion
        n_max_gen
            Maximum generations to allow
        n_max_evals
            Maximum function calls to allow
        cv_tol
            Constraint violation tolerance
        cv_period
            Constraint violation memory length.
        """
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


class SeparatedNSGA2(Algorithm):
    """
    Optimise a single or multi objective portfolio problem by optimising each site individually with NSGA-II.

    The site solutions are recombined into portfolio solutions as follows:
        1. Select a site's set of solutions as the "recombined" set.
        2. Select another site's set of solutions as the "incoming" set.
        3. Perform a dot product between the "recombined" and "incoming" sets to create a list of all feasible portfolio
           solutions.
        4. Pareto optimise the list of portfolios. This list now becomes the "recombined" set.
        5. Repeat steps 2-4 until all sites have been utilised.
    """

    def __init__(
        self,
        pop_size: int = 128,
        sampling: SamplingMethod = SamplingMethod.RANDOM,
        n_offsprings: int = 64,
        prob_crossover: float = 0.2,
        n_crossover: int = 2,
        prob_mutation: float = 0.9,
        std_scaler: float = 0.2,
        tol: float = 0.0001,
        period: int = 25,
        n_max_gen: int = 10000,
        n_max_evals: int = int(1e14),
        cv_tol: float = 1,
        cv_period: int = 10000,
        pop_size_incr_scalar: float = 0.1,
        pop_size_incr_threshold: float = 0.5,
        return_least_infeasible: bool = True,
    ):
        """
        Define NSGA2 hyperparameters.

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
        pop_size_incr_scalar
            Scalar value to increase the pop_size and n_offsprings by for the next generation when the number of
            optimal scenarios surpasses pop_size_incr_threshold percent of the pop_size.
        pop_size_incr_threshold
            Percent of the pop_size to set as the threshold to increase the pop_size.
        """
        self.return_least_infeasible = return_least_infeasible
        self.NSGA2_param = NSGA2HyperParam(
            pop_size=pop_size,
            n_offsprings=n_offsprings,
            prob_crossover=prob_crossover,
            n_crossover=n_crossover,
            prob_mutation=prob_mutation,
            std_scaler=std_scaler,
            tol=tol,
            period=period,
            cv_tol=cv_tol,
            cv_period=cv_period,
            n_max_gen=n_max_gen,
            n_max_evals=n_max_evals,
            sampling=sampling,
            pop_size_incr_scalar=pop_size_incr_scalar,
            pop_size_incr_threshold=pop_size_incr_threshold,
            return_least_infeasible=True,
        )

    def run(
        self,
        objectives: list[Metric],
        constraints: Constraints,
        portfolio: list[Site],
    ) -> OptimisationResult:
        """
        Run optimisation.

        Parameters
        ----------
        objectives
            Objectives to optimise.
        constraints
            Constraints on the metrics to apply.
        portfolio
            Portfolio of sites to optimise.

        Returns
        -------
        OptimisationResult
            solutions: Pareto-front of evaluated candidate portfolio solutions.
            exec_time: Time taken for optimisation process to conclude.
            n_evals: Number of simulation evaluations taken for optimisation process to conclude.
        """
        start_time = datetime.now(UTC)
        new_constraints = {}
        if Metric.capex in constraints:
            capex_limit = constraints[Metric.capex].get("max", None)
            if capex_limit is not None:
                new_constraints[Metric.capex] = Bounds(max=capex_limit)
        sub_solutions: list[list[PortfolioSolution]] = []
        n_evals = 0
        for site in portfolio:
            alg = NSGA2(**dict(self.NSGA2_param))
            res = alg.run(objectives=objectives, constraints=new_constraints, portfolio=[site])
            sub_solutions.append(res.solutions)
            n_evals += res.n_evals

        combined_solutions = sub_solutions[0]
        for sub_solution in sub_solutions[1:]:
            combined_solutions = merge_and_optimise_two_portfolio_solution_lists(
                combined_solutions, sub_solution, objectives, capex_limit
            )

        mask = is_in_constraints(constraints, combined_solutions)
        if any(mask) > 0:
            combined_solutions = np.array(combined_solutions)[mask].tolist()
        elif not self.return_least_infeasible and not any(mask):
            combined_solutions = [get_baseline_portfolio_solution(portfolio)]

        total_exec_time = datetime.now(UTC) - start_time

        return OptimisationResult(solutions=combined_solutions, n_evals=n_evals, exec_time=total_exec_time)


class SeparatedNSGA2xNSGA2(Algorithm):
    """
    Optimise a single or multi objective portfolio problem by first applying the SeparatedNSGA2 algorithm to the problem.

    This is followed by applying the NSGA2 algorithm to the problem with as starting population,
    the solutions from the SeparatedNSGA2 algorithm.

    This algorithm will perform better than either of its parts for extensive (many components) multi objective portfolio
    problems with more than 3 sites. This is because it leverages the fast execution time of the SeparatedNSGA2 algorithm to
    find "good enough" solutions which it refines with the NSGA2 algorithm.

    Note: If the problem doesn't have an upper CAPEX bound, the SeparatedNSGA2 will likely return the same results.
    """

    def __init__(self, SeparatedNSGA2_param: NSGA2HyperParam | None = None, NSGA2_param: NSGA2HyperParam | None = None):
        """
        Create the SeparatedNSGA2xNSGA2 optimiser.

        Parameters
        ----------
        SeparatedNSGA2_param
            Parameters for the separated part, as hyperparameters. Picks sensible defaults if not provided
        NSGA2_param
            Parameters for the NSGA2 part; picks sensible defaults if None.
        """
        if SeparatedNSGA2_param is None:
            SeparatedNSGA2_param = NSGA2HyperParam()
        if NSGA2_param is None:
            NSGA2_param = NSGA2HyperParam()
        self.SeparatedNSGA2_param = SeparatedNSGA2_param
        self.NSGA2_param = NSGA2_param

    def run(
        self,
        objectives: list[Metric],
        constraints: Constraints,
        portfolio: list[Site],
    ) -> OptimisationResult:
        """
        Run optimisation.

        Parameters
        ----------
        objectives
            Objectives to optimise.
        constraints
            Constraints on the metrics to apply.
        portfolio
            Portfolio of sites to optimise.

        Returns
        -------
        OptimisationResult
            solutions: Pareto-front of evaluated candidate portfolio solutions.
            exec_time: Time taken for optimisation process to conclude.
            n_evals: Number of simulation evaluations taken for optimisation process to conclude.
        """
        separatednsga2 = SeparatedNSGA2(**dict(self.SeparatedNSGA2_param))
        separatednsga2_res = separatednsga2.run(objectives=objectives, constraints=constraints, portfolio=portfolio)

        nsga2 = NSGA2(**dict(self.NSGA2_param))
        nsga2_res = nsga2.run(
            objectives=objectives, constraints=constraints, portfolio=portfolio, existing_solutions=separatednsga2_res.solutions
        )

        return OptimisationResult(
            solutions=nsga2_res.solutions,
            n_evals=separatednsga2_res.n_evals + nsga2_res.n_evals,
            exec_time=separatednsga2_res.exec_time + nsga2_res.exec_time,
        )
