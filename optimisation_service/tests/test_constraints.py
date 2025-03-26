from app.internal.constraints import get_shortfall_constraints
from app.models.core import Site
from app.models.metrics import Metric


class TestGetShortfallConstraints:
    def test_good_inputs(self, default_portfolio: list[Site]):
        constraints = get_shortfall_constraints(portfolio=default_portfolio, heat_tolerance=0.01)
        assert constraints[Metric.total_electrical_shortfall]["max"] == 1
        assert constraints[Metric.total_heat_shortfall]["max"] >= 1
