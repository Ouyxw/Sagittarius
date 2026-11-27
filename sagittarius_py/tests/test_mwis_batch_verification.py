from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

PROJECT_DIR = Path(__file__).resolve().parents[1] / "projects" / "mwis_udg"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from batch_verify import (  # noqa: E402
    MWIS_BATCH_ARTIFACT_TYPE,
    MWIS_BATCH_SCHEMA_VERSION,
    generate_random_udg,
    solve_mwis_ilp,
    verify_mwis_batch,
)
from solution_verify import calculate_weight, verify_independent_set  # noqa: E402


class ExactSolver:
    def __init__(self, graph, blockade_radius=1.0):
        self.graph = graph

    def solve_full(self, config=None, duration=1.0):
        bitstring, _, _ = solve_mwis_ilp(self.graph)
        basis_value = sum(bit << index for index, bit in enumerate(bitstring))
        basis = list(range(2 ** self.graph.number_of_nodes()))
        probabilities = np.zeros(len(basis))
        probabilities[basis_value] = 1.0
        return np.array(bitstring), probabilities, basis


class EmptySolver:
    def __init__(self, graph, blockade_radius=1.0):
        self.graph = graph

    def solve(self, config=None, duration=1.0):
        return [0] * self.graph.number_of_nodes()


def test_generate_random_udg_is_seeded_and_weighted():
    first = generate_random_udg(6, density=0.7, seed=123)
    second = generate_random_udg(6, density=0.7, seed=123)

    assert first.number_of_nodes() == 6
    assert sorted(first.edges()) == sorted(second.edges())
    assert [first.nodes[node]["pos"] for node in first.nodes()] == [second.nodes[node]["pos"] for node in second.nodes()]
    assert all(1.0 <= first.nodes[node]["weight"] <= 1.5 for node in first.nodes())


def test_solve_mwis_ilp_returns_valid_optimum():
    graph = generate_random_udg(7, density=0.8, seed=77)

    bitstring, weight, status = solve_mwis_ilp(graph)

    assert status == "Optimal"
    assert verify_independent_set(graph, np.array(bitstring))
    assert weight == calculate_weight(graph, np.array(bitstring))


def test_verify_mwis_batch_reports_exact_matches_with_injected_solver():
    report = verify_mwis_batch(
        n_instances=3,
        n_nodes=5,
        densities=(0.4, 0.7),
        seed=5,
        duration=1.5,
        solver_factory=ExactSolver,
    )

    payload = report.to_dict()

    assert payload["schema_version"] == MWIS_BATCH_SCHEMA_VERSION
    assert payload["artifact_type"] == MWIS_BATCH_ARTIFACT_TYPE
    assert payload["success_count"] == 3
    assert payload["valid_count"] == 3
    assert payload["mean_approximation_ratio"] == 1.0
    assert payload["mean_optimal_probability"] == 1.0
    assert [instance["density"] for instance in payload["instances"]] == [0.4, 0.7, 0.4]
    assert all(instance["ilp_status"] == "Optimal" for instance in payload["instances"])


def test_verify_mwis_batch_records_suboptimal_aqc_output():
    report = verify_mwis_batch(
        n_instances=2,
        n_nodes=5,
        densities=(0.5,),
        seed=9,
        solver_factory=EmptySolver,
    )

    assert report.valid_count == 2
    assert report.success_count < report.n_instances
    assert report.mean_approximation_ratio < 1.0
    assert all(instance.aqc_valid_independent_set for instance in report.instances)
