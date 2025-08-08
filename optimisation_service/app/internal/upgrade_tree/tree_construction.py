import itertools
from collections.abc import Iterable
from typing import cast

import networkx as nx

from app.models.core import PortfolioOptimisationResult

type ResultsDict = dict[str, PortfolioOptimisationResult]


def is_in_elec_shortfall(key: str, all_results: ResultsDict, thresh: float = 0.0) -> bool:
    """
    Check if this node is in electricity shortfall.

    Parameters
    ----------
    key
        Node to look up
    all_results
        Metrics dictionary with `key` in it
    thresh
        Maximum allowable electrical shortfall

    Returns
    -------
    bool
        True if there is no information about the shortfall, or if the shortfall is above the thresh
    """
    if all_results[key].metrics.total_electrical_shortfall is None:
        return True
    return cast(float, all_results[key].metrics.total_electrical_shortfall) > thresh


def is_in_heat_shortfall(key: str, all_results: ResultsDict, thresh: float = 0.0) -> bool:
    """
    Check if this node is in heat shortfall.

    Parameters
    ----------
    key
        Node to look up
    all_results
        Metrics dictionary with `key` in it
    thresh
        Maximum allowable heat shortfall

    Returns
    -------
    bool
        True if there is no information about the shortfall, or if the shortfall is above the thresh
    """
    if all_results[key].metrics.total_electrical_shortfall is None:
        return True
    return cast(float, all_results[key].metrics.total_heat_shortfall) > thresh


def hamming_distance(s1: Iterable, s2: Iterable) -> int:
    """
    Get the hamming distance between two strings.

    The Hamming Distance is the number of single character changes between two strings.
    e.g. hamming_distance("000", "111") = 3

    Parameters
    ----------
    s1
        String of characters
    s2
        String of characters

    Returns
    -------
    int
        Number of single character changes to make to turn s1 into s2
    """
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))


def generate_label(key: str, possible_components: Iterable[str]) -> str:
    """
    Generate a label about components from a key.

    The key should be a bitstring in the form "10101", and a "1" indicates that we include
    that component in the label.

    Parameters
    ----------
    key
        Component inclusion bitstring
    possible_components
        Human readable names of the components

    Returns
    -------
    str
        Components installed at each node, linked by newlines
    """
    label = ",\n".join(comp for c, comp in zip(key, possible_components) if bool(int(c)))
    return label


def generate_graph(all_results: ResultsDict, possible_components: list[str]) -> nx.DiGraph:
    dG: nx.DiGraph = nx.DiGraph()
    x_scale, y_scale = 10.0, 5.0
    tiers = []
    for length in range(4):
        items_with_length = sorted(filter(lambda s: sum(item == "1" for item in s) == length, all_results.keys()))
        tiers.append(items_with_length)

    dG.add_nodes_from(all_results.keys())
    for lo, hi in itertools.pairwise(tiers):
        dG.add_edges_from(
            filter(
                lambda t: (
                    hamming_distance(t[0], t[1]) == 1
                    and not is_in_elec_shortfall(t[1], all_results)
                    and not is_in_heat_shortfall(t[1], all_results)
                ),
                itertools.product(lo, hi),
            )
        )

    nx.set_node_attributes(
        dG,
        values={key: generate_label(key, possible_components=possible_components) for key in dG.nodes},
        name="label",
    )

    pos: dict[str, tuple[float, float]] = {}
    for tier_rank, tier_contents in enumerate(tiers):
        tier_len = len(tier_contents)
        for idx, item in enumerate(tier_contents):
            pos[item] = ((idx - tier_len / 2) * x_scale, tier_rank * y_scale)
    nx.set_node_attributes(dG, values=pos, name="pos")
    nx.set_node_attributes(dG, values={key: all_results[key].metrics.capex for key in all_results.keys()}, name="capex")
    edge_lengths: dict[tuple[str, str], float] = {}
    step_prices: dict[tuple[str, str], float] = {}
    carbon_savings: dict[tuple[str, str], float] = {}
    for u, v in dG.edges():
        u_cost = all_results[u].metrics.total_electricity_import_cost + all_results[u].metrics.total_gas_import_cost  # type: ignore
        v_cost = all_results[v].metrics.total_electricity_import_cost + all_results[v].metrics.total_gas_import_cost  # type: ignore

        edge_lengths[u, v] = v_cost - u_cost
        step_prices[u, v] = all_results[v].metrics.capex - all_results[u].metrics.capex  # type: ignore
        v_co2 = all_results[v].metrics.carbon_balance_scope_1 + all_results[v].metrics.carbon_balance_scope_2  # type: ignore
        u_co2 = all_results[u].metrics.carbon_balance_scope_1 + all_results[u].metrics.carbon_balance_scope_2  # type: ignore
        carbon_savings[u, v] = v_co2 - u_co2
    nx.set_edge_attributes(dG, edge_lengths, "operating_cost")
    nx.set_edge_attributes(dG, step_prices, "capex")
    nx.set_edge_attributes(dG, carbon_savings, "carbon_balance")
    return dG


def find_maximising_path(G: nx.Graph, source: str, sink: str, weight: str, sign: int = 1) -> list[str]:
    """
    Find the path the maximises (or minimises) the `weight` metric at each step.

    This starts at the `source` node and selects the edge based on what maximises (or minimises)
    the increase in the `weight` which should be a property of the edges (e.g. "operating cost")
    If you want to maximise, have `sign=1` and `sign=-1` minimises.

    Parameters
    ----------
    G
        Graph to traverse, ideally with a path between `source` and `sink`
    source
        Start node
    sink
        End node
    weight
        Edge attributes to check
    sign
        Whether to maximise (1) or minimise (-1)

    Returns
    -------
    list[str]
        List of nodes to visit in order
    """
    curr_node = source
    path = [curr_node]
    while curr_node != sink and G.neighbors(curr_node):
        neighbours = sorted(G[curr_node])
        if not neighbours:
            break
        best_saving_node = max(neighbours, key=lambda n: sign * G.get_edge_data(curr_node, n)[weight])
        curr_node = best_saving_node
        path.append(curr_node)
    return path
