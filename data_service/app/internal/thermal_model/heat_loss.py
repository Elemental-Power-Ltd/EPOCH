"""Peak Heat Loss calculation methods for comparison with MCS survey."""

from collections import defaultdict

from .building_elements import BuildingElement
from .integrator import update_temperatures
from .links import ConductiveLink, ConvectiveLink, RadiativeLink, ThermalNodeAttrDict, ThermalRadiativeLink
from .network import HeatNetwork


def calculate_maximum_dynamic_heat_loss(
    graph: HeatNetwork,
    internal_temperature: float = 21.0,
    external_temperature: float = -2.0,
    dt: float = 300.0,
) -> float:
    """
    Calculate the maximum heat loss at a given set of external and internal temperatures.

    This calculation will disable the heating system and heat source of the building, and just
    presume that the internal air and relevant building elements start off at the specified
    design internal temperature (e.g. 21°C).
    Then, the temperatures will equilibrate until the external-facing elements are at a stable temperature,
    which will ideally be between the design internal and external temperatures.

    This will generally provide a slightly smaller value than `calculate_maximum_static_heat_loss`

    Parameters
    ----------
    graph
        Heat network graph of the building of interest (this will be copied and heating / solar gains removed)
    internal_temperature
        Internal temperature the building is maintained at on the coldest day
    external_temperature
        External design temperature representing the 1% coldest day of the year
    dt
        Simulation timestep in seconds. This is less physically meaningful than in `simulate`, but pick a value
        that converges nicely.

    Returns
    -------
    peak_heat_loss
        Peak heat loss in Watts of this building given the internal and external conditions.
        Normal values are 6kW for domestic buildings and of the order of 50-200 W / m^2 of floor area.
    """
    graph.nodes[BuildingElement.ExternalAir]["temperature"] = external_temperature
    graph.nodes[BuildingElement.Ground]["temperature"] = external_temperature

    for link_type in ["radiative", "conductive", "convective"]:
        graph.get_edge_data(BuildingElement.HeatSource, BuildingElement.HeatingSystem)[link_type] = None
        graph.get_edge_data(BuildingElement.HeatingSystem, BuildingElement.InternalAir)[link_type] = None
        graph.get_edge_data(BuildingElement.InternalGains, BuildingElement.InternalAir)[link_type] = None

    # There's no solar gains on our hypothetical oldest day.
    for u in graph.neighbors(BuildingElement.Sun):
        graph.get_edge_data(BuildingElement.Sun, u)["radiative"] = None

    # Pre-heat all the building elements as it's quicker for them to cool down.
    for u in [
        BuildingElement.WallSouth,
        BuildingElement.WallNorth,
        BuildingElement.WallWest,
        BuildingElement.WallEast,
        BuildingElement.Floor,
        BuildingElement.Roof,
        BuildingElement.WindowsEast,
        BuildingElement.WindowsNorth,
        BuildingElement.WindowsWest,
        BuildingElement.WallSouth,
    ]:
        if u in graph.nodes:
            graph.nodes[u]["temperature"] = internal_temperature

    # TODO (2024-11-25 MHJB): make this iterate until convergence instead of just doing
    # a number of steps.
    energy_changes: list[float] = []
    for _ in range(100):
        # Reset the internal air temperature every timestep to assume that we got the right amount of heat
        # from various internal gains and heating systems.
        graph.nodes[BuildingElement.InternalAir]["temperature"] = internal_temperature
        for u, v, edge_attrs in graph.edges(data=True):
            u_attrs, v_attrs = graph.nodes[u], graph.nodes[v]
            if edge_attrs.get("conductive") is not None:
                edge_attrs["conductive"].step(u_attrs, v_attrs, dt)
            if edge_attrs.get("convective") is not None:
                edge_attrs["convective"].step(u_attrs, v_attrs, dt)
            if edge_attrs.get("radiative") is not None:
                edge_attrs["radiative"].step(u_attrs, v_attrs, dt)
        energy_changes.append(graph.nodes[BuildingElement.InternalAir]["energy_change"])
        update_temperatures(graph)
    return max(item / dt for item in energy_changes)


def calculate_maximum_static_heat_loss(
    graph: HeatNetwork, internal_temperature: float = 21.0, external_temperature: float = -2.0, ground_temperature: float = 11.3
) -> float:
    """
    Calculate the maximum static heat loss of the building, which is the loss of the internal air to all fabric components.

    This is a different methodology to the `calculate_maximum_dynamic_heat_loss` and will return slightly different numbers
    (this one generally overestimates).

    Parameters
    ----------
    graph
        Heat network graph of the building of interest
    internal_temperature
        Temperature of the air and fabric elements within the building's thermal envelope
    external_temperature
        Temperature of the air and ground on the day of interest (likely the 1% codlest day)

    Returns
    -------
    float
        Maximum static heat loss in Watts of this building on a day where it's `external_temperature` degrees inside
        and `internal_temperature` degrees inside.
    """
    return sum(
        calculate_maximum_static_heat_loss_breakdown(
            graph=graph,
            internal_temperature=internal_temperature,
            external_temperature=external_temperature,
            ground_temperature=ground_temperature,
        ).values()
    )


def calculate_maximum_static_heat_loss_breakdown(
    graph: HeatNetwork, internal_temperature: float = 21.0, external_temperature: float = -2.0, ground_temperature: float = 11.3
) -> dict[tuple[BuildingElement, BuildingElement], float]:
    """
    Calculate the maximum static heat loss of the building, which is the loss of the internal air to all fabric components.

    This is a different methodology to the `calculate_maximum_dynamic_heat_loss` and will return slightly different numbers
    (this one generally overestimates).

    Parameters
    ----------
    graph
        Heat network graph of the building of interest
    internal_temperature
        Temperature of the air and fabric elements within the building's thermal envelope
    external_temperature
        Temperature of the air and ground on the day of interest (likely the 1% coldest day)
    floor_temperature
        Temperature of the ground on the day of interest (most likely the Mean Air Temperature over the year)

    Returns
    -------
    float
        Maximum static heat loss in Watts of this building on a day where it's `external_temperature` degrees inside
        and `internal_temperature` degrees inside.
    """
    component_energy_changes: dict[tuple[BuildingElement, BuildingElement], float] = defaultdict(lambda: 0)
    for v in graph.neighbors(BuildingElement.InternalAir):
        if v in {BuildingElement.InternalGains, BuildingElement.HeatingSystem, BuildingElement.Sun}:
            # Skip these as they don't contribute to heat losses.
            continue
        edge = graph.get_edge_data(BuildingElement.InternalAir, v)
        v_attrs = graph.nodes[v]
        for link in edge.values():
            if v in {BuildingElement.Ground, BuildingElement.Floor}:
                # The ground is much warmer than the air as it has a huge thermal mass
                v_temperature = ground_temperature
            elif v == BuildingElement.Roof:
                # Roof space is modelled to be precisely 11°C colder than indoors.
                v_temperature = internal_temperature - 11.0
            else:
                v_temperature = external_temperature
            if isinstance(link, RadiativeLink | ConductiveLink | ConvectiveLink | ThermalRadiativeLink):
                u_attrs = ThermalNodeAttrDict(
                    temperature=internal_temperature,
                    thermal_mass=graph.nodes[BuildingElement.InternalAir]["thermal_mass"],
                    energy_change=0.0,
                )
                v_attrs = ThermalNodeAttrDict(
                    temperature=v_temperature, thermal_mass=graph.nodes[v]["thermal_mass"], energy_change=0.0
                )
                component_energy_changes[BuildingElement.InternalAir, v] = -link.step(u_attrs, v_attrs, dt=1.0)

    return dict(component_energy_changes)
