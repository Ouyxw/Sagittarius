"""Classical feasibility and objective helpers for weighted MWIS instances."""

from __future__ import annotations

from typing import Dict, List, Tuple

import networkx as nx
import numpy as np


def get_mwis_classical(graph: nx.Graph) -> Tuple[List[int], float, Dict[str, float | int]]:
    """Return an exact weighted solution and cardinality-MIS hardness counts.

    This small branch-and-bound reference is for verification instances, not
    performance claims.
    """
    nodes = list(graph.nodes())
    weights = {node: float(graph.nodes[node].get("weight", 1.0)) for node in nodes}
    best_weight = 0.0
    best_set: list[int] = []

    def solve_weighted(current: list[int], remaining: list[int], weight: float) -> None:
        nonlocal best_weight, best_set
        if not remaining:
            if weight > best_weight + 1e-9:
                best_weight, best_set = weight, list(current)
            return
        if weight + sum(weights[node] for node in remaining) <= best_weight + 1e-9:
            return
        node, rest = remaining[0], remaining[1:]
        if all(neighbor not in current for neighbor in graph.neighbors(node)):
            solve_weighted(
                current + [node],
                [candidate for candidate in rest if candidate not in graph.neighbors(node)],
                weight + weights[node],
            )
        solve_weighted(current, rest, weight)

    solve_weighted([], nodes, 0.0)

    maximum_size = 0
    counts = {"n_mis": 0, "n_mis_minus_1": 0}

    def find_maximum_size(current: list[int], remaining: list[int]) -> None:
        nonlocal maximum_size
        if not remaining:
            maximum_size = max(maximum_size, len(current))
            return
        if len(current) + len(remaining) <= maximum_size:
            return
        node, rest = remaining[0], remaining[1:]
        if all(neighbor not in current for neighbor in graph.neighbors(node)):
            find_maximum_size(
                current + [node],
                [candidate for candidate in rest if candidate not in graph.neighbors(node)],
            )
        find_maximum_size(current, rest)

    def count_sets(current: list[int], remaining: list[int]) -> None:
        if not remaining:
            if len(current) == maximum_size:
                counts["n_mis"] += 1
            elif len(current) == maximum_size - 1:
                counts["n_mis_minus_1"] += 1
            return
        if len(current) + len(remaining) < maximum_size - 1:
            return
        node, rest = remaining[0], remaining[1:]
        if all(neighbor not in current for neighbor in graph.neighbors(node)):
            count_sets(
                current + [node],
                [candidate for candidate in rest if candidate not in graph.neighbors(node)],
            )
        count_sets(current, rest)

    find_maximum_size([], nodes)
    count_sets([], nodes)
    return (
        [1 if node in best_set else 0 for node in nodes],
        best_weight,
        {
            "mis_size": maximum_size,
            "n_mis": counts["n_mis"],
            "n_mis_minus_1": counts["n_mis_minus_1"],
            "h_param": counts["n_mis_minus_1"] / counts["n_mis"] if counts["n_mis"] else 0.0,
        },
    )


def verify_independent_set(graph: nx.Graph, bitstring: np.ndarray) -> bool:
    """Return whether ``bitstring`` selects no adjacent pair in ``graph``."""
    nodes = list(graph.nodes())
    if len(bitstring) != len(nodes):
        raise ValueError("bitstring length must match the graph node count")
    active_nodes = [nodes[index] for index, value in enumerate(bitstring) if int(value) == 1]
    return not any(
        graph.has_edge(first, second)
        for index, first in enumerate(active_nodes)
        for second in active_nodes[index + 1 :]
    )


def calculate_weight(graph: nx.Graph, bitstring: np.ndarray) -> float:
    """Return the selected node-weight sum in graph-node iteration order."""
    nodes = list(graph.nodes())
    if len(bitstring) != len(nodes):
        raise ValueError("bitstring length must match the graph node count")
    return float(
        sum(
            float(graph.nodes[node].get("weight", 1.0))
            for index, node in enumerate(nodes)
            if int(bitstring[index]) == 1
        )
    )
