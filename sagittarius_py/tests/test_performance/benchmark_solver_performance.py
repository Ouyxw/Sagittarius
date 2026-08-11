"""Phase 16 CPU solver-method and execution-path correctness benchmarks."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from sagittarius import (
    PulseSequence,
    Register,
    Simulation,
    SolverConfig,
    benchmark_failure_from_exception,
    doctor,
    make_benchmark_row,
    write_benchmark_artifacts,
    write_benchmark_suite_artifact,
)
from sagittarius.ablation import benchmark_ablation_modes


FAMILY = "backend_performance"
TIER = "correctness"
PATH_ATOL = 1e-10
METHOD_ATOL = 1e-6
OBSERVABLES = {"names": ["pop0"], "count": 1, "output_sample_count": 9}
BACKEND = {"requested_backend": "CPU", "path": "cpu"}


def _save_result(result: Any, output: Path, scenario_id: str) -> tuple[dict[str, str], dict[str, Any]]:
    result_path = output / f"{scenario_id}.result.json"
    manifest_path = output / f"{scenario_id}.manifest.json"
    result.save(str(result_path))
    manifest_path.write_text(json.dumps(result.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ({"result_artifact": str(result_path), "run_manifest": str(manifest_path)}, {"label": scenario_id, "path": str(manifest_path), "manifest": result.manifest})


def _failed_row(
    scenario_id: str, problem: Mapping[str, Any], solver: Mapping[str, Any], exc: BaseException, *, stage: str
) -> dict[str, Any]:
    return make_benchmark_row(
        row_id=f"{FAMILY}-{TIER}-{scenario_id}", scenario_id=scenario_id,
        family=FAMILY, tier=TIER, status="failed", stage=stage,
        problem=problem, solver=solver, backend=BACKEND, observables=OBSERVABLES,
        metrics={}, failure=benchmark_failure_from_exception(exc, stage=stage), disclosure_status="local_only",
    )


def _path_rows(*, repeat_count: int, ablation_repeats: int) -> list[dict[str, Any]]:
    register = Register.chain(4, spacing=0.6, C6=10.0)
    sequence = PulseSequence(omega=0.5, delta=[0.0, 0.1, -0.1, 0.2])
    problem = {"benchmark": "hamiltonian_execution_path", "atom_count": 4, "spacing": 0.6, "C6": 10.0, "blockade_radius": 0.8}
    rows: list[dict[str, Any]] = []
    for repeat_index in range(repeat_count):
        raw_rows, _ = benchmark_ablation_modes(
            register, sequence, blockade_radius=0.8, repeats=ablation_repeats,
            warmups=1, seed=20260811 + repeat_index, include_gpu=False,
        )
        for raw in raw_rows:
            scenario_id = f"path-{raw['mode']}-repeat-{repeat_index}"
            solver = {"path_mode": raw["mode"], "representation": raw["representation"], "warmup_runs": 1, "measured_repeats": ablation_repeats}
            if raw["status"] == "skipped":
                rows.append(make_benchmark_row(
                    row_id=f"{FAMILY}-{TIER}-{scenario_id}", scenario_id=scenario_id,
                    family=FAMILY, tier=TIER, status="skipped", stage="setup",
                    problem=problem, solver=solver, backend={"requested_backend": raw["backend"], "path": raw["mode"]}, observables={"names": [], "count": 0, "output_sample_count": 0},
                    metrics={"repeat_index": repeat_index},
                    failure={"stage": "setup", "code": "BENCHMARK_PATH_UNAVAILABLE", "message": raw["reason"], "remediation": "Enable the documented backend only after its doctor checks pass."},
                    disclosure_status="local_only",
                ))
                continue
            reference_error = raw.get("reference_error")
            reference_atol = 1e-7 if raw["mode"] in {"full_dense", "full_sparse"} else PATH_ATOL
            if reference_error is None or reference_error > reference_atol:
                rows.append(_failed_row(scenario_id, problem, solver, AssertionError(f"{raw['mode']} reference error {reference_error!r} exceeds {reference_atol}"), stage="validation"))
                continue
            rows.append(make_benchmark_row(
                row_id=f"{FAMILY}-{TIER}-{scenario_id}", scenario_id=scenario_id,
                family=FAMILY, tier=TIER, status="passed", stage="validation",
                problem=problem, solver=solver, backend={"requested_backend": raw["backend"], "path": raw["mode"]}, observables={"names": [], "count": 0, "output_sample_count": 0},
                metrics={"repeat_index": repeat_index, "reference_error": reference_error, "reference_atol": reference_atol, "total_time_seconds": raw["total_time_s"], "time_per_operation_seconds": raw["time_per_operation_s"], "basis_size": raw["basis_size"], "full_dim": raw["full_dim"]},
                disclosure_status="local_only",
            ))
    return rows


def _method_rows(output: Path, *, repeat_count: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    register = Register.chain(3, spacing=0.5, C6=10.0)
    sequence = PulseSequence(omega=[0.2, 0.3, 0.25], delta=[-0.1, 0.0, 0.1])
    times = np.linspace(0.0, 0.3, 9).tolist()
    reference_config = SolverConfig(method="Tsit5", reltol=1e-10, abstol=1e-10, blockade_radius=0.6, saveat=times)
    reference_sim = Simulation(register, sequence, reference_config)
    initial = np.zeros(reference_sim.validate(), dtype=np.complex128)
    initial[0] = 1.0
    reference_result = reference_sim.run(initial, 0.0, 0.3, observables={"pop0": 0})
    reference_values = np.asarray(reference_result.data["pop0"], dtype=float)
    reference_artifacts, reference_manifest = _save_result(reference_result, output, "solver_reference_tsit5")
    problem = {"benchmark": "solver_method_trajectory", "atom_count": 3, "blockade_radius": 0.6, "duration": 0.3, "output_grid": times}
    configurations = (
        ("Tsit5", SolverConfig(method="Tsit5", reltol=1e-9, abstol=1e-9, blockade_radius=0.6, saveat=times)),
        ("Vern9", SolverConfig(method="Vern9", reltol=1e-9, abstol=1e-9, blockade_radius=0.6, saveat=times)),
        ("RK4", SolverConfig(method="RK4", adaptive=False, dt=1e-3, blockade_radius=0.6, saveat=times)),
    )
    rows: list[dict[str, Any]] = []
    manifests = [reference_manifest]
    for method, config in configurations:
        for repeat_index in range(repeat_count):
            scenario_id = f"solver-{method.lower()}-repeat-{repeat_index}"
            solver = {"method": method, "reltol": config.reltol, "abstol": config.abstol, "adaptive": config.adaptive, "dt": config.dt, "warmup_runs": 0, "measured_repeats": 1}
            started = time.perf_counter()
            try:
                result = Simulation(register, sequence, config).run(initial, 0.0, 0.3, observables={"pop0": 0})
                values = np.asarray(result.data["pop0"], dtype=float)
                error = float(np.max(np.abs(values - reference_values)))
                artifacts, manifest = _save_result(result, output, scenario_id)
                manifests.append(manifest)
                artifacts["reference_result_artifact"] = reference_artifacts["result_artifact"]
                if error > METHOD_ATOL:
                    raise AssertionError(f"{method} trajectory error {error} exceeds {METHOD_ATOL}")
                rows.append(make_benchmark_row(
                    row_id=f"{FAMILY}-{TIER}-{scenario_id}", scenario_id=scenario_id,
                    family=FAMILY, tier=TIER, status="passed", stage="validation",
                    problem=problem, solver=solver, backend=BACKEND, observables=OBSERVABLES,
                    metrics={"repeat_index": repeat_index, "reference_method": "Tsit5", "max_abs_error": error, "reference_atol": METHOD_ATOL, "runtime_seconds": time.perf_counter() - started, "effective_solver": result.diagnostics.get("simulation", {})},
                    artifacts=artifacts, disclosure_status="local_only",
                ))
            except Exception as exc:
                rows.append(_failed_row(scenario_id, problem, solver, exc, stage="validation"))
    return rows, manifests


def benchmark_solver_performance(output_dir: str | Path = "benchmark-output", *, repeat_count: int = 2, ablation_repeats: int = 5) -> dict[str, Any]:
    """Run repeated execution-path and solver-method correctness measurements."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    diagnostics = doctor(backend="CPU", initialize_backend=True)
    rows = _path_rows(repeat_count=repeat_count, ablation_repeats=ablation_repeats)
    method_rows, manifests = _method_rows(output, repeat_count=repeat_count)
    rows.extend(method_rows)
    artifact = write_benchmark_artifacts(
        output_dir=output, stem="solver_performance", name="Phase 16 solver and execution-path correctness benchmark",
        description="Repeated CPU dense/sparse/reduced path checks and Tsit5/Vern9/RK4 trajectory checks. Runtime values are local diagnostics only.",
        parameters={"reduced_path_reference_atol": PATH_ATOL, "full_path_reference_atol": 1e-7, "method_reference_atol": METHOD_ATOL, "repeat_count": repeat_count, "ablation_repeats": ablation_repeats, "gpu_cache_policy": "reported as skipped unless an opt-in CUDA protocol validates it"},
        rows=rows, backend="CPU", diagnostics=diagnostics, run_manifests=manifests,
        columns=["row_id", "scenario_id", "status", "stage", "problem", "solver", "metrics", "artifacts", "failure"],
        benchmark_context={"protocol_version": "benchmark-protocol/v1", "family": FAMILY, "tier": TIER, "warmup_runs": 1, "measured_repeats": repeat_count, "disclosure_status": "local_only"},
    )
    artifact["suite"] = write_benchmark_suite_artifact(
        output_dir=output, stem="solver_performance_suite", suite_id="phase16-solver-performance-correctness",
        family=FAMILY, tier=TIER, rows=rows, source=artifact["artifact"]["versions"],
        environment={"doctor": diagnostics}, scenario_defaults={"backend": "CPU", "reduced_path_reference_atol": PATH_ATOL, "full_path_reference_atol": 1e-7, "method_reference_atol": METHOD_ATOL},
    )
    return artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Phase 16 solver/performance correctness benchmarks.")
    parser.add_argument("--output-dir", default="benchmark-output")
    parser.add_argument("--repeat-count", type=int, default=2)
    parser.add_argument("--ablation-repeats", type=int, default=5)
    arguments = parser.parse_args()
    paths = benchmark_solver_performance(arguments.output_dir, repeat_count=arguments.repeat_count, ablation_repeats=arguments.ablation_repeats)
    print(f"Solver/performance benchmark complete. Results saved to {paths['json']}")
