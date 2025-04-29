"""Tests to make sure we can serialize old versions of TaskData stored in the database."""

import pydantic
import pytest

from app.models.epoch_types.task_data_type import Building


def test_building_serialization() -> None:
    """Test we can serialize a normal building model."""
    data = {
        "scalar_heat_load": 1.0,
        "scalar_electrical_load": 2.0,
        "fabric_intervention_index": 3
    }

    building = Building.model_validate(data)

    assert building.scalar_heat_load == 1.0
    assert building.scalar_electrical_load == 2.0
    assert building.fabric_intervention_index == 3


def test_building_without_heat_load_serialization() -> None:
    """Test that a building without a heat load uses the default scalar_heat_load."""
    data = {
        "scalar_electrical_load": 1.0,
        "fabric_intervention_index": 0
    }

    building = Building.model_validate(data)

    assert building.scalar_heat_load == 1.0


def test_building_with_unknown_parameter_serialization() -> None:
    """Test that a building with an unknown parameter serializes without that parameter."""
    data = {
        "scalar_heat_load": 1.0,
        "scalar_electrical_load": 1.0,
        "fabric_intervention_index": 0,
        "some_deprecated_parameter": 5
    }

    building = Building.model_validate(data)

    assert not hasattr(building, "some_deprecated_parameter")


def test_building_with_none_serialization() -> None:
    """Test that we don't accept None for parameter values."""
    data = {
        "scalar_heat_load": 1.0,
        "scalar_electrical_load": None,
        "fabric_intervention_index": 3
    }

    with pytest.raises(pydantic.ValidationError):
        _ = Building.model_validate(data)


def test_building_with_null_serialization() -> None:
    """Test that we don't accept null for parameter values."""
    data = '''{
        "scalar_heat_load": 1.0,
        "scalar_electrical_load": null,
        "fabric_intervention_index": 3
    }'''

    with pytest.raises(pydantic.ValidationError):
        _ = Building.model_validate_json(data)
