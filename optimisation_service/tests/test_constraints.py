from app.internal.constraints import (
    apply_default_constraints,
    count_constraints,
    get_capex_constraints,
    get_shortfall_constraints,
    merge_constraints,
)
from app.models.constraints import Bounds, Constraints
from app.models.core import Site
from app.models.metrics import _METRICS, Metric


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


class TestGetShortfallConstraints:
    def test_good_inputs(self, default_site: Site):
        constraints = get_shortfall_constraints(site=default_site, heat_tolerance=0.01)
        assert constraints[Metric.total_electrical_shortfall]["max"] == 1
        assert constraints[Metric.total_heat_shortfall]["max"] >= 1


class TestGetCapexConstraints:
    def test_good_inputs(self):
        constraints = get_capex_constraints()
        assert constraints[Metric.capex]["min"] <= 1
        assert constraints[Metric.capex]["min"] >= 0


class TestApplyDefaultConstraints:
    def test_good_inputs(self, default_portfolio: list[Site], default_constraints: Constraints):
        portfolio, constraints = apply_default_constraints(
            exsiting_portfolio=default_portfolio, existing_constraints=default_constraints
        )
        assert constraints[Metric.capex]["min"] <= 1
        assert constraints[Metric.capex]["min"] > 0
        assert constraints[Metric.cost_balance]["min"] == 0
        for site in portfolio:
            assert site.constraints[Metric.total_electrical_shortfall]["max"] == 1
            assert site.constraints[Metric.total_heat_shortfall]["max"] >= 1


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
