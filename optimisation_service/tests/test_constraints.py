from app.internal.constraints import (
    get_capex_constraints,
    get_default_constraints,
    get_shortfall_constraints,
    merge_constraints,
)
from app.models.constraints import Bounds
from app.models.core import Site
from app.models.metrics import Metric


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
