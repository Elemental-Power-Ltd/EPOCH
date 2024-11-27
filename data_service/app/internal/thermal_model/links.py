"""Thermal links between two objects: conductive, radiative, convective."""

from typing import TypedDict


class ThermalNodeAttrDict(TypedDict):
    """Typed dict for a thermal element node which has a temperature, a heat capacity, and an energy change accumulator."""

    temperature: float
    thermal_mass: float
    energy_change: float


class ConductiveLink:
    """Conductive links represent two bodies in thermal contact with one another."""

    def __init__(self, interface_area: float, heat_transfer: float) -> None:
        """
        Set up the conductive link with an interface area and a U-value.

        Parameters
        ----------
        interface_area
            Size of the conductive link in m^2
        heat_transfer
            Heat transfer coefficient (U-value) in W / m^2 K
        """
        self.interface_area = interface_area
        self.heat_transfer = heat_transfer

    def __repr__(self) -> str:
        """Create a string showing the arguments used to create this link."""
        return f"ConductiveLink(interface_area={self.interface_area}, heat_transfer={self.heat_transfer})"

    def step(self, u_attrs: ThermalNodeAttrDict, v_attrs: ThermalNodeAttrDict, dt: float) -> float:
        """
        Pass heat between the two sides of this conductive link.

        The hotter body will lose temperature linearly to the colder body.

        Parameters
        ----------
        u_attrs
            Networkx node attributes dictionary with `temperature` and `energy_change` properties.
        v_attrs
            Networkx node attributes dictionary with `temperature` and `energy_change` properties.
        dt
            Timestep over which this transfer happens in seconds.

        Returns
        -------
        energy_change
            Total energy transferred during this step. Positive if transferring from v to u, negative otherwise.
        """
        temperature_diff = v_attrs["temperature"] - u_attrs["temperature"]

        energy_change_j = self.heat_transfer * self.interface_area * temperature_diff * dt
        u_attrs["energy_change"] += energy_change_j
        v_attrs["energy_change"] -= energy_change_j

        return energy_change_j


class RadiativeLink:
    """
    Radiative links are constant power gains from one body to another.

    For example, the roof gains power from the sun roughly independently of its own temperature.
    This is also used to model internal gains from metabolism or electrical appliances.
    """

    def __init__(self, power: float) -> None:
        """
        Initialise the radiative link with a specific power.

        This might vary over time if the edge is updated.

        Parameters
        ----------
        power
            Power in W
        """
        self.power = power

    def __repr__(self) -> str:
        """Create a string showing the arguments used to create this link."""
        return f"RadiativeLink(power={self.power})"

    def step(self, u_attrs: ThermalNodeAttrDict, v_attrs: ThermalNodeAttrDict, dt: float) -> float:
        """
        Pass heat between the two sides of this radiative link.

        Node `u` will gain energy from node `v`.

        Parameters
        ----------
        u_attrs
            Networkx node attributes dictionary with `temperature` and `energy_change` properties.
        v_attrs
            Networkx node attributes dictionary with `temperature` and `energy_change` properties.
        dt
            Timestep over which this transfer happens in seconds.

        Returns
        -------
        energy_change
            Total energy transferred during this step.
        """
        energy_change_j = self.power * dt

        u_attrs["energy_change"] += energy_change_j
        v_attrs["energy_change"] -= energy_change_j

        return energy_change_j


class ThermalRadiativeLink:
    """
    A thermal radiative link represents an exchange of black body radiation between two hot objects.

    For example, the roof radiates heat to the sky depending on its own temperature,
    or radiators radiate into the rooms depending on how hot they are.
    """

    def __init__(self, power: float, delta_t: float = 50.0):
        """
        Establish the power and rated temperature for this radiative link.

        This is most representative for radiators, which have a kW rating generally at a 50 degree difference.

        Parameters
        ----------
        power
            Maximum power output in W at the given delta_t
        delta_t
            Designed temperature difference between hot and cold bodies when `power` Watts are emitted.
        """
        self.power = power
        self.delta_t = delta_t

    def __repr__(self) -> str:
        """Create a string showing the arguments used to create this link."""
        return f"ThermalRadiativeLink(power={self.power}, delta_t={self.delta_t})"

    def step(self, u_attrs: ThermalNodeAttrDict, v_attrs: ThermalNodeAttrDict, dt: float) -> float:
        """
        Pass heat between the two sides of this thermal radiative link.

        Node `u` will gain energy from node `v`.

        Parameters
        ----------
        u_attrs
            Networkx node attributes dictionary with `temperature` and `energy_change` properties.
        v_attrs
            Networkx node attributes dictionary with `temperature` and `energy_change` properties.
        dt
            Timestep over which this transfer happens in seconds.

        Returns
        -------
        energy_change
            Total energy transferred during this step. Positive if transferring from v to u, negative otherwise.
        """
        system_delta_t = max(v_attrs["temperature"] - u_attrs["temperature"], -float("inf"))
        energy_change_j = self.power * dt * system_delta_t / self.delta_t

        u_attrs["energy_change"] += energy_change_j
        v_attrs["energy_change"] -= energy_change_j

        return energy_change_j


class BoilerRadiativeLink:
    """Energy gains from a thermostat controlled boiler."""

    def __init__(self, power: float, delta_t: float = 50.0, setpoint_temperature: float = 21.0, is_on: bool = False):
        """
        Establish the boiler, which is either On or Off depending on a setpoint temperature.

        Parameters
        ----------
        power
            Maximum power output of this heat source in W at the specified delta_t
        delta_t
            Temperature difference between source and sink in K at which `power` is emitted.
        setpoint_temperature
            Temperature of ambient air at which this heat source kicks in
        is_on
            Hysteresis control flag, whether this boiler was on at the previous timestep.
        """
        self.power = power
        self.delta_t = delta_t
        self.setpoint_temperature = setpoint_temperature
        self.is_on = is_on

    def __repr__(self) -> str:
        """Create a string showing the arguments used to create this link."""
        return (
            f"BoilerRadiativeLink(power={self.power}, delta_t={self.delta_t},"
            + f"setpoint_temperature={self.setpoint_temperature}, is_on={self.is_on})"
        )

    def step(
        self, u_attrs: ThermalNodeAttrDict, v_attrs: ThermalNodeAttrDict, dt: float, thermostat_temperature: float
    ) -> float:
        """
        Pass heat from the heat source into the heating system, depending on the measured temperature.

        If `thermostat_temperature < self.setpoint_temperature` the boiler will come on, with +-0.5K hysteresis
        either side.

        Node `u` will gain energy from node `v`.

        Parameters
        ----------
        u_attrs
            Networkx node attributes dictionary with `temperature` and `energy_change` properties.
        v_attrs
            Networkx node attributes dictionary with `temperature` and `energy_change` properties.
        dt
            Timestep over which this transfer happens in seconds.
        thermostat_temperature
            The measured internal air temperature used to control the boiler.

        Returns
        -------
        energy_change
            Total energy transferred during this step. Positive if transferring from v to u, negative otherwise.
        """
        energy_change_j = 0.0
        if thermostat_temperature > self.setpoint_temperature + 0.5:
            self.is_on = False

        if thermostat_temperature < self.setpoint_temperature - 0.5:
            self.is_on = True

        if self.is_on:
            system_delta_t = max(v_attrs["temperature"] - u_attrs["temperature"], 0.0)

            energy_change_j = self.power * dt * system_delta_t / self.delta_t

        u_attrs["energy_change"] += energy_change_j
        v_attrs["energy_change"] -= energy_change_j
        return energy_change_j


# TODO (2024-11-22 MHJB): this is a pretty crude convective link
class ConvectiveLink:
    """ConvectiveLinks represent air flow between two volumes of air."""

    def __init__(self, ach: float):
        """
        Set up the convective link measured in air changes per hour.

        Parameters
        ----------
        ach
            Air changes per hour
        """
        self.ach = ach

    def __repr__(self) -> str:
        """Create a string showing the arguments used to create this link."""
        return f"ConvectiveLink(ach={self.ach})"

    def step(self, u_attrs: ThermalNodeAttrDict, v_attrs: ThermalNodeAttrDict, dt: float) -> float:
        """
        Pass heat in the form of hot air between the two sides of this convective link.

        Parameters
        ----------
        u_attrs
            Networkx node attributes dictionary with `temperature` and `energy_change` properties.
        v_attrs
            Networkx node attributes dictionary with `temperature` and `energy_change` properties.
        dt
            Timestep over which this transfer happens in seconds.

        Returns
        -------
        energy_change
            Total energy transferred during this step. Positive if transferring from v to u, negative otherwise.
        """
        air_changes = self.ach * dt / 3600.0
        temperature_diff = v_attrs["temperature"] - u_attrs["temperature"]
        energy_change_j = air_changes * u_attrs["thermal_mass"] * temperature_diff

        u_attrs["energy_change"] += energy_change_j
        v_attrs["energy_change"] -= energy_change_j

        return energy_change_j


class ThermalEdgeAttrDict(TypedDict):
    """Typed dict for an edge which has conductive, radiative and convective links that might be None."""

    conductive: ConductiveLink | None
    radiative: RadiativeLink | BoilerRadiativeLink | ThermalRadiativeLink | None
    convective: ConvectiveLink | None
