"""Thermal network construction."""

import json
from pathlib import Path

import networkx as nx
import numpy as np

from ...models.heating_load import SurveyedSizes
from .building_elements import BuildingElement
from .heat_capacities import (
    AIR_HEAT_CAPACITY,
    BRICK_HEAT_CAPACITY,
    CONCRETE_HEAT_CAPACITY,
    FLOOR_U_VALUE,
    GLASS_HEAT_CAPACITY,
    TILE_HEAT_CAPACITY,
    U_VALUES_PATH,
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
from .rdsap import estimate_window_area


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
    wall_width: float,
    window_area: float,
    wall_height: float | None = None,
    floor_area: float | None = None,
    roof_area: float | None = None,
    air_volume: float | None = None,
    air_changes_per_hour: float = 1.5,
    u_values_path: Path = U_VALUES_PATH,
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
    wall_width
        Width in m of each the four walls of this building, presuming they're all the same size (excluding windows!).
    wall_height
        Height in m of each the four walls of this building, presuming they're all the same size (excluding windows!).
        If None, presumed to be half the width of the wall.
    window_area
        Area in m^2 of the windows on the North & South walls of the building, presuming they're all one big bit of glass.
    floor_area
        Area of the floor of this building in contact with the gound. If None, presume it's the same as one wall for a cube.
    roof_area
        Area of the roof of this building receiving sunlight. If None, presume the same as the floor area.
    u_value_path
        Path to a JSON file containing U values
    """
    u_values = json.loads(u_values_path.read_text())
    if wall_height is None:
        wall_height = wall_width / 2.0

    wall_area = (wall_width * wall_height) - window_area
    assert BuildingElement.InternalAir not in G.nodes, "Must not have already added a structure."
    if floor_area is None:
        floor_area = wall_area

    if roof_area is None:
        roof_area = floor_area

    if air_volume is None:
        air_volume = floor_area * wall_width * wall_height

    # Note that this is often overridden
    wall_u_value = u_values["Brick 102mm, cavity, 100mm standard aerated block (k=0.17), 12.5mm plasterboard on dabs"]
    WALL_DEPTH = 0.25  # m
    G.add_node(BuildingElement.InternalAir, thermal_mass=air_volume * AIR_HEAT_CAPACITY, temperature=18.0, energy_change=0.0)
    G.add_node(
        BuildingElement.WallSouth,
        thermal_mass=BRICK_HEAT_CAPACITY * wall_area * WALL_DEPTH,
        temperature=18.0,
        energy_change=0.0,
    )
    G.add_node(
        BuildingElement.WallEast, thermal_mass=BRICK_HEAT_CAPACITY * wall_area * WALL_DEPTH, temperature=18.0, energy_change=0.0
    )
    G.add_node(
        BuildingElement.WallWest, thermal_mass=BRICK_HEAT_CAPACITY * wall_area * WALL_DEPTH, temperature=18.0, energy_change=0.0
    )
    G.add_node(
        BuildingElement.WallNorth,
        thermal_mass=BRICK_HEAT_CAPACITY * wall_area * WALL_DEPTH,
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

    # Presume that the existing windows are rubbish
    glass_u_value = u_values["Wood/PVC Single Glazed"]
    for window in [BuildingElement.WindowsSouth, BuildingElement.WindowsNorth]:
        G.add_edge(
            BuildingElement.InternalAir,
            window,
            conductive=ConductiveLink(interface_area=window_area / 2.0, heat_transfer=glass_u_value),
            radiative=None,
        )
        G.add_edge(
            window,
            BuildingElement.ExternalAir,
            conductive=ConductiveLink(interface_area=window_area / 2.0, heat_transfer=glass_u_value),
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
    roof_code = (
        "Pitched roof - Slates or tiles, sarking felt, ventilated air space,"
        + " 50mm insulation between rafters, 9.5 mm plasterboard"
    )
    roof_u_value = u_values[roof_code]
    G.add_edge(
        BuildingElement.InternalAir,
        BuildingElement.Roof,
        # This represents ceiling insulation
        conductive=ConductiveLink(interface_area=roof_area, heat_transfer=roof_u_value),
        radiative=None,
    )
    G.add_edge(
        BuildingElement.Roof,
        BuildingElement.ExternalAir,
        # This is tiles-to-air
        conductive=ConductiveLink(interface_area=roof_area, heat_transfer=roof_u_value),
        radiative=ThermalRadiativeLink(0, delta_t=20.0),
    )
    # These are defaults, that are overwritten by the real potential solar gains times area elsewhere
    G.add_edge(BuildingElement.Sun, BuildingElement.Roof, conductive=None, radiative=RadiativeLink(1000))
    G.add_edge(BuildingElement.Sun, BuildingElement.WallSouth, conductive=None, radiative=RadiativeLink(150))
    G.add_edge(BuildingElement.InternalGains, BuildingElement.InternalAir, conductive=None, radiative=RadiativeLink(power=1000))
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

    RADIATOR_SIZE = 1000  # W
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
        radiative=BoilerRadiativeLink(power=RADIATOR_SIZE * n_radiators * 5 + 1e4, delta_t=50.0, setpoint_temperature=21.0),
    )

    G.add_edge(
        BuildingElement.HeatingSystem,
        BuildingElement.InternalAir,
        conductive=None,
        radiative=ThermalRadiativeLink(power=RADIATOR_SIZE * n_radiators, delta_t=50.0),
    )
    return G


def create_simple_structure(
    *,
    wall_width: float,
    window_area: float,
    wall_height: float | None = None,
    floor_area: float | None = None,
    roof_area: float | None = None,
    air_volume: float | None = None,
    design_flow_temperature: float = 70.0,
    n_radiators: int = 4,
    u_values_path: Path = U_VALUES_PATH,
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
    u_value_path
        Path to a JSON file containing U values for the structure

    Returns
    -------
    HeatNetwork
        Heat Network of this particular simple building

    """
    G = initialise_outdoors()
    G = add_structure_to_graph(
        G,
        wall_width=wall_width,
        wall_height=wall_height,
        window_area=window_area,
        floor_area=floor_area,
        roof_area=roof_area,
        air_volume=air_volume,
        u_values_path=u_values_path,
    )
    G = add_heating_system_to_graph(G, design_flow_temperature=design_flow_temperature, n_radiators=n_radiators)
    return G


def create_structure_from_params(
    scale_factor: float = 1.0,
    ach: float = 1.0,
    u_value: float = 2.2,
    boiler_power: float = 24e3,
    setpoint: float = 21,
    u_values_path: Path = U_VALUES_PATH,
) -> HeatNetwork:
    """
    Create a simple structure with some fitted parameters.

    This wraps around create_simple_structure, and then changes the parameters of the links
    directly afterwards.

    You should use this if you want to get exactly the same structure as you'd get oufr om
    `simulate_parameters`.

    Parameters
    ----------
    scale_factor
        Scale factor of the building compared to the default, which is 50m^2 with 5m high walls.
    ach
        Air changes per hour in this building (as a fraction of total air)
    u_value
        U value of main structural material for walls.
    boiler_power
        Boiler power in W, also scales up the size of the heating system linearlly.
    setpoint
        Equivalent 24/7 thermostat setpoint for the boiler.

    Returns
    -------
    HeatNetwork
        Simple structure with the values changed.
    """
    floor_area = 50.0 * scale_factor
    hm = create_simple_structure(
        # Walls are 2D, so scale them appropriately.
        wall_width=10.0 * np.sqrt(scale_factor),
        wall_height=5.0 * np.sqrt(scale_factor),
        # Assuming about 20% window to floor area ratio
        window_area=estimate_window_area(floor_area),
        floor_area=floor_area,
        u_values_path=u_values_path,
    )

    hm.edges[BuildingElement.HeatSource, BuildingElement.HeatingSystem]["radiative"].power = boiler_power
    hm.edges[BuildingElement.HeatSource, BuildingElement.HeatingSystem]["radiative"].setpoint_temperature = setpoint

    # Radiators are assumed to be slightly undersized compared to the boiler.
    hm.edges[BuildingElement.HeatingSystem, BuildingElement.InternalAir]["radiative"].power = boiler_power * 0.75

    # Scale up the thermal mass of the heating system according to the boiler size
    hm.nodes[BuildingElement.HeatingSystem]["thermal_mass"] *= (
        boiler_power / hm.edges[BuildingElement.HeatSource, BuildingElement.HeatingSystem]["radiative"].power
    )

    hm.edges[BuildingElement.InternalAir, BuildingElement.ExternalAir]["convective"].ach = ach
    for v in [BuildingElement.WallEast, BuildingElement.WallSouth, BuildingElement.WallNorth, BuildingElement.WallWest]:
        hm.edges[BuildingElement.InternalAir, v]["conductive"].heat_transfer = u_value
    return hm


def create_structure_from_survey(surveyed_sizes: SurveyedSizes, u_values_path: Path = U_VALUES_PATH) -> HeatNetwork:
    """
    Create a simple structure with some fitted parameters.

    This wraps around create_simple_structure, and then changes the parameters of the links
    directly afterwards.

    You should use this if you want to get exactly the same structure as you'd get oufr om
    `simulate_parameters`.

    Parameters
    ----------
    surveyed_sizes
        Sizes of the walls, floor, loft etc from a survey.

    Returns
    -------
    HeatNetwork
        Simple structure with the values changed.
    """
    hm = create_simple_structure(
        # Walls are 2D, so scale them appropriately.
        wall_width=np.sqrt(surveyed_sizes.exterior_wall_area) / 4,
        wall_height=np.sqrt(surveyed_sizes.exterior_wall_area) / 4,
        # Assuming about 20% window to floor area ratio
        window_area=surveyed_sizes.window_area,
        floor_area=surveyed_sizes.total_floor_area / surveyed_sizes.window_area,
        u_values_path=u_values_path,
    )

    hm.edges[BuildingElement.HeatSource, BuildingElement.HeatingSystem]["radiative"].power = surveyed_sizes.boiler_power

    # Radiators are assumed to be slightly undersized compared to the boiler.
    hm.edges[BuildingElement.HeatingSystem, BuildingElement.InternalAir]["radiative"].power = surveyed_sizes.boiler_power

    # Scale up the thermal mass of the heating system according to the boiler size
    hm.nodes[BuildingElement.HeatingSystem]["thermal_mass"] *= (
        surveyed_sizes.boiler_power / hm.edges[BuildingElement.HeatSource, BuildingElement.HeatingSystem]["radiative"].power
    )

    hm.edges[BuildingElement.InternalAir, BuildingElement.ExternalAir]["convective"].ach = surveyed_sizes.ach
    return hm
