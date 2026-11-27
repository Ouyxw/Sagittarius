"""Opt-in matched CPU/CUDA scans, with one persistent process per backend."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

import numpy as np

from .benchmark_failures import benchmark_failure_context
from .benchmark_measurement import linux_process_memory, runtime_summary, write_json
from .benchmarking import make_benchmark_row, write_benchmark_artifacts
from .benchmark_suite import write_benchmark_suite_artifact
from .cuda_parity import json_native, solve_pair_gate

FAMILY, TIER = "backend_performance", "performance"
SIZES = (2, 4, 8, 12, 16, 20)
WORKLOAD_VERSION = "matched-cpu-cuda-scan/v2"
SOURCE_FILES = ("gpu_benchmark.py", "cuda_parity.py", "benchmark_measurement.py",
                "benchmarking.py", "benchmark_suite.py", "benchmark_failures.py", "api.py", "runtime.py", "scaling_benchmark.py")
THREAD_KEYS = ("JULIA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")


def chain_scenario(n, *, legacy=False):
    return {"scenario_id": "chain_n3_cpu_cuda" if legacy else f"chain_n{n}_cpu_cuda",
            "geometry": "chain", "N": n, "coordinates": [[i * (.5 if legacy else 4.), 0., 0.] for i in range(n)],
            "C6": 10. if legacy else 100., "blockade_radius": .6 if legacy else 4.4,
            "omega": .3 if legacy else 2 * math.pi, "delta": .05 if legacy else 0.,
            "duration": .25 if legacy else .5, "observables": {"pop0": 0}, "required": True}


def mwis_scenario():
    project = Path(__file__).resolve().parents[1] / "projects" / "mwis_udg"
    sys.path.insert(0, str(project))
    try:
        from batch_verify import generate_random_udg
        graph = generate_random_udg(2, density=1., blockade_radius=1., seed=3)
        nodes = list(graph.nodes())
        coordinates = [[*graph.nodes[node]["pos"], 0.] for node in nodes]
        weights = [float(graph.nodes[node]["weight"]) for node in nodes]
        edges = [list(edge) for edge in graph.edges()]
    finally:
        sys.path.remove(str(project))
    return {"scenario_id": "weighted_udg_n2_seed3_cpu_cuda", "geometry": "weighted_udg",
            "N": 2, "coordinates": coordinates, "C6": 1., "blockade_radius": 1.,
            "duration": .1, "weights": weights, "edges": edges, "seed": 3, "density": 1.,
            "omega_max": 2 * math.pi, "observables": {"pop0": 0, "pop1": 1}, "required": True}


def scenarios(sizes=SIZES, *, include_fixtures=True):
    sizes = list(sizes)
    if not sizes or len(set(sizes)) != len(sizes) or any(type(n) is not int or not 1 <= n <= 20 for n in sizes):
        raise ValueError("Select unique integer sizes in [1,20]")
    result = [chain_scenario(n) for n in sizes]
    if include_fixtures:
        lattice = chain_scenario(4)
        lattice.update(scenario_id="lattice_2x2_cpu_cuda", geometry="lattice_2x2",
                       coordinates=[[0., 0., 0.], [4., 0., 0.], [0., 4., 0.], [4., 4., 0.]])
        result.extend([lattice, mwis_scenario()])
    return result


def basis_values(s):
    coordinates = np.asarray(s["coordinates"])
    forbidden = [(i, j) for i in range(s["N"]) for j in range(i)
                 if np.linalg.norm(coordinates[i] - coordinates[j]) < s["blockade_radius"]]
    neighbors = [0] * s["N"]
    for i, j in forbidden:
        neighbors[i] |= 1 << j
        neighbors[j] |= 1 << i
    values = []
    def visit(index, bits):
        if index == s["N"]:
            values.append(bits)
            return
        visit(index + 1, bits)
        if not bits & neighbors[index]:
            visit(index + 1, bits | (1 << index))
    visit(0, 0)
    return sorted(values)


def settings(*, warmups=2, repeat_count=5, timeout_seconds=1200., memory_limit_mb=9216., parity_atol=1e-6):
    if type(warmups) is not int or warmups < 0 or type(repeat_count) is not int or repeat_count < 1:
        raise ValueError("warmups >=0 and repeat_count >=1 must be integers")
    if not all(math.isfinite(v) and v > 0 for v in (timeout_seconds, memory_limit_mb, parity_atol)):
        raise ValueError("Limits and tolerance must be positive and finite")
    return dict(warmups=warmups, repeat_count=repeat_count, timeout_seconds=timeout_seconds,
                memory_limit_bytes=int(memory_limit_mb * 1024**2), parity_atol=parity_atol,
                method="Tsit5", adaptive=True, dt=None, reltol=1e-8, abstol=1e-10, output_count=101,
                precision="complex128", initial_state="all_ground")


def _simulation(s, cfg, backend):
    from . import Atom, Pulse, PulseSequence, Register, Simulation, SolverConfig
    register = Register([Atom(*xyz) for xyz in s["coordinates"]], C6=s["C6"])
    if s["geometry"] == "weighted_udg":
        sequence = PulseSequence(omega=Pulse.sin_squared(amplitude=s["omega_max"], duration=s["duration"]),
            delta=[Pulse.ramp(start=-2 * s["omega_max"], end=w * 2 * math.pi, duration=s["duration"]) for w in s["weights"]])
    else:
        sequence = PulseSequence(omega=s["omega"], delta=s["delta"])
    times = np.linspace(0., s["duration"], cfg["output_count"]).tolist()
    solver = SolverConfig(blockade_radius=s["blockade_radius"], use_gpu=backend == "CUDA", gpu_backend="CUDA",
        method=cfg["method"], adaptive=cfg["adaptive"], dt=cfg["dt"], reltol=cfg["reltol"], abstol=cfg["abstol"], saveat=times)
    return Simulation(register, sequence, solver), times


def timed_solve(simulation, initial, duration, observables, *, synchronize=None, clock=time.perf_counter):
    """Reset before synchronization; stop before checks and artifact writes."""
    if hasattr(initial, "amplitudes"):
        from . import PreparedState
        state = PreparedState(initial.amplitudes.copy(), dict(initial.metadata))
    else:
        state = initial.copy()
    if synchronize:
        synchronize()
    started = clock()
    result = simulation.run(state, 0., duration, observables=observables)
    if synchronize:
        synchronize()
    return result, clock() - started


def scenario_gate(cpu, cuda, s, cfg):
    from .api import _pulse_manifest
    times = np.linspace(0., s["duration"], cfg["output_count"]).tolist()
    gate = solve_pair_gate(cpu, cuda, times, cfg["parity_atol"], tuple(s["observables"]))
    expected_simulation, _ = _simulation(s, cfg, "CPU")
    expected_pulse = {key: _pulse_manifest(getattr(expected_simulation.sequence, key)) for key in ("omega", "delta")}
    for result in (cpu, cuda):
        manifest = result.manifest
        if manifest["register"]["atoms"] != s["coordinates"] or manifest["register"]["C6"] != s["C6"]:
            raise AssertionError("Executed register differs from frozen scenario")
        for key in ("method", "adaptive", "dt", "reltol", "abstol"):
            if manifest["solver"][key] != cfg[key]:
                raise AssertionError("Executed solver differs from freeze")
        if manifest["solver"]["blockade_radius"] != s["blockade_radius"] or manifest["initial_state"]["basis_size"] != len(basis_values(s)):
            raise AssertionError("Executed basis/radius differs from freeze")
        if manifest["pulse"] != expected_pulse or manifest["solver"]["observables"] != s["observables"]:
            raise AssertionError("Executed pulse/observable declarations differ from freeze")
        preparation = manifest["initial_state"].get("preparation") or {}
        if preparation.get("type") != "all_ground" or preparation.get("bitstring") != "0" * s["N"] or abs(manifest["initial_state"]["norm"] - 1.) > 1e-14:
            raise AssertionError("Executed initial state differs from all-ground freeze")
    if s["geometry"] == "weighted_udg":
        basis = basis_values(s)
        distributions = [r.final_bitstring_distribution() for r in (cpu, cuda)]
        expected_keys = {format(bits, f"0{s['N']}b")[::-1] for bits in basis}
        if any(set(p) != expected_keys or any(not math.isfinite(v) or v < -cfg["parity_atol"] for v in p.values()) or abs(sum(p.values()) - 1.) > cfg["parity_atol"] for p in distributions):
            raise AssertionError("MWIS basis/probability normalization failed")
        error = max(abs(distributions[0][k] - distributions[1][k]) for k in expected_keys)
        best = int(max(distributions[1], key=distributions[1].get)[::-1], 2)
        feasible = all(not ((best >> i) & (best >> j) & 1) for i, j in s["edges"])
        objective = lambda bits: sum(w for i, w in enumerate(s["weights"]) if bits >> i & 1)
        optimum = max(objective(bits) for bits in basis)
        gate.update(cpu_cuda_probability_max_abs_error=error, cuda_feasible=feasible,
                    cuda_objective=objective(best), exact_objective=optimum,
                    exact_reference="exhaustive enumeration of frozen two-node graph",
                    passed=gate["passed"] and feasible and error <= cfg["parity_atol"])
    return gate


def _gpu_snapshot(jl):
    try:
        raw = jl.seval('Dict("total_bytes" => Int(CUDA.total_memory()), "available_bytes" => Int(CUDA.free_memory()))')
        return {str(k): int(v) for k, v in raw.items()}
    except Exception as exc:
        return {"unavailable_reason": str(exc)}


def _worker(config_path, backend):
    from . import doctor
    from .runtime import get_julia
    from .scaling_benchmark import _runtime_context
    frozen = json.loads(Path(config_path).read_text())
    s, cfg = frozen["scenario"], frozen["settings"]
    directory = Path(config_path).parent / backend.lower()
    directory.mkdir()
    checkpoint = directory / "checkpoint.json"
    state = {"stage": "setup", "records": [], "backend": backend}
    def save():
        state["memory"] = linux_process_memory(os.getpid())
        write_json(checkpoint, state)
    try:
        if backend == "CUDA" and os.environ.get("SAGITTARIUS_ENABLE_GPU_TESTS") != "1":
            raise RuntimeError("CUDA opt-in disabled")
        for relative, digest in frozen["source_sha256"].items():
            if hashlib.sha256((Path(frozen["source_root"]) / relative).read_bytes()).hexdigest() != digest:
                raise RuntimeError("Frozen source changed during campaign")
        started = time.perf_counter()
        state["doctor"] = json_native(doctor(backend=backend, initialize_backend=True))
        state["initialization_seconds"] = time.perf_counter() - started
        save()
        if not state["doctor"].get("available") or not (state["doctor"].get("backend_probe") or {}).get("available"):
            raise RuntimeError(f"{backend} initialization failed")
        jl, _ = get_julia()
        state["runtime_context"] = _runtime_context()
        project = Path(str(jl.seval("Base.active_project()")))
        state["runtime_files"] = {}
        for path in (project, project.with_name("Manifest.toml")):
            if path.is_file():
                shutil.copyfile(path, directory / path.name)
                state["runtime_files"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        state["baseline_memory"] = linux_process_memory(os.getpid())
        started = time.perf_counter()
        simulation, times = _simulation(s, cfg, backend)
        dimension = simulation.validate()
        state["construction_seconds"] = time.perf_counter() - started
        if list(map(int, simulation._basis)) != basis_values(s):
            raise AssertionError("Executed basis differs from frozen geometry")
        state["basis_size"] = dimension
        from . import all_ground_state
        initial = all_ground_state(simulation)
        sync = (lambda: jl.seval("CUDA.synchronize()")) if backend == "CUDA" else None
        if backend == "CUDA":
            state["gpu_memory"] = {"before": _gpu_snapshot(jl), "peak_bytes": None,
                "unavailable_reason": "Device free/total snapshots are not peaks and include caches/other users."}
        state["stage"] = "ready"
        save()
        request_path = directory / "request.json"
        while True:
            if not request_path.exists():
                time.sleep(.02)
                continue
            label = json.loads(request_path.read_text())["label"]
            request_path.unlink()
            state["stage"] = "solve"
            save()
            call_started = time.monotonic()
            result, seconds = timed_solve(simulation, initial, s["duration"], s["observables"], synchronize=sync)
            record = {"label": label, "runtime_seconds": seconds, "call_started_monotonic": call_started,
                      "call_finished_monotonic": time.monotonic(), "artifacts": {}}
            state["records"].append(record)
            state["stage"] = "artifact"
            save()
            result_path, manifest_path = directory / f"{label}.result.json", directory / f"{label}.manifest.json"
            result.save(str(result_path))
            write_json(manifest_path, result.manifest)
            record["artifacts"] = {"result_artifact": str(result_path), "run_manifest": str(manifest_path)}
            if backend == "CUDA":
                record["gpu_memory_snapshot"] = _gpu_snapshot(jl)
                state["gpu_memory"]["after"] = record["gpu_memory_snapshot"]
            state.update(stage="ready", completed_label=label)
            save()
    except BaseException as exc:
        state["failure"] = benchmark_failure_context(exc, stage=state["stage"], backend_probe=state.get("doctor"))
        save()
        raise


class _Workers:
    """Two path processes, with independent sampled RSS and a scenario deadline."""
    def __init__(self, config_path, cfg):
        self.config_path, self.cfg = Path(config_path), cfg
        self.children, self.states, self.peaks = {}, {}, {}
        self.started = time.monotonic()

    def start(self, backend):
        log = (self.config_path.parent / f"{backend.lower()}.log").open("w")
        env = os.environ.copy()
        env.update({key: "1" for key in THREAD_KEYS})
        command = [sys.executable, "-m", "sagittarius.gpu_benchmark", "--worker", str(self.config_path), backend]
        write_json(self.config_path.parent / f"{backend.lower()}.command.json", {"argv": command, "cwd": str(Path.cwd()), "threads": {k: env[k] for k in THREAD_KEYS}})
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                   text=True, env=env, start_new_session=True)
        self.children[backend] = (process, log)
        self.wait(backend)

    def refresh(self):
        for backend, (process, _) in self.children.items():
            checkpoint = self.config_path.parent / backend.lower() / "checkpoint.json"
            if checkpoint.exists():
                self.states[backend] = json.loads(checkpoint.read_text())
            memory = linux_process_memory(process.pid)
            peak = memory["peak_bytes"]
            if peak is not None:
                self.peaks[backend] = max(self.peaks.get(backend, 0), peak)
            if memory["rss_bytes"] is not None and memory["rss_bytes"] > self.cfg["memory_limit_bytes"]:
                raise MemoryError(f"{backend} worker exceeded sampled RSS budget")
        if time.monotonic() - self.started > self.cfg["timeout_seconds"]:
            raise TimeoutError("CPU/CUDA scenario exceeded wall-time limit")

    def wait(self, backend, label=None):
        while True:
            self.refresh()
            state = self.states.get(backend, {})
            if state.get("failure"):
                raise RuntimeError(state["failure"]["message"])
            if state.get("stage") == "ready" and (label is None or state.get("completed_label") == label):
                return state
            process = self.children[backend][0]
            if process.poll() is not None:
                raise RuntimeError(f"{backend} worker exited {process.returncode}; inspect retained log/checkpoint")
            time.sleep(.05)

    def solve(self, backend, label):
        write_json(self.config_path.parent / backend.lower() / "request.json", {"label": label})
        return self.wait(backend, label)["records"][-1]

    def close(self):
        for process, log in self.children.values():
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait()
            log.close()


def pair_statistics(pairs, cfg, *, valid_campaign=True):
    measured = [pair for pair in pairs if pair["phase"] == "measured"]
    summaries = {}
    for backend in ("CPU", "CUDA"):
        records = [{"row_id": pair["row_id"], "eligible": bool(pair.get("gate", {}).get("passed")),
                    "runtime_seconds": pair["paths"][backend]["runtime_seconds"]}
                   for pair in measured if backend in pair["paths"]]
        summaries[backend] = runtime_summary(records, cfg["repeat_count"])
    qualified = valid_campaign and cfg["warmups"] >= 2 and all(s["eligible"] >= 5 for s in summaries.values())
    denominator = summaries["CUDA"]["runtime_seconds"]["median"]
    qualified = qualified and denominator is not None and denominator > 0
    return {"statistics": summaries,
            "median_cpu_over_cuda": summaries["CPU"]["runtime_seconds"]["median"] / denominator if qualified else None,
            "ratio_definition": "median(CPU runtime) / median(CUDA runtime)",
            "ratio_unavailable_reason": None if qualified else "Requires successful full-grid/configuration gates, two warmups and at least five eligible repeats per path."}


def measure_row(s, cfg, directory, frozen, *, cancelled=False):
    from . import SimulationResult
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    config_path = directory / "config.json"
    write_json(config_path, {**frozen, "scenario": s, "settings": cfg})
    pairs, failure, status = [], None, "passed"
    workers = _Workers(config_path, cfg)
    skipped = os.environ.get("SAGITTARIUS_ENABLE_GPU_TESTS") != "1"
    d = len(basis_values(s))
    estimate = 2 * 1024**3 + d * (512 + 128 * s["N"]) + cfg["output_count"] * len(s["observables"]) * 8
    if cancelled:
        status = "incomplete"
        failure = {"stage": "setup", "code": "BENCHMARK_CAMPAIGN_INTERRUPTED", "message": "Not started after campaign interruption", "remediation": "Retain progress and start a new campaign."}
    elif skipped or estimate > cfg["memory_limit_bytes"]:
        status = "skipped"
        failure = {"stage": "setup", "code": "BENCHMARK_GPU_OPT_IN_DISABLED" if skipped else "BENCHMARK_MEMORY_BUDGET_EXCLUSION",
            "message": "Requires SAGITTARIUS_ENABLE_GPU_TESTS=1" if skipped else "Construction estimate exceeds per-path memory budget",
            "remediation": "Retain exclusion; rerun in a new campaign with explicit hardware opt-in and adequate limits."}
    else:
        try:
            workers.start("CPU")
            workers.start("CUDA")
            phases = [("first", 0)] + [("warmup", i) for i in range(cfg["warmups"])] + [("measured", i) for i in range(cfg["repeat_count"])]
            for phase, index in phases:
                label = f"{phase}-{index}"
                order = ["CPU", "CUDA"] if index % 2 == 0 else ["CUDA", "CPU"]
                pair = {"row_id": f"{s['scenario_id']}-{label}", "phase": phase, "index": index, "pair_order": order, "paths": {}}
                pairs.append(pair)
                write_json(directory / "pairs.json", pairs)
                for backend in order:
                    pair["paths"][backend] = workers.solve(backend, label)
                    write_json(directory / "pairs.json", pairs)
                results = {b: SimulationResult.load(pair["paths"][b]["artifacts"]["result_artifact"]) for b in order}
                pair["gate"] = scenario_gate(results["CPU"], results["CUDA"], s, cfg)
                write_json(directory / "pairs.json", pairs)
                if not pair["gate"]["passed"]:
                    raise AssertionError("CPU/CUDA full observable trajectory parity failed")
            if cfg["warmups"] < 2 or cfg["repeat_count"] < 5:
                status = "incomplete"
                failure = {"stage": "validation", "code": "BENCHMARK_INSUFFICIENT_REPEATS", "message": "Pilot has fewer than two warmups/five repeats", "remediation": "Run a frozen complete campaign."}
        except BaseException as exc:
            status = "incomplete" if isinstance(exc, (TimeoutError, KeyboardInterrupt)) else "failed"
            failure = next((state["failure"] for state in workers.states.values() if state.get("failure")), None)
            failure = failure or benchmark_failure_context(exc, stage="validation" if isinstance(exc, AssertionError) else "solve", timeout_seconds=cfg["timeout_seconds"])
        finally:
            workers.close()
    for backend in ("CPU", "CUDA"):
        path = directory / backend.lower() / "checkpoint.json"
        if path.exists():
            workers.states[backend] = json.loads(path.read_text())
    metrics = {"pairs": pairs, "paths": workers.states, "sampled_peak_bytes": workers.peaks,
               "teardown_policy": "Workers deliberately terminated as process groups after checkpoint retention; failures/timeouts preserve the same checkpoints.",
               "worker_returncodes": {b: process.returncode for b, (process, _) in workers.children.items()},
               "estimated_peak_bytes_per_path": estimate, "basis_size": d, "full_dim": 2**s["N"],
               "supervision_seconds": time.monotonic() - workers.started,
               "memory_scope": "Separate backend worker lifetimes including doctor/construction/writes, excluding controller references. RSS sampled every 50ms, not a hard cap.",
               **pair_statistics(pairs, cfg, valid_campaign=status == "passed")}
    row = make_benchmark_row(row_id=s["scenario_id"], scenario_id=s["scenario_id"], family=FAMILY, tier=TIER,
        status=status, stage="validation" if status == "passed" else (failure or {}).get("stage", "setup"),
        problem={**s, "atom_count": s["N"], "basis_size": d, "full_dim": 2**s["N"], "basis": "blockade_reduced",
                 "atom_order": "atom i is bit i (LSB); ascending bitstrings", "units": {"length": "um", "time": "us", "frequency": "rad/us", "C6": "rad*um^6/us"}},
        solver=cfg, backend={"requested_backend": "CUDA", "path": "matched_cpu_cuda", "per_path_doctor": "metrics.paths"},
        observables={"names": list(s["observables"]), "count": len(s["observables"]), "output_sample_count": cfg["output_count"]},
        metrics=metrics, artifacts={"config": str(config_path), "paired_records": str(directory / "pairs.json") if pairs else None},
        failure=failure, disclosure_status="local_only")
    measured = [p for p in pairs if p["phase"] == "measured"]
    first = measured[0]["paths"] if measured else {}
    row.update(N=s["N"], basis_size=d, t_cpu_s=first.get("CPU", {}).get("runtime_seconds"),
               t_gpu_s=first.get("CUDA", {}).get("runtime_seconds"), speedup=metrics["median_cpu_over_cuda"],
               max_rss=None, max_rss_unit=None)
    metrics["legacy_memory_unavailable_reason"] = "Use per-path byte-normalized memory; no combined process RSS measurement."
    # make_benchmark_row copies metrics; append optional summary columns there.
    row["metrics"]["legacy_memory_unavailable_reason"] = metrics["legacy_memory_unavailable_reason"]
    for backend in ("CPU", "CUDA"):
        summary = metrics["statistics"][backend]
        prefix = backend.lower()
        row[f"{prefix}_eligible"] = summary["eligible"]
        for statistic, value in summary["runtime_seconds"].items():
            row[f"{prefix}_{statistic}_s"] = value
    row["max_trajectory_error"] = max((p["gate"]["parity_max_abs_error"] for p in pairs if p.get("gate", {}).get("parity_max_abs_error") is not None), default=None)
    row["raw_records"] = f"[pairs]({s['scenario_id']}/pairs.json)" if pairs else None
    for backend in ("CPU", "CUDA"):
        state = workers.states.get(backend, {})
        prefix = backend.lower()
        row[f"{prefix}_initialization_s"] = state.get("initialization_seconds")
        row[f"{prefix}_first_solve_s"] = next((p["paths"].get(backend, {}).get("runtime_seconds") for p in pairs if p["phase"] == "first"), None)
        row[f"{prefix}_peak_bytes"] = state.get("memory", {}).get("peak_bytes")
    return row


def benchmark_gpu(n_range=None, output_dir=".", *, include_fixtures=True, scenario_list=None, stem="gpu_bench_results", **options):
    from .runtime import version_info
    cfg = settings(**options)
    selected = scenarios(SIZES if n_range is None else n_range, include_fixtures=include_fixtures) if scenario_list is None else scenario_list
    if not selected or len({s["scenario_id"] for s in selected}) != len(selected):
        raise ValueError("Select nonempty unique scenarios")
    output = Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a new empty output directory to preserve evidence")
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    sources = [Path(__file__).with_name(name) for name in SOURCE_FILES]
    sources += list((root / "Sagittarius.jl" / "src").glob("*.jl"))
    sources += [Path(__file__).resolve().parents[1] / "projects/mwis_udg/batch_verify.py"]
    sources += [root / name for name in ("scripts/audit_gpu_campaign.py", "sagittarius_py/tests/test_gpu_benchmark.py",
        "sagittarius_py/tests/test_performance/benchmark_gpu.py", "sagittarius_py/tests/test_performance/benchmark_cuda_mwis_protocol.py",
        "sagittarius_py/pyproject.toml", "sagittarius_py/uv.lock", "Sagittarius.jl/Project.toml")]
    source_hashes = {}
    for path in sources:
        relative = path.relative_to(root)
        target = output / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        source_hashes[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    freeze = {"scenarios": selected, "settings": cfg, "source_sha256": source_hashes}
    campaign = {**freeze, "config_sha256": hashlib.sha256(json.dumps(freeze, sort_keys=True).encode()).hexdigest(),
        "source_root": str(root), "output_dir": str(output), "source": version_info(initialize_backend=False),
        "command": sys.argv, "cwd": str(Path.cwd()), "created_at": datetime.now(timezone.utc).isoformat(),
        "plan_version": "benchmark-implementation-plan/v2", "workload_version": WORKLOAD_VERSION,
        "thread_environment": {k: "1" for k in THREAD_KEYS}, "opt_in": os.environ.get("SAGITTARIUS_ENABLE_GPU_TESTS") == "1",
        "timer_policy": "End-to-end Simulation.run including construction/transfers/collection/manifest; CUDA sync before/after. Reset/references/checks/writes/reporting excluded.",
        "cache_policy": "Fresh process per scenario/backend; initialized doctor before first solve; persistent JIT; actual-scenario warmups; operators reconstructed per SDK call. First solve is not process-cold.",
        "stop_policy": "Continue; retain failures, partial records and every declared scenario.",
        "classification": "local_only; same-method implementation parity, no independent scientific validation or public performance approval"}
    write_json(output / "campaign.json", campaign)
    rows, cancelled = [], False
    for s in selected:
        row = measure_row(s, cfg, output / s["scenario_id"], {"source_root": str(root), "source_sha256": source_hashes}, cancelled=cancelled)
        cancelled = cancelled or (row.get("failure") or {}).get("exception_type") == "KeyboardInterrupt"
        rows.append(row)
        write_json(output / "progress.json", rows)
        print(f"{s['scenario_id']} D={row['basis_size']}: {row['status']}", flush=True)
    paths = write_benchmark_artifacts(output_dir=output, stem=stem, name="Matched CPU/CUDA scan v2",
        description=campaign["classification"], parameters=campaign, rows=rows, backend="CUDA",
        diagnostics={"initialized_doctor": "per-backend checkpoints"},
        columns=["scenario_id", "status", "N", "basis_size", "cpu_eligible", "cuda_eligible",
                 "cpu_median_s", "cpu_min_s", "cpu_max_s", "cpu_p25_s", "cpu_p75_s",
                 "cuda_median_s", "cuda_min_s", "cuda_max_s", "cuda_p25_s", "cuda_p75_s",
                 "speedup", "max_trajectory_error", "t_cpu_s", "t_gpu_s", "cpu_initialization_s", "cuda_initialization_s",
                 "cpu_first_solve_s", "cuda_first_solve_s", "cpu_peak_bytes", "cuda_peak_bytes", "raw_records"],
        benchmark_context={"family": FAMILY, "tier": TIER, "disclosure_status": "local_only", "workload_version": WORKLOAD_VERSION})
    paths["suite"] = write_benchmark_suite_artifact(output_dir=output, stem=f"{stem}_suite", suite_id="phase16-p1-gpu-v2",
        family=FAMILY, tier=TIER, rows=rows, source=campaign["source"], environment={"threads": campaign["thread_environment"]}, scenario_defaults={"campaign": str(output / "campaign.json")})
    write_json(output / "gpu_repeats.json", [{"scenario_id": r["scenario_id"], **p} for r in rows for p in r["metrics"]["pairs"]])
    expected_scenarios = scenarios()
    expected = {s["scenario_id"] for s in expected_scenarios}
    passed = {r["scenario_id"] for r in rows if r["status"] == "passed"}
    write_json(output / "coverage.json", {"declared_rows_accounted": len(rows) == len(selected), "all_p1_gpu_passed": all(s in selected for s in expected_scenarios) and expected <= passed,
        "missing_successful_scenarios": sorted(expected - passed), "classification": "local_only"})
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", nargs=2, help=argparse.SUPPRESS)
    parser.add_argument("--sizes", nargs="+", type=int, default=list(SIZES))
    parser.add_argument("--chains-only", action="store_true")
    parser.add_argument("--output-dir", default="benchmark-output/gpu-v2")
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--repeat-count", type=int, default=5)
    parser.add_argument("--timeout-seconds", type=float, default=1200.)
    parser.add_argument("--memory-limit-mb", type=float, default=9216.)
    parser.add_argument("--parity-atol", type=float, default=1e-6)
    args = parser.parse_args()
    if args.worker:
        _worker(*args.worker)
    else:
        benchmark_gpu(args.sizes, args.output_dir, include_fixtures=not args.chains_only, warmups=args.warmups,
            repeat_count=args.repeat_count, timeout_seconds=args.timeout_seconds, memory_limit_mb=args.memory_limit_mb, parity_atol=args.parity_atol)


if __name__ == "__main__":
    main()
