from app.internal.constraints import count_constraints, is_in_constraints
from app.models.constraints import Bounds
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
