"""Supervised plan-v2 ablation campaign; separate process per scenario/path."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import contextlib
import ctypes
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time

import numpy as np

from . import PulseSequence, Register, doctor
from .ablation import (ABLATION_BENCHMARK_MODES, CPU_MODES, WORKLOAD_VERSION,
                       benchmark_ablation_modes, construction_estimate)
from .benchmark_failures import benchmark_failure_context
from .benchmark_measurement import linux_process_memory, runtime_summary, supervise, write_json
from .benchmark_suite import write_benchmark_suite_artifact
from .benchmarking import make_benchmark_row, write_benchmark_artifacts
from .runtime import version_info
from .scaling_benchmark import basis_dimension, _runtime_context

SIZES = (4, 8, 12, 16, 20)
FAMILY, TIER = "backend_performance", "performance"
OBSERVABLES = {"names": [], "count": 0, "output_sample_count": 0}
SOURCE_FILES = ("ablation.py", "ablation_benchmark.py", "benchmark_measurement.py",
                "benchmarking.py", "benchmark_suite.py", "benchmark_failures.py", "api.py", "runtime.py",
                "scaling_benchmark.py")


def scenarios(sizes=SIZES, *, spacing=2., blockade_radius=3.):
    if not math.isfinite(spacing) or spacing <= 0 or not math.isfinite(blockade_radius) or blockade_radius < 0:
        raise ValueError("Spacing must be positive and radius nonnegative, both finite")
    sizes = tuple(sizes)
    if not sizes or len(set(sizes)) != len(sizes) or any(isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 20 for n in sizes):
        raise ValueError("Select unique integer atom counts in [1, 20]")
    output = []
    for n in sizes:
        problem = {"N": n, "atom_count": n, "geometry": "chain", "spacing": spacing,
                   "coordinates": [[i * spacing, 0., 0.] for i in range(n)], "C6": 100.,
                   "blockade_radius": blockade_radius, "radius_ratio": blockade_radius / spacing,
                   "omega": 2 * math.pi, "delta": 0., "full_dim": 2**n,
                   "atom_order": "atom i is bit i (LSB); ascending bitstring basis",
                   "units": {"length": "um", "time": "us", "angular_frequency": "rad/us", "C6": "rad*um^6/us"}}
        reduced_dim = basis_dimension(problem)
        for descriptor in ABLATION_BENCHMARK_MODES:
            mode = descriptor["mode"]
            d = 2**n if mode.startswith("full_") else reduced_dim
            output.append({**problem, **descriptor, "scenario_id": f"chain-n{n}-{mode}",
                           "basis_size": d, "reduced_basis_size": reduced_dim,
                           "pruned_fraction": 1 - d / 2**n,
                           "basis": "full" if mode.startswith("full_") else "blockade_reduced",
                           "required": n <= 12 and mode in CPU_MODES,
                           "estimated_peak_bytes": construction_estimate(mode, n, d)})
    return output


def _blas_threads():
    """Read loaded OpenBLAS runtime counts; retain unknown providers explicitly."""
    providers = []
    for path in sorted({line.split()[-1] for line in Path("/proc/self/maps").read_text().splitlines()
                        if "openblas" in line.lower() and line.split()[-1].startswith("/")}):
        library = ctypes.CDLL(path)
        for symbol in ("scipy_openblas_get_num_threads64_", "scipy_openblas_get_num_threads",
                       "openblas_get_num_threads64_", "openblas_get_num_threads"):
            try:
                count = int(getattr(library, symbol)())
            except AttributeError:
                continue
            providers.append({"library": path, "symbol": symbol, "effective_threads": count})
            break
    return {"providers": providers, "unavailable_reason": None if providers else "No supported loaded OpenBLAS thread-count symbol; requested environment retained."}


def _child(config_path, checkpoint_path):
    config = json.loads(Path(config_path).read_text())
    s, settings = config["scenario"], config["settings"]
    state = {"stage": "setup"}
    def checkpoint(row=None):
        if row is not None:
            state["row"] = row
            state["stage"] = row["stage"]
        state["memory"] = linux_process_memory(os.getpid())
        write_json(checkpoint_path, state)
    checkpoint()
    try:
        for name, expected in config["source_file_sha256"].items():
            if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != expected:
                raise RuntimeError("Frozen source changed during campaign")
        started = time.perf_counter()
        state["doctor"] = doctor(backend="CPU", initialize_backend=True)
        state["initialized_cpu_doctor_seconds"] = time.perf_counter() - started
        if not state["doctor"].get("available") or not (state["doctor"].get("backend_probe") or {}).get("available"):
            raise RuntimeError("Initialized CPU diagnostics failed")
        state["runtime_context"] = _runtime_context()
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            np.show_config()
        state["runtime_context"]["numpy_config"] = buffer.getvalue()
        state["runtime_context"]["python_blas"] = _blas_threads()
        if any(p["effective_threads"] != 1 for p in state["runtime_context"]["python_blas"]["providers"]):
            raise RuntimeError("Effective Python BLAS threads differ from frozen single-thread anchor")
        state["runtime_context"]["environment"].update({key: os.environ.get(key) for key in
            ("JULIA_CONDAPKG_BACKEND", "JULIA_PYTHONCALL_EXE")})
        state["runtime_context"]["project_files"] = {}
        project = state["runtime_context"]["environment"].get("PYTHON_JULIACALL_PROJECT")
        if project:
            for name in ("Project.toml", "Manifest.toml"):
                source = Path(project) / name
                if source.is_file():
                    target = Path(checkpoint_path).parent / name
                    shutil.copyfile(source, target)
                    state["runtime_context"]["project_files"][name] = {"path": str(target), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
        state["memory_baseline"] = linux_process_memory(os.getpid())
        register = Register.chain(s["N"], spacing=s["spacing"], C6=s["C6"])
        sequence = PulseSequence(omega=s["omega"], delta=s["delta"])
        rows, _ = benchmark_ablation_modes(register, sequence, **settings["measurement"],
            blockade_radius=s["blockade_radius"], modes=[s["mode"]],
            directory=Path(checkpoint_path).parent, checkpoint=checkpoint)
        checkpoint(rows[0])
    except Exception as exc:
        state["failure"] = benchmark_failure_context(exc, stage=state["stage"])
        checkpoint()


def campaign_row(s, settings, state, supervision, *, exclusion=None):
    raw = state.get("row", {})
    measurements = raw.get("measurements", [])
    summary = runtime_summary(measurements, settings["measurement"]["repeat_count"])
    failure = state.get("failure") or raw.get("failure")
    status = raw.get("measurement_status", "incomplete")
    if exclusion:
        status = "skipped"
        failure = {"stage": "setup", "code": "BENCHMARK_RESOURCE_EXCLUDED" if s["mode"] in CPU_MODES else "BENCHMARK_CUDA_DISABLED",
                   "message": exclusion, "remediation": "Retain exclusion and freeze a new campaign before changing limits or opt-in."}
    elif supervision.get("reason") in {"timeout", "interrupted"}:
        status = "incomplete"
        failure = benchmark_failure_context(TimeoutError("Child timed out or campaign interrupted"), stage=state.get("stage", "setup"), timeout_seconds=settings["timeout_seconds"])
    elif supervision.get("reason") == "memory":
        status = "failed"
        failure = benchmark_failure_context(MemoryError("Child exceeded RSS budget"), stage=state.get("stage", "setup"))
    elif supervision.get("returncode", 0) != 0:
        status = "failed"
        failure = benchmark_failure_context(RuntimeError(f"Child exited {supervision['returncode']}"), stage=state.get("stage", "setup"))
    elif failure:
        status = "failed"
    elif raw.get("status") == "skipped":
        status = "skipped"
    if status != "passed" and not failure:
        failure = {"stage": state.get("stage", "setup"), "code": "BENCHMARK_INSUFFICIENT_EVIDENCE",
                   "message": raw.get("reason") or "Two warmups, five eligible measurements and reference gates required",
                   "remediation": "Inspect retained partial evidence; rerun in a new directory with the required counts and references."}
    if failure:
        failure.update(limits={k: settings[k] for k in ("timeout_seconds", "memory_limit_bytes")},
                       backend_probe=state.get("doctor", {}).get("backend_probe"), process_memory=state.get("memory"))
    backend = {"requested_backend": s["backend"], "path": s["mode"], "precision": "complex128",
               "implementation": "Python/NumPy/SciPy" if s["mode"] in CPU_MODES else "Julia CUDA ODE through Python SDK"}
    metrics = {**raw, "statistics": summary, "supervision": supervision,
               "memory": state.get("memory"), "memory_baseline": state.get("memory_baseline"),
               "memory_scope": "fresh scenario/path process lifetime including doctor, construction, references and serialization",
               "runtime_context": state.get("runtime_context"), "initialized_cpu_doctor_seconds": state.get("initialized_cpu_doctor_seconds"),
               "timer_scope": "fixed-input H*psi batch only; excludes construction, references, validation and writes" if s["mode"] in CPU_MODES else "SDK end-to-end CUDA ODE solve, synchronization included; separate workload, no matvec/solve ratio",
               "cache_policy": "fresh process per scenario/path; doctor then construction/reference, first operation, actual-scenario warmups; operator reused"}
    row = make_benchmark_row(row_id=s["scenario_id"], scenario_id=s["scenario_id"], family=FAMILY, tier=TIER,
        status=status, stage=failure["stage"] if failure else "artifact", problem=s,
        solver=raw.get("solver", {"operation_count": settings["measurement"]["repeats"], "repeat_count": settings["measurement"]["repeat_count"], "method": "not applicable: CPU matvec"}),
        backend=backend, observables=OBSERVABLES if s["mode"] in CPU_MODES else {"names": ["pop0"], "count": 1, "output_sample_count": 101},
        metrics=metrics, artifacts=raw.get("artifacts"), failure=failure)
    for key in ("mode", "workload", "atom_count", "full_dim", "basis_size", "pruned_fraction"):
        row[key] = s[key]
    for key in ("repeats", "duration_s", "total_time_s", "time_per_operation_s", "reference_error", "reference_relative_error", "max_rss", "max_rss_unit"):
        row[key] = raw.get(key)
    row["median_batch_time_s"] = summary["runtime_seconds"]["median"]
    return row


def benchmark_ablation(atom_count=10, spacing=2., blockade_radius=3., repeats=50,
                       include_gpu=False, output_dir=".", *, sizes=None, repeat_count=5,
                       warmups=2, seed=1234, max_full_dim=4096, memory_limit_mb=9216,
                       timeout_seconds=600., full_rtol=1e-12, reduced_atol=1e-10, gpu_duration=.2):
    selected = scenarios((atom_count,) if sizes is None else sizes, spacing=spacing, blockade_radius=blockade_radius)
    # Validate before freezing or launching any work, using the helper's public contract.
    for name, value, minimum in (("repeats", repeats, 1), ("repeat_count", repeat_count, 1),
                                 ("warmups", warmups, 0), ("seed", seed, 0), ("max_full_dim", max_full_dim, 1)):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    if not all(math.isfinite(v) and v > 0 for v in (memory_limit_mb, timeout_seconds, full_rtol, reduced_atol, gpu_duration)):
        raise ValueError("Limits, tolerances and duration must be finite and positive")
    settings = {"measurement": dict(repeats=repeats, repeat_count=repeat_count, warmups=warmups,
        seed=seed, max_full_dim=max_full_dim, memory_limit_mb=memory_limit_mb, include_gpu=include_gpu,
        full_rtol=full_rtol, reduced_atol=reduced_atol, gpu_duration=gpu_duration),
        "memory_limit_bytes": int(memory_limit_mb * 1024**2), "timeout_seconds": timeout_seconds,
        "gpu_opt_in": os.environ.get("SAGITTARIUS_ENABLE_GPU_TESTS") == "1"}
    output = Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a new empty output directory to preserve prior evidence")
    output.mkdir(parents=True, exist_ok=True)
    freeze = {"scenarios": selected, "settings": settings}
    digest = hashlib.sha256(json.dumps(freeze, sort_keys=True).encode()).hexdigest()
    env = os.environ.copy()
    for key in ("JULIA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        env[key] = "1"
    campaign = {**freeze, "config_sha256": digest, "output_dir": str(output),
                "plan_version": "benchmark-implementation-plan/v2", "protocol_version": "benchmark-protocol/v1",
                "workload_version": WORKLOAD_VERSION, "frozen_at": datetime.now(timezone.utc).isoformat(),
                "command": sys.argv, "cwd": str(Path.cwd()), "python_executable": sys.executable,
                "source": version_info(initialize_backend=False), "thread_environment": {k: env[k] for k in ("JULIA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
                "include_gpu": include_gpu, "repeats": repeats, "repeat_count": repeat_count,
                "stop_policy": "continue, preserve all declared paths and partial measurements",
                "classification": "local_only; software/numerical evidence, no public performance or physical approximation claims"}
    try:
        campaign["hardware"] = {"cpu_model": next(line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")),
                                "physical_memory_bytes": os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")}
    except (OSError, ValueError, StopIteration):
        campaign["hardware"] = {"unavailable_reason": "CPU/physical memory metadata unavailable"}
    (output / "source").mkdir()
    campaign["source_file_sha256"] = {}
    for name in SOURCE_FILES:
        source = Path(__file__).with_name(name)
        shutil.copyfile(source, output / "source" / name)
        campaign["source_file_sha256"][name] = hashlib.sha256(source.read_bytes()).hexdigest()
    write_json(output / "campaign.json", campaign)
    rows, interrupted = [], False
    for s in selected:
        directory = output / s["scenario_id"]
        directory.mkdir()
        config_path, checkpoint_path = directory / "config.json", directory / "checkpoint.json"
        write_json(config_path, {"scenario": s, "settings": settings, "source_file_sha256": campaign["source_file_sha256"], "config_sha256": digest})
        exclusion = None
        if s["mode"] not in CPU_MODES and not (include_gpu and settings["gpu_opt_in"]):
            exclusion = "Optional CUDA disabled; requires --include-gpu and SAGITTARIUS_ENABLE_GPU_TESTS=1"
        elif s["mode"].startswith("full_") and s["full_dim"] > max_full_dim:
            exclusion = f"full_dim {s['full_dim']} exceeds max_full_dim {max_full_dim}"
        elif s["estimated_peak_bytes"] > settings["memory_limit_bytes"]:
            exclusion = "Construction/reference estimate exceeds declared memory budget"
        state, supervision = {}, {}
        if not exclusion and not interrupted:
            command = [sys.executable, "-m", "sagittarius.ablation_benchmark", "--child", str(config_path), str(checkpoint_path)]
            write_json(directory / "command.json", {"argv": command, "cwd": str(Path.cwd())})
            try:
                supervision = supervise(command, cwd=str(Path.cwd()), env=env, log_path=directory / "child.log",
                    timeout_seconds=timeout_seconds, memory_limit_bytes=settings["memory_limit_bytes"])
            except KeyboardInterrupt:
                interrupted = True
                supervision = {"reason": "interrupted"}
            except Exception as exc:
                state["failure"] = benchmark_failure_context(exc, stage="setup")
            if checkpoint_path.exists():
                try:
                    state = json.loads(checkpoint_path.read_text())
                except (OSError, ValueError) as exc:
                    state["failure"] = benchmark_failure_context(exc, stage="artifact")
        row = campaign_row(s, settings, state, supervision, exclusion=exclusion)
        row["artifacts"].update(config=str(config_path), checkpoint=str(checkpoint_path) if checkpoint_path.exists() else None)
        row["metrics"]["config_sha256"] = digest
        for item in row["metrics"].get("measurements", []):
            item["row_id"] = f"{s['scenario_id']}-repeat-{item['repeat_index']}"
        row["metrics"]["statistics"] = runtime_summary(row["metrics"].get("measurements", []), repeat_count)
        rows.append(row)
        write_json(output / "progress.json", {"rows": rows})
        print(f"{s['scenario_id']} D={s['basis_size']}: {row['status']}", flush=True)
    paths = write_benchmark_artifacts(output_dir=output, stem="ablation_bench_results", name="Hamiltonian execution path ablation v2",
        description="Fixed normalized Python matvec batches; optional CUDA ODE is separate diagnostic evidence.",
        parameters=campaign, rows=rows, backend="CPU", diagnostics={"initialized_doctor": "per-path checkpoints"},
        run_manifests=[manifest for r in rows for manifest in r["metrics"].get("run_manifests", [])],
        columns=["row_id", "mode", "status", "workload", "atom_count", "full_dim", "basis_size", "repeats", "total_time_s", "time_per_operation_s", "median_batch_time_s", "reference_error", "reference_relative_error", "max_rss", "max_rss_unit"],
        benchmark_context={"family": FAMILY, "tier": TIER, "disclosure_status": "local_only", "workload_version": WORKLOAD_VERSION})
    paths["suite"] = write_benchmark_suite_artifact(output_dir=output, stem="ablation_bench_results_suite",
        suite_id="phase16-p0-ablation-v2", family=FAMILY, tier=TIER, rows=rows,
        source=campaign["source"], environment={"threads": campaign["thread_environment"]},
        scenario_defaults={"campaign": str(output / "campaign.json"), "settings": settings})
    repeat_rows = []
    for row in rows:
        for item in row["metrics"].get("measurements", []):
            repeat_rows.append(make_benchmark_row(row_id=item["row_id"], scenario_id=row["scenario_id"], family=FAMILY, tier=TIER,
                status="passed" if item["eligible"] else "incomplete" if row["workload"] == "ode_solve" else "failed", stage="validation",
                problem=row["problem"], solver=row["solver"], backend=row["backend"], observables=row["observables"],
                metrics={k: v for k, v in item.items() if k != "artifacts"}, artifacts=item["artifacts"],
                failure=None if item["eligible"] else {"stage": "validation", "code": "BENCHMARK_REPEAT_INELIGIBLE", "message": "Repeat lacks applicable numerical gate", "remediation": "Inspect retained outputs and reference requirements."}))
    write_json(output / "ablation_repeats.json", repeat_rows)
    expected = scenarios()
    required = {s["scenario_id"] for s in expected if s["required"]}
    cpu = {s["scenario_id"] for s in expected if s["mode"] in CPU_MODES and (s["N"] <= 12 or not s["mode"].startswith("full_"))}
    passed = {r["scenario_id"] for r in rows if r["status"] == "passed"}
    write_json(output / "coverage.json", {"required_small_cpu_passed": all(s in selected for s in expected) and required <= passed,
        "all_target_cpu_paths_passed": all(s in selected for s in expected) and cpu <= passed,
        "declared_rows_accounted": len(rows) == len(selected),
        "missing_successful_cpu_paths": sorted(cpu - passed),
        "successful_n20_paths": [r["scenario_id"] for r in rows if r["atom_count"] == 20 and r["status"] == "passed"],
        "optional_cuda_status": "separate GPU-suite parity required; skips do not close CUDA scope",
        "classification": "local_only"})
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", nargs=2, help=argparse.SUPPRESS)
    parser.add_argument("--atom-count", type=int)
    parser.add_argument("--sizes", nargs="+", type=int)
    parser.add_argument("--spacing", type=float, default=2.)
    parser.add_argument("--blockade-radius", type=float, default=3.)
    parser.add_argument("--repeats", type=int, default=50, help="H*psi operations per timed batch (legacy meaning)")
    parser.add_argument("--repeat-count", type=int, default=5, help="Independent measured batches")
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--max-full-dim", type=int, default=4096)
    parser.add_argument("--memory-limit-mb", type=float, default=9216)
    parser.add_argument("--timeout-seconds", type=float, default=600.)
    parser.add_argument("--full-rtol", type=float, default=1e-12)
    parser.add_argument("--reduced-atol", type=float, default=1e-10)
    parser.add_argument("--gpu-duration", type=float, default=.2)
    parser.add_argument("--include-gpu", action="store_true")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()
    if args.child:
        _child(*args.child)
        return
    if args.sizes is not None and args.atom_count is not None:
        parser.error("Choose --sizes or --atom-count")
    options = vars(args)
    options.pop("child")
    options["sizes"] = args.sizes if args.sizes is not None else (args.atom_count,) if args.atom_count is not None else SIZES
    options["atom_count"] = args.atom_count or 10
    benchmark_ablation(**options)


if __name__ == "__main__":
    main()
