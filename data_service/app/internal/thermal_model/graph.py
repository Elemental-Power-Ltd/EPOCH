"""Drawn graphs and visualisations of the network."""

from collections import defaultdict

import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx

from .building_elements import BuildingElement


def draw_heat_network(G: nx.Graph, ax: mpl.axes._axes.Axes | None = None) -> mpl.axes._axes.Axes:
    """
    Draw a network representation of this graph.

    Here, nodes are coloured by their material type and each node has an encompassing circle representing temperature.
    Red is hot nodes, blue is cool nodes.

    The edges represent thermal links between the nodes, but aren't sorted by type.

    Parameters
    ----------
    G
        The heat network to draw
    ax
        The axis to draw onto, but will create one if necessary

    Returns
    -------
        Drawn upon axis for this rendering of the heat network.
    """
    if ax is None:
        _, ax = plt.subplots()

    cmap = plt.get_cmap("coolwarm")
    norm = mpl.colors.Normalize(vmin=15, vmax=21, clip=True)
    COLOUR_DICT: dict[BuildingElement, str] = defaultdict(lambda: "#4376b1")
    COLOUR_DICT = COLOUR_DICT | {
        BuildingElement.WallEast: "#ba7950",
        BuildingElement.WallWest: "#ba7950",
        BuildingElement.WallSouth: "#ba7950",
        BuildingElement.WallNorth: "#ba7950",
        BuildingElement.Sun: "#f3e682",
        BuildingElement.Roof: "#a1a5a8",
        BuildingElement.Floor: "#a1a5a8",
        BuildingElement.Ground: "#948d84",
        BuildingElement.HeatingSystem: "#e7e3e1",
    }

    nx.draw_networkx(
        G,
        ax=ax,
        node_color=[COLOUR_DICT[node] for node in G.nodes()],
        edgecolors=[cmap(norm(item["temperature"])) for _, item in G.nodes(data=True)],
        linewidths=2.0,
    )
    return ax
