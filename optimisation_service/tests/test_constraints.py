from app.internal.constraints import (
    count_constraints,
    get_capex_constraints,
    get_default_constraints,
    get_shortfall_constraints,
    is_in_constraints,
    merge_constraints,
)
from app.models.constraints import Bounds
from app.models.core import Site
from app.models.metrics import _METRICS, Metric
from app.models.result import PortfolioSolution


class TestCountConstraints:
    def test_empty_constraints(self):
        assert count_constraints({}) == 0

    def test_min_constraints(self):
        constraints = {metric: Bounds(min=0) for metric in _METRICS}
        assert count_constraints(constraints) == len(_METRICS)

    def test_max_constraints(self):
        constraints = {metric: Bounds(max=10) for metric in _METRICS}
        assert count_constraints(constraints) == len(_METRICS)

    def test_min_and_max_constraints(self):
        constraints = {metric: Bounds(min=0, max=10) for metric in _METRICS}
        assert count_constraints(constraints) == len(_METRICS) * 2


class TestIsInConstraints:
    def test_empty_constraints(self, default_portfolio_solutions: list[PortfolioSolution]):
        mask = is_in_constraints(constraints={}, solutions=default_portfolio_solutions)
        assert sum(mask) == len(default_portfolio_solutions)

    def test_min_and_max_constraints(self, default_portfolio_solutions: list[PortfolioSolution]):
        for solution in default_portfolio_solutions:
            solution.metric_values[Metric.capex] = -10
        default_portfolio_solutions[0].metric_values[Metric.capex] = 10
        default_portfolio_solutions[1].metric_values[Metric.capex] = 30
        mask = is_in_constraints(constraints={Metric.capex: Bounds(min=0, max=20)}, solutions=default_portfolio_solutions)
        assert sum(mask) == 1

    def test_multiple_constraints(self, default_portfolio_solutions: list[PortfolioSolution]):
        constraints = {Metric.capex: Bounds(min=0), Metric.cost_balance: Bounds(max=20)}
        for solution in default_portfolio_solutions:
            solution.metric_values[Metric.capex] = -10
            solution.metric_values[Metric.cost_balance] = 10
        default_portfolio_solutions[0].metric_values[Metric.capex] = 10
        mask = is_in_constraints(constraints=constraints, solutions=default_portfolio_solutions)
        assert sum(mask) == 1


class TestGetShortfallConstraints:
    def test_good_inputs(self, default_portfolio: list[Site]):
        constraints = get_shortfall_constraints(portfolio=default_portfolio, heat_tolerance=0.01)
        assert constraints[Metric.total_electrical_shortfall]["max"] == 1
        assert constraints[Metric.total_heat_shortfall]["max"] >= 1


class TestGetCapexConstraints:
    def test_good_inputs(self):
        constraints = get_capex_constraints()
        assert constraints[Metric.capex]["min"] <= 1
        assert constraints[Metric.capex]["min"] >= 0


class TestGetDefaultConstraints:
    def test_good_inputs(self, default_portfolio: list[Site]):
        constraints = get_default_constraints(portfolio=default_portfolio)
        assert constraints[Metric.total_electrical_shortfall]["max"] == 1
        assert constraints[Metric.total_heat_shortfall]["max"] >= 1
        assert constraints[Metric.capex]["min"] <= 1
        assert constraints[Metric.capex]["min"] >= 0


class TestMergeConstrains:
    def test_min_merge(self):
        constraints_A = {Metric.capex: Bounds(min=5)}
        constraints_B = {Metric.capex: Bounds(min=10)}
        constraints_C = {Metric.capex: Bounds(min=0)}
        merged = merge_constraints([constraints_A, constraints_B, constraints_C])
        assert merged == {Metric.capex: Bounds(min=10)}

    def test_max_merge(self):
        constraints_A = {Metric.capex: Bounds(max=10)}
        constraints_B = {Metric.capex: Bounds(max=0)}
        constraints_C = {Metric.capex: Bounds(max=5)}
        merged = merge_constraints([constraints_A, constraints_B, constraints_C])
        assert merged == {Metric.capex: Bounds(max=0)}
