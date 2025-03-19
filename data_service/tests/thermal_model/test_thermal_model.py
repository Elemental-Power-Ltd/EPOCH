"""Tests for the thermal model: static and dynamic heat loss, structure heat networks etc."""

import datetime

import numpy as np
import pytest

from app.internal.thermal_model import HeatNetwork, add_heating_system_to_graph, add_structure_to_graph, initialise_outdoors
from app.internal.thermal_model.building_elements import BuildingElement
from app.internal.thermal_model.heat_loss import (
    calculate_maximum_dynamic_heat_loss,
    calculate_maximum_static_heat_loss,
    calculate_maximum_static_heat_loss_breakdown,
)
from app.internal.thermal_model.matrix import interpolate_heating_power
from app.internal.thermal_model.network import create_simple_structure


@pytest.fixture
def test_structure() -> HeatNetwork:
    """Create a simple cube building to match the MCS calculations."""
    return create_simple_structure(
        wall_width=10, wall_height=5.0, window_area=1.0, floor_area=10 * 10, roof_area=10 * 10, air_volume=10 * 10 * 5
    )


class TestCreateHeatNetwork:
    """Test that we create heat networks with the right properties."""

    def test_create_structure_from_nothing(self) -> None:
        """Test that we can create a structure and that the steps are additive."""
        G = initialise_outdoors()
        G2 = add_structure_to_graph(G, wall_width=10, wall_height=5.0, window_area=1.0, floor_area=10 * 10, roof_area=10 * 10)
        G3 = add_heating_system_to_graph(G2, 70, 4)

        assert set(G.nodes) <= set(G2.nodes)
        assert set(G2.nodes) <= set(G3.nodes)

        for required_node in [
            BuildingElement.WallEast,
            BuildingElement.WallSouth,
            BuildingElement.WallNorth,
            BuildingElement.WallWest,
            BuildingElement.WindowsSouth,
            BuildingElement.WindowsNorth,
            BuildingElement.Floor,
            BuildingElement.Roof,
        ]:
            assert required_node in set(G3.nodes), f"Missing node {required_node}"

    def test_cant_add_two_structure(self) -> None:
        """Test that we can't add a structure twice."""
        G = initialise_outdoors()
        G2 = add_structure_to_graph(G, 10.0, 1.0, 50.0, 50.0)
        with pytest.raises(AssertionError):
            add_structure_to_graph(G2, 10.0, 1.0, 50.0, 50.0)

    def test_cant_add_heating_system_without_structure(self) -> None:
        """Test that a heating system can only be added after a building."""
        G = initialise_outdoors()
        with pytest.raises(AssertionError):
            add_heating_system_to_graph(G, 70, 4)

    def test_cant_add_two_heating_system(self) -> None:
        """Test that a building can only have one heating system."""
        G = initialise_outdoors()
        G2 = add_structure_to_graph(G, 10.0, 1.0, 50.0, 50.0)
        G3 = add_heating_system_to_graph(G2, 70, 4)
        with pytest.raises(AssertionError):
            add_heating_system_to_graph(G3, 70, 4)


class TestDynamicHeatLoss:
    """Test values and physical trends for dynamic heat loss calculations."""

    def test_reasonable(self, test_structure: HeatNetwork) -> None:
        """Test that we get a reasonable value of 4-6kW dynamic heat loss for this building."""
        static_heat_loss = calculate_maximum_static_heat_loss(test_structure, internal_temperature=21, external_temperature=-2)
        heat_loss = calculate_maximum_dynamic_heat_loss(test_structure, internal_temperature=21, external_temperature=-2)
        assert 0.5 * static_heat_loss > heat_loss > static_heat_loss

    def test_internal_temperature_range(self, test_structure: HeatNetwork) -> None:
        """Test that warmer indoors leads to a large dynamic heat loss."""
        heat_losses = [
            calculate_maximum_dynamic_heat_loss(test_structure, internal_temperature=internal_t, external_temperature=-2)
            for internal_t in [16, 18, 21, 22, 25]
        ]

        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as internal T increases"

    def test_external_temperature_range(self, test_structure: HeatNetwork) -> None:
        """Test that colder outdoors leads to a larger dynamic heat loss."""
        heat_losses = [
            calculate_maximum_dynamic_heat_loss(test_structure, internal_temperature=21.0, external_temperature=external_t)
            for external_t in [2, 0, -2, -4]
        ]

        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as external T decreases"

    def test_wall_size_increase(self) -> None:
        """Test that large buildings lose more dynamic heat."""
        heat_losses = []
        for wall_width in [5, 10, 15, 20]:
            G = create_simple_structure(
                wall_width=wall_width,
                wall_height=5.0,
                window_area=1.0,
                floor_area=10 * 10,
                roof_area=10 * 10,
                air_volume=10 * 10 * 5,
            )
            heat_losses.append(calculate_maximum_dynamic_heat_loss(G, internal_temperature=21.0, external_temperature=-2.0))

        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as the building gets large"

    def test_window_size_increase(self) -> None:
        """Test that larger windows lose more heat."""
        heat_losses = []
        for window_area in [1, 2, 3, 4, 5]:
            G = create_simple_structure(
                wall_width=10,
                wall_height=5.0,
                window_area=window_area,
                floor_area=10 * 10,
                roof_area=10 * 10,
                air_volume=10 * 10 * 5,
            )
            heat_losses.append(calculate_maximum_dynamic_heat_loss(G, internal_temperature=21.0, external_temperature=-2.0))
        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as the windows get larger"

    def test_roof_size_increase(self) -> None:
        """Test that larger roofs lose more heat."""
        heat_losses = []
        for roof_area in [5, 10, 15, 20]:
            G = create_simple_structure(
                wall_width=10, wall_height=5.0, window_area=1.0, floor_area=10 * 10, roof_area=roof_area, air_volume=10 * 10 * 5
            )
            heat_losses.append(calculate_maximum_dynamic_heat_loss(G, internal_temperature=21.0, external_temperature=-2.0))
        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as the roof gets larger"

    def test_floor_size_increase(self) -> None:
        """Test that larger floors lose more heat."""
        heat_losses = []
        for floor_area in [5, 10, 15, 20]:
            G = create_simple_structure(
                wall_width=10,
                wall_height=5.0,
                window_area=1.0,
                floor_area=floor_area,
                roof_area=10 * 10,
                air_volume=10 * 10 * 5,
            )
            heat_losses.append(calculate_maximum_dynamic_heat_loss(G, internal_temperature=21.0, external_temperature=-2.0))
        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as the floor gets larger"


class TestStaticHeatLoss:
    """Test values and physical trends for static heat loss calculations."""

    def test_reasonable(self, test_structure: HeatNetwork) -> None:
        """Test that we get a reasonable value of 10-12kW static heat loss for this building."""
        heat_loss = calculate_maximum_static_heat_loss(test_structure, internal_temperature=21, external_temperature=-2.3)
        assert heat_loss == pytest.approx(-10686.73)

    def test_breakdown_matches_mcs(self, test_structure: HeatNetwork) -> None:
        """Test that we get a reasonable value of 10-12kW static heat loss for this building."""
        heat_losses = calculate_maximum_static_heat_loss_breakdown(
            test_structure, internal_temperature=21, external_temperature=-2.3
        )

        walls = [BuildingElement.WallEast, BuildingElement.WallNorth, BuildingElement.WallWest, BuildingElement.WallSouth]
        windows = [
            # BuildingElement.WindowsEast,
            BuildingElement.WindowsNorth,
            # BuildingElement.WindowsWest,
            BuildingElement.WindowsSouth,
        ]
        assert sum(heat_losses[BuildingElement.InternalAir, wall] for wall in walls) == pytest.approx(-3653.44)
        assert heat_losses[BuildingElement.InternalAir, BuildingElement.Floor] == pytest.approx(-494.70)
        assert heat_losses[BuildingElement.InternalAir, BuildingElement.ExternalAir] == pytest.approx(-5766.75)
        assert heat_losses[BuildingElement.InternalAir, BuildingElement.Roof] == pytest.approx(-660.00)
        assert sum(heat_losses[BuildingElement.InternalAir, window] for window in windows) == pytest.approx(-111.84)
        assert {item[1] for item in heat_losses.keys()} == {
            *walls,
            *windows,
            BuildingElement.Floor,
            BuildingElement.Roof,
            BuildingElement.ExternalAir,
        }

    def test_internal_temperature_range(self) -> None:
        """Test that warmer indoors leads to a large static heat loss."""
        G = create_simple_structure(wall_height=10.0, wall_width=10.0, window_area=1.0, floor_area=20.0, roof_area=20.0)
        heat_losses = [
            calculate_maximum_static_heat_loss(G, internal_temperature=internal_t, external_temperature=-2)
            for internal_t in [16, 18, 21, 22, 25]
        ]

        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as internal T increases"

    def test_external_temperature_range(self) -> None:
        """Test that colder outdoors leads to a large static heat loss."""
        G = create_simple_structure(wall_height=10.0, wall_width=10.0, window_area=1.0, floor_area=20.0, roof_area=20.0)
        heat_losses = [
            calculate_maximum_static_heat_loss(G, internal_temperature=21.0, external_temperature=external_t)
            for external_t in [2, 0, -2, -4]
        ]

        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as external T decreases"

    def test_wall_size_increase(self) -> None:
        """Test that large buildings lose more heat."""
        heat_losses = []
        for wall_area in [5, 10, 15, 20]:
            G = create_simple_structure(
                wall_height=wall_area, wall_width=10.0, window_area=1.0, floor_area=20.0, roof_area=20.0
            )

            heat_losses.append(calculate_maximum_static_heat_loss(G, internal_temperature=21.0, external_temperature=-2.0))

        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as the building gets large"

    def test_window_size_increase(self) -> None:
        """Test that larger windows lose more heat."""
        heat_losses = []
        for window_area in [1, 2, 3, 4, 5]:
            G = create_simple_structure(
                wall_height=10.0, wall_width=10.0, window_area=window_area, floor_area=20.0, roof_area=20.0
            )

            heat_losses.append(calculate_maximum_static_heat_loss(G, internal_temperature=21.0, external_temperature=-2.0))
        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as the windows get larger"

    def test_roof_size_increase(self) -> None:
        """Test that larger roofs lose more heat."""
        heat_losses = []
        for roof_area in [5, 10, 15, 20]:
            G = create_simple_structure(
                wall_height=10.0, wall_width=10.0, window_area=1.0, floor_area=20.0, roof_area=roof_area
            )
            heat_losses.append(calculate_maximum_static_heat_loss(G, internal_temperature=21.0, external_temperature=-2.0))
        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as the roof gets larger"

    def test_floor_size_increase(self) -> None:
        """Test that larger floors lose more heat."""
        heat_losses = []
        for floor_area in [5, 10, 15, 20]:
            G = create_simple_structure(wall_height=10.0, wall_width=10.0, window_area=1.0, floor_area=floor_area)
            heat_losses.append(calculate_maximum_static_heat_loss(G, internal_temperature=21.0, external_temperature=-2.0))
        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as the floor gets larger"


class TestInterpolateHeatingPower:
    """Test the matrix time series solution approach from HEM."""

    def test_reasonable(self, test_structure: HeatNetwork) -> None:
        """Test that we get a reasonable value of 10-12kW static heat loss for this building."""
        heat_loss = (
            interpolate_heating_power(
                test_structure, internal_temperature=21, external_temperature=-2.3, dt=datetime.timedelta(days=1)
            )
            / datetime.timedelta(days=1).total_seconds()
        )
        assert heat_loss == pytest.approx(-5597.62)

    def test_internal_temperature_range(self) -> None:
        """Test that warmer indoors leads to a large static heat loss."""
        G = create_simple_structure(wall_height=10.0, wall_width=10.0, window_area=1.0, floor_area=20.0)
        heat_losses = [
            interpolate_heating_power(
                G, internal_temperature=internal_t, external_temperature=-2.3, dt=datetime.timedelta(days=1)
            )
            / datetime.timedelta(days=1).total_seconds()
            for internal_t in [16, 18, 21, 22, 25]
        ]

        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as internal T increases"

    def test_external_temperature_range(self) -> None:
        """Test that colder outdoors leads to a large static heat loss."""
        G = create_simple_structure(wall_height=10.0, wall_width=10.0, window_area=1.0, floor_area=20.0)
        heat_losses = [
            interpolate_heating_power(
                G, internal_temperature=21, external_temperature=external_t, dt=datetime.timedelta(days=1)
            )
            / datetime.timedelta(days=1).total_seconds()
            for external_t in [2, 0, -2, -4]
        ]

        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as external T decreases"

    def test_wall_size_increase(self) -> None:
        """Test that large buildings lose more heat."""
        heat_losses = []
        for wall_area in [5, 10, 15, 20]:
            G = create_simple_structure(wall_height=wall_area, wall_width=wall_area, window_area=5.0, floor_area=20.0)
            heat_losses.append(
                interpolate_heating_power(G, internal_temperature=21, external_temperature=-2.3, dt=datetime.timedelta(days=1))
                / datetime.timedelta(days=1).total_seconds()
            )

        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as the building gets large"

    def test_window_size_increase(self) -> None:
        """Test that larger windows lose more heat."""
        heat_losses = []
        for window_area in [1, 2, 3, 4, 5]:
            G = create_simple_structure(wall_height=10.0, wall_width=10.0, window_area=window_area, floor_area=20.0)
            heat_losses.append(
                interpolate_heating_power(G, internal_temperature=21, external_temperature=-2.3, dt=datetime.timedelta(days=1))
                / datetime.timedelta(days=1).total_seconds()
            )
        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as the windows get larger"

    def test_floor_size_increase(self) -> None:
        """Test that larger floors lose more heat."""
        heat_losses = []
        for floor_area in [5, 10, 15, 20]:
            G = create_simple_structure(
                wall_height=10.0, wall_width=10.0, window_area=1.0, roof_area=10.0, floor_area=floor_area
            )
            heat_losses.append(
                interpolate_heating_power(G, internal_temperature=21, external_temperature=-2.3, dt=datetime.timedelta(days=1))
                / datetime.timedelta(days=1).total_seconds()
            )
        assert all(np.ediff1d(heat_losses) < 0), "Heat losses must increase as the floor gets larger"

    def test_consistent_with_power(self, test_structure: HeatNetwork) -> None:
        """Test that different max heating powers lead to reasonably consistent required heating powers."""
        results = []
        for power in [1e3, 5e3, 1e4, 5e4, 1e5]:
            res = (
                interpolate_heating_power(
                    test_structure,
                    internal_temperature=21,
                    external_temperature=-2.3,
                    dt=datetime.timedelta(days=1),
                    max_heat_power=power,
                )
                / datetime.timedelta(days=1).total_seconds()
            )
            results.append(res)
        assert np.allclose(results, results[0])
