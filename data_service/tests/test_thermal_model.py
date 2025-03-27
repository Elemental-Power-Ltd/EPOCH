"""Tests for the non-endpoint thermal model code."""

# ruff: noqa: D101, D102
from copy import deepcopy

import pytest

from app.internal.thermal_model import apply_fabric_interventions
from app.internal.thermal_model.building_fabric import apply_thermal_model_fabric_interventions
from app.internal.thermal_model.costs import calculate_intervention_costs_params
from app.models.heating_load import InterventionEnum, ThermalModelResult
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


class TestApplySavingsBait:
    def test_apply_no_savings(self, default_coefs: BaitAndModelCoefs) -> None:
        """Test that we can apply no savings at all."""
        assert apply_fabric_interventions(default_coefs, []) == default_coefs

    def test_doesnt_mutate_original(self, default_coefs: BaitAndModelCoefs) -> None:
        """Test that we don't mangle the original coefficients."""
        coefs = deepcopy(default_coefs)
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


class TestThermalModelInterventions:
    @pytest.fixture
    def initial_parameters(self) -> ThermalModelResult:
        """Reasonable physical parameters for the building."""
        return ThermalModelResult(scale_factor=1.0, ach=15.0, u_value=4.0, boiler_power=24e3, setpoint=21.0, dhw_usage=100.0)

    def test_unchanged_if_none(self, initial_parameters: ThermalModelResult) -> None:
        """Test that we get the same result if we apply no interventions."""
        stored_params = deepcopy(initial_parameters)
        new_params = apply_thermal_model_fabric_interventions(initial_parameters, [])
        assert new_params == stored_params

    def test_u_value_improves(self, initial_parameters: ThermalModelResult) -> None:
        """Test that we get an improvement if we do all interventions."""
        stored_params = deepcopy(initial_parameters)
        new_params = apply_thermal_model_fabric_interventions(
            initial_parameters, [InterventionEnum.Cladding, InterventionEnum.DoubleGlazing, InterventionEnum.Loft]
        )
        assert new_params.u_value < stored_params.u_value

    def test_cant_beat_brilliant(self, initial_parameters: ThermalModelResult) -> None:
        """Test that we don't make things worse."""
        initial_parameters.u_value = 0.1  # wow!
        stored_params = deepcopy(initial_parameters)
        new_params = apply_thermal_model_fabric_interventions(
            initial_parameters, [InterventionEnum.Cladding, InterventionEnum.DoubleGlazing, InterventionEnum.Loft]
        )
        assert new_params.u_value == stored_params.u_value

    @pytest.mark.parametrize("intervention", [InterventionEnum.Cladding, InterventionEnum.DoubleGlazing, InterventionEnum.Loft])
    def test_each_intervention_helps(self, initial_parameters: ThermalModelResult, intervention: InterventionEnum) -> None:
        """Test that the interventions all help one at a time."""
        stored_params = deepcopy(initial_parameters)
        new_params = apply_thermal_model_fabric_interventions(initial_parameters, [intervention])
        assert new_params.u_value < stored_params.u_value


class TestCosts:
    @pytest.fixture
    def initial_parameters(self) -> ThermalModelResult:
        """Reasonable physical parameters for the building."""
        return ThermalModelResult(scale_factor=1.0, ach=15.0, u_value=4.0, boiler_power=24e3, setpoint=21.0, dhw_usage=100.0)

    @pytest.mark.parametrize("intervention", [InterventionEnum.Cladding, InterventionEnum.DoubleGlazing, InterventionEnum.Loft])
    def test_each_intervention_costs(self, initial_parameters: ThermalModelResult, intervention: InterventionEnum) -> None:
        """Test that the interventions all help one at a time."""
        costs = calculate_intervention_costs_params(initial_parameters, [intervention])
        assert costs > 0

    def test_no_intervention_zero(self, initial_parameters: ThermalModelResult) -> None:
        """Test that zero interventions costs zero."""
        costs = calculate_intervention_costs_params(initial_parameters, [])
        assert costs == 0

    @pytest.mark.parametrize("intervention", [InterventionEnum.Cladding, InterventionEnum.DoubleGlazing, InterventionEnum.Loft])
    def test_each_intervention_costs_scale(
        self, initial_parameters: ThermalModelResult, intervention: InterventionEnum
    ) -> None:
        """Test that the interventions all help one at a time."""
        mid_cost = calculate_intervention_costs_params(initial_parameters, [intervention])
        initial_parameters.scale_factor *= 2
        high_cost = calculate_intervention_costs_params(initial_parameters, [intervention])
        initial_parameters.scale_factor /= 4
        low_cost = calculate_intervention_costs_params(initial_parameters, [intervention])
        assert low_cost < mid_cost < high_cost
