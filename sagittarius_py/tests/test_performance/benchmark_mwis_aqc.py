"""Phase 16 deterministic weighted-MWIS/UDG benchmark family.

The tiers verify the mapping and evidence contract; they do not establish an
optimization-performance claim.  Every scenario retains its seeded graph,
schedule metadata, exact ILP reference, and (when the AQC run completes)
final-state optimal-solution probability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import numpy as np

from sagittarius import (
    SolverConfig,
    doctor,
    make_benchmark_failure_row,
    make_benchmark_row,
    write_benchmark_artifacts,
    write_benchmark_suite_artifact,
)

PROJECT_DIR = Path(__file__).resolve().parents[2] / "projects" / "mwis_udg"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from batch_verify import generate_random_udg, solve_mwis_ilp  # noqa: E402
from mwis_solver import MWIS_AQC  # noqa: E402
from solution_verify import calculate_weight, verify_independent_set  # noqa: E402


FAMILY = "optimization_aqc"
BACKEND = {"requested_backend": "CPU", "path": "cpu"}
OBSERVABLES = {"names": ["final_basis_probabilities"], "count": 1, "output_sample_count": 1}
WEIGHT_RANGE = (1.0, 1.5)
TIER_SCENARIOS = {
    "smoke": (
        {"scenario_id": "udg_weighted_n2_seed3", "n_nodes": 2, "density": 1.0, "seed": 3, "duration": 0.1},
    ),
    "correctness": (
        {"scenario_id": "udg_weighted_n3_seed17", "n_nodes": 3, "density": 0.6, "seed": 17, "duration": 0.15},
        {"scenario_id": "udg_weighted_n4_seed19", "n_nodes": 4, "density": 0.8, "seed": 19, "duration": 0.15},
    ),
    "scaling": (
        {"scenario_id": "udg_weighted_n2_seed101", "n_nodes": 2, "density": 0.8, "seed": 101, "duration": 0.15},
        {"scenario_id": "udg_weighted_n4_seed102", "n_nodes": 4, "density": 0.8, "seed": 102, "duration": 0.15},
        {"scenario_id": "udg_weighted_n6_seed103", "n_nodes": 6, "density": 0.8, "seed": 103, "duration": 0.15},
    ),
}


def _graph_payload(graph: Any) -> dict[str, Any]:
    nodes = [
        {
            "node": int(node),
            "position": [float(value) for value in graph.nodes[node]["pos"]],
            "weight": float(graph.nodes[node]["weight"]),
        }
        for node in graph.nodes()
    ]
    edges = [[int(first), int(second)] for first, second in sorted(graph.edges())]
    canonical = json.dumps({"nodes": nodes, "edges": edges}, sort_keys=True, separators=(",", ":"))
    return {
        "nodes": nodes,
        "edges": edges,
        "edge_count": len(edges),
        "average_degree": float(np.mean([degree for _, degree in graph.degree()])),
        "graph_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def _problem(scenario: Mapping[str, Any], graph_payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "problem_type": "weighted_unit_disk_mwis",
        "instance_seed": int(scenario["seed"]),
        "atom_count": int(scenario["n_nodes"]),
        "density": float(scenario["density"]),
        "blockade_radius": 1.0,
        "weight_range": list(WEIGHT_RANGE),
        "graph_sha256": graph_payload["graph_sha256"],
        "edge_count": graph_payload["edge_count"],
        "edge_list": graph_payload["edges"],
        "node_weights": [node["weight"] for node in graph_payload["nodes"]],
        "average_degree": graph_payload["average_degree"],
    }


def _solver(scenario: Mapping[str, Any]) -> dict[str, Any]:
    omega_max = float(2 * np.pi)
    return {
        "solver_type": "MWIS_AQC",
        "reference_solver": "PuLP_CBC_ILP",
        "blockade_radius": 1.0,
        "schedule": {
            "duration": float(scenario["duration"]),
            "omega": "sin_squared",
            "omega_max": omega_max,
            "delta_start": -2.0 * omega_max,
            "delta_end": "2*pi*node_weight",
        },
    }


def _optimal_probability(
    graph: Any,
    probabilities: Iterable[float],
    basis: Iterable[int],
    exact_weight: float,
    *,
    tolerance: float = 1e-6,
) -> float:
    probability = 0.0
    for value, basis_value in zip(probabilities, basis):
        bitstring = np.asarray(
            [(int(basis_value) >> index) & 1 for index in range(graph.number_of_nodes())],
            dtype=int,
        )
        if verify_independent_set(graph, bitstring) and calculate_weight(graph, bitstring) >= exact_weight - tolerance:
            probability += float(value)
    return probability


def _reference_report(
    output_dir: Path,
    scenario: Mapping[str, Any],
    graph_payload: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> str:
    path = output_dir / f"{scenario['scenario_id']}.reference.json"
    path.write_text(json.dumps({"graph": graph_payload, **payload}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def _run_scenario(
    scenario: Mapping[str, Any],
    *,
    tier: str,
    output_dir: Path,
    backend_probe: Mapping[str, Any],
    solver_factory: Callable[..., Any],
) -> dict[str, Any]:
    graph = generate_random_udg(
        int(scenario["n_nodes"]), density=float(scenario["density"]),
        blockade_radius=1.0, weight_range=WEIGHT_RANGE, seed=int(scenario["seed"]),
    )
    graph_payload = _graph_payload(graph)
    problem = _problem(scenario, graph_payload)
    solver_metadata = _solver(scenario)
    stage = "reference"
    reference_path: str | None = None
    started = time.perf_counter()
    try:
        exact_bitstring, exact_weight, ilp_status = solve_mwis_ilp(graph)
        exact_seconds = time.perf_counter() - started
        reference_path = _reference_report(
            output_dir, scenario, graph_payload,
            {
                "scenario": dict(scenario),
                "exact": {
                    "solver": "PuLP_CBC_ILP", "status": ilp_status,
                    "weight": exact_weight, "bitstring": exact_bitstring,
                    "solve_seconds": exact_seconds,
                },
                "schedule": solver_metadata["schedule"],
            },
        )
        stage = "solve"
        aqc_started = time.perf_counter()
        aqc = solver_factory(graph, blockade_radius=1.0)
        bitstring, probabilities, basis = aqc.solve_full(
            config=SolverConfig(blockade_radius=1.0), duration=float(scenario["duration"]),
        )
        aqc_seconds = time.perf_counter() - aqc_started
        candidate = np.asarray(bitstring, dtype=int)
        feasible = verify_independent_set(graph, candidate)
        candidate_weight = calculate_weight(graph, candidate)
        feasible_weight = candidate_weight if feasible else 0.0
        objective_gap = max(0.0, float(exact_weight - feasible_weight))
        approximation_ratio = feasible_weight / exact_weight if exact_weight else 1.0
        optimal_probability = _optimal_probability(graph, probabilities, basis, exact_weight)
        reference_path = _reference_report(
            output_dir, scenario, graph_payload,
            {
                "scenario": dict(scenario),
                "exact": {
                    "solver": "PuLP_CBC_ILP", "status": ilp_status,
                    "weight": exact_weight, "bitstring": exact_bitstring,
                    "solve_seconds": exact_seconds,
                },
                "aqc": {
                    "bitstring": candidate.tolist(), "weight": candidate_weight,
                    "feasible": feasible, "solve_seconds": aqc_seconds,
                    "optimal_probability": optimal_probability,
                },
                "schedule": solver_metadata["schedule"],
            },
        )
        return make_benchmark_row(
            row_id=f"{FAMILY}-{tier}-{scenario['scenario_id']}",
            scenario_id=str(scenario["scenario_id"]), family=FAMILY, tier=tier,
            status="passed", stage="validation", problem=problem, solver=solver_metadata,
            backend=BACKEND, observables=OBSERVABLES,
            metrics={
                "ilp_status": ilp_status,
                "exact_objective": exact_weight,
                "candidate_objective": candidate_weight,
                "feasible_objective": feasible_weight,
                "feasible": feasible,
                "objective_gap": objective_gap,
                "approximation_ratio": approximation_ratio,
                "exact_match": bool(feasible and objective_gap <= 1e-6),
                "optimal_success_probability": optimal_probability,
                "exact_solve_seconds": exact_seconds,
                "aqc_solve_seconds": aqc_seconds,
                "total_runtime_seconds": time.perf_counter() - started,
            },
            artifacts={"reference_report": reference_path}, disclosure_status="local_only",
        )
    except Exception as exc:
        row = make_benchmark_failure_row(
            row_id=f"{FAMILY}-{tier}-{scenario['scenario_id']}",
            scenario_id=str(scenario["scenario_id"]), family=FAMILY, tier=tier,
            stage=stage, exc=exc, problem=problem, solver=solver_metadata,
            backend=BACKEND, observables=OBSERVABLES, backend_probe=backend_probe,
            disclosure_status="local_only",
        )
        row["metrics"]["total_runtime_seconds"] = time.perf_counter() - started
        if reference_path is not None:
            row["artifacts"]["reference_report"] = reference_path
        return row


def benchmark_mwis_aqc_tier(
    tier: str,
    output_dir: str | Path = ".",
    *,
    solver_factory: Callable[..., Any] = MWIS_AQC,
) -> dict[str, Any]:
    """Run one deterministic MWIS/UDG tier and retain every scenario row."""
    if tier not in TIER_SCENARIOS:
        raise ValueError(f"Unknown MWIS benchmark tier {tier!r}.")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    backend_probe = doctor(backend="CPU", initialize_backend=False)
    rows = [
        _run_scenario(
            scenario, tier=tier, output_dir=output,
            backend_probe=backend_probe, solver_factory=solver_factory,
        )
        for scenario in TIER_SCENARIOS[tier]
    ]
    artifact = write_benchmark_artifacts(
        output_dir=output, stem=f"mwis_aqc_{tier}",
        name=f"Phase 16 weighted MWIS/UDG {tier} benchmark",
        description=(
            "Deterministic weighted UDG instances with exact PuLP/CBC references. "
            "Runtime values are local diagnostics, not optimization-performance claims."
        ),
        parameters={
            "tier": tier, "scenarios": list(TIER_SCENARIOS[tier]), "weight_range": list(WEIGHT_RANGE),
            "backend": "CPU", "disclosure_status": "local_only",
        },
        rows=rows, backend="CPU", diagnostics=backend_probe,
        columns=["row_id", "scenario_id", "status", "stage", "problem", "solver", "metrics", "artifacts", "failure"],
        benchmark_context={
            "protocol_version": "benchmark-protocol/v1", "family": FAMILY, "tier": tier,
            "command": "uv run python tests/test_performance/benchmark_mwis_aqc.py",
            "failure_policy": "Retain one structured failed row for every scenario exception.",
            "disclosure_status": "local_only",
        },
    )
    artifact["suite"] = write_benchmark_suite_artifact(
        output_dir=output, stem=f"mwis_aqc_{tier}_suite",
        suite_id=f"phase16-mwis-aqc-{tier}", family=FAMILY, tier=tier, rows=rows,
        source=artifact["artifact"]["versions"], environment={"doctor": backend_probe},
        scenario_defaults={"weight_range": list(WEIGHT_RANGE), "blockade_radius": 1.0},
    )
    return artifact


def benchmark_mwis_aqc(
    output_dir: str | Path = ".",
    *,
    tiers: Iterable[str] = tuple(TIER_SCENARIOS),
    solver_factory: Callable[..., Any] = MWIS_AQC,
) -> dict[str, dict[str, Any]]:
    """Run smoke, correctness, and bounded scaling tiers."""
    return {
        tier: benchmark_mwis_aqc_tier(tier, output_dir, solver_factory=solver_factory)
        for tier in tiers
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Phase 16 deterministic weighted MWIS/UDG benchmarks.")
    parser.add_argument("--output-dir", default="benchmark-output")
    parser.add_argument("--tier", choices=sorted(TIER_SCENARIOS), action="append", dest="tiers")
    arguments = parser.parse_args()
    results = benchmark_mwis_aqc(arguments.output_dir, tiers=tuple(arguments.tiers or TIER_SCENARIOS))
    for tier, paths in results.items():
        print(f"MWIS/AQC {tier} benchmark complete. Results saved to {paths['json']}")
