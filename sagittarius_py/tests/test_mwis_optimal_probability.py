"""Regression coverage for MWIS probability/feasibility semantics."""

from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parents[1] / "projects" / "mwis_udg"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from batch_verify import _optimal_probability, solve_mwis_ilp  # noqa: E402


def test_optimal_probability_excludes_infeasible_high_weight_basis_states():
    graph = nx.Graph()
    graph.add_nodes_from((node, {"weight": 1.0}) for node in range(3))
    graph.add_edges_from(((0, 1), (1, 2)))
    _, exact_weight, status = solve_mwis_ilp(graph)

    # ``111`` has a larger raw weight than the independent-set optimum, but
    # cannot contribute to the probability of an optimal feasible solution.
    probability = _optimal_probability(
        graph,
        probabilities=np.asarray([1.0]),
        basis=[0b111],
        exact_weight=exact_weight,
        tolerance=1e-6,
    )

    assert status == "Optimal"
    assert probability == 0.0
