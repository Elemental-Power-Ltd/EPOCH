"""Simulation and differential equation integration functions (time propagation)."""

import datetime
from collections import defaultdict
from copy import deepcopy

import numpy as np
import numpy.typing as npt
import pandas as pd

from ..utils.conversions import kelvin_to_celsius
from .building_elements import BuildingElement
from .links import BoilerRadiativeLink
from .matrix import create_node_to_index_map, interpolate_heating_power, solve_heat_balance_equation
from .network import HeatNetwork


def step_graph_midpoint(g: HeatNetwork, dt: float) -> HeatNetwork:
    """
    Update the temperatures over a timestep given the midpoint integration method.

    This will treat the heating power as being the average of the heating power at the start
    and end of a timestep, and propagate that.
    It is slower but more accurate than the naive method.

    Parameters
    ----------
    g
        A HeatNetwork you wish to propagate through time.
    dt
        A timestep in seconds

    Returns
    -------
    HeatNetwork
        The HeatNetwork after `dt` seconds have passed, integrated with the midpoint method.
    """
    g2 = deepcopy(g)
    for u, v, edge_attrs in g.edges(data=True):
        u_attrs, v_attrs = g.nodes[u], g.nodes[v]
        if edge_attrs.get("conductive") is not None:
            edge_attrs["conductive"].step(u_attrs, v_attrs, dt)
        if edge_attrs.get("convective") is not None:
            edge_attrs["convective"].step(u_attrs, v_attrs, dt)
        if edge_attrs.get("radiative") is not None:
            edge_attrs["radiative"].step(u_attrs, v_attrs, dt)
    # g2 is the heat network after a single Euler timestep.
    g2 = deepcopy(g)
    update_temperatures(g2)

    for u, v, edge_attrs in g2.edges(data=True):
        u_attrs, v_attrs = g2.nodes[u], g2.nodes[v]
        if edge_attrs.get("conductive") is not None:
            edge_attrs["conductive"].step(u_attrs, v_attrs, dt)
        if edge_attrs.get("convective") is not None:
            edge_attrs["convective"].step(u_attrs, v_attrs, dt)
        if edge_attrs.get("radiative") is not None:
            edge_attrs["radiative"].step(u_attrs, v_attrs, dt)

    for u in g.nodes(data=False):
        g.nodes[u]["energy_change"] += g2.nodes[u]["energy_change"]
        g.nodes[u]["energy_change"] /= 2.0
    update_temperatures(g)
    return g


def update_temperatures(graph: HeatNetwork) -> HeatNetwork:
    """
    Update the temperatures of the graph after all the energy changes have happened.

    This will reset the energy changes metric, so make sure you've used it before now.

    Parameters
    ----------
    graph
        A networkx graph, where the nodes have attributes `"energy_change"`, `"thermal_mass"` and `"temperature"`.

    Returns
    -------
    HeatNetwork
        Graph from arguments with temperature attributes updated.
    """
    for u, data in sorted(graph.nodes(data=True)):
        delta_t = data["energy_change"] / data["thermal_mass"]
        if not np.isfinite(delta_t):
            delta_t = 0.0
        graph.nodes[u]["temperature"] += delta_t
        # Reset the energy changes now we've used them
        graph.nodes[u]["energy_change"] = 0.0
    return graph


def update_temperatures_from_vec(graph: HeatNetwork, vec: npt.NDArray) -> HeatNetwork:
    """
    Update the temperatures of the graph after all the energy changes have happened.

    This will reset the energy changes metric, so make sure you've used it before now.

    Parameters
    ----------
    graph
        A networkx graph, where the nodes have attributes `"energy_change"`, `"thermal_mass"` and `"temperature"`.

    Returns
    -------
    HeatNetwork
        Graph from arguments with temperature attributes updated.
    """
    node_to_idx = create_node_to_index_map(graph)

    for u, idx in node_to_idx.items():
        graph.nodes[u]["temperature"] = vec[idx]
        # Reset the energy changes now we've used them
        graph.nodes[u]["energy_change"] = 0.0
    return graph


def lerp(ts: pd.Timestamp | datetime.datetime, times: pd.DatetimeIndex, values: pd.Series) -> float:
    """
    Interpolate a given timestamp from an array of existing times and measurements.

    Mostly here to keep numpy and mypy happy.

    Parameters
    ----------
    ts
        Timestamp to interpolate for (x)
    times
        Times of the taken values (xs)
    values
        Values to interpolate between (ys)

    Returns
    -------
    float
        Interpolated value
    """
    x = np.datetime64(ts).astype(np.float64)
    xs: npt.NDArray[np.float64] = times.to_numpy(dtype=np.datetime64).astype(np.float64)

    return float(np.interp(x, xs, values))


def simulate(
    graph: HeatNetwork,
    start_ts: datetime.datetime,
    external_df: pd.DataFrame | None = None,
    end_ts: datetime.datetime | None = None,
    dt: datetime.timedelta | None = None,
) -> pd.DataFrame:
    """
    Simulate the time series evolution of this heating network.

    At each step, we'll iterate over the edges of the graph. The nodes on either side will be
    updated, according to the connections along those edges.
    We calculate an energy change first, and then turn that into a temperature later on.

    Parameters
    ----------
    graph
        A heat network graph where nodes have temperatures and thermal masses, and edges represent thermal links
    external_df
        Dataframe of external weather, with a time series index and columns `temp` and `solarradiation`.
    start_time
        Earliest time point to start simulation at
    end_time
        Time point to finish the simulation at (may not finish at exactly this time depending on dt)
    dt
        Timestep between updates. Should be relatively short (of the order of five minutes), and defaults to 5 min.

    Returns
    -------
    pd.DataFrame
        Pandas dataframe with DatetimeIndex of timestamps between start_ts and end_ts, with each timestamp representing
        the start of a simulated period.
        Columns are "temperature", representing InternalAir temperature, "energy_change",
        representing the InternalAir energy change and "heating_usage" representing the energy from the heating system.
    """
    times = []
    temperatures = defaultdict(list)
    energy_changes = defaultdict(list)

    if end_ts is None:
        end_ts = start_ts.replace(year=start_ts.year + 1)
    if dt is None:
        dt = datetime.timedelta(minutes=5)
    iters = int((end_ts - start_ts).total_seconds() // dt.total_seconds())

    times = [(start_ts + i * dt).timestamp() for i in range(iters)]
    if external_df is not None:
        assert isinstance(external_df.index, pd.DatetimeIndex)
        external_temperatures = np.interp(times, external_df.index.astype("int64") // 10**9, external_df.temp)
        solar_radiations = np.interp(times, external_df.index.astype("int64") // 10**9, external_df.solarradiation)
    for i in range(iters):
        if external_df is not None:
            graph.nodes[BuildingElement.ExternalAir]["temperature"] = external_temperatures[i]
            graph.nodes[BuildingElement.Ground]["temperature"] = external_temperatures[i] - 11.0
            graph.get_edge_data(BuildingElement.Sun, BuildingElement.Roof)["radiative"].power = solar_radiations[i] * 50 * 0.33
            graph.get_edge_data(BuildingElement.Sun, BuildingElement.WallSouth)["radiative"].power = (
                solar_radiations[i] * 10 * 0.25
            )

        for u, v, edge_attrs in graph.edges(data=True):
            u_attrs, v_attrs = graph.nodes[u], graph.nodes[v]
            if edge_attrs.get("conductive") is not None:
                edge_attrs["conductive"].step(u_attrs, v_attrs, dt.total_seconds())
            if edge_attrs.get("convective") is not None:
                edge_attrs["convective"].step(u_attrs, v_attrs, dt.total_seconds())
            if edge_attrs.get("radiative") is not None:
                if isinstance(edge_attrs.get("radiative"), BoilerRadiativeLink):
                    edge_attrs["radiative"].step(
                        u_attrs, v_attrs, dt.total_seconds(), graph.nodes[BuildingElement.InternalAir]["temperature"]
                    )
                else:
                    change = edge_attrs["radiative"].step(u_attrs, v_attrs, dt.total_seconds())
                    if change != 0:
                        u_new_temp = (
                            graph.nodes[u]["temperature"] + graph.nodes[u]["energy_change"] / graph.nodes[u]["thermal_mass"]
                        )
                        v_new_temp = (
                            graph.nodes[v]["temperature"] + graph.nodes[v]["energy_change"] / graph.nodes[v]["thermal_mass"]
                        )
                        print(u, graph.nodes[u]["temperature"], u_new_temp, v, graph.nodes[v]["temperature"], v_new_temp)

        for u, temp in graph.nodes(data="temperature"):
            temperatures[u].append(temp)

        for u, energy_change in graph.nodes(data="energy_change"):
            energy_changes[u].append(energy_change)

        total_energy_change = sum(item for _, item in graph.nodes(data="energy_change"))
        assert abs(total_energy_change) < 1, f"Energy change must be < 1e-8, got {total_energy_change}"

        update_temperatures(graph)

    df = pd.DataFrame(
        index=times,
        data={
            "energy_changes": energy_changes[BuildingElement.InternalAir],
            "temperatures": temperatures[BuildingElement.InternalAir],
            "heating_usage": energy_changes[BuildingElement.HeatSource]
            if BuildingElement.HeatSource in energy_changes
            else [float("NaN") for _ in energy_changes[BuildingElement.InternalAir]],
        },
    )
    return df


def simulate_midpoint(
    graph: HeatNetwork,
    start_ts: datetime.datetime,
    external_df: pd.DataFrame | None = None,
    end_ts: datetime.datetime | None = None,
    dt: datetime.timedelta | None = None,
) -> pd.DataFrame:
    """
    Simulate the time series evolution of this heating network using the midpoint method.

    At each step, we'll iterate over the edges of the graph. The nodes on either side will be
    updated, according to the connections along those edges.
    We calculate an energy change first, and then turn that into a temperature later on.

    Parameters
    ----------
    graph
        A heat network graph where nodes have temperatures and thermal masses, and edges represent thermal links
    external_df
        Dataframe of external weather, with a time series index and columns `temp` and `solarradiation`.
    start_time
        Earliest time point to start simulation at
    end_time
        Time point to finish the simulation at (may not finish at exactly this time depending on dt)
    dt
        Timestep between updates. Should be relatively short (of the order of five minutes), and defaults to 5 min.

    Returns
    -------
    pd.DataFrame
        Pandas dataframe with DatetimeIndex of timestamps between start_ts and end_ts, with each timestamp representing
        the start of a simulated period.
        Columns are "temperature", representing InternalAir temperature, "energy_change",
        representing the InternalAir energy change and "heating_usage" representing the energy from the heating system.
    """
    times = []
    temperatures = defaultdict(list)
    energy_changes = defaultdict(list)

    if end_ts is None:
        end_ts = start_ts.replace(year=start_ts.year + 1)
    if dt is None:
        dt = datetime.timedelta(minutes=5)
    iters = int((end_ts - start_ts).total_seconds() // dt.total_seconds())

    for i in range(iters):
        time = start_ts + i * dt
        times.append(time)
        if external_df is not None:
            assert isinstance(external_df.index, pd.DatetimeIndex)
            graph.nodes[BuildingElement.ExternalAir]["temperature"] = lerp(time, external_df.index, external_df["temp"])
            graph.nodes[BuildingElement.Ground]["temperature"] = lerp(time, external_df.index, external_df["temp"]) - 11.0
            graph.get_edge_data(BuildingElement.Sun, BuildingElement.Roof)["radiative"].power = (
                lerp(time, external_df.index, external_df["solarradiation"]) * 50 * 0.33
            )
            graph.get_edge_data(BuildingElement.Sun, BuildingElement.WallSouth)["radiative"].power = (
                lerp(time, external_df.index, external_df["solarradiation"]) * 10 * 0.25
            )
        graph = step_graph_midpoint(g=graph, dt=dt.total_seconds())

        for u, temp in sorted(graph.nodes(data="temperature")):
            temperatures[u].append(temp)

        for u, energy_change in sorted(graph.nodes(data="energy_change")):
            energy_changes[u].append(energy_change)

        total_energy_change = sum(item for _, item in graph.nodes(data="energy_change"))
        assert abs(total_energy_change) < 1e-8, f"Energy change must be < 1e-8, got {total_energy_change}"

        update_temperatures(graph)

    df = pd.DataFrame(
        index=times,
        data={
            "energy_changes": energy_changes[BuildingElement.InternalAir],
            "temperatures": temperatures[BuildingElement.InternalAir],
            "heating_usage": energy_changes[BuildingElement.HeatSource]
            if BuildingElement.HeatSource in energy_changes
            else [float("NaN") for _ in energy_changes[BuildingElement.InternalAir]],
        },
    )
    return df


def simulate_heat_balance(
    graph: HeatNetwork,
    external_df: pd.DataFrame,
    start_ts: datetime.datetime,
    end_ts: datetime.datetime | None = None,
    dt: datetime.timedelta | None = None,
) -> pd.DataFrame:
    """
    Simulate the time series evolution of this heating network using the heat balance equations.

    At each step, we'll iterate over the edges of the graph. The nodes on either side will be
    updated, according to the connections along those edges.
    We calculate an energy change first, and then turn that into a temperature later on.

    Parameters
    ----------
    graph
        A heat network graph where nodes have temperatures and thermal masses, and edges represent thermal links
    external_df
        Dataframe of external weather, with a time series index and columns `temp` and `solarradiation`.
    start_time
        Earliest time point to start simulation at
    end_time
        Time point to finish the simulation at (may not finish at exactly this time depending on dt)
    dt
        Timestep between updates. Should be relatively short (of the order of five minutes), and defaults to 5 min.

    Returns
    -------
    pd.DataFrame
        Pandas dataframe with DatetimeIndex of timestamps between start_ts and end_ts, with each timestamp representing
        the start of a simulated period.
        Columns are "temperature", representing InternalAir temperature, "energy_change",
        representing the InternalAir energy change and "heating_usage" representing the energy from the heating system.
    """
    times = []
    temperatures = defaultdict(list)
    energy_changes = defaultdict(list)

    if end_ts is None:
        end_ts = start_ts.replace(year=start_ts.year + 1)
    if dt is None:
        dt = datetime.timedelta(minutes=5)
    iters = int((end_ts - start_ts).total_seconds() // dt.total_seconds())
    assert isinstance(external_df.index, pd.DatetimeIndex)
    for i in range(iters):
        time = start_ts + i * dt
        times.append(time)
        graph.nodes[BuildingElement.ExternalAir]["temperature"] = lerp(time, external_df.index, external_df["temp"])
        graph.nodes[BuildingElement.Ground]["temperature"] = lerp(time, external_df.index, external_df["temp"]) - 11.0
        graph.get_edge_data(BuildingElement.Sun, BuildingElement.Roof)["radiative"].power = (
            lerp(time, external_df.index, external_df["solarradiation"]) * 50 * 0.33
        )
        graph.get_edge_data(BuildingElement.Sun, BuildingElement.WallSouth)["radiative"].power = (
            lerp(time, external_df.index, external_df["solarradiation"]) * 10 * 0.25
        )

        heating_power = (
            interpolate_heating_power(
                graph,
                dt=dt,
                internal_temperature=21.0,
                external_temperature=kelvin_to_celsius(graph.nodes[BuildingElement.ExternalAir]["temperature"]),
            )
            / dt.total_seconds()
        )  # remember to divide by dt to go from heating eneryg to watts

        new_temp_vec = solve_heat_balance_equation(hm=graph, dt=dt, heating_power=heating_power)

        for u, temp in sorted(graph.nodes(data="temperature")):
            temperatures[u].append(temp)

        for u, energy_change in sorted(graph.nodes(data="energy_change")):
            energy_changes[u].append(energy_change)

        total_energy_change = sum(item for _, item in graph.nodes(data="energy_change"))
        assert abs(total_energy_change) < 1e-8, f"Energy change must be < 1e-8, got {total_energy_change}"

        update_temperatures_from_vec(graph, new_temp_vec)

    df = pd.DataFrame(
        index=times,
        # TODO (2024-12-11 MHJB): can we get the energy changes from the matrix? should be just the LHS times temperatures
        data={
            "energy_changes": [np.nan for _ in temperatures[BuildingElement.InternalAir]],
            "temperatures": temperatures[BuildingElement.InternalAir],
            "heating_usage": energy_changes[BuildingElement.HeatSource],
        },
    )
    return df
