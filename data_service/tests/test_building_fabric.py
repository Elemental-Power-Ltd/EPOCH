"""Tests for the currently janky building fabric savings."""

# ruff: noqa: D101
import copy

import pytest
from app.internal.thermal_model import apply_fabric_interventions
from app.models.heating_load import InterventionEnum
from app.models.weather import BaitAndModelCoefs


@pytest.fixture
def default_coefs() -> BaitAndModelCoefs:
    """Get some sensible default coefficients for the BAIT model."""
    return BaitAndModelCoefs(
        solar_gain=0.012,
        wind_chill=-0.20,
        humidity_discomfort=-0.05,
        smoothing=0.5,
        threshold=15.5,
        heating_kwh=1.0,
        dhw_kwh=1.0,
        r2_score=1.0,
    )


class TestApplySavings:
    def test_apply_no_savings(self, default_coefs: BaitAndModelCoefs) -> None:
        """Test that we can apply no savings at all."""
        assert apply_fabric_interventions(default_coefs, []) == default_coefs

    def test_doesnt_mutate_original(self, default_coefs: BaitAndModelCoefs) -> None:
        """Test that we don't mangle the original coefficients."""
        coefs = copy.deepcopy(default_coefs)
        mutated = apply_fabric_interventions(coefs, [InterventionEnum.Loft])
        assert mutated != coefs
        assert coefs == default_coefs

    def test_can_apply_many_in_sequence(self, default_coefs: BaitAndModelCoefs) -> None:
        """Test that we can apply multiple interventions after one another."""
        after_loft = apply_fabric_interventions(default_coefs, [InterventionEnum.Loft])
        after_loft_and_windows = apply_fabric_interventions(after_loft, [InterventionEnum.DoubleGlazing])
        assert after_loft.heating_kwh < default_coefs.heating_kwh
        assert after_loft_and_windows.heating_kwh < after_loft.heating_kwh

    def test_can_apply_many_in_parallel(self, default_coefs: BaitAndModelCoefs) -> None:
        """Test that we can apply multiple interventions after one another."""
        after_loft = apply_fabric_interventions(default_coefs, [InterventionEnum.Loft])
        after_loft_and_windows = apply_fabric_interventions(
            default_coefs, [InterventionEnum.Loft, InterventionEnum.DoubleGlazing]
        )
        assert after_loft.heating_kwh < default_coefs.heating_kwh
        assert after_loft_and_windows.heating_kwh < after_loft.heating_kwh
