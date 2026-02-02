from app.internal.bayesian.bayesian import split_into_sub_portfolios
from app.internal.bayesian.distributed_portfolio_optimiser import DistributedPortfolioOptimiser, select_starting_solutions
from app.models.constraints import Constraints
from app.models.core import Site
from app.models.metrics import Metric
from app.models.optimisers import NSGA2HyperParam
from app.models.result import PortfolioSolution

from .conftest import gen_dummy_portfolio_solutions


class TestDistributedPortfolioOptimiser:
    def test_init(
        self, default_portfolio: list[Site], default_constraints: Constraints, default_objectives: list[Metric]
    ) -> None:
        sub_portfolios = split_into_sub_portfolios(default_portfolio, 1)
        dpo = DistributedPortfolioOptimiser(
            sub_portfolios=sub_portfolios,
            objectives=default_objectives,
            constraints=default_constraints,
            NSGA2_param=NSGA2HyperParam(),
        )
        assert len(dpo.sub_portfolio_combinations) == len(sub_portfolios)
        assert len(dpo.sub_portfolio_solutions) == len(sub_portfolios)
        assert len(dpo.init_solutions) >= 1

    def test_evaluate(
        self, default_portfolio: list[Site], default_constraints: Constraints, default_objectives: list[Metric]
    ) -> None:
        sub_portfolios = split_into_sub_portfolios(default_portfolio, 1)
        dpo = DistributedPortfolioOptimiser(
            sub_portfolios=sub_portfolios,
            objectives=default_objectives,
            constraints=default_constraints,
            NSGA2_param=NSGA2HyperParam(),
        )
        dpo.evaluate([10000 for _ in default_portfolio])

    def test_merge_and_optimise_portfolio_solution_lists(
        self, default_portfolio: list[Site], default_constraints: Constraints, default_objectives: list[Metric]
    ) -> None:
        sub_portfolios = split_into_sub_portfolios(default_portfolio, 1)
        dpo = DistributedPortfolioOptimiser(
            sub_portfolios=sub_portfolios,
            objectives=default_objectives,
            constraints=default_constraints,
            NSGA2_param=NSGA2HyperParam(),
        )
        solutions = [gen_dummy_portfolio_solutions([site]) for site in default_portfolio]
        dpo.merge_and_optimise_portfolio_solution_lists(
            solutions=solutions, objectives=default_objectives, capex_limits=dpo.max_capexs, constraints=default_constraints
        )


class TestSelectStartingSolutions:
    def test_good_inputs(self, dummy_portfolio_solutions: list[PortfolioSolution]) -> None:
        select_starting_solutions(dummy_portfolio_solutions, {Metric.capex: {"max": 99999}})
