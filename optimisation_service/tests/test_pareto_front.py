from itertools import combinations

import pytest

from app.internal.pareto_front import merge_and_optimise_two_portfolio_solution_lists, portfolio_pareto_front
from app.models.core import Site
from app.models.metrics import _OBJECTIVES, Metric, MetricDirection

from .conftest import gen_dummy_portfolio_solution


class TestPortfolioParetoFront:
    @pytest.mark.parametrize(
        "objectives",
        [_OBJECTIVES] + [[metric] for metric in _OBJECTIVES],
    )
    def test_single_portfolio(self, objectives: list[Metric], default_portfolio: list[Site]) -> None:
        portfolio_solution = gen_dummy_portfolio_solution(default_portfolio)
        res = portfolio_pareto_front([portfolio_solution], objectives)
        assert res == [portfolio_solution]

    @pytest.mark.parametrize("objective", _OBJECTIVES)
    def test_single_objective(self, objective: Metric, default_portfolio: list[Site]) -> None:
        portfolio_solution_list = []
        for _ in range(4):
            portfolio_solution = gen_dummy_portfolio_solution(default_portfolio)
            portfolio_solution.metric_values[objective] = 10 * MetricDirection[objective]
            portfolio_solution_list.append(portfolio_solution)
        portfolio_solution = gen_dummy_portfolio_solution(default_portfolio)
        portfolio_solution.metric_values[objective] = 10 * -MetricDirection[objective]
        portfolio_solution_list.append(portfolio_solution)
        res = portfolio_pareto_front(portfolio_solution_list, [objective])
        assert res == [portfolio_solution]

    @pytest.mark.parametrize("objectives", list(combinations(_OBJECTIVES, 2)))
    def test_two_objectives(self, objectives: list[Metric], default_portfolio: list[Site]) -> None:
        non_optimal_list = []
        optimal_list = []
        for i in range(1, 6):
            portfolio_solution = gen_dummy_portfolio_solution(default_portfolio)
            portfolio_solution.metric_values[objectives[0]] = i * -MetricDirection[objectives[0]]
            portfolio_solution.metric_values[objectives[1]] = (6 - i) * -MetricDirection[objectives[1]]
            optimal_list.append(portfolio_solution)

        for i in range(2, 6):
            portfolio_solution = gen_dummy_portfolio_solution(default_portfolio)
            portfolio_solution.metric_values[objectives[0]] = i * -MetricDirection[objectives[0]]
            portfolio_solution.metric_values[objectives[1]] = (6 - i) * -MetricDirection[objectives[1]]
            non_optimal_list.append(portfolio_solution)

        portfolio_solution_list = optimal_list + non_optimal_list
        res = portfolio_pareto_front(portfolio_solution_list, objectives)
        assert res == optimal_list


class TestMergeAndOptimiseTwoPortfolioSolutionLists:
    def test_it_works(self, default_objectives: list[Metric], default_portfolio: list[Site]):
        site_names = [site.site_data.site_id for site in default_portfolio]
        portfolio_solutions_1 = [gen_dummy_portfolio_solution(default_portfolio) for _ in range(10)]
        for site in default_portfolio:
            site.site_data.site_id += "_2"
            site_names.append(site.site_data.site_id)
        portfolio_solutions_2 = [gen_dummy_portfolio_solution(default_portfolio) for _ in range(10)]
        pfs = merge_and_optimise_two_portfolio_solution_lists(portfolio_solutions_1, portfolio_solutions_2, default_objectives)
        assert len(pfs) >= 1
        for solution in pfs:
            assert all(site in solution.scenario.keys() for site in site_names)
