from typing import cast

import numpy as np

from app.internal.constraints import is_in_constraints
from app.internal.NSGA2 import NSGA2
from app.internal.pareto_front import merge_and_optimise_two_portfolio_solution_lists, portfolio_pareto_front
from app.models.constraints import Bounds, Constraints
from app.models.core import Site
from app.models.metrics import Metric
from app.models.optimisers import NSGA2HyperParam
from app.models.result import PortfolioSolution


class DistributedPortfolioOptimiser:
    """
    Optimise a portfolio that is split into N sub-portfolios for various CAPEX allocations.

    Each sub-portfolio is optimised individually with NSGA-II.
    """

    def __init__(
        self, sub_portfolios: list[list[Site]], objectives: list[Metric], constraints: Constraints, NSGA2_param: NSGA2HyperParam
    ):
        """
        Define the problem and NSGA-II algoritm and initialise the optimiser.

        Parameters
        ----------
        sub_portfolios
            A list of portfolios.
        objectives
            Metrics to optimise for.
        constraints
            Constraints to apply to the output metrics.
        NSGA2_param
            Hyperparameters for NSGA2 optimiser.
        """
        self.sub_portfolios = sub_portfolios
        self.objectives = objectives
        self.constraints = constraints
        self.NSGA2_param = NSGA2_param
        self.n_evals = 0
        # maintain a cache of solutions for each sub-portfolio
        self.sub_portfolio_solutions: list[set[PortfolioSolution]] = [set() for _ in sub_portfolios]
        # maintain a cache for each step in the sub-portfolio merging loop
        self.sub_portfolio_combinations: list[set[PortfolioSolution]] = [set() for _ in sub_portfolios]
        self.init_solutions, self.max_capexs = self._initialise()

    def _initialise(self) -> tuple[list[PortfolioSolution], list[float]]:
        """
        Initialise the optimiser by tackling the problem as if it were seperable.

        Returns
        -------
        solutions
            Portfolio solutions generated form initialisation of optimiser.
        max_capexs
            Maximum CAPEX per sub-portfolio.
        """
        capex_limit = self.constraints[Metric.capex]["max"]
        max_capexs = []
        sub_solutions: list[list[PortfolioSolution]] = []
        for sub_portfolio in self.sub_portfolios:
            alg = NSGA2(**dict(self.NSGA2_param))
            constraints = {Metric.capex: Bounds(max=capex_limit)}
            res = alg.run(objectives=self.objectives, constraints=constraints, portfolio=sub_portfolio)
            sub_solutions.append(res.solutions)
            self.n_evals += res.n_evals
            max_capex = 0.0
            for solution in res.solutions:
                max_capex = max(max_capex, solution.metric_values[Metric.capex])
            max_capexs.append(max_capex)

        capex_limits = [capex_limit] * len(self.sub_portfolios)
        solutions = self.merge_and_optimise_portfolio_solution_lists(
            sub_solutions, self.objectives, capex_limits, self.constraints
        )

        # update sub_portfolio_solutions
        for sub_portfolio_solution_list, new_sub_portfolio_solution_list in zip(
            self.sub_portfolio_solutions, sub_solutions, strict=False
        ):
            sub_portfolio_solution_list.update(set(new_sub_portfolio_solution_list))

        return solutions, max_capexs

    def evaluate(self, capex_limits: list[float]) -> list[PortfolioSolution]:
        """
        Evaluate a CAPEX allocation.

        Parameters
        ----------
        capex_limits
            A list of upper CAPEX bounds, one for each sub portfolio.

        Returns
        -------
        solutions
            A list of new (unseen before) optimal solutions.
        """
        sub_solutions: list[list[PortfolioSolution]] = []
        for i, capex_limit in enumerate(capex_limits):
            alg = NSGA2(**dict(self.NSGA2_param))
            constraints = {Metric.capex: Bounds(max=capex_limit)}
            selected_solutions = select_starting_solutions(
                existing_solutions=list(self.sub_portfolio_solutions[i]), constraints=constraints
            )
            if len(selected_solutions) > alg.algorithm.pop_size * 0.9:
                pop_to_offspring = alg.algorithm.n_offsprings / alg.algorithm.pop_size
                alg.algorithm.pop_size = int(len(selected_solutions) * 1.1)
                alg.algorithm.n_offsprings = int(pop_to_offspring * alg.algorithm.pop_size)
            res = alg.run(
                objectives=self.objectives,
                constraints=constraints,
                portfolio=self.sub_portfolios[i],
                existing_solutions=selected_solutions,
            )
            sub_solutions.append(res.solutions)
            self.n_evals += res.n_evals

        solutions = self.merge_and_optimise_portfolio_solution_lists(
            sub_solutions, self.objectives, capex_limits, self.constraints
        )

        # update sub_portfolio_solutions
        for sub_portfolio_solution_list, new_sub_portfolio_solution_list in zip(
            self.sub_portfolio_solutions, sub_solutions, strict=True
        ):
            sub_portfolio_solution_list.update(set(new_sub_portfolio_solution_list))

        return solutions

    def merge_and_optimise_portfolio_solution_lists(
        self,
        solutions: list[list[PortfolioSolution]],
        objectives: list[Metric],
        capex_limits: list[float],
        constraints: Constraints,
    ) -> list[PortfolioSolution]:
        """
        Merge and optimise a list of portfolio solution lists into a single portfolio solution Pareto-optimal front.

        Uses cached sub-portfolio solutions to avoid recomputing existing solutions.

        Parameters
        ----------
        solutions
            A list of portfolio solutions lists.
        objectives
            The objectives to optimise for.
        capex_limits
            CAPEX allocated to each sub-portfolio.
        constraints
            Constraints on the entire portfolio.

        Returns
        -------
        new_combinations
            Pareto optimal portfolio solutions.
        """
        combined_capex_limit = capex_limits[0]

        new_combinations = list(set(solutions[0]) - self.sub_portfolio_combinations[0])
        combinations_to_cache = [new_combinations]

        existing_combinations = list(self.sub_portfolio_combinations[0])
        mask = is_in_constraints(constraints={Metric.capex: Bounds(max=combined_capex_limit)}, solutions=existing_combinations)
        existing_combinations = np.array(existing_combinations)[mask].tolist()

        for i in range(1, len(solutions)):
            new_solutions = list(set(solutions[i]) - self.sub_portfolio_solutions[i])
            existing_solutions = list(self.sub_portfolio_solutions[i])
            mask = is_in_constraints(constraints={Metric.capex: Bounds(max=capex_limits[i])}, solutions=existing_solutions)
            existing_solutions = np.array(existing_solutions)[mask].tolist()

            if len(new_combinations) > 0 and len(new_solutions) > 0:
                new_combs_n_sols = merge_and_optimise_two_portfolio_solution_lists(new_combinations, new_solutions, objectives)
            else:
                new_combs_n_sols = []
            if len(new_combinations) > 0 and len(existing_solutions) > 0:
                new_combs_n_existing_sols = merge_and_optimise_two_portfolio_solution_lists(
                    new_combinations, existing_solutions, objectives
                )
            else:
                new_combs_n_existing_sols = []
            if len(new_solutions) > 0 and len(existing_combinations) > 0:
                existing_combs_n_new_sols = merge_and_optimise_two_portfolio_solution_lists(
                    existing_combinations, new_solutions, objectives
                )
            else:
                existing_combs_n_new_sols = []

            combined_capex_limit += capex_limits[i]

            new_combinations = new_combs_n_sols + new_combs_n_existing_sols + existing_combs_n_new_sols
            combinations_to_cache.append(new_combinations)

            existing_combinations = list(self.sub_portfolio_combinations[i])
            mask = is_in_constraints(
                constraints={Metric.capex: Bounds(max=combined_capex_limit)}, solutions=existing_combinations
            )
            existing_combinations = np.array(existing_combinations)[mask].tolist()

            if len(new_combinations) > 0:
                all_combinations = new_combinations + existing_combinations

                if i == len(solutions) - 1:
                    mask = is_in_constraints(constraints, all_combinations)
                    all_combinations = np.array(all_combinations)[mask].tolist()

                if len(all_combinations) > 0:
                    new_combinations = portfolio_pareto_front(all_combinations, objectives)
                else:
                    new_combinations = []

            new_combinations = list(set(new_combinations) - self.sub_portfolio_combinations[i])

        # update sub_portfolio_combinations
        for combination_set, new_combination_set in zip(self.sub_portfolio_combinations, combinations_to_cache, strict=False):
            combination_set.update(set(new_combination_set))

        return new_combinations


def select_starting_solutions(existing_solutions: list[PortfolioSolution], constraints: Constraints) -> list[PortfolioSolution]:
    """
    Select a set of solutions to use to initialise an algorithm with from a set of existing solutions.

    Parameters
    ----------
    existing_solutions
        Existing portfolio solutions to select from.
    constraints
        Constraints that selected solutions must respect.

    Returns
    -------
    selected_solutions
        A subset of the existing_solutions.
    """
    mask = is_in_constraints(constraints, existing_solutions)
    selected_solutions = np.array(existing_solutions)[mask].tolist()

    return cast(list[PortfolioSolution], selected_solutions)
