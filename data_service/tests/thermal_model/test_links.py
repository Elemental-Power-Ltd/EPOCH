"""Test that the individual thermal link elements behave reasonably."""

# ruff: noqa: D101
from collections.abc import Callable

import pytest
from app.internal.thermal_model.links import (
    ConductiveLink,
    ConvectiveLink,
    RadiativeLink,
    ThermalNodeAttrDict,
    ThermalRadiativeLink,
)


@pytest.fixture
def basic_link() -> ConductiveLink:
    """Fixture providing a basic ConductiveLink instance."""
    return ConductiveLink(interface_area=1.0, heat_transfer=1.0)


@pytest.fixture
def node_attrs_factory() -> Callable[[float], ThermalNodeAttrDict]:
    """Fixture providing a factory function for node attributes."""

    def create_attrs(temp: float) -> ThermalNodeAttrDict:
        return {"temperature": temp, "energy_change": 0.0, "thermal_mass": 100.0}

    return create_attrs


class TestConductiveLink:
    def test_conductive_link_initialization(self) -> None:
        """Test that ConductiveLink initializes with correct attributes."""
        link = ConductiveLink(interface_area=2.0, heat_transfer=5.0)
        assert link.interface_area == 2.0
        assert link.heat_transfer == 5.0

    def test_conductive_link_repr(self) -> None:
        """Test the string representation of ConductiveLink."""
        link = ConductiveLink(interface_area=2.0, heat_transfer=5.0)
        expected = "ConductiveLink(interface_area=2.0, heat_transfer=5.0)"
        assert repr(link) == expected

    def test_heat_flow_hot_to_cold(
        self, basic_link: ConductiveLink, node_attrs_factory: Callable[[float], ThermalNodeAttrDict]
    ) -> None:
        """Test heat flows from hot to cold body."""
        hot_attrs = node_attrs_factory(300.0)  # 300K
        cold_attrs = node_attrs_factory(280.0)  # 280K
        dt = 1.0  # 1 second

        energy_change = basic_link.step(cold_attrs, hot_attrs, dt)

        # Energy should flow from hot to cold (negative when flowing from v to u)
        assert energy_change < 0
        # Energy loss in hot body should equal energy gain in cold body
        assert abs(hot_attrs["energy_change"]) == abs(cold_attrs["energy_change"])
        assert hot_attrs["energy_change"] == -cold_attrs["energy_change"]
        # Hot body should lose energy (negative energy_change)
        assert hot_attrs["energy_change"] < 0
        # Cold body should gain energy (positive energy_change)
        assert cold_attrs["energy_change"] > 0

    def test_heat_flow_cold_to_hot(
        self, basic_link: ConductiveLink, node_attrs_factory: Callable[[float], ThermalNodeAttrDict]
    ) -> None:
        """Test heat flows from hot to cold body even when positions are swapped."""
        hot_attrs = node_attrs_factory(300.0)
        cold_attrs = node_attrs_factory(280.0)
        dt = 1.0

        energy_change = basic_link.step(hot_attrs, cold_attrs, dt)

        # Energy should flow from hot to cold (positive when flowing from u to v)
        assert energy_change > 0
        # Energy loss in hot body should equal energy gain in cold body
        assert abs(hot_attrs["energy_change"]) == abs(cold_attrs["energy_change"])
        assert hot_attrs["energy_change"] == -cold_attrs["energy_change"]
        # Hot body should lose energy (negative energy_change)
        assert hot_attrs["energy_change"] < 0
        # Cold body should gain energy (positive energy_change)
        assert cold_attrs["energy_change"] > 0

    def test_no_heat_flow_equal_temps(
        self, basic_link: ConductiveLink, node_attrs_factory: Callable[[float], ThermalNodeAttrDict]
    ) -> None:
        """Test that no heat flows when temperatures are equal."""
        temp = 300.0
        attrs1 = node_attrs_factory(temp)
        attrs2 = node_attrs_factory(temp)
        dt = 1.0

        energy_change = basic_link.step(attrs1, attrs2, dt)

        assert energy_change == 0.0
        assert attrs1["energy_change"] == 0.0
        assert attrs2["energy_change"] == 0.0

    def test_energy_flow_proportional_to_dt(
        self, basic_link: ConductiveLink, node_attrs_factory: Callable[[float], ThermalNodeAttrDict]
    ) -> None:
        """Test that energy flow scales linearly with time step."""
        hot_attrs = node_attrs_factory(300.0)
        cold_attrs = node_attrs_factory(280.0)

        # Test with dt = 1.0
        energy_1s = basic_link.step(cold_attrs, hot_attrs, dt=1.0)

        # Reset energy changes
        hot_attrs["energy_change"] = 0.0
        cold_attrs["energy_change"] = 0.0

        # Test with dt = 2.0
        energy_2s = basic_link.step(cold_attrs, hot_attrs, dt=2.0)

        # Energy transfer should double with double the time
        assert pytest.approx(energy_2s, rel=1e-10) == 2 * energy_1s

    def test_energy_flow_proportional_to_area(self, node_attrs_factory: Callable[[float], ThermalNodeAttrDict]) -> None:
        """Test that energy flow scales linearly with interface area."""
        # Create two links with different areas
        link1 = ConductiveLink(interface_area=1.0, heat_transfer=1.0)
        link2 = ConductiveLink(interface_area=2.0, heat_transfer=1.0)

        hot_attrs1 = node_attrs_factory(300.0)
        cold_attrs1 = node_attrs_factory(280.0)
        hot_attrs2 = node_attrs_factory(300.0)
        cold_attrs2 = node_attrs_factory(280.0)

        energy1 = link1.step(cold_attrs1, hot_attrs1, dt=1.0)
        energy2 = link2.step(cold_attrs2, hot_attrs2, dt=1.0)

        # Energy transfer should double with double the area
        assert pytest.approx(energy2, rel=1e-10) == 2 * energy1


class TestRadiativeLink:
    def test_initialization(self) -> None:
        """Test that RadiativeLink initializes with correct power."""
        link = RadiativeLink(power=100.0)
        assert link.power == 100.0

    def test_repr(self) -> None:
        """Test the string representation of RadiativeLink."""
        link = RadiativeLink(power=100.0)
        expected = "RadiativeLink(power=100.0)"
        assert repr(link) == expected

    def test_energy_transfer_direction(self, node_attrs_factory: Callable[[float], ThermalNodeAttrDict]) -> None:
        """Test that energy always flows from u to v regardless of temperature."""
        link = RadiativeLink(power=100.0)

        # Test with v hotter than u
        u_attrs = node_attrs_factory(280.0)
        v_attrs = node_attrs_factory(300.0)
        dt = 1.0

        energy_change = link.step(u_attrs, v_attrs, dt)

        # Energy should flow from u to v
        assert energy_change > 0
        assert u_attrs["energy_change"] < 0
        assert v_attrs["energy_change"] > 0

        # Energy conservation
        assert abs(u_attrs["energy_change"]) == abs(v_attrs["energy_change"])

    def test_energy_transfer_independence_from_temperature(
        self, node_attrs_factory: Callable[[float], ThermalNodeAttrDict]
    ) -> None:
        """Test that energy transfer is independent of node temperatures."""
        link = RadiativeLink(power=100.0)
        dt = 1.0

        # Test with different temperature combinations
        temp_pairs = [
            (280.0, 300.0),  # Cold to hot
            (300.0, 280.0),  # Hot to cold
            (300.0, 300.0),  # Equal temperatures
            (0.0, 100.0),  # Extreme difference
        ]

        expected_energy = link.power * dt

        for u_temp, v_temp in temp_pairs:
            u_attrs = node_attrs_factory(u_temp)
            v_attrs = node_attrs_factory(v_temp)

            energy_change = link.step(u_attrs, v_attrs, dt)

            assert energy_change == pytest.approx(expected_energy)
            assert u_attrs["energy_change"] == pytest.approx(-expected_energy)
            assert v_attrs["energy_change"] == pytest.approx(expected_energy)

    def test_energy_transfer_scales_with_time(self, node_attrs_factory: Callable[[float], ThermalNodeAttrDict]) -> None:
        """Test that energy transfer scales linearly with time step."""
        link = RadiativeLink(power=100.0)
        u_attrs = node_attrs_factory(300.0)
        v_attrs = node_attrs_factory(280.0)

        # Test with different time steps
        time_steps = [0.5, 1.0, 2.0, 5.0]
        base_energy = link.power * 1.0  # Energy transfer for 1 second

        for dt in time_steps:
            # Reset energy changes
            u_attrs["energy_change"] = 0.0
            v_attrs["energy_change"] = 0.0

            energy_change = link.step(u_attrs, v_attrs, dt)
            expected_energy = base_energy * dt

            assert energy_change == pytest.approx(expected_energy)
            assert u_attrs["energy_change"] == pytest.approx(-expected_energy)
            assert v_attrs["energy_change"] == pytest.approx(expected_energy)

    def test_zero_power_transfer(self, node_attrs_factory: Callable[[float], ThermalNodeAttrDict]) -> None:
        """Test that zero power results in no energy transfer."""
        link = RadiativeLink(power=0.0)
        u_attrs = node_attrs_factory(300.0)
        v_attrs = node_attrs_factory(280.0)
        dt = 1.0

        energy_change = link.step(u_attrs, v_attrs, dt)

        assert energy_change == 0.0
        assert u_attrs["energy_change"] == 0.0
        assert v_attrs["energy_change"] == 0.0

    def test_negative_power_transfer(self, node_attrs_factory: Callable[[float], ThermalNodeAttrDict]) -> None:
        """Test that negative power reverses the direction of energy flow."""
        link = RadiativeLink(power=-100.0)
        u_attrs = node_attrs_factory(300.0)
        v_attrs = node_attrs_factory(280.0)
        dt = 1.0

        energy_change = link.step(u_attrs, v_attrs, dt)

        assert energy_change < 0
        assert u_attrs["energy_change"] > 0
        assert v_attrs["energy_change"] < 0
        assert abs(u_attrs["energy_change"]) == abs(v_attrs["energy_change"])


class TestThermalRadiativeLink:
    @pytest.fixture
    def basic_link(self) -> ThermalRadiativeLink:
        """Create a basic thermal radiative link with default parameters."""
        return ThermalRadiativeLink(power=1000.0)  # 1kW radiator

    def test_initialization(self) -> None:
        """Test initialization with various parameters."""
        # Test with default delta_t
        link1 = ThermalRadiativeLink(power=1000.0)
        assert link1.power == 1000.0
        assert link1.delta_t == 50.0

        # Test with custom delta_t
        link2 = ThermalRadiativeLink(power=1000.0, delta_t=40.0)
        assert link2.power == 1000.0
        assert link2.delta_t == 40.0

    def test_repr(self) -> None:
        """Test string representation."""
        link = ThermalRadiativeLink(power=1000.0, delta_t=40.0)
        expected = "ThermalRadiativeLink(power=1000.0, delta_t=40.0)"
        assert repr(link) == expected

    def test_rated_power_at_design_temperature(self, node_attrs_factory: Callable) -> None:
        """Test that link delivers rated power at design temperature difference."""
        link = ThermalRadiativeLink(power=1000.0, delta_t=50.0)
        hot_attrs = node_attrs_factory(70.0)  # 70°C
        cold_attrs = node_attrs_factory(20.0)  # 20°C (50° difference)
        dt = 1.0

        energy_change = link.step(hot_attrs, cold_attrs, dt)

        assert energy_change == pytest.approx(1000.0)  # Should deliver rated power
        assert hot_attrs["energy_change"] == pytest.approx(-1000.0)
        assert cold_attrs["energy_change"] == pytest.approx(1000.0)

    def test_linear_power_scaling(self, node_attrs_factory: Callable) -> None:
        """Test that power scales linearly with temperature difference."""
        link = ThermalRadiativeLink(power=1000.0, delta_t=50.0)
        dt = 1.0

        # Test at half the design temperature difference
        hot_attrs = node_attrs_factory(45.0)  # 45°C
        cold_attrs = node_attrs_factory(20.0)  # 20°C (25° difference)

        energy_change = link.step(hot_attrs, cold_attrs, dt)
        assert energy_change == pytest.approx(500.0)  # Should deliver half power

    def test_time_scaling(self, node_attrs_factory: Callable) -> None:
        """Test that energy transfer scales linearly with time."""
        link = ThermalRadiativeLink(power=1000.0, delta_t=50.0)
        hot_attrs = node_attrs_factory(70.0)
        cold_attrs = node_attrs_factory(20.0)

        # Test with different time steps
        energy_1s = link.step(hot_attrs, cold_attrs, dt=1.0)

        # Reset energy changes
        hot_attrs["energy_change"] = 0.0
        cold_attrs["energy_change"] = 0.0

        energy_2s = link.step(hot_attrs, cold_attrs, dt=2.0)

        assert energy_2s == pytest.approx(2 * energy_1s)

    def test_equal_temperatures(self, node_attrs_factory: Callable) -> None:
        """Test behavior when temperatures are equal."""
        link = ThermalRadiativeLink(power=1000.0)
        temp = 20.0
        attrs1 = node_attrs_factory(temp)
        attrs2 = node_attrs_factory(temp)
        dt = 1.0

        energy_change = link.step(attrs1, attrs2, dt)

        assert energy_change == pytest.approx(0.0)
        assert attrs1["energy_change"] == pytest.approx(0.0)
        assert attrs2["energy_change"] == pytest.approx(0.0)

    def test_energy_conservation(self, node_attrs_factory: Callable) -> None:
        """Test that energy is conserved during transfer."""
        link = ThermalRadiativeLink(power=1000.0)
        hot_attrs = node_attrs_factory(70.0)
        cold_attrs = node_attrs_factory(20.0)
        dt = 1.0

        energy_change = link.step(hot_attrs, cold_attrs, dt)

        assert abs(hot_attrs["energy_change"]) == pytest.approx(abs(cold_attrs["energy_change"]))
        assert energy_change == pytest.approx(-hot_attrs["energy_change"])
        assert energy_change == pytest.approx(cold_attrs["energy_change"])

    def test_zero_power(self, node_attrs_factory: Callable) -> None:
        """Test behavior with zero power rating."""
        link = ThermalRadiativeLink(power=0.0)
        hot_attrs = node_attrs_factory(70.0)
        cold_attrs = node_attrs_factory(20.0)
        dt = 1.0

        energy_change = link.step(hot_attrs, cold_attrs, dt)

        assert energy_change == pytest.approx(0.0)
        assert hot_attrs["energy_change"] == pytest.approx(0.0)
        assert cold_attrs["energy_change"] == pytest.approx(0.0)


class TestConvectiveLink:
    @pytest.fixture
    def node_attrs_factory(self) -> Callable[[float, float], ThermalNodeAttrDict]:
        """Create a factory function for node attributes."""

        def create_attrs(temp: float, thermal_mass: float) -> ThermalNodeAttrDict:
            return {"temperature": temp, "energy_change": 0.0, "thermal_mass": thermal_mass}

        return create_attrs

    @pytest.fixture
    def basic_link(self) -> ConvectiveLink:
        """Create a basic convective link with 1 ACH."""
        return ConvectiveLink(ach=1.0)

    def test_initialization(self) -> None:
        """Test that ConvectiveLink initializes with correct ACH value."""
        link = ConvectiveLink(ach=2.0)
        assert link.ach == 2.0

    def test_repr(self) -> None:
        """Test the string representation of ConvectiveLink."""
        link = ConvectiveLink(ach=2.0)
        expected = "ConvectiveLink(ach=2.0)"
        assert repr(link) == expected

    def test_one_hour_full_exchange(self, node_attrs_factory: Callable) -> None:
        """Test that one air change per hour transfers expected energy over one hour."""
        link = ConvectiveLink(ach=1.0)
        dt = 3600.0  # One hour

        # Setup two rooms with different temperatures
        hot_attrs = node_attrs_factory(temp=30.0, thermal_mass=1000.0)  # 30°C, 1000 J/K
        cold_attrs = node_attrs_factory(temp=20.0, thermal_mass=1000.0)  # 20°C, 1000 J/K

        energy_change = link.step(hot_attrs, cold_attrs, dt)

        # Should exchange one full volume of air
        expected_energy = 1.0 * hot_attrs["thermal_mass"] * (30.0 - 20.0)
        assert energy_change == pytest.approx(expected_energy), "Net energy change wrong"
        assert hot_attrs["energy_change"] == pytest.approx(-expected_energy), "Hot energy change wrong"
        assert cold_attrs["energy_change"] == pytest.approx(expected_energy), "Cold energy change wrong"

    def test_time_scaling(self, node_attrs_factory: Callable) -> None:
        """Test that energy transfer scales correctly with time."""
        link = ConvectiveLink(ach=1.0)

        hot_attrs = node_attrs_factory(temp=30.0, thermal_mass=1000.0)
        cold_attrs = node_attrs_factory(temp=20.0, thermal_mass=1000.0)

        # Test for 1 hour vs 30 minutes
        energy_1h = link.step(hot_attrs, cold_attrs, dt=3600.0)

        # Reset energy changes
        hot_attrs["energy_change"] = 0.0
        cold_attrs["energy_change"] = 0.0

        energy_30m = link.step(hot_attrs, cold_attrs, dt=1800.0)

        assert energy_30m == pytest.approx(energy_1h / 2.0)

    def test_ach_scaling(self, node_attrs_factory: Callable) -> None:
        """Test that energy transfer scales linearly with ACH."""
        link1 = ConvectiveLink(ach=1.0)
        link2 = ConvectiveLink(ach=2.0)
        dt = 3600.0

        hot_attrs = node_attrs_factory(temp=30.0, thermal_mass=1000.0)
        cold_attrs = node_attrs_factory(temp=20.0, thermal_mass=1000.0)

        energy1 = link1.step(hot_attrs, cold_attrs, dt)

        # Reset energy changes
        hot_attrs["energy_change"] = 0.0
        cold_attrs["energy_change"] = 0.0

        energy2 = link2.step(hot_attrs, cold_attrs, dt)

        assert energy2 == pytest.approx(2.0 * energy1)

    def test_thermal_mass_scaling(self, node_attrs_factory: Callable) -> None:
        """Test that energy transfer scales with thermal mass."""
        link = ConvectiveLink(ach=1.0)
        dt = 3600.0

        # Test with different thermal masses
        hot_attrs1 = node_attrs_factory(temp=30.0, thermal_mass=1000.0)
        cold_attrs1 = node_attrs_factory(temp=20.0, thermal_mass=1000.0)
        hot_attrs2 = node_attrs_factory(temp=30.0, thermal_mass=2000.0)
        cold_attrs2 = node_attrs_factory(temp=20.0, thermal_mass=2000.0)

        energy1 = link.step(hot_attrs1, cold_attrs1, dt)
        energy2 = link.step(hot_attrs2, cold_attrs2, dt)

        assert energy2 == pytest.approx(2.0 * energy1)

    def test_equal_temperatures(self, node_attrs_factory: Callable) -> None:
        """Test that no energy is transferred when temperatures are equal."""
        link = ConvectiveLink(ach=1.0)
        temp = 25.0
        attrs1 = node_attrs_factory(temp=temp, thermal_mass=1000.0)
        attrs2 = node_attrs_factory(temp=temp, thermal_mass=1000.0)
        dt = 3600.0

        energy_change = link.step(attrs1, attrs2, dt)

        assert energy_change == pytest.approx(0.0)
        assert attrs1["energy_change"] == pytest.approx(0.0)
        assert attrs2["energy_change"] == pytest.approx(0.0)

    def test_zero_ach(self, node_attrs_factory: Callable) -> None:
        """Test that no energy is transferred with zero air changes per hour."""
        link = ConvectiveLink(ach=0.0)
        hot_attrs = node_attrs_factory(temp=30.0, thermal_mass=1000.0)
        cold_attrs = node_attrs_factory(temp=20.0, thermal_mass=1000.0)
        dt = 3600.0

        energy_change = link.step(hot_attrs, cold_attrs, dt)

        assert energy_change == pytest.approx(0.0)
        assert hot_attrs["energy_change"] == pytest.approx(0.0)
        assert cold_attrs["energy_change"] == pytest.approx(0.0)

    def test_energy_conservation(self, node_attrs_factory: Callable) -> None:
        """Test that energy is conserved during transfer."""
        link = ConvectiveLink(ach=1.0)
        hot_attrs = node_attrs_factory(temp=30.0, thermal_mass=1000.0)
        cold_attrs = node_attrs_factory(temp=20.0, thermal_mass=1000.0)
        dt = 3600.0

        energy_change = link.step(hot_attrs, cold_attrs, dt)

        assert abs(hot_attrs["energy_change"]) == pytest.approx(abs(cold_attrs["energy_change"]))
        assert energy_change == pytest.approx(-hot_attrs["energy_change"])
        assert energy_change == pytest.approx(cold_attrs["energy_change"])

    def test_different_thermal_masses(self, node_attrs_factory: Callable) -> None:
        """Test that energy transfer only depends on source (u) thermal mass."""
        link = ConvectiveLink(ach=1.0)
        dt = 3600.0

        # Test with different thermal masses for v node
        u_attrs = node_attrs_factory(temp=30.0, thermal_mass=1000.0)
        v_attrs1 = node_attrs_factory(temp=20.0, thermal_mass=500.0)  # Smaller thermal mass
        v_attrs2 = node_attrs_factory(temp=20.0, thermal_mass=2000.0)  # Larger thermal mass
        v_attrs3 = node_attrs_factory(temp=20.0, thermal_mass=float("inf"))  # Infinite thermal mass

        # Calculate energy transfer for each case
        energy1 = link.step(u_attrs, v_attrs1, dt)

        # Reset u_attrs energy change
        u_attrs["energy_change"] = 0.0
        energy2 = link.step(u_attrs, v_attrs2, dt)

        # Reset u_attrs energy change
        u_attrs["energy_change"] = 0.0
        energy3 = link.step(u_attrs, v_attrs3, dt)

        # Energy transfer should be the same in all cases
        assert energy1 == pytest.approx(energy2)
        assert energy2 == pytest.approx(energy3)

        # The energy change should be based only on u's thermal mass and temperature difference
        expected_energy = -1.0 * u_attrs["thermal_mass"] * (30.0 - 20.0) * (dt / 3600.0)
        assert energy1 == pytest.approx(-expected_energy)

        # Test that energy conservation still holds even with infinite thermal mass
        assert abs(u_attrs["energy_change"]) == pytest.approx(abs(v_attrs3["energy_change"]))
