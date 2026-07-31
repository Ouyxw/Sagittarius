"""Phase 16 CPU correctness benchmarks for physics baselines.

The runner is optional in ordinary PR CI.  It retains an aggregate
``benchmark-artifact/v1`` and one result/manifest pair for every SDK solver
case.  Runtime metrics are local diagnostics, never performance claims.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from sagittarius import (
    Atom,
    Pulse,
    PulseSequence,
    Register,
    Simulation,
    SolverConfig,
    benchmark_failure_from_exception,
    current_memory_usage,
    dense_vs_reduced_validation,
    doctor,
    make_benchmark_row,
    write_benchmark_artifacts,
)

FAMILY = "physics_baselines"
TIER = "correctness"
_ENVIRONMENT_KEYS = ("JULIA_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "SAGITTARIUS_ENABLE_GPU_TESTS")


def _memory_mb() -> float | None:
    usage = current_memory_usage()
    if not usage["available"] or usage["max_rss"] is None:
        return None
    return float(usage["max_rss"]) / (1024.0 if "KiB" in str(usage["max_rss_unit"]) else 1024.0**2)


def _backend(diagnostics: dict[str, Any]) -> dict[str, Any]:
    return {"requested_backend": "CPU", "path": "cpu", "doctor_available": diagnostics.get("available"), "backend_probe": diagnostics.get("backend_probe")}


def _save_result(result: Any, output: Path, scenario_id: str) -> tuple[dict[str, str], dict[str, Any]]:
    result_path = output / f"{scenario_id}.result.json"
    manifest_path = output / f"{scenario_id}.manifest.json"
    result.save(str(result_path))
    manifest_path.write_text(json.dumps(result.manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return ({"result_artifact": str(result_path), "run_manifest": str(manifest_path)}, {"label": scenario_id, "path": str(manifest_path), "manifest": result.manifest})


def _solver(sim: Simulation, result: Any) -> dict[str, Any]:
    config = sim.config
    return {"method": config.method, "reltol": config.reltol, "abstol": config.abstol, "adaptive": config.adaptive, "dt": config.dt, "saveat": config.saveat, "basis_mode": "reduced" if config.blockade_radius > 0 else "full", "effective": result.diagnostics.get("simulation", {})}


def _rabi() -> dict[str, Any]:
    omega, times = float(2 * np.pi), [0.0, 0.125, 0.25, 0.375, 0.5]
    return {"id": "rabi_n1_cpu_seed_none", "problem": {"type": "single_atom_rabi", "atom_count": 1, "omega": omega, "delta": 0.0, "duration": 0.5, "seed": None}, "sim": Simulation(Register([Atom(0, 0)], C6=0), PulseSequence(omega=omega), SolverConfig(reltol=1e-9, abstol=1e-9, saveat=times)), "psi0": np.array([1, 0], dtype=complex), "duration": 0.5, "observables": {"rydberg_population": 0}, "reference": {"kind": "analytic_rabi_population", "series": "rydberg_population", "values": np.sin(omega * np.asarray(times) / 2) ** 2, "tolerance": 1e-6}}


def _blockade() -> dict[str, Any]:
    omega, times = float(2 * np.pi), [0.0, 0.0625, 0.125, 0.1875, 0.25]
    return {"id": "blockade_n2_reduced_cpu_seed_none", "problem": {"type": "two_atom_ideal_rydberg_blockade", "atom_count": 2, "spacing": 0.5, "C6": 100.0, "blockade_radius": 0.6, "duration": 0.25, "seed": None}, "sim": Simulation(Register([Atom(0, 0), Atom(0.5, 0)], C6=100), PulseSequence(omega=omega), SolverConfig(blockade_radius=0.6, reltol=1e-9, abstol=1e-9, saveat=times)), "psi0": np.array([1, 0, 0], dtype=complex), "duration": 0.25, "observables": {"total_rydberg_population": {"type": "total_rydberg_population"}, "double_excitation": {"type": "bitstring_probability", "bitstring": "11"}}, "reference": {"kind": "analytic_ideal_blockade_bright_state", "series": "total_rydberg_population", "values": np.sin(np.sqrt(2) * omega * np.asarray(times) / 2) ** 2, "tolerance": 1e-6, "double_excitation_tolerance": 1e-12}}


def _landau_zener() -> dict[str, Any]:
    omega, velocity, extent = 1.0, 0.5, 50.0
    duration = 2 * extent / velocity
    times = [0.0, duration / 4, duration / 2, 3 * duration / 4, duration]
    return {"id": "landau_zener_n1_cpu_seed_none", "problem": {"type": "single_atom_landau_zener", "atom_count": 1, "omega": omega, "detuning_start": -extent, "detuning_end": extent, "sweep_rate": velocity, "duration": duration, "seed": None}, "sim": Simulation(Register([Atom(0, 0)], C6=0), PulseSequence(omega=omega, delta=Pulse.ramp(start=-extent, end=extent, duration=duration)), SolverConfig(reltol=1e-10, abstol=1e-10, saveat=times)), "psi0": np.array([1, 0], dtype=complex), "duration": duration, "observables": {"rydberg_population": 0}, "reference": {"kind": "analytic_landau_zener_asymptotic_transition_probability", "series": "rydberg_population", "final_value": float(1 - np.exp(-np.pi * omega**2 / (2 * abs(velocity)))), "tolerance": 1.5e-2}}


def _small_chain() -> dict[str, Any]:
    return {"id": "small_chain_n3_dense_vs_reduced_cpu_seed_none", "problem": {"type": "small_chain_dense_vs_reduced", "atom_count": 3, "spacing": 0.5, "C6": 10.0, "blockade_radius": 0.6, "duration": 0.7, "omega": [0.2, 0.3, 0.4], "delta": [-0.1, 0.0, 0.2], "seed": None}, "register": Register.chain(3, spacing=0.5, C6=10), "sequence": PulseSequence(omega=[0.2, 0.3, 0.4], delta=[-0.1, 0.0, 0.2]), "atol": 1e-10}


SCENARIOS: dict[str, Callable[[], dict[str, Any]]] = {"rabi": _rabi, "blockade": _blockade, "landau_zener": _landau_zener, "small_chain": _small_chain}


def _simulation_row(name: str, scenario: dict[str, Any], output: Path, diagnostics: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    sim, ref = scenario["sim"], scenario["reference"]
    start = time.perf_counter()
    result = sim.run(scenario["psi0"], 0.0, scenario["duration"], observables=scenario["observables"])
    values = np.asarray(result.data[ref["series"]], dtype=float)
    metrics: dict[str, Any] = {"reference_kind": ref["kind"], "reference_tolerance": ref["tolerance"], "runtime_seconds": time.perf_counter() - start, "process_peak_memory_mb": _memory_mb()}
    if "values" in ref:
        metrics["max_abs_error"] = float(np.max(np.abs(values - np.asarray(ref["values"], dtype=float))))
        if metrics["max_abs_error"] > ref["tolerance"]:
            raise AssertionError(f"{name} error exceeds its reference tolerance.")
    else:
        metrics["reference_final_value"] = ref["final_value"]
        metrics["final_state_error"] = float(abs(values[-1] - ref["final_value"]))
        if metrics["final_state_error"] > ref["tolerance"]:
            raise AssertionError(f"{name} final-state error exceeds its reference tolerance.")
    if name == "blockade":
        metrics["max_double_excitation"] = float(np.max(np.abs(np.asarray(result.data["double_excitation"], dtype=float))))
        metrics["double_excitation_tolerance"] = ref["double_excitation_tolerance"]
        if metrics["max_double_excitation"] > ref["double_excitation_tolerance"]:
            raise AssertionError("Ideal-blockade double-excitation probability exceeds tolerance.")
    artifacts, manifest = _save_result(result, output, scenario["id"])
    row = make_benchmark_row(row_id=f"physics-correctness-{name}", scenario_id=scenario["id"], family=FAMILY, tier=TIER, status="passed", stage="artifact", problem=scenario["problem"], solver=_solver(sim, result), backend=_backend(diagnostics), observables={"names": list(scenario["observables"]), "count": len(scenario["observables"]), "output_sample_count": len(result.data["t"])}, metrics=metrics, artifacts=artifacts, disclosure_status="local_only")
    return row, manifest


def _small_chain_row(scenario: dict[str, Any], output: Path, diagnostics: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    start = time.perf_counter()
    report = dense_vs_reduced_validation(scenario["register"], scenario["sequence"], blockade_radius=0.6, duration=0.7, atol=scenario["atol"])
    if not report["ok"]:
        raise AssertionError("Projected dense and reduced chain references differ.")
    reference_path = output / f"{scenario['id']}.dense-vs-reduced.json"
    reference_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    metrics = {"reference_kind": "projected_dense_matrix_exponential", "reference_tolerance": report["atol"], "max_hamiltonian_error": report["max_hamiltonian_error"], "max_state_error": report["max_state_error"], "full_basis_size": report["full_basis_size"], "basis_size": report["reduced_basis_size"], "basis_pruning_ratio": report["reduced_basis_pruning_ratio"], "runtime_seconds": time.perf_counter() - start, "process_peak_memory_mb": _memory_mb()}
    row = make_benchmark_row(row_id="physics-correctness-small-chain", scenario_id=scenario["id"], family=FAMILY, tier=TIER, status="passed", stage="validation", problem=scenario["problem"], solver={"reference_method": "scipy.linalg.expm", "basis_mode": "projected_dense_vs_reduced", "duration": 0.7}, backend=_backend(diagnostics), observables={"names": [], "count": 0, "output_sample_count": 0}, metrics=metrics, artifacts={"reference_report": str(reference_path)}, disclosure_status="local_only")
    return row, {"label": scenario["id"], "path": str(reference_path), "reference": report}


def _failed_row(name: str, scenario: dict[str, Any], exc: BaseException, diagnostics: dict[str, Any], elapsed: float) -> dict[str, Any]:
    return make_benchmark_row(row_id=f"physics-correctness-{name}", scenario_id=scenario.get("id", name), family=FAMILY, tier=TIER, status="failed", stage="validation", problem=scenario.get("problem", {"type": "unknown", "seed": None}), solver={}, backend=_backend(diagnostics), observables={"names": [], "count": 0, "output_sample_count": 0}, metrics={"runtime_seconds": elapsed, "process_peak_memory_mb": _memory_mb()}, failure=benchmark_failure_from_exception(exc, stage="validation"), disclosure_status="local_only")


def benchmark_physics_correctness(output_dir: str | Path = ".", *, scenario_names: tuple[str, ...] = tuple(SCENARIOS)) -> dict[str, Any]:
    """Run all correctness scenarios while preserving structured failure rows."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    results = output / "physics_correctness_results"
    results.mkdir(parents=True, exist_ok=True)
    diagnostics = doctor(backend="CPU", initialize_backend=True)
    rows, manifests = [], []
    for name in scenario_names:
        if name not in SCENARIOS:
            rows.append(_failed_row(name, {}, ValueError(f"Unknown scenario: {name}"), diagnostics, 0.0))
            continue
        scenario, start = SCENARIOS[name](), time.perf_counter()
        try:
            row, manifest = _small_chain_row(scenario, results, diagnostics) if name == "small_chain" else _simulation_row(name, scenario, results, diagnostics)
            rows.append(row)
            manifests.append(manifest)
        except Exception as exc:
            rows.append(_failed_row(name, scenario, exc, diagnostics, time.perf_counter() - start))
    return write_benchmark_artifacts(output_dir=output, stem="physics_correctness", name="Phase 16 physics baseline CPU correctness benchmark", description="Analytic Rabi, ideal blockade, and Landau-Zener checks plus a projected dense-vs-reduced chain reference. Runtime is diagnostic only.", parameters={"scenarios": list(scenario_names), "backend": "CPU", "seed_policy": "deterministic/no stochastic seed"}, rows=rows, backend="CPU", diagnostics=diagnostics, run_manifests=manifests, columns=["row_id", "scenario_id", "status", "stage", "metrics", "artifacts", "failure"], benchmark_context={"protocol_version": "benchmark-protocol/v1", "family": FAMILY, "tier": TIER, "command": "uv run python tests/test_performance/benchmark_physics_correctness.py", "working_directory": str(Path.cwd()), "environment_variables": {key: os.environ[key] for key in _ENVIRONMENT_KEYS if key in os.environ}, "warmup_runs": 0, "measured_repeats": 1, "timeout_policy": "No runner timeout; every scenario exception is retained as a failed row.", "failure_policy": "Continue after per-scenario failures and retain structured diagnostics.", "disclosure_status": "local_only"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Phase 16 CPU physics correctness benchmarks.")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--scenario", action="append", choices=sorted(SCENARIOS), dest="scenarios")
    args = parser.parse_args()
    paths = benchmark_physics_correctness(args.output_dir, scenario_names=tuple(args.scenarios) if args.scenarios else tuple(SCENARIOS))
    print(f"Physics correctness benchmark complete. Results saved to {paths['json']}")
