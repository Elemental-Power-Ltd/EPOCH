import numpy as np

from app.internal.constraints import is_in_constraints
from app.internal.NSGA2 import NSGA2
from app.internal.pareto_front import merge_and_optimise_two_portfolio_solution_lists, portfolio_pareto_front
from app.models.constraints import Bounds, Constraints
from app.models.core import Site
from app.models.metrics import Metric
from app.models.result import PortfolioSolution


class DistributedPortfolioOptimiser:
    """
    Splits a portfolio into sub portfolios of N sites.
    Can then be used to evaluate the portfolio for a given allocation of
    """

    def __init__(self, sub_portfolios: list[list[Site]], objectives: list[Metric], alg: NSGA2, constraints: Constraints):
        self.sub_portfolios = sub_portfolios
        self.objectives = objectives
        self.constraints = constraints
        self.alg = alg
        self.n_evals = 0
        self.init_solutions, self.max_capexs = self._initialise()

    def _initialise(self) -> list[PortfolioSolution]:
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
            res = self.alg.run(
                objectives=self.objectives, constraints={Metric.capex: {"max": capex_limit}}, portfolio=sub_portfolio
            )
            max_capex = 0
            for solution in res.solutions:
                if solution.metric_values[Metric.capex] > max_capex:
                    max_capex = solution.metric_values[Metric.capex]
            max_capexs.append(max_capex)
            sub_solutions.append(res.solutions)
            self.n_evals += res.n_evals

        self.sub_portfolio_solutions = [set(sub_portfolio) for sub_portfolio in sub_solutions]

        solutions = sub_solutions[0]
        self.sub_portfolio_combinations = [set(solutions)]
        for sub_solution in sub_solutions[1:]:
            solutions = merge_and_optimise_two_portfolio_solution_lists(solutions, sub_solution, self.objectives, capex_limit)
            self.sub_portfolio_combinations.append(set(solutions))

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
            constraints = {Metric.capex: Bounds(max=capex_limit)}
            selected_solutions = select_starting_solutions(
                existing_solutions=list(self.sub_portfolio_solutions[i]),
                constraints=constraints,
                objectives=self.objectives,
                n_select=self.alg.algorithm.pop_size,
            )
            res = self.alg.run(
                objectives=self.objectives,
                constraints=constraints,
                portfolio=self.sub_portfolios[i],
                existing_solutions=selected_solutions,
            )
            sub_solutions.append(res.solutions)
            self.n_evals += res.n_evals

        solutions, new_sub_portfolio_combinations = self.merge_and_optimise_portfolio_solution_lists(
            sub_solutions, self.objectives, capex_limits
        )
        # update sub_portfolio_solutions
        for sub_portfolio_solution_list, new_sub_portfolio_solution_list in zip(self.sub_portfolio_solutions, sub_solutions):
            sub_portfolio_solution_list.update(set(new_sub_portfolio_solution_list))

        # remove already visited solutions
        solutions = list(set(solutions) - self.sub_portfolio_combinations[-1])

        # update sub_portfolio_combinations
        for combination_set, new_combination_set in zip(self.sub_portfolio_combinations, new_sub_portfolio_combinations):
            combination_set.update(set(new_combination_set))

        mask = is_in_constraints(self.constraints, solutions)

        solutions = np.array(solutions)[mask].tolist()

        return solutions

    def merge_and_optimise_portfolio_solution_lists(
        self,
        solutions: list[list[PortfolioSolution]],
        objectives: list[Metric],
        capex_limits: list[float],
    ) -> tuple[list[PortfolioSolution], list[list[PortfolioSolution]]]:
        """
        Merge and optimise a list of portfolio solution lists into a single portfolio solution Pareto-optimal front.

        Parameters
        ----------
        solutions
            A list of portfolio solutions lists.
        objectives
            The objectives to optimise for.

        Returns
        -------
        new_solutions

        """
        new_solutions = solutions[0]
        combined_capex_limit = capex_limits[0]
        new_combinations = [new_solutions]
        for i in range(1, len(solutions)):
            new_solutions_combined = list(set(new_solutions) - self.sub_portfolio_combinations[i - 1])
            old_solutions_combined = list(self.sub_portfolio_combinations[i - 1])

            mask = is_in_constraints(
                constraints={Metric.capex: Bounds(max=combined_capex_limit)}, solutions=old_solutions_combined
            )
            old_solutions_combined = np.array(old_solutions_combined)[mask].tolist()

            new_solutions_incoming = list(set(solutions[i]) - self.sub_portfolio_solutions[i])
            old_solutions_incoming = list(self.sub_portfolio_solutions[i])

            mask = is_in_constraints(constraints={Metric.capex: Bounds(max=capex_limits[i])}, solutions=old_solutions_incoming)
            old_solutions_incoming = np.array(old_solutions_incoming)[mask].tolist()

            if len(new_solutions_combined) > 0 and len(new_solutions_incoming) > 0:
                new_new = merge_and_optimise_two_portfolio_solution_lists(
                    new_solutions_combined, new_solutions_incoming, objectives
                )
            else:
                new_new = []
            if len(new_solutions_combined) > 0 and len(old_solutions_incoming) > 0:
                new_old = merge_and_optimise_two_portfolio_solution_lists(
                    new_solutions_combined, old_solutions_incoming, objectives
                )
            else:
                new_old = []
            if len(new_solutions_incoming) > 0 and len(old_solutions_combined) > 0:
                old_new = merge_and_optimise_two_portfolio_solution_lists(
                    old_solutions_combined, new_solutions_incoming, objectives
                )
            else:
                old_new = []

            new_solutions = new_new + new_old + old_new
            combined_capex_limit += capex_limits[i]

            existing_combinations = list(self.sub_portfolio_combinations[i])
            mask = is_in_constraints(
                constraints={Metric.capex: Bounds(max=combined_capex_limit)}, solutions=existing_combinations
            )
            existing_combinations = np.array(existing_combinations)[mask].tolist()

            if len(new_solutions) > 0:
                new_solutions = portfolio_pareto_front(new_solutions + existing_combinations, objectives)

            new_combinations.append(new_solutions)

        return new_solutions, new_combinations


def select_starting_solutions(
    existing_solutions: list[PortfolioSolution], constraints: Constraints, objectives: list[Metric], n_select: int
) -> list[PortfolioSolution]:
    """
    Select a set of solutions to use to initialise an algorithm with from a set of existing solutions.

    Parameters
    ---------
    existing_solutions
        Existing portfolio solutions to select from.
    constraints
        Constraints that selected solutions must respect.
    objectives
        Objectives to prioritise solutions for.
    n_select
        Number of solutions to select.
        If len(existing_solutions) < n_select, all existing_solutions within constraints are returned.

    Returns
    -------
    selected_solutions
        A subset of the existing_solutions.
    """
    rng = np.random.default_rng()
    mask = is_in_constraints(constraints, existing_solutions)
    selected_solutions = np.array(existing_solutions)[mask].tolist()
    if len(selected_solutions) > 0:
        if len(selected_solutions) > n_select:
            selected_solutions = portfolio_pareto_front(selected_solutions, objectives)  # select pareto-front
            if len(selected_solutions) > n_select:  # cut down if too many
                selected_solutions = rng.choice(selected_solutions, n_select, replace=False)
            elif len(selected_solutions) < n_select:  # random fill if pareto-front is smaller than pop-size
                selected_solutions = np.concatenate(
                    [
                        selected_solutions,
                        rng.choice(
                            existing_solutions,  # type: ignore
                            min(n_select - len(selected_solutions), len(existing_solutions)),
                            replace=False,
                        ),
                    ]
                )
        return selected_solutions

    return []
