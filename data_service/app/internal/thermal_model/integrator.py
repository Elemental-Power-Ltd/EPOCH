"""Simulation and differential equation integration functions (time propagation)."""

import datetime
from collections import defaultdict

import networkx as nx
import numpy as np
import numpy.typing as npt
import pandas as pd

from .links import BoilerRadiativeLink


def update_temperatures(graph: nx.Graph) -> nx.Graph:
    """
    Update the temperatures of the graph after all the energy changes have happened.

    This will reset the energy changes metric, so make sure you've used it before now.

    Parameters
    ----------
    graph
        A networkx graph, where the nodes have attributes `"energy_change"`, `"thermal_mass"` and `"temperature"`.

    Returns
    -------
    nx.Graph
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


def property_to_list(graph: nx.Graph, attr: str) -> list[float]:
    """
    Extract an attribute held by graph nodes (temperature, energy change) and create a list.

    These lists will be sorted consistently by the names of the nodes.

    Parameters
    ----------
    graph
        Graph with sortable node names and some properties
    property
        Name of the property to extract into a list

    Returns
    -------
        list of that property from each node, sorted by node names
    """
    return [prop for _, prop in sorted(graph.nodes(data=attr), key=lambda t: t[0])]


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
    xs: npt.NDArray[np.float64] = times.to_numpy().astype(np.float64)

    return float(np.interp(x, xs, values))


def simulate(
    graph: nx.Graph,
    external_df: pd.DataFrame,
    start_time: datetime.datetime,
    end_time: datetime.datetime | None = None,
    dt: float = 300.0,
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
        Timestep in seconds between updates. Should be relatively short ()
    """
    times = []
    temperatures = defaultdict(list)
    energy_changes = defaultdict(list)

    if end_time is None:
        end_time = start_time.replace(year=start_time.year + 1)

    iters = int((end_time - start_time).total_seconds() // dt)
    assert isinstance(external_df.index, pd.DatetimeIndex)
    for it in range(iters):
        time = start_time + datetime.timedelta(seconds=dt * it)
        times.append(time)
        graph.nodes["External"]["temperature"] = lerp(time, external_df.index, external_df["temp"])
        graph.nodes["Ground"]["temperature"] = lerp(time, external_df.index, external_df["temp"]) - 11.0
        graph.get_edge_data("Sun", "Roof")["radiative"].power = (
            lerp(time, external_df.index, external_df["solarradiation"]) * 50 * 0.33
        )
        graph.get_edge_data("Sun", "Wall_South")["radiative"].power = (
            lerp(time, external_df.index, external_df["solarradiation"]) * 10 * 0.25
        )
        for u, v, edge_attrs in graph.edges(data=True):
            u_attrs, v_attrs = graph.nodes[u], graph.nodes[v]
            if edge_attrs.get("conductive") is not None:
                edge_attrs["conductive"].step(u_attrs, v_attrs, dt)
            if edge_attrs.get("convective") is not None:
                edge_attrs["convective"].step(u_attrs, v_attrs, dt)
            if edge_attrs.get("radiative") is not None:
                if isinstance(edge_attrs.get("radiative"), BoilerRadiativeLink):
                    edge_attrs["radiative"].step(u_attrs, v_attrs, dt, graph.nodes["Air"]["temperature"])
                else:
                    edge_attrs["radiative"].step(u_attrs, v_attrs, dt)

        for u, temp in sorted(graph.nodes(data="temperature")):
            temperatures[u].append(temp)

        for u, energy_change in sorted(graph.nodes(data="energy_change")):
            energy_changes[u].append(energy_change)

        total_energy_change = sum(item for _, item in graph.nodes(data="energy_change"))
        assert abs(total_energy_change) < 1e-8, f"Energy change must be < 1e-8, got {total_energy_change}"

        update_temperatures(graph)

    df = pd.DataFrame(
        index=times,
        data={"energy_changes": energy_changes, "temperatures": temperatures},
    )
    return df
