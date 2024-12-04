"""Functions for the matrix formulation of temperature flows."""
from typing import NewType

import numpy as np
import numpy.typing as npt

from ..utils.conversions import celsius_to_kelvin, kelvin_to_celsius
from .building_elements import BuildingElement
from .links import BoilerRadiativeLink, ConductiveLink, ConvectiveLink, RadiativeLink, ThermalRadiativeLink
from .network import HeatNetwork

GraphSize = NewType("GraphSize", int)


def network_to_temperature_vec(hm: HeatNetwork) -> npt.NDArray[GraphSize, np.float64]:
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
    node_to_idx = {node: i for i, node in enumerate(sorted(hm.nodes))}
    temperature_vec = np.zeros([len(hm)], dtype=np.float64)
    for node, attrs in hm.nodes(data=True):
        idx = node_to_idx[node]
        temperature = attrs["temperature"]
        temperature_vec[idx] = celsius_to_kelvin(temperature) if np.isfinite(temperature) else 1.0
    return temperature_vec


def network_to_energy_matrix(hm: HeatNetwork) -> npt.NDArray[GraphSize, GraphSize, np.float64]:
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
    node_to_idx = {node: i for i, node in enumerate(sorted(hm.nodes))}

    # We use many different matrices for ease of debugging.
    # At the end, we'll group all of these into a single matrix.
    temperature_vec = network_to_temperature_vec(hm)
    heat_capacity_arr = np.zeros([len(hm), len(hm)], dtype=np.float64)
    conductive_arr = np.zeros_like(heat_capacity_arr)
    convective_arr = np.zeros_like(heat_capacity_arr)
    radiative_arr = np.zeros_like(heat_capacity_arr)
    additive_radiative_arr = np.zeros_like(heat_capacity_arr)
    boiler_radiative_arr = np.zeros_like(heat_capacity_arr)

    for node, attrs in hm.nodes(data=True):
        idx = node_to_idx[node]
        heat_cap = attrs["thermal_mass"]

        heat_capacity_arr[idx, idx] = heat_cap * temperature_vec[idx] if np.isfinite(heat_cap) else 0.0

    for u, v, e_attrs in hm.edges(data=True):
        u_idx, v_idx = node_to_idx[u], node_to_idx[v]
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
            # These are actually added on at the end as they change the total energy
            # of the system, but for the ease of doing one matrix multiplication we divide by the temperatures here
            # !! watch out for the sign convention here !! U loses and V gains (argh)
            additive_radiative_arr[u_idx, u_idx] += e_attrs["radiative"].power / temperature_vec[u_idx]
            additive_radiative_arr[v_idx, v_idx] -= e_attrs["radiative"].power / temperature_vec[v_idx]
    return conductive_arr + convective_arr + radiative_arr + additive_radiative_arr + boiler_radiative_arr
