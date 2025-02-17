from itertools import combinations

import pytest

from app.internal.pareto_front import portfolio_pareto_front
from app.models.core import Site
from app.models.metrics import _METRICS, Metric, MetricDirection

from .conftest import dummy_portfolio_results


class TestPortfolioParetoFront:
    @pytest.mark.parametrize(
        "objectives",
        [_METRICS] + [[metric] for metric in _METRICS],
    )
    def test_single_portfolio(self, objectives: list[Metric], default_portfolio: list[Site]) -> None:
        portfolio_solution = dummy_portfolio_results(default_portfolio)
        res = portfolio_pareto_front([portfolio_solution], objectives)
        assert res == [portfolio_solution]

    @pytest.mark.parametrize("objective", _METRICS)
    def test_single_objective(self, objective: Metric, default_portfolio: list[Site]) -> None:
        portfolio_solution_list = []
        for _ in range(4):
            portfolio_solution = dummy_portfolio_results(default_portfolio)
            portfolio_solution.metric_values[objective] = 10 * MetricDirection[objective]
            portfolio_solution_list.append(portfolio_solution)
        portfolio_solution = dummy_portfolio_results(default_portfolio)
        portfolio_solution.metric_values[objective] = 10 * -MetricDirection[objective]
        portfolio_solution_list.append(portfolio_solution)
        res = portfolio_pareto_front(portfolio_solution_list, [objective])
        assert res == [portfolio_solution]

    @pytest.mark.parametrize("objectives", list(combinations(_METRICS, 2)))
    def test_two_objectives(self, objectives: list[Metric], default_portfolio: list[Site]) -> None:
        non_optimal_list = []
        optimal_list = []
        for i in range(1, 6):
            portfolio_solution = dummy_portfolio_results(default_portfolio)
            portfolio_solution.metric_values[objectives[0]] = i * -MetricDirection[objectives[0]]
            portfolio_solution.metric_values[objectives[1]] = (6 - i) * -MetricDirection[objectives[1]]
            optimal_list.append(portfolio_solution)

        for i in range(2, 6):
            portfolio_solution = dummy_portfolio_results(default_portfolio)
            portfolio_solution.metric_values[objectives[0]] = i * -MetricDirection[objectives[0]]
            portfolio_solution.metric_values[objectives[1]] = (6 - i) * -MetricDirection[objectives[1]]
            non_optimal_list.append(portfolio_solution)

        portfolio_solution_list = optimal_list + non_optimal_list
        res = portfolio_pareto_front(portfolio_solution_list, objectives)
        assert res == optimal_list
