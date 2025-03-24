from app.internal.bayesian.bayesian import split_into_sub_portfolios
from app.internal.bayesian.distributed_portfolio_optimiser import DistributedPortfolioOptimiser, select_starting_solutions
from app.internal.NSGA2 import NSGA2
from app.models.core import Site
from app.models.metrics import Metric
from app.models.result import PortfolioSolution

from .conftest import dummy_portfolio_solutions


class TestDistributedPortfolioOptimiser:
    def test_init(self, default_portfolio: list[Site], default_constraints: list[Site], default_objectives: list[Metric]):
        alg = NSGA2(pop_size=256, n_offsprings=128)
        sub_portfolios = split_into_sub_portfolios(default_portfolio, 1)
        dpo = DistributedPortfolioOptimiser(
            sub_portfolios=sub_portfolios,
            objectives=default_objectives,
            alg=alg,
            constraints=default_constraints,
        )
        assert len(dpo.sub_portfolio_combinations) == len(default_portfolio)
        assert len(dpo.sub_portfolio_solutions) == len(default_portfolio)
        assert len(dpo.init_solutions) >= 1

    def test_evaluate(self, default_portfolio: list[Site], default_constraints: list[Site], default_objectives: list[Metric]):
        alg = NSGA2(pop_size=256, n_offsprings=128)
        sub_portfolios = split_into_sub_portfolios(default_portfolio, 1)
        dpo = DistributedPortfolioOptimiser(
            sub_portfolios=sub_portfolios,
            objectives=default_objectives,
            alg=alg,
            constraints=default_constraints,
        )
        dpo.evaluate([10000 for _ in default_portfolio])

    def test_merge_and_optimise_portfolio_solution_lists(
        self, default_portfolio: list[Site], default_constraints: list[Site], default_objectives: list[Metric]
    ):
        alg = NSGA2(pop_size=256, n_offsprings=128)
        sub_portfolios = split_into_sub_portfolios(default_portfolio, 1)
        dpo = DistributedPortfolioOptimiser(
            sub_portfolios=sub_portfolios,
            objectives=default_objectives,
            alg=alg,
            constraints=default_constraints,
        )
        solutions = [dummy_portfolio_solutions([site]) for site in default_portfolio]
        dpo.merge_and_optimise_portfolio_solution_lists(solutions, default_objectives)


class TestSelectStartingSolutions:
    def test_good_inputs(self, default_portfolio_solutions: list[PortfolioSolution], default_objectives: list[Metric]):
        select_starting_solutions(default_portfolio_solutions, {Metric.capex: {"max": 99999}}, default_objectives, 2)
