"""CPU smoke benchmarks for the Phase 16 physics-baseline family.

This runner is deliberately a smoke-tier command: its runtime values are
diagnostic only. It writes one ``benchmark-artifact/v1`` envelope and persists
each successful simulation's ``result-artifact/v1`` and ``run-manifest/v1``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from sagittarius import (
    Atom,
    PulseSequence,
    Register,
    Simulation,
    SolverConfig,
    benchmark_failure_from_exception,
    current_memory_usage,
    doctor,
    make_benchmark_row,
    write_benchmark_artifacts,
    write_benchmark_suite_artifact,
)

_FAMILY = "physics_baselines"
_TIER = "smoke"
_DISCLOSURE_STATUS = "local_only"
_ENVIRONMENT_KEYS = (
    "JULIA_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "SAGITTARIUS_ENABLE_GPU_TESTS",
)


def _memory_megabytes() -> float | None:
    memory = current_memory_usage()
    if not memory["available"] or memory["max_rss"] is None:
        return None
    value = float(memory["max_rss"])
    return value / 1024.0 if "KiB" in str(memory["max_rss_unit"]) else value / (1024.0**2)


def _rabi() -> tuple[dict[str, Any], Simulation, np.ndarray, float, dict[str, Any], dict[str, Any]]:
    omega = float(2.0 * np.pi)
    config = SolverConfig(reltol=1e-9, abstol=1e-9, saveat=[0.0, 0.5, 1.0])
    simulation = Simulation(
        Register([Atom(0.0, 0.0)], C6=0.0),
        PulseSequence(omega=omega, delta=0.0),
        config,
    )
    expected = np.sin(omega * np.asarray(config.saveat, dtype=float) / 2.0) ** 2
    return (
        {
            "scenario_id": "rabi_n1_cpu_seed_none",
            "problem": {
                "type": "single_atom_rabi",
                "atom_count": 1,
                "geometry": "single_atom",
                "omega": omega,
                "delta": 0.0,
                "duration": 1.0,
                "seed": None,
            },
            "observables": {"names": ["rydberg_population"], "count": 1, "output_sample_count": 3},
        },
        simulation,
        np.array([1.0, 0.0], dtype=np.complex128),
        1.0,
        {"rydberg_population": 0},
        {"reference": expected, "tolerance": 1e-6},
    )


def _blockade() -> tuple[dict[str, Any], Simulation, np.ndarray, float, dict[str, Any], dict[str, Any]]:
    config = SolverConfig(blockade_radius=1.5, reltol=1e-9, abstol=1e-9, saveat=3)
    simulation = Simulation(
        Register([Atom(0.0, 0.0), Atom(1.0, 0.0)], C6=100.0),
        PulseSequence(omega=float(2.0 * np.pi), delta=0.0),
        config,
    )
    return (
        {
            "scenario_id": "blockade_n2_reduced_cpu_seed_none",
            "problem": {
                "type": "two_atom_rydberg_blockade",
                "atom_count": 2,
                "geometry": "chain",
                "spacing": 1.0,
                "C6": 100.0,
                "blockade_radius": 1.5,
                "duration": 0.5,
                "seed": None,
            },
            "observables": {"names": ["double_excitation"], "count": 1, "output_sample_count": 3},
        },
        simulation,
        np.array([1.0, 0.0, 0.0], dtype=np.complex128),
        0.5,
        {"double_excitation": {"type": "bitstring_probability", "bitstring": "11"}},
        {"tolerance": 1e-12},
    )


_SCENARIOS: dict[str, Callable[[], tuple[dict[str, Any], Simulation, np.ndarray, float, dict[str, Any], dict[str, Any]]]] = {
    "rabi": _rabi,
    "blockade": _blockade,
}


def _solver_metadata(simulation: Simulation, result: Any) -> dict[str, Any]:
    diagnostics = result.diagnostics.get("simulation", {})
    return {
        "method": simulation.config.method,
        "reltol": simulation.config.reltol,
        "abstol": simulation.config.abstol,
        "adaptive": simulation.config.adaptive,
        "dt": simulation.config.dt,
        "saveat": simulation.config.saveat,
        "effective": diagnostics,
    }


def _backend_metadata(diagnostics: dict[str, Any]) -> dict[str, Any]:
    return {
        "requested_backend": "CPU",
        "path": "cpu",
        "doctor_available": diagnostics.get("available"),
        "backend_probe": diagnostics.get("backend_probe"),
    }


def _unknown_scenario_row(scenario: str, diagnostics: dict[str, Any]) -> dict[str, Any]:
    failure = {
        "stage": "setup",
        "exception_type": "ValueError",
        "code": "BENCHMARK_SCENARIO_UNKNOWN",
        "message": f"Unknown physics smoke scenario {scenario!r}.",
        "remediation": "Choose one of: " + ", ".join(sorted(_SCENARIOS)),
        "deterministic": True,
    }
    return make_benchmark_row(
        row_id=f"physics-smoke-{scenario}",
        scenario_id=scenario,
        family=_FAMILY,
        tier=_TIER,
        status="failed",
        stage="setup",
        problem={"type": "unknown", "seed": None},
        solver={},
        backend=_backend_metadata(diagnostics),
        observables={"names": [], "count": 0, "output_sample_count": 0},
        metrics={"process_peak_memory_mb": _memory_megabytes()},
        failure=failure,
        disclosure_status=_DISCLOSURE_STATUS,
    )


def benchmark_physics_smoke(
    output_dir: str | Path = ".",
    *,
    scenario_names: tuple[str, ...] = ("rabi", "blockade"),
) -> dict[str, Any]:
    """Run Rabi and blockade CPU smoke cases and emit retained evidence."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    results_path = output_path / "physics_smoke_results"
    results_path.mkdir(parents=True, exist_ok=True)
    diagnostics = doctor(backend="CPU", initialize_backend=True)
    rows: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []

    for name in scenario_names:
        scenario_factory = _SCENARIOS.get(name)
        if scenario_factory is None:
            rows.append(_unknown_scenario_row(name, diagnostics))
            continue

        scenario, simulation, initial_state, duration, observables, reference = scenario_factory()
        scenario_id = scenario["scenario_id"]
        start = time.perf_counter()
        try:
            result = simulation.run(initial_state, 0.0, duration, observables=observables)
            elapsed = time.perf_counter() - start
            if name == "rabi":
                error = float(np.max(np.abs(np.asarray(result.data["rydberg_population"]) - reference["reference"])))
                if error > reference["tolerance"]:
                    raise AssertionError(f"Rabi max_abs_error {error} exceeds tolerance {reference['tolerance']}.")
                correctness = {"max_abs_error": error, "reference": "analytic_rabi_population"}
            else:
                max_double_excitation = float(np.max(np.abs(np.asarray(result.data["double_excitation"]))))
                if max_double_excitation > reference["tolerance"]:
                    raise AssertionError(
                        f"Blockade double-excitation probability {max_double_excitation} exceeds tolerance {reference['tolerance']}."
                    )
                correctness = {
                    "max_abs_error": max_double_excitation,
                    "reference": "reduced_basis_forbids_bitstring_11",
                }

            result_path = results_path / f"{scenario_id}.result.json"
            manifest_path = results_path / f"{scenario_id}.manifest.json"
            result.save(str(result_path))
            manifest_path.write_text(json.dumps(result.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            artifacts = {"run_manifest": str(manifest_path), "result_artifact": str(result_path)}
            rows.append(
                make_benchmark_row(
                    row_id=f"physics-smoke-{name}",
                    scenario_id=scenario_id,
                    family=_FAMILY,
                    tier=_TIER,
                    status="passed",
                    stage="artifact",
                    problem=scenario["problem"],
                    solver=_solver_metadata(simulation, result),
                    backend=_backend_metadata(diagnostics),
                    observables={**scenario["observables"], "output_sample_count": len(result.data["t"])},
                    metrics={
                        **correctness,
                        "runtime_seconds": elapsed,
                        "process_peak_memory_mb": _memory_megabytes(),
                    },
                    artifacts=artifacts,
                    disclosure_status=_DISCLOSURE_STATUS,
                )
            )
            manifests.append({"label": scenario_id, "path": str(manifest_path), "manifest": result.manifest})
        except Exception as exc:
            rows.append(
                make_benchmark_row(
                    row_id=f"physics-smoke-{name}",
                    scenario_id=scenario_id,
                    family=_FAMILY,
                    tier=_TIER,
                    status="failed",
                    stage="validation",
                    problem=scenario["problem"],
                    solver={
                        "method": simulation.config.method,
                        "reltol": simulation.config.reltol,
                        "abstol": simulation.config.abstol,
                        "adaptive": simulation.config.adaptive,
                        "dt": simulation.config.dt,
                        "saveat": simulation.config.saveat,
                    },
                    backend=_backend_metadata(diagnostics),
                    observables=scenario["observables"],
                    metrics={"runtime_seconds": time.perf_counter() - start, "process_peak_memory_mb": _memory_megabytes()},
                    failure=benchmark_failure_from_exception(exc, stage="validation"),
                    disclosure_status=_DISCLOSURE_STATUS,
                )
            )

    context = {
        "protocol_version": "benchmark-protocol/v1",
        "family": _FAMILY,
        "tier": _TIER,
        "command": "uv run python tests/test_performance/benchmark_physics_smoke.py",
        "working_directory": str(Path.cwd()),
        "environment_variables": {key: os.environ[key] for key in _ENVIRONMENT_KEYS if key in os.environ},
        "warmup_runs": 0,
        "measured_repeats": 1,
        "timeout_policy": "No runner timeout; every scenario exception is retained as a failed row.",
        "failure_policy": "Continue after per-scenario failures and retain structured diagnostics.",
        "disclosure_status": _DISCLOSURE_STATUS,
    }
    artifact_paths = write_benchmark_artifacts(
        output_dir=output_path,
        stem="physics_smoke",
        name="Phase 16 physics baseline CPU smoke benchmark",
        description="CPU smoke cases for single-atom Rabi and two-atom blockade; runtime values are local diagnostics, not performance claims.",
        parameters={"scenarios": list(scenario_names), "backend": "CPU", "seed_policy": "deterministic/no stochastic seed"},
        rows=rows,
        backend="CPU",
        diagnostics=diagnostics,
        run_manifests=manifests,
        columns=["row_id", "scenario_id", "status", "stage", "metrics", "failure"],
        benchmark_context=context,
    )
    suite_paths = write_benchmark_suite_artifact(
        output_dir=output_path,
        stem="physics_smoke_suite",
        suite_id="phase16-physics-baselines-smoke",
        family=_FAMILY,
        tier=_TIER,
        rows=rows,
        source=artifact_paths["artifact"]["versions"],
        environment={"benchmark_context": context, "doctor": diagnostics},
        scenario_defaults={"backend": "CPU", "seed_policy": "deterministic/no stochastic seed"},
    )
    artifact_paths["suite"] = suite_paths
    return artifact_paths


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 16 CPU physics smoke benchmarks.")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--scenario", action="append", choices=sorted(_SCENARIOS), dest="scenarios")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    selected = tuple(args.scenarios) if args.scenarios else ("rabi", "blockade")
    paths = benchmark_physics_smoke(args.output_dir, scenario_names=selected)
    print(f"Physics smoke benchmark complete. Results saved to {paths['json']}")
