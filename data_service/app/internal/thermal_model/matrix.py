"""Functions for the matrix formulation of temperature flows."""

import copy
import datetime
from collections import defaultdict
from collections.abc import Mapping
from typing import NewType

import numpy as np
import scipy.linalg

from ..utils.conversions import celsius_to_kelvin, kelvin_to_celsius
from .building_elements import BuildingElement
from .links import BoilerRadiativeLink, ConductiveLink, ConvectiveLink, RadiativeLink, ThermalRadiativeLink
from .network import HeatNetwork

GraphSize = NewType("GraphSize", int)


def create_node_to_index_map(hm: HeatNetwork) -> Mapping[BuildingElement, int | None]:
    """
    Create the node to index mapping for this graph with a consistent ordering.

    The keys of this mapping will be the nodes of the graph, which must be unique.
    The values of this mapping will be an index into a given array, e.g.
    the first node in the graph might be at index 0 in any of the arrays we use
    for thermal modelling.

    Currently sorts nodes alphabetically ascending.

    Parameters
    ----------
    hm
        HeatNetwork with unique keys

    Returns
    -------
        node: array index mapping
    """
    res: dict[BuildingElement, int | None] = defaultdict(lambda: None)
    return res | {
        node: i
        for i, (node, _) in enumerate(
            filter(lambda x: np.isfinite(x[1]["temperature"]) and np.isfinite(x[1]["thermal_mass"]), hm.nodes(data=True))
        )
    }


def network_to_temperature_vec(hm: HeatNetwork) -> np.ndarray[tuple[GraphSize], np.dtype[np.float64]]:
    """
    Generate a temperature vector in Kelvin for this heat network.

    The temperature vector is an Nx1 column vector with each entry being the temperature in Kelvin
    of a given element.
    Elements that have infinite temperature are overridden to have a temperature of 1K here (it makes
    the multiplications easier sometimes).

    Parameters
    ----------
    hm
        HeatNetwork with sortable node names, each with a "temperature" attribute

    Returns
    -------
        Nx1 vector of temperatures in Kelvin
    """
    node_to_idx = create_node_to_index_map(hm)
    temperature_vec = np.zeros([len(node_to_idx)], dtype=np.float64)
    for node, attrs in hm.nodes(data=True):
        idx = node_to_idx[node]
        if idx is None:
            continue
        temperature = attrs["temperature"]
        temperature_vec[idx] = celsius_to_kelvin(temperature) if np.isfinite(temperature) else 1.0
    return temperature_vec


def network_to_energy_matrix(hm: HeatNetwork) -> np.ndarray[tuple[GraphSize, GraphSize], np.dtype[np.float64]]:
    """
    Create an energy matrix representing the total energy flows across the network.

    An energy matrix is an NxN square matrix where the elements have units W / K and represent heat flows
    between two elements depending on their temperature.
    For example, a simple matrix between two elements with a single coupling coefficient K might be of the form
    [[-K, K], [K, -K]]

    This means that when you multiply the temperature column vector  [[T1], [T2]] by this energy matrix you get

    [[ K (T2 - T1)], [K (T1 - T2)]]

    which is the correct heat flows depending on the temperature different that we would expect.

    The matrix includes radiative, convective, and conductive links. The radiative links are a bit of a hack,
    so be careful of them.

    Parameters
    ----------
    hm
        HeatNetwork where edges represent thermal links between nodes.

    Returns
    -------
    NxN

    """
    # Make sure that we always associated the same matrix entry with the
    # correct node by using a consistent sort (here, alphabetically by node name)
    node_to_idx = create_node_to_index_map(hm)

    # We use many different matrices for ease of debugging.
    # At the end, we'll group all of these into a single matrix.
    temperature_vec = network_to_temperature_vec(hm)

    conductive_arr = np.zeros([len(node_to_idx), len(node_to_idx)], dtype=np.float64)
    convective_arr = np.zeros_like(conductive_arr)
    radiative_arr = np.zeros_like(conductive_arr)
    additive_radiative_arr = np.zeros_like(conductive_arr)
    boiler_radiative_arr = np.zeros_like(conductive_arr)

    for u, v, e_attrs in hm.edges(data=True):
        u_idx, v_idx = node_to_idx[u], node_to_idx[v]
        if u_idx is None or v_idx is None:
            continue
        u_attrs = hm.nodes[u]
        v_attrs = hm.nodes[v]
        if isinstance(e_attrs.get("conductive"), ConductiveLink):
            # For the matrix equation, we can view each conductive link not as gaining or losing to a single neighbour,
            # but instead:
            # `u` losing its share of heat to a zero temperature body
            # `v` gaining its share of heat from that intermediate body
            # This means that when we do [[-K_uv, K_uv], [K_uv, -K_uv]] @ [[T_u], [T_v]]
            # we correctly get [[K_uv (T_v - T_u)], [-K_uv (T_v - T_u)]]
            conductive_arr[u_idx, u_idx] -= e_attrs["conductive"].heat_transfer * e_attrs["conductive"].interface_area

            conductive_arr[u_idx, v_idx] += e_attrs["conductive"].heat_transfer * e_attrs["conductive"].interface_area
            conductive_arr[v_idx, u_idx] += e_attrs["conductive"].heat_transfer * e_attrs["conductive"].interface_area

            conductive_arr[v_idx, v_idx] -= e_attrs["conductive"].heat_transfer * e_attrs["conductive"].interface_area

        if isinstance(e_attrs.get("convective"), ConvectiveLink):
            # For the matrix equation, we can view each convective link not as gaining or losing to a single neighbour,
            # but instead:
            # `u` losing its share of heat to a zero temperature body
            # `v` gaining its share of heat from that intermediate body
            # This means that when we do [[-K_uv, K_uv], [K_uv, -K_uv]] @ [[T_u], [T_v]]
            # we correctly get [[K_uv (T_v - T_u)], [-K_uv (T_v - T_u)]]
            # Where K_uv is the convective coefficient.
            # Note that convective only works in one direction currently, with u losing and
            # v gaining (this is used to model convection with the infinite outdoors)
            convective_arr[u_idx, u_idx] -= e_attrs["convective"].ach * u_attrs["thermal_mass"] / 3600

            convective_arr[u_idx, v_idx] += e_attrs["convective"].ach * u_attrs["thermal_mass"] / 3600
            convective_arr[v_idx, u_idx] += e_attrs["convective"].ach * u_attrs["thermal_mass"] / 3600

            convective_arr[v_idx, v_idx] -= e_attrs["convective"].ach * u_attrs["thermal_mass"] / 3600

        if isinstance(e_attrs.get("radiative"), ThermalRadiativeLink):
            radiative_arr[u_idx, u_idx] -= e_attrs["radiative"].power / e_attrs["radiative"].delta_t

            radiative_arr[u_idx, v_idx] += e_attrs["radiative"].power / e_attrs["radiative"].delta_t
            radiative_arr[v_idx, u_idx] += e_attrs["radiative"].power / e_attrs["radiative"].delta_t

            radiative_arr[v_idx, v_idx] -= e_attrs["radiative"].power / e_attrs["radiative"].delta_t

        if isinstance(e_attrs.get("radiative"), BoilerRadiativeLink):
            if e_attrs.get("radiative").is_on and v_attrs["temperature"] > u_attrs["temperature"]:
                boiler_power = e_attrs["radiative"].power / e_attrs["radiative"].delta_t
            else:
                boiler_power = 0.0
            boiler_radiative_arr[u_idx, u_idx] -= boiler_power

            boiler_radiative_arr[u_idx, v_idx] += boiler_power
            boiler_radiative_arr[v_idx, u_idx] += boiler_power

            boiler_radiative_arr[v_idx, v_idx] -= boiler_power

            # We still need this step to check if the boiler is on in the next calculation,
            # but at dt = 0 to avoid changing anything.
            e_attrs["radiative"].step(
                u_attrs,
                v_attrs,
                dt=0.0,
                thermostat_temperature=kelvin_to_celsius(temperature_vec[node_to_idx[BuildingElement.InternalAir]]),
            )

        if isinstance(e_attrs.get("radiative"), RadiativeLink):
            # We don't actually handle the direct energy gains here, as they
            # should be on the right hand side of the heat balance equation (I think)
            pass
    return conductive_arr + convective_arr + radiative_arr + additive_radiative_arr + boiler_radiative_arr


def network_to_gains_vector(hm: HeatNetwork) -> np.ndarray[tuple[GraphSize], np.dtype[np.float64]]:
    """
    Create the vector on the right-hand-size of the heat balance network representing thermal gains in W.

    This includes:
    - Solar gains
    - Internal gains

    Note that it does not include the heat capacity vector, which you should get via
    `network_to_heat_capacity_vector(hm)`.

    Parameters
    ----------
    hm
        HeatNetwork where nodes have temperature in °C and thermal_mass in J / K, and edges representing thermal gains.

    Returns
    -------
        Vector with units of W
    """
    node_to_idx = create_node_to_index_map(hm)
    vec = np.zeros([len(node_to_idx)], dtype=np.float64)

    for node in hm.nodes(data=False):
        idx = node_to_idx[node]
        if idx is None:
            continue
        # Watch out as neighbours may not be symmetric in a directed graph,
        # i.e. the edge (u, v) means that v is a neighbour of u, but not that u is a neighbour of v.
        # Your gain edges (solar, internal, heating) should specifically be from heat source to heat sink
        for neighbour in hm.neighbors(node):
            edge = hm.edges[node, neighbour]
            if isinstance(edge.get("radiative"), RadiativeLink):
                v_idx = node_to_idx[neighbour]
                vec[idx] += edge["radiative"].power
                vec[v_idx] -= edge["radiative"].power
            if isinstance(edge.get("radiative"), BoilerRadiativeLink):
                # TODO (2024-12-05 MHJB): heating power should come in here?
                pass

    for u, v, e_attrs in hm.edges(data=True):
        if BuildingElement.ExternalAir in (u, v):
            u_attrs, v_attrs = hm.nodes[u], hm.nodes[v]

            # We don't track the energy change for the external air here,
            # as it has an infinite thermal mass.
            # So select the index corresponding to the non-External-Air edge
            idx = node_to_idx[u] if u != BuildingElement.ExternalAir else node_to_idx[v]

            if isinstance(e_attrs.get("convective"), ConvectiveLink):
                vec[idx] += e_attrs["convective"].step(u_attrs, v_attrs, dt=1.0)

            if isinstance(e_attrs.get("conductive"), ConductiveLink):
                vec[idx] += e_attrs["conductive"].step(u_attrs, v_attrs, dt=1.0)

            # TODO (2024-12-06 MHJB): other links implemented here?

    return vec


def network_to_heat_capacity_vec(hm: HeatNetwork) -> np.ndarray[tuple[GraphSize], np.dtype[np.float64]]:
    """
    Create a vector of heat capacities by node.

    This vector may be useful to embed on the diagonal of a larger matrix,
    as the product of this and the current temperatures will give you the thermal energy
    of every node in the system.

    Nodes with an infinite heat capacity are overwritten with zero heat capacity, so be careful.

    Parameters
    ----------
    hm
        HeatNetwork where nodes have temperature in °C and thermal_mass in J / K

    Returns
    -------
        Vector with units of J / K
    """
    node_to_idx = create_node_to_index_map(hm)

    hc_vec = np.zeros([len(node_to_idx)], dtype=np.float64)
    for node, heat_capacity in hm.nodes(data="thermal_mass"):
        idx = node_to_idx[node]
        if idx is None:
            continue
        hc_vec[idx] = heat_capacity if np.isfinite(heat_capacity) else 0.0
    return hc_vec


def solve_heat_balance_equation(
    hm: HeatNetwork, dt: datetime.timedelta, heating_power: float = 0.0
) -> np.ndarray[tuple[GraphSize], np.dtype[np.float64]]:
    """
    Solve the heat balance equation to get a new set of temperatures in Kelvin.

    The heat balance equations are of the form
    (heat capacity + internal flows * dt) * T_new = (heat capacity * T_old) + external gains * dt
    such that the balance of internal flows and external gains / losses leads to consistent temperatures.

    Assigning heat flows to either the left hand side (flows matrix) or the right hand side (gains vector)
    can be difficult.
    Generally, you only want to include elements in the flows matrix if they have a finite heat capacity or temperature
    which you are interested in tracking.
    Elements with :
        * infinite temperatures (the sun),
        * non-temperature-varying gains (internal electricals) or
        * infinite heat capacities (outside air)
    should be included in the RHS gains vector.

    Parameters
    ----------
    hm
        A HeatNetwork where edges represent thermal links, and nodes have temperatures and heat capacities.
    dt
        Timestep over which to accumulate gains and do internal flows.
    heating_power
        Power from the heating system in Watts

    Returns
    -------
        New temperatures in Kelvin.
    """
    dt_seconds = dt.total_seconds()

    # TODO (2024-12-06 MHJB: the heat capacity and energy matrix vectors shouldn't change over time,
    # so can we keep them between invocations?
    rhs_vec = (network_to_heat_capacity_vec(hm) * network_to_temperature_vec(hm)) + (network_to_gains_vector(hm) * dt_seconds)

    if heating_power != 0.0:
        heating_vec = np.zeros_like(rhs_vec)
        node_to_idx = create_node_to_index_map(hm)
        # Heating contributions go straight to the internal air, bypassing the heating system
        # TODO (2024-12-09 MHJB): I don't like this, but solving the system of equations doesn't seem to
        # correctly distribute the heat
        heating_vec[node_to_idx[BuildingElement.InternalAir]] += heating_power * dt_seconds
        rhs_vec += heating_vec

    lhs_matr = np.diag(network_to_heat_capacity_vec(hm)) + (network_to_energy_matrix(hm) * dt_seconds)

    assert scipy.linalg.issymmetric(lhs_matr), "Matrix is not symmetric"

    res: np.ndarray[tuple[GraphSize], np.dtype[np.float64]] = scipy.linalg.solve(lhs_matr, rhs_vec, assume_a="sym")  # type: ignore
    return res


def interpolate_heating_power(
    hm: HeatNetwork,
    dt: datetime.timedelta,
    internal_temperature: float = 21.0,
    external_temperature: float = -2.0,
    max_heat_power: float = 1e4,
) -> float:
    """
    Find the heating energy required over a time period in J for a heat network with an ExternalAir component.

    This will find the required heating power by interpolating between the internal temperature at 0 heating power,
    and the internal temperature at MAX_HEAT_POWER heating power.
    The heating power required is then the interpolation at `internal_air_temperature` degrees between those two points.

    The heat network's `ExternalAir` temperature will be set to the external air temperature, which should be the
    mean air temperature over the period of interest.

    Parameters
    ----------
    hm
        HeatNetwork with InternalAir, ExternalAir and fabric nodes. Set the ExternalAir "temperature" parameter to the
        mean air temperature over the time period of interest.
    dt
        Timestep to solve for energy flows over
    internal_air_temperature
        Internal air temperature that we want to target with the thermstat
    external_air_temperature
        External air temperature during the period of interest, probably the mean air temperature
    max_heat_power
        The maximum power of a hypothetical boiler, which should be enough to moderately overheat the building.

    Parameters
    ----------
        Heating energy in Joules (note: not power in Watts!) required to keep the given internal temperature
        over this time period given a specific external temperature. You probably want to turn this into kWh
        for presentation, or keep it in J for further calculations.
    """
    hm_2: HeatNetwork = copy.deepcopy(hm)

    hm_2.nodes[BuildingElement.InternalAir]["temperature"] = internal_temperature
    hm_2.nodes[BuildingElement.ExternalAir]["temperature"] = external_temperature

    cold_temperatures = solve_heat_balance_equation(hm_2, dt, heating_power=0.0)
    hot_temperatures = solve_heat_balance_equation(hm_2, dt, heating_power=max_heat_power)

    internal_air_idx = create_node_to_index_map(hm)[BuildingElement.InternalAir]
    return float(
        dt.total_seconds()
        * max_heat_power
        * (celsius_to_kelvin(internal_temperature) - cold_temperatures[internal_air_idx])
        / (hot_temperatures[internal_air_idx] - cold_temperatures[internal_air_idx])
    )
