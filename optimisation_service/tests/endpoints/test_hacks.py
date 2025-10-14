# Test hack methods

from app.internal.hacks import extend_config_capex_limits_to_constraints
from app.models.core import Task
from app.models.metrics import Metric


class TestExtendConfigCapexLimitsToConstraints:
    def test_constraints_added(self, default_task: Task) -> None:
        """Check that constraints are correctly generated from config capex limits."""
        for site in default_task.portfolio:
            site.constraints = {}
            site.site_range.config.capex_limit = 12345
        extend_config_capex_limits_to_constraints(default_task.portfolio)

        assert all(site.constraints[Metric.capex]["max"] == 12345 for site in default_task.portfolio)
