"""Thermal network construction."""

import networkx as nx

from .building_elements import BuildingElement
from .heat_capacities import (
    AIR_HEAT_CAPACITY,
    BRICK_HEAT_CAPACITY,
    BRICK_U_VALUE,
    CONCRETE_HEAT_CAPACITY,
    CONCRETE_U_VALUE,
    FLOOR_U_VALUE,
    GLASS_HEAT_CAPACITY,
    GLASS_U_VALUE,
    ROOF_U_VALUE,
    TILE_HEAT_CAPACITY,
)
from .links import (
    BoilerRadiativeLink,
    ConductiveLink,
    ConvectiveLink,
    RadiativeLink,
    ThermalEdgeAttrDict,
    ThermalNodeAttrDict,
    ThermalRadiativeLink,
)


class HeatNetwork(nx.DiGraph):
    """A Heat Network is a directed graph where nodes are fabric elements and edges are thermal links."""

    node_attr_dict_factory = ThermalNodeAttrDict
    edge_attr_dict_factory = ThermalEdgeAttrDict


def initialise_outdoors() -> HeatNetwork:
    """
    Initialise the outdoors, which will be the base of any future structures.

    The outdoors consists of the Sun, the Ground and some ExternalAir.

    Parameters
    ----------
    None
        We start fresh for the outdoors!

    Returns
    -------
    nx.Graph
        A networkx graph with only nodes representing Ground, Sun and ExternalAir with no thermal links.
    """
    G = HeatNetwork()

    G.add_node(BuildingElement.Ground, thermal_mass=float("inf"), temperature=7, energy_change=0.0)
    G.add_node(BuildingElement.Sun, thermal_mass=float("inf"), temperature=float("inf"), energy_change=0.0)
    G.add_node(BuildingElement.ExternalAir, thermal_mass=float("inf"), temperature=15.0, energy_change=0.0)

    return G


def add_structure_to_graph(
    G: HeatNetwork,
    wall_area: float,
    window_area: float,
    floor_area: float | None = None,
    roof_area: float | None = None,
    air_volume: float | None = None,
    air_changes_per_hour: float = 1.5,
) -> HeatNetwork:
    """
    Add a structure to an existing graph.

    The existing graph should contain just the outdoors and have no building, as this isn't currently idempotent.
    A structure is made of walls, windows, one floor and one roof. It is aligned directly with the compass,
    and the building elements are connected to each other and to the outside world.

    This structure does not have a heating system included.

    Parameters
    ----------
    G
        Graph from `initialise_outdoors()` to add a structure to
    wall_area
        Area in m^2 of each the four walls of this building, presuming they're all the same size (excluding windows!)
    window_area
        Area in m^2 of the windows on the North & South walls of the building, presuming they're all one big bit of glass.
    floor_area
        Area of the floor of this building in contact with the gound. If None, presume it's the same as one wall for a cube.
    roof_area
        Area of the roof of this building receiving sunlight. If None, presume the same as the floor area.
    """
    assert BuildingElement.InternalAir not in G.nodes, "Must not have already added a structure."
    if floor_area is None:
        floor_area = wall_area

    if roof_area is None:
        roof_area = floor_area

    if air_volume is None:
        air_volume = floor_area * wall_area ** (0.5)
    wall_u_value = BRICK_U_VALUE
    WALL_WIDTH = 0.25  # m
    G.add_node(BuildingElement.InternalAir, thermal_mass=air_volume * AIR_HEAT_CAPACITY, temperature=18.0, energy_change=0.0)
    G.add_node(
        BuildingElement.WallSouth,
        thermal_mass=BRICK_HEAT_CAPACITY * wall_area * WALL_WIDTH,
        temperature=18.0,
        energy_change=0.0,
    )
    G.add_node(
        BuildingElement.WallEast, thermal_mass=BRICK_HEAT_CAPACITY * wall_area * WALL_WIDTH, temperature=18.0, energy_change=0.0
    )
    G.add_node(
        BuildingElement.WallWest, thermal_mass=BRICK_HEAT_CAPACITY * wall_area * WALL_WIDTH, temperature=18.0, energy_change=0.0
    )
    G.add_node(
        BuildingElement.WallNorth,
        thermal_mass=BRICK_HEAT_CAPACITY * wall_area * WALL_WIDTH,
        temperature=18.0,
        energy_change=0.0,
    )

    G.add_node(
        BuildingElement.WindowsSouth, thermal_mass=GLASS_HEAT_CAPACITY * window_area, temperature=18.0, energy_change=0.0
    )
    G.add_node(
        BuildingElement.WindowsNorth, thermal_mass=GLASS_HEAT_CAPACITY * window_area, temperature=18.0, energy_change=0.0
    )
    G.add_node(BuildingElement.Roof, thermal_mass=TILE_HEAT_CAPACITY * roof_area, temperature=18.0, energy_change=0.0)

    G.add_node(
        BuildingElement.Floor, thermal_mass=CONCRETE_HEAT_CAPACITY * floor_area * 0.25, temperature=18.0, energy_change=0.0
    )
    G.add_node(BuildingElement.InternalGains, thermal_mass=float("inf"), temperature=float("inf"), energy_change=0.0)

    for wall in [BuildingElement.WallSouth, BuildingElement.WallEast, BuildingElement.WallNorth, BuildingElement.WallWest]:
        G.add_edge(
            BuildingElement.InternalAir,
            wall,
            conductive=ConductiveLink(interface_area=wall_area, heat_transfer=wall_u_value),
            radiative=None,
        )
        G.add_edge(
            wall,
            BuildingElement.ExternalAir,
            conductive=ConductiveLink(interface_area=wall_area, heat_transfer=wall_u_value),
        )

    for window in [BuildingElement.WindowsSouth, BuildingElement.WindowsNorth]:
        G.add_edge(
            BuildingElement.InternalAir,
            window,
            conductive=ConductiveLink(interface_area=window_area / 2.0, heat_transfer=GLASS_U_VALUE),
            radiative=None,
        )
        G.add_edge(
            window,
            BuildingElement.ExternalAir,
            conductive=ConductiveLink(interface_area=window_area / 2.0, heat_transfer=GLASS_U_VALUE),
        )

    G.add_edge(
        BuildingElement.InternalAir,
        BuildingElement.Floor,
        conductive=ConductiveLink(interface_area=floor_area, heat_transfer=FLOOR_U_VALUE),
        radiative=None,
    )
    G.add_edge(
        BuildingElement.Floor,
        BuildingElement.Ground,
        conductive=ConductiveLink(interface_area=floor_area, heat_transfer=FLOOR_U_VALUE),
        radiative=None,
    )

    # TODO (2024-11-27 MHJB): do we need to treat the loft as a separate air volume?
    # ideally it doesn't heat the home downwards, and exchanges lots of air with
    # the outside, so it'd be easier to just have a whole loft volume with a heat capacity
    G.add_edge(
        BuildingElement.InternalAir,
        BuildingElement.Roof,
        # This represents ceiling insulation
        conductive=ConductiveLink(interface_area=roof_area, heat_transfer=ROOF_U_VALUE),
        radiative=None,
    )
    G.add_edge(
        BuildingElement.Roof,
        BuildingElement.ExternalAir,
        # This is tiles-to-air
        conductive=ConductiveLink(interface_area=roof_area, heat_transfer=CONCRETE_U_VALUE),
        radiative=ThermalRadiativeLink(0, delta_t=20.0),
    )

    G.add_edge(BuildingElement.Sun, BuildingElement.Roof, conductive=None, radiative=RadiativeLink(1000))
    G.add_edge(BuildingElement.Sun, BuildingElement.WallSouth, conductive=None, radiative=RadiativeLink(150))
    G.add_edge(BuildingElement.InternalGains, BuildingElement.InternalAir, conductive=None, radiative=RadiativeLink(1000))
    G.add_edge(
        BuildingElement.InternalAir,
        BuildingElement.ExternalAir,
        conductive=None,
        radiative=None,
        convective=ConvectiveLink(air_changes_per_hour),
    )
    return G


def add_heating_system_to_graph(G: HeatNetwork, design_flow_temperature: float = 70.0, n_radiators: int = 4) -> HeatNetwork:
    """
    Include a heating system in this heat network.

    A heating system consists of a HeatSource, representing either a boiler or an ASHP, and a HeatingSystem
    which is radiators, underfloor heating, etc.
    All the emitters and piping in the heating system is joined into a single mega-emitter with a large heat capacity
    and radiative link.

    Parameters
    ----------
    G
        Graph of a structure with an InternalAir node.
    design_flow_temperature
        The temperature of the HeatSource to provide hot water at
    n_radiators
        Number of 1kW radiators to join into the mega-emitter.

    Returns
    -------
    nx.Graph
        Heat network with a heating system included.
    """
    assert BuildingElement.InternalAir in G.nodes, "Must have already added a structure."
    assert BuildingElement.HeatingSystem not in G.nodes, "Must not have already added a heating system."
    assert 20 <= design_flow_temperature <= 100, "Design flow temperature must be between 20°C and 100°C."
    assert n_radiators > 0, "Number of radiators must be positive."
    HEATING_SYSTEM_HEAT_CAPACITY = 27500 + (
        (9025 + 1494) * 1.2 * n_radiators * 1
    )  # 10x 1kW radiators weighting 19kg with 3.6L of water, plus pipes

    RADIATOR_SIZE = 1.0  # m^2
    G.add_node(BuildingElement.HeatSource, thermal_mass=float("inf"), temperature=design_flow_temperature, energy_change=0.0)
    G.add_node(
        BuildingElement.HeatingSystem,
        thermal_mass=HEATING_SYSTEM_HEAT_CAPACITY * n_radiators,
        temperature=65.0,
        energy_change=0.0,
    )

    G.add_edge(
        BuildingElement.HeatSource,
        BuildingElement.HeatingSystem,
        conductive=None,
        radiative=BoilerRadiativeLink(RADIATOR_SIZE * n_radiators * 5 + 1e4, delta_t=50.0, setpoint_temperature=21.0),
    )

    G.add_edge(
        BuildingElement.HeatingSystem,
        BuildingElement.InternalAir,
        conductive=None,
        radiative=ThermalRadiativeLink(RADIATOR_SIZE * n_radiators, delta_t=50.0),
    )
    return G


def create_simple_structure(
    wall_area: float,
    window_area: float,
    floor_area: float | None = None,
    roof_area: float | None = None,
    air_volume: float | None = None,
    design_flow_temperature: float = 70.0,
    n_radiators: int = 4,
) -> HeatNetwork:
    """
    Create a simple structure of four walls, two windows and a heating system.

    See `add_structure_to_graph` and `add_heating_system_to_graph` for more explanation.

    Parameters
    ----------
    wall_area
        Area in m^2 of each the four walls of this building, presuming they're all the same size (excluding windows!)
    window_area
        Area in m^2 of the windows on the North & South walls of the building, presuming they're all one big bit of glass.
    floor_area
        Area of the floor of this building in contact with the gound. If None, presume it's the same as one wall for a cube.
    roof_area
        Area of the roof of this building receiving sunlight. If None, presume the same as the floor area.
    design_flow_temperature
        The temperature of the HeatSource to provide hot water at in °C
    n_radiators
        Number of 1kW radiators to join into the mega-emitter.

    Returns
    -------
    HeatNetwork
        Heat Network of this particular simple building

    """
    G = initialise_outdoors()
    G = add_structure_to_graph(
        G, wall_area=wall_area, window_area=window_area, floor_area=floor_area, roof_area=roof_area, air_volume=air_volume
    )
    G = add_heating_system_to_graph(G, design_flow_temperature=design_flow_temperature, n_radiators=n_radiators)
    return G
