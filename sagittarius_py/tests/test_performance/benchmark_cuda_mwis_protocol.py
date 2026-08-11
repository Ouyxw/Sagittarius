"""Opt-in Phase 16 CUDA parity and weighted-MWIS GPU protocol.

This runner is deliberately local-only evidence.  It never initializes or
uses CUDA unless ``SAGITTARIUS_ENABLE_GPU_TESTS=1`` and a fully initialized
``doctor(backend="CUDA", initialize_backend=True)`` report is available.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from sagittarius import (
    Atom,
    PulseSequence,
    Register,
    Simulation,
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


DISCLOSURE_STATUS = "local_only"
PARITY_FAMILY = "backend_performance"
MWIS_FAMILY = "optimization_aqc"
TIER = "parity"
OBSERVABLES = {"names": ["pop0"], "count": 1, "output_sample_count": None}


def _enabled() -> bool:
    return os.environ.get("SAGITTARIUS_ENABLE_GPU_TESTS") == "1"


def _cuda_metadata(report: Mapping[str, Any]) -> dict[str, Any]:
    probe = dict(report.get("backend_probe") or {})
    runtime = dict(probe.get("runtime") or {})
    versions = dict(probe.get("versions") or {})
    return {
        "requested_backend": "CUDA",
        "path": "cpu_cuda_parity",
        "devices": list(probe.get("devices") or report.get("gpu", {}).get("devices") or []),
        "driver_version": runtime.get("driver_version") or report.get("gpu", {}).get("driver", {}).get("version"),
        "cuda_runtime_version": runtime.get("runtime_version"),
        "cuda_jl_version": versions.get("CUDA.jl"),
        "julia_version": report.get("runtime", {}).get("julia", {}).get("version"),
    }


def _cuda_memory_snapshot() -> dict[str, Any]:
    """Return best-effort CUDA memory data after doctor has initialized CUDA."""
    from juliacall import Main as jl

    raw = jl.seval(
        """
        begin
            using CUDA
            CUDA.synchronize()
            total = try CUDA.totalmem() catch; missing end
            available = try CUDA.available_memory() catch; missing end
            Dict(
                "total_bytes" => string(total),
                "available_bytes" => string(available),
                "used_bytes" => string(try total - available catch; missing end),
            )
        end
        """
    )
    return dict(raw)


def _cuda_synchronize() -> None:
    from juliacall import Main as jl

    jl.seval("using CUDA; CUDA.synchronize()")


def _write_reference(output_dir: Path, name: str, payload: Mapping[str, Any]) -> str:
    path = output_dir / f"{name}.reference.json"
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def _skip_row(*, family: str, scenario_id: str, problem: Mapping[str, Any], solver: Mapping[str, Any]) -> dict[str, Any]:
    return make_benchmark_row(
        row_id=f"{family}-{TIER}-{scenario_id}", scenario_id=scenario_id,
        family=family, tier=TIER, status="skipped", stage="setup",
        problem=problem, solver=solver, backend={"requested_backend": "CUDA", "path": "not_started"},
        observables=OBSERVABLES, metrics={},
        failure={
            "stage": "setup", "code": "BENCHMARK_GPU_OPT_IN_DISABLED",
            "message": "CUDA protocol requires SAGITTARIUS_ENABLE_GPU_TESTS=1.",
            "remediation": "Set SAGITTARIUS_ENABLE_GPU_TESTS=1 on a CUDA-capable host, then rerun the documented command.",
        },
        disclosure_status=DISCLOSURE_STATUS,
    )


def _doctor_failure_row(
    *, family: str, scenario_id: str, problem: Mapping[str, Any], solver: Mapping[str, Any], report: Mapping[str, Any]
) -> dict[str, Any]:
    error = RuntimeError("CUDA initialization failed: " + "; ".join(str(item) for item in report.get("issues", [])))
    return make_benchmark_failure_row(
        row_id=f"{family}-{TIER}-{scenario_id}", scenario_id=scenario_id,
        family=family, tier=TIER, stage="setup", exc=error, problem=problem,
        solver=solver, backend=_cuda_metadata(report), observables=OBSERVABLES,
        backend_probe=report, disclosure_status=DISCLOSURE_STATUS,
    )


def _parity_row(output_dir: Path, report: Mapping[str, Any]) -> dict[str, Any]:
    scenario_id = "chain_n3_cpu_cuda"
    problem = {"problem_type": "rydberg_chain", "atom_count": 3, "spacing": 0.5, "C6": 10.0, "blockade_radius": 0.6}
    solver = {"method": "Tsit5", "duration": 0.25, "reltol": 1e-8, "abstol": 1e-8, "warmup_runs": 1, "measured_repeats": 1}
    started = time.perf_counter()
    reference_path: str | None = None
    try:
        register = Register.chain(3, spacing=0.5, C6=10.0)
        sequence = PulseSequence(omega=0.3, delta=0.05)
        cpu = Simulation(register, sequence, SolverConfig(blockade_radius=0.6, reltol=1e-8, abstol=1e-8))
        basis_size = cpu.validate()
        initial = np.zeros(basis_size, dtype=np.complex128)
        initial[0] = 1.0

        cpu_started = time.perf_counter()
        cpu_result = cpu.run(initial, 0.0, 0.25, observables={"pop0": 0})
        cpu_seconds = time.perf_counter() - cpu_started

        gpu = Simulation(register, sequence, SolverConfig(blockade_radius=0.6, reltol=1e-8, abstol=1e-8, use_gpu=True, gpu_backend="CUDA"))
        memory_before = _cuda_memory_snapshot()
        cold_started = time.perf_counter()
        gpu.run(initial, 0.0, 0.25, observables={"pop0": 0})
        _cuda_synchronize()
        cold_start_seconds = time.perf_counter() - cold_started
        memory_after_cold = _cuda_memory_snapshot()

        warmup_started = time.perf_counter()
        gpu.run(initial, 0.0, 0.25, observables={"pop0": 0})
        _cuda_synchronize()
        warmup_seconds = time.perf_counter() - warmup_started
        warm_started = time.perf_counter()
        gpu_result = gpu.run(initial, 0.0, 0.25, observables={"pop0": 0})
        _cuda_synchronize()
        warm_seconds = time.perf_counter() - warm_started
        memory_after_warm = _cuda_memory_snapshot()

        cpu_t = np.asarray(cpu_result.data["t"], dtype=float)
        gpu_t = np.asarray(gpu_result.data["t"], dtype=float)
        cpu_values = np.asarray(cpu_result.data["pop0"], dtype=float)
        gpu_values = np.asarray(gpu_result.data["pop0"], dtype=float)
        max_abs_error = float(np.max(np.abs(np.interp(gpu_t, cpu_t, cpu_values) - gpu_values)))
        reference_path = _write_reference(output_dir, scenario_id, {"cpu": cpu_result.manifest, "cuda": gpu_result.manifest, "max_abs_error": max_abs_error})
        if max_abs_error > 1e-6:
            raise AssertionError(f"CPU/CUDA observable parity error {max_abs_error} exceeds 1e-6")
        return make_benchmark_row(
            row_id=f"{PARITY_FAMILY}-{TIER}-{scenario_id}", scenario_id=scenario_id,
            family=PARITY_FAMILY, tier=TIER, status="passed", stage="validation",
            problem=problem, solver=solver, backend=_cuda_metadata(report), observables=OBSERVABLES,
            metrics={
                "basis_size": basis_size, "cpu_seconds": cpu_seconds,
                "cuda_cold_start_seconds": cold_start_seconds, "cuda_warmup_seconds": warmup_seconds,
                "cuda_warm_seconds": warm_seconds, "cpu_cuda_max_abs_error": max_abs_error,
                "parity_atol": 1e-6, "parity_passed": max_abs_error <= 1e-6,
                "gpu_memory_before": memory_before, "gpu_memory_after_cold": memory_after_cold,
                "gpu_memory_after_warm": memory_after_warm, "total_runtime_seconds": time.perf_counter() - started,
            },
            artifacts={"reference_report": reference_path, "cpu_run_manifest": cpu_result.manifest, "cuda_run_manifest": gpu_result.manifest},
            disclosure_status=DISCLOSURE_STATUS,
        )
    except Exception as exc:
        row = make_benchmark_failure_row(
            row_id=f"{PARITY_FAMILY}-{TIER}-{scenario_id}", scenario_id=scenario_id,
            family=PARITY_FAMILY, tier=TIER, stage="validation", exc=exc, problem=problem,
            solver=solver, backend=_cuda_metadata(report), observables=OBSERVABLES,
            backend_probe=report, disclosure_status=DISCLOSURE_STATUS,
        )
        if reference_path is not None:
            row["artifacts"]["reference_report"] = reference_path
        return row


def _mwis_gpu_row(output_dir: Path, report: Mapping[str, Any]) -> dict[str, Any]:
    scenario_id = "weighted_udg_n2_seed3_cpu_cuda"
    graph = generate_random_udg(2, density=1.0, blockade_radius=1.0, seed=3)
    weights = [float(graph.nodes[node]["weight"]) for node in graph.nodes()]
    problem = {"problem_type": "weighted_unit_disk_mwis", "atom_count": 2, "instance_seed": 3, "density": 1.0, "blockade_radius": 1.0, "edge_list": [list(edge) for edge in graph.edges()], "node_weights": weights}
    solver = {"solver_type": "MWIS_AQC", "reference_solver": "PuLP_CBC_ILP", "duration": 0.1, "warmup_runs": 1, "measured_repeats": 1}
    started = time.perf_counter()
    reference_path: str | None = None
    try:
        exact_bits, exact_weight, ilp_status = solve_mwis_ilp(graph)
        cpu_solver = MWIS_AQC(graph, blockade_radius=1.0)
        cpu_started = time.perf_counter()
        cpu_bits, cpu_probabilities, basis = cpu_solver.solve_full(SolverConfig(blockade_radius=1.0), duration=0.1)
        cpu_seconds = time.perf_counter() - cpu_started

        gpu_solver = MWIS_AQC(graph, blockade_radius=1.0)
        memory_before = _cuda_memory_snapshot()
        cold_started = time.perf_counter()
        gpu_solver.solve_full(SolverConfig(blockade_radius=1.0, use_gpu=True, gpu_backend="CUDA"), duration=0.1)
        _cuda_synchronize()
        cold_start_seconds = time.perf_counter() - cold_started
        memory_after_cold = _cuda_memory_snapshot()

        gpu_solver = MWIS_AQC(graph, blockade_radius=1.0)
        gpu_solver.solve_full(SolverConfig(blockade_radius=1.0, use_gpu=True, gpu_backend="CUDA"), duration=0.1)
        _cuda_synchronize()
        warm_started = time.perf_counter()
        gpu_bits, gpu_probabilities, gpu_basis = gpu_solver.solve_full(SolverConfig(blockade_radius=1.0, use_gpu=True, gpu_backend="CUDA"), duration=0.1)
        _cuda_synchronize()
        warm_seconds = time.perf_counter() - warm_started
        memory_after_warm = _cuda_memory_snapshot()

        cpu_bits = np.asarray(cpu_bits, dtype=int)
        gpu_bits = np.asarray(gpu_bits, dtype=int)
        gpu_feasible = verify_independent_set(graph, gpu_bits)
        gpu_weight = calculate_weight(graph, gpu_bits) if gpu_feasible else 0.0
        probability_error = float(np.max(np.abs(np.asarray(cpu_probabilities) - np.asarray(gpu_probabilities))))
        reference_path = _write_reference(output_dir, scenario_id, {
            "exact": {"bitstring": exact_bits, "weight": exact_weight, "ilp_status": ilp_status},
            "cpu": {"bitstring": cpu_bits.tolist(), "probabilities": np.asarray(cpu_probabilities).tolist(), "basis": list(basis)},
            "cuda": {"bitstring": gpu_bits.tolist(), "probabilities": np.asarray(gpu_probabilities).tolist(), "basis": list(gpu_basis)},
        })
        if not gpu_feasible:
            raise AssertionError("CUDA MWIS candidate is not an independent set")
        if probability_error > 1e-6 or list(basis) != list(gpu_basis):
            raise AssertionError("CPU/CUDA MWIS final probability or basis parity mismatch")
        return make_benchmark_row(
            row_id=f"{MWIS_FAMILY}-{TIER}-{scenario_id}", scenario_id=scenario_id,
            family=MWIS_FAMILY, tier=TIER, status="passed", stage="validation",
            problem=problem, solver=solver, backend=_cuda_metadata(report), observables=OBSERVABLES,
            metrics={
                "ilp_status": ilp_status, "exact_objective": exact_weight,
                "cuda_feasible": gpu_feasible, "cuda_objective": gpu_weight,
                "cuda_objective_gap": max(0.0, exact_weight - gpu_weight),
                "cpu_cuda_probability_max_abs_error": probability_error, "parity_atol": 1e-6,
                "parity_passed": probability_error <= 1e-6 and list(basis) == list(gpu_basis),
                "cpu_seconds": cpu_seconds, "cuda_cold_start_seconds": cold_start_seconds,
                "cuda_warm_seconds": warm_seconds, "gpu_memory_before": memory_before,
                "gpu_memory_after_cold": memory_after_cold, "gpu_memory_after_warm": memory_after_warm,
                "total_runtime_seconds": time.perf_counter() - started,
            },
            artifacts={"reference_report": reference_path}, disclosure_status=DISCLOSURE_STATUS,
        )
    except Exception as exc:
        row = make_benchmark_failure_row(
            row_id=f"{MWIS_FAMILY}-{TIER}-{scenario_id}", scenario_id=scenario_id,
            family=MWIS_FAMILY, tier=TIER, stage="validation", exc=exc, problem=problem,
            solver=solver, backend=_cuda_metadata(report), observables=OBSERVABLES,
            backend_probe=report, disclosure_status=DISCLOSURE_STATUS,
        )
        if reference_path is not None:
            row["artifacts"]["reference_report"] = reference_path
        return row


def _write_family(output: Path, *, family: str, name: str, row: Mapping[str, Any], report: Mapping[str, Any]) -> dict[str, Any]:
    artifact = write_benchmark_artifacts(
        output_dir=output, stem=name, name=f"Phase 16 CUDA {family} parity protocol",
        description="Opt-in CPU/CUDA parity evidence. Runtime values are local diagnostics only.",
        parameters={"opt_in_environment_variable": "SAGITTARIUS_ENABLE_GPU_TESTS=1", "doctor_initialize_backend": True},
        rows=[row], backend="CUDA", diagnostics=report,
        columns=["row_id", "scenario_id", "status", "stage", "problem", "solver", "backend", "metrics", "artifacts", "failure"],
        benchmark_context={"protocol_version": "benchmark-protocol/v1", "family": family, "tier": TIER, "disclosure_status": DISCLOSURE_STATUS, "failure_policy": "Retain opt-in skips, CUDA doctor failures, and scenario failures as structured rows."},
    )
    artifact["suite"] = write_benchmark_suite_artifact(
        output_dir=output, stem=f"{name}_suite", suite_id=f"phase16-{name}",
        family=family, tier=TIER, rows=[row], source=artifact["artifact"]["versions"],
        environment={"doctor": dict(report)}, scenario_defaults={"backend": "CUDA", "opt_in": True},
    )
    return artifact


def benchmark_cuda_mwis_protocol(
    output_dir: str | Path = "benchmark-output", *, doctor_fn: Callable[..., Mapping[str, Any]] = doctor
) -> dict[str, dict[str, Any]]:
    """Emit opt-in CUDA parity and MWIS GPU protocol artifacts."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parity_problem = {"problem_type": "rydberg_chain", "atom_count": 3, "blockade_radius": 0.6}
    parity_solver = {"method": "Tsit5", "duration": 0.25}
    mwis_problem = {"problem_type": "weighted_unit_disk_mwis", "atom_count": 2, "instance_seed": 3}
    mwis_solver = {"solver_type": "MWIS_AQC", "duration": 0.1}
    if not _enabled():
        report: Mapping[str, Any] = {"available": False, "issues": ["GPU protocol opt-in disabled"], "backend_probe": None}
        parity_row = _skip_row(family=PARITY_FAMILY, scenario_id="chain_n3_cpu_cuda", problem=parity_problem, solver=parity_solver)
        mwis_row = _skip_row(family=MWIS_FAMILY, scenario_id="weighted_udg_n2_seed3_cpu_cuda", problem=mwis_problem, solver=mwis_solver)
    else:
        report = doctor_fn(backend="CUDA", initialize_backend=True)
        if not report.get("available"):
            parity_row = _doctor_failure_row(family=PARITY_FAMILY, scenario_id="chain_n3_cpu_cuda", problem=parity_problem, solver=parity_solver, report=report)
            mwis_row = _doctor_failure_row(family=MWIS_FAMILY, scenario_id="weighted_udg_n2_seed3_cpu_cuda", problem=mwis_problem, solver=mwis_solver, report=report)
        else:
            parity_row = _parity_row(output, report)
            mwis_row = _mwis_gpu_row(output, report)
    return {
        "parity": _write_family(output, family=PARITY_FAMILY, name="cuda_parity", row=parity_row, report=report),
        "mwis": _write_family(output, family=MWIS_FAMILY, name="mwis_gpu_parity", row=mwis_row, report=report),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the opt-in Phase 16 CUDA/MWIS parity protocol.")
    parser.add_argument("--output-dir", default="benchmark-output")
    arguments = parser.parse_args()
    paths = benchmark_cuda_mwis_protocol(arguments.output_dir)
    print(f"CUDA parity artifact: {paths['parity']['json']}")
    print(f"MWIS GPU parity artifact: {paths['mwis']['json']}")
