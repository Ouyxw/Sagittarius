"""Phase 16 resumable parameter-sweep and ParallelSimulation benchmark."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

from sagittarius import (
    ParallelSimulation,
    benchmark_failure_from_exception,
    doctor,
    load_sweep_artifact,
    make_benchmark_row,
    make_sweep_artifact,
    resume_item_ids,
    save_sweep_artifact,
    write_benchmark_artifacts,
    write_benchmark_suite_artifact,
)
from sagittarius.runtime import get_julia


FAMILY = "sweep_cluster_execution"
TIER = "scaling"
BACKEND = {"requested_backend": "CPU", "path": "parallel"}
OBSERVABLES = {"names": [], "count": 0, "output_sample_count": 0}


def _item_id(omega: float) -> str:
    return f"omega-{omega:.3f}".replace(".", "p")


def _new_sweep(values: Iterable[float]) -> dict[str, Any]:
    values = [float(value) for value in values]
    return make_sweep_artifact(
        axes=[{"name": "omega", "path": "pulse.omega", "values": values}],
        items=[{"item_id": _item_id(value), "parameters": {"omega": value}, "status": "pending", "attempts": 0, "result_path": None, "manifest_path": None, "failure": None} for value in values],
        base_config={"benchmark": "phase16_parallel_parameter_sweep", "kernel": "omega^2 + 0.5"},
    )


def _define_kernel() -> None:
    jl, _ = get_julia()
    jl.seval("using Distributed; @everywhere phase16_sweep_kernel(omega) = omega^2 + 0.5")


def _write_item_outputs(output: Path, item_id: str, omega: float, value: float, *, requested_workers: int, effective_workers: int) -> tuple[str, str]:
    result_path = output / f"{item_id}.parallel-result.json"
    manifest_path = output / f"{item_id}.parallel-manifest.json"
    result_path.write_text(json.dumps({"schema_version": "parallel-sweep-result/v1", "omega": omega, "value": value}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps({"schema_version": "parallel-sweep-manifest/v1", "kernel": "omega^2 + 0.5", "requested_workers": requested_workers, "effective_workers": effective_workers}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(result_path), str(manifest_path)


def _execute_sweep(output: Path, artifact: Mapping[str, Any], *, requested_workers: int) -> tuple[dict[str, Any], dict[str, Any]]:
    pending_ids = resume_item_ids(artifact)
    items = [dict(item) for item in artifact["items"]]
    by_id = {item["item_id"]: item for item in items}
    pending = [by_id[item_id] for item_id in pending_ids]
    if not pending:
        return make_sweep_artifact(axes=artifact["axes"], items=items, base_config=artifact["base_config"]), {"pending_count": 0, "completed_count": len(items), "runtime_seconds": 0.0, "effective_workers": None, "max_abs_error": 0.0}
    parallel = ParallelSimulation(n_workers=requested_workers)
    _define_kernel()
    jl, _ = get_julia()
    effective_workers = int(jl.seval("Distributed.nprocs()"))
    omegas = [float(item["parameters"]["omega"]) for item in pending]
    started = time.perf_counter()
    values = [float(value) for value in parallel.map("phase16_sweep_kernel", omegas)]
    runtime_seconds = time.perf_counter() - started
    max_abs_error = 0.0
    for item, omega, value in zip(pending, omegas, values):
        expected = omega**2 + 0.5
        max_abs_error = max(max_abs_error, abs(value - expected))
        result_path, manifest_path = _write_item_outputs(output, item["item_id"], omega, value, requested_workers=requested_workers, effective_workers=effective_workers)
        item.update({"status": "succeeded", "attempts": int(item["attempts"]) + 1, "result_path": result_path, "manifest_path": manifest_path, "failure": None})
    completed = make_sweep_artifact(axes=artifact["axes"], items=items, base_config=artifact["base_config"])
    return completed, {"pending_count": len(pending), "completed_count": len(items), "runtime_seconds": runtime_seconds, "effective_workers": effective_workers, "max_abs_error": max_abs_error}


def benchmark_sweep_cluster(
    output_dir: str | Path = "benchmark-output", *, worker_counts: Iterable[int] = (1, 2), values: Iterable[float] = (0.1, 0.2, 0.3, 0.4), resume_from: str | Path | None = None
) -> dict[str, Any]:
    """Benchmark parallel sweep throughput and optionally resume one saved sweep."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    worker_counts = tuple(int(value) for value in worker_counts)
    values = tuple(float(value) for value in values)
    if not worker_counts or any(value <= 0 for value in worker_counts):
        raise ValueError("worker_counts must contain positive integers")
    if resume_from is not None:
        resumed_axes = load_sweep_artifact(resume_from)["axes"]
        values = tuple(float(value) for value in resumed_axes[0]["values"])
    if resume_from is not None and len(worker_counts) != 1:
        raise ValueError("resume_from requires exactly one requested worker count")
    diagnostics = doctor(backend="CPU", initialize_backend=True)
    rows: list[dict[str, Any]] = []
    sweep_paths: list[str] = []
    for requested_workers in worker_counts:
        scenario_id = f"parallel-sweep-workers-{requested_workers}"
        problem = {"problem_type": "parameter_sweep", "axis": "omega", "value_count": len(tuple(values)), "requested_workers": requested_workers}
        solver = {"kernel": "omega^2 + 0.5", "resume_policy": "retry_pending_running_and_failed"}
        checkpoint = output / f"{scenario_id}.checkpoint.json"
        final_path = output / f"{scenario_id}.sweep.json"
        try:
            initial = load_sweep_artifact(resume_from) if resume_from is not None else _new_sweep(values)
            save_sweep_artifact(initial, checkpoint)
            completed, metrics = _execute_sweep(output, initial, requested_workers=requested_workers)
            saved = save_sweep_artifact(completed, final_path)
            sweep_paths.append(str(final_path))
            if metrics["max_abs_error"] > 1e-12:
                raise AssertionError("Parallel sweep kernel result differs from its analytic reference")
            throughput = metrics["pending_count"] / metrics["runtime_seconds"] if metrics["runtime_seconds"] else None
            rows.append(make_benchmark_row(
                row_id=f"{FAMILY}-{TIER}-{scenario_id}", scenario_id=scenario_id,
                family=FAMILY, tier=TIER, status="passed", stage="artifact",
                problem=problem, solver=solver, backend={**BACKEND, "effective_workers": metrics["effective_workers"]}, observables=OBSERVABLES,
                metrics={**metrics, "throughput_items_per_second": throughput, "resumed_item_count": metrics["pending_count"], "completed_item_ids": saved["resumability"]["completed_item_ids"]},
                artifacts={"sweep_artifact": str(final_path), "sweep_checkpoint": str(checkpoint)}, disclosure_status="local_only",
            ))
        except Exception as exc:
            rows.append(make_benchmark_row(
                row_id=f"{FAMILY}-{TIER}-{scenario_id}", scenario_id=scenario_id,
                family=FAMILY, tier=TIER, status="failed", stage="solve",
                problem=problem, solver=solver, backend=BACKEND, observables=OBSERVABLES,
                metrics={}, failure=benchmark_failure_from_exception(exc, stage="solve"),
                artifacts={"sweep_checkpoint": str(checkpoint)}, disclosure_status="local_only",
            ))
    artifact = write_benchmark_artifacts(
        output_dir=output, stem="sweep_cluster", name="Phase 16 parallel sweep throughput and resume benchmark",
        description="ParallelSimulation parameter-map throughput and sweep-artifact resume checks. Runtime values are local diagnostics only.",
        parameters={"worker_counts": list(worker_counts), "values": [float(value) for value in values], "resume_from": None if resume_from is None else str(resume_from)},
        rows=rows, backend="CPU", diagnostics=diagnostics,
        columns=["row_id", "scenario_id", "status", "stage", "problem", "solver", "backend", "metrics", "artifacts", "failure"],
        benchmark_context={"protocol_version": "benchmark-protocol/v1", "family": FAMILY, "tier": TIER, "disclosure_status": "local_only", "failure_policy": "Retain one row per worker-count scenario."},
    )
    artifact["suite"] = write_benchmark_suite_artifact(
        output_dir=output, stem="sweep_cluster_suite", suite_id="phase16-sweep-cluster-scaling",
        family=FAMILY, tier=TIER, rows=rows, source=artifact["artifact"]["versions"],
        environment={"doctor": diagnostics}, scenario_defaults={"kernel": "omega^2 + 0.5", "resumability": "sweep-artifact/v1"},
    )
    artifact["sweep_artifacts"] = sweep_paths
    return artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Phase 16 ParallelSimulation sweep benchmark.")
    parser.add_argument("--output-dir", default="benchmark-output")
    parser.add_argument("--workers", type=int, action="append", dest="workers")
    parser.add_argument("--resume-from")
    arguments = parser.parse_args()
    paths = benchmark_sweep_cluster(arguments.output_dir, worker_counts=tuple(arguments.workers or (1, 2)), resume_from=arguments.resume_from)
    print(f"Sweep/cluster benchmark complete. Results saved to {paths['json']}")
