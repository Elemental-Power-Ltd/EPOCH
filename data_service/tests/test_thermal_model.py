"""Tests for the non-endpoint thermal model code."""

# ruff: noqa: D101, D102
from copy import deepcopy

import pytest

from app.internal.heating.building_fabric import apply_thermal_model_fabric_interventions
from app.models.heating_load import InterventionEnum, ThermalModelResult


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
