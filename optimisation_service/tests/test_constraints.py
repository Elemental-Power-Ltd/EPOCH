import pytest
from app.internal.constraints import (
    apply_default_constraints,
    are_metrics_in_constraints,
    count_constraints,
    get_shortfall_constraints,
    is_in_constraints,
    merge_constraints,
    update_feasibility,
)
from app.internal.epoch.converters import simulation_result_to_metric_dict
from app.models.constraints import Bounds, Constraints
from app.models.core import Site
from app.models.database import site_id_t
from app.models.metrics import _METRICS, Metric, MetricValues
from app.models.result import PortfolioSolution

from .conftest import gen_dummy_sim_result


@pytest.fixture
def dummy_metric_values() -> MetricValues:
    sim_result = gen_dummy_sim_result()
    return simulation_result_to_metric_dict(sim_result)


class TestCountConstraints:
    def test_empty_constraints(self) -> None:
        assert count_constraints({}) == 0

    def test_min_constraints(self) -> None:
        constraints = {metric: Bounds(min=0) for metric in _METRICS}
        assert count_constraints(constraints) == len(_METRICS)

    def test_max_constraints(self) -> None:
        constraints = {metric: Bounds(max=10) for metric in _METRICS}
        assert count_constraints(constraints) == len(_METRICS)

    def test_min_and_max_constraints(self) -> None:
        constraints = {metric: Bounds(min=0, max=10) for metric in _METRICS}
        assert count_constraints(constraints) == len(_METRICS) * 2


class TestIsInConstraints:
    def test_empty_constraints(self, dummy_portfolio_solutions: list[PortfolioSolution]) -> None:
        mask = is_in_constraints(constraints={}, solutions=dummy_portfolio_solutions)
        assert sum(mask) == len(dummy_portfolio_solutions)

    def test_min_and_max_constraints(self, dummy_portfolio_solutions: list[PortfolioSolution]) -> None:
        for solution in dummy_portfolio_solutions:
            solution.metric_values[Metric.capex] = -10
        dummy_portfolio_solutions[0].metric_values[Metric.capex] = 10
        dummy_portfolio_solutions[1].metric_values[Metric.capex] = 30
        mask = is_in_constraints(constraints={Metric.capex: Bounds(min=0, max=20)}, solutions=dummy_portfolio_solutions)
        assert sum(mask) == 1

    def test_equal_to_constraints(self, dummy_portfolio_solutions: list[PortfolioSolution]) -> None:
        for solution in dummy_portfolio_solutions:
            solution.metric_values[Metric.capex] = 5
        dummy_portfolio_solutions[0].metric_values[Metric.capex] = 10
        dummy_portfolio_solutions[1].metric_values[Metric.capex] = 0
        mask = is_in_constraints(constraints={Metric.capex: Bounds(min=0, max=10)}, solutions=dummy_portfolio_solutions)
        assert sum(mask) == len(dummy_portfolio_solutions)

    def test_multiple_constraints(self, dummy_portfolio_solutions: list[PortfolioSolution]) -> None:
        constraints = {Metric.capex: Bounds(min=0), Metric.cost_balance: Bounds(max=20)}
        for solution in dummy_portfolio_solutions:
            solution.metric_values[Metric.capex] = -10
            solution.metric_values[Metric.cost_balance] = 10
        dummy_portfolio_solutions[0].metric_values[Metric.capex] = 10
        mask = is_in_constraints(constraints=constraints, solutions=dummy_portfolio_solutions)
        assert sum(mask) == 1


class TestGetShortfallConstraints:
    def test_good_inputs(self, default_site: Site) -> None:
        constraints = get_shortfall_constraints(site=default_site, heat_tolerance=0.01)
        assert constraints[Metric.total_electrical_shortfall]["max"] == 1
        assert constraints[Metric.total_heat_shortfall]["max"] >= 1
        assert constraints[Metric.total_ch_shortfall]["max"] >= 1
        assert constraints[Metric.total_dhw_shortfall]["max"] >= 1


class TestApplyDefaultConstraints:
    def test_good_inputs(self, default_portfolio: list[Site], default_constraints: Constraints) -> None:
        portfolio, _ = apply_default_constraints(existing_portfolio=default_portfolio, existing_constraints=default_constraints)
        for site in portfolio:
            assert site.constraints[Metric.total_electrical_shortfall]["max"] == 1
            assert site.constraints[Metric.total_heat_shortfall]["max"] >= 1
            assert site.constraints[Metric.total_ch_shortfall]["max"] >= 1
            assert site.constraints[Metric.total_dhw_shortfall]["max"] >= 1


class TestMergeConstrains:
    def test_min_merge(self) -> None:
        constraints_A = {Metric.capex: Bounds(min=5)}
        constraints_B = {Metric.capex: Bounds(min=10)}
        constraints_C = {Metric.capex: Bounds(min=0)}
        merged = merge_constraints([constraints_A, constraints_B, constraints_C])
        assert merged == {Metric.capex: Bounds(min=10)}

    def test_max_merge(self) -> None:
        constraints_A = {Metric.capex: Bounds(max=10)}
        constraints_B = {Metric.capex: Bounds(max=0)}
        constraints_C = {Metric.capex: Bounds(max=5)}
        merged = merge_constraints([constraints_A, constraints_B, constraints_C])
        assert merged == {Metric.capex: Bounds(max=0)}


class TestAreMetricsInConstraints:
    def test_empty_constraints(self, dummy_metric_values: MetricValues) -> None:
        constraints: Constraints = {}
        assert are_metrics_in_constraints(constraints=constraints, metric_values=dummy_metric_values)

    def test_min_and_max_constraints(self, dummy_metric_values: MetricValues) -> None:
        constraints = {Metric.capex: Bounds(min=0, max=20)}

        dummy_metric_values[Metric.capex] = 10
        assert are_metrics_in_constraints(constraints=constraints, metric_values=dummy_metric_values)

        dummy_metric_values[Metric.capex] = 30
        assert not are_metrics_in_constraints(constraints=constraints, metric_values=dummy_metric_values)

        dummy_metric_values[Metric.capex] = -10
        assert not are_metrics_in_constraints(constraints=constraints, metric_values=dummy_metric_values)

    def test_equal_to_constraints(self, dummy_metric_values: MetricValues) -> None:
        constraints = {Metric.capex: Bounds(min=0, max=10)}

        dummy_metric_values[Metric.capex] = 0
        assert are_metrics_in_constraints(constraints=constraints, metric_values=dummy_metric_values)

        dummy_metric_values[Metric.capex] = 10
        assert are_metrics_in_constraints(constraints=constraints, metric_values=dummy_metric_values)

        dummy_metric_values[Metric.capex] = -10
        assert not are_metrics_in_constraints(constraints=constraints, metric_values=dummy_metric_values)

    def test_multiple_constraints(self, dummy_metric_values: MetricValues) -> None:
        constraints = {Metric.capex: Bounds(min=0), Metric.cost_balance: Bounds(max=20)}

        dummy_metric_values[Metric.capex] = 10
        dummy_metric_values[Metric.cost_balance] = 10
        assert are_metrics_in_constraints(constraints=constraints, metric_values=dummy_metric_values)

        dummy_metric_values[Metric.capex] = -10
        dummy_metric_values[Metric.cost_balance] = 10
        assert not are_metrics_in_constraints(constraints=constraints, metric_values=dummy_metric_values)

        dummy_metric_values[Metric.capex] = 10
        dummy_metric_values[Metric.cost_balance] = 30
        assert not are_metrics_in_constraints(constraints=constraints, metric_values=dummy_metric_values)

        dummy_metric_values[Metric.capex] = -10
        dummy_metric_values[Metric.cost_balance] = 30
        assert not are_metrics_in_constraints(constraints=constraints, metric_values=dummy_metric_values)


class TestUpdateFeasibility:
    def test_empty_constraints(
        self,
        dummy_portfolio_solution: PortfolioSolution,
    ) -> None:
        site_constraints_dict: dict[site_id_t, Constraints] = {}
        constraints: Constraints = {}
        portfolio_solution = update_feasibility(
            site_constraints_dict=site_constraints_dict, constraints=constraints, portfolio_solution=dummy_portfolio_solution
        )

        assert portfolio_solution.is_feasible

    def test_feasible_solutions(
        self,
        dummy_portfolio_solution: PortfolioSolution,
    ) -> None:
        for site_name in dummy_portfolio_solution.scenario.keys():
            dummy_portfolio_solution.scenario[site_name].metric_values[Metric.capex] = 10
        dummy_portfolio_solution.metric_values[Metric.capex] = 10

        constraints = {Metric.capex: Bounds(max=100)}
        site_constraints_dict = {key: {Metric.capex: Bounds(max=100)} for key in dummy_portfolio_solution.scenario.keys()}

        portfolio_solution = update_feasibility(
            site_constraints_dict=site_constraints_dict, constraints=constraints, portfolio_solution=dummy_portfolio_solution
        )

        assert portfolio_solution.is_feasible

    def test_infeasible_site_solutions(self, dummy_portfolio_solution: PortfolioSolution) -> None:
        for site_name in dummy_portfolio_solution.scenario.keys():
            dummy_portfolio_solution.scenario[site_name].metric_values[Metric.capex] = 110
        dummy_portfolio_solution.metric_values[Metric.capex] = 10

        constraints = {Metric.capex: Bounds(max=100)}
        site_constraints_dict = {key: {Metric.capex: Bounds(max=100)} for key in dummy_portfolio_solution.scenario.keys()}

        portfolio_solution = update_feasibility(
            site_constraints_dict=site_constraints_dict, constraints=constraints, portfolio_solution=dummy_portfolio_solution
        )

        assert not portfolio_solution.is_feasible
        assert not any(site_solution.is_feasible for site_solution in portfolio_solution.scenario.values())

    def test_infeasible_portfolio_solution(self, dummy_portfolio_solution: PortfolioSolution) -> None:
        for site_name in dummy_portfolio_solution.scenario.keys():
            dummy_portfolio_solution.scenario[site_name].metric_values[Metric.capex] = 10
        dummy_portfolio_solution.metric_values[Metric.capex] = 110

        constraints = {Metric.capex: Bounds(max=100)}
        site_constraints_dict = {key: {Metric.capex: Bounds(max=100)} for key in dummy_portfolio_solution.scenario.keys()}

        portfolio_solution = update_feasibility(
            site_constraints_dict=site_constraints_dict, constraints=constraints, portfolio_solution=dummy_portfolio_solution
        )

        assert not portfolio_solution.is_feasible
        assert all(site_solution.is_feasible for site_solution in portfolio_solution.scenario.values())
