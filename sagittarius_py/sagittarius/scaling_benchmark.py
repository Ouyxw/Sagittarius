"""CPU reduced-basis scaling campaign (plan v2); no solver semantics live here."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time
from datetime import datetime, timezone

import numpy as np

from . import Atom, Register, PulseSequence, Simulation, SolverConfig, doctor
from .benchmarking import current_memory_usage, make_benchmark_row, write_benchmark_artifacts
from .benchmark_failures import benchmark_failure_context
from .benchmark_measurement import linux_process_memory, runtime_summary, supervise, write_json
from .benchmark_suite import write_benchmark_suite_artifact
from .runtime import get_julia, version_info

SIZES = (2, 4, 6, 8, 12, 16, 20)
SHAPES = {2: (1, 2), 4: (2, 2), 6: (2, 3), 8: (2, 4),
          12: (3, 4), 16: (4, 4), 20: (4, 5)}
RADII = (1.1, 1.5, 2.1)
TIMES = np.linspace(0., .5, 101).tolist()
FAMILY, TIER = "backend_performance", "scaling"
BACKEND = {"requested_backend": "CPU", "path": "cpu", "precision": "complex128",
           "implementation": "Julia matrix-free Schrodinger through Python SDK"}
OBSERVABLES = {"names": ["pop0"], "declarations": {"pop0": 0}, "count": 1,
               "output_sample_count": 101}


def _runtime_context():
    jl, _ = get_julia()
    jl.seval("using LinearAlgebra")
    return {"threads": {"julia": int(jl.seval("Threads.nthreads()")),
                        "blas": int(jl.seval("BLAS.get_num_threads()")),
                        "blas_config": str(jl.seval("BLAS.get_config()"))},
            "environment": {key: os.environ.get(key) for key in (
                "PYTHON_JULIACALL_EXE", "PYTHON_JULIACALL_PROJECT", "PYTHON_JULIACALL_BINDIR",
                "PYTHON_JULIAPKG_PROJECT", "JULIA_PROJECT", "JULIA_DEPOT_PATH",
                "JULIA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")}}


def scenarios(sizes=SIZES, geometries=("chain", "rectangle"), radii=RADII, *, allow_zero_radius=False):
    output = []
    for geometry in geometries:
        if geometry not in {"chain", "rectangle"}:
            raise ValueError("Geometry must be chain or rectangle.")
        for radius in radii:
            if not math.isfinite(radius) or radius < 0 or (radius == 0 and not allow_zero_radius):
                raise ValueError("Radius ratio must be finite and positive.")
            for n in sizes:
                if isinstance(n, bool) or not isinstance(n, int) or not 2 <= n <= 20:
                    raise ValueError("Scaling sizes must be integers in [2, 20].")
                if geometry == "rectangle" and n not in SHAPES:
                    raise ValueError("Rectangle sizes must have a declared v2 shape.")
                height, width = (1, n) if geometry == "chain" else SHAPES[n]
                coords = [[4. * x, 4. * y, 0.] for y in range(height) for x in range(width)]
                output.append({"scenario_id": f"{geometry}-r{radius:g}-n{n}",
                               "N": n, "geometry": geometry, "shape": [height, width],
                               "coordinates": coords, "spacing": 4., "radius_ratio": radius,
                               "blockade_radius": radius * 4., "C6": 100.,
                               "omega": 2 * math.pi, "delta": 0., "duration": .5,
                               "units": {"length": "um", "time": "us", "angular_frequency": "rad/us",
                                         "C6": "rad*um^6/us"},
                               "atom_order": "row-major x-fastest; atom i is bit i (LSB)",
                               "initial_state": "all_ground", "basis": "blockade_reduced",
                               "required": True, "full_dim": 2**n})
    if not output or len({s["scenario_id"] for s in output}) != len(output):
        raise ValueError("Select a nonempty matrix without duplicate scenarios.")
    return output


def basis_dimension(scenario):
    """Count independent sets without allocating a full/reduced state vector."""
    coords, n, radius = scenario["coordinates"], scenario["N"], scenario["blockade_radius"]
    neighbors = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            if math.dist(coords[i], coords[j]) < radius:
                neighbors[i] |= 1 << j
                neighbors[j] |= 1 << i
    memo = {0: 1}
    def count(mask):
        if mask not in memo:
            bit = mask & -mask
            rest = mask ^ bit
            memo[mask] = count(rest) + count(rest & ~neighbors[bit.bit_length() - 1])
        return memo[mask]
    return count((1 << n) - 1)


def memory_estimate(scenario):
    """Construction/state/output allowance plus Julia/JIT reserve; not a measurement.

    Matrix-free path: 256 bytes per reduced state/atom for mappings/transitions,
    64 complex state workspaces, output samples, and a 2 GiB runtime reserve.
    Dense reference temporaries are budgeted only at N<=8.
    """
    n, d = scenario["N"], scenario["basis_size"]
    dense = 16 * (2**n)**2 * 8 if n <= 8 else 0
    return 2 * 1024**3 + d * (256 * n + 64 * 16) + dense + 101 * 16


def projected_dense_reference(register, scenario, basis, times):
    """Independent full-space matrix projected onto exactly the executed basis."""
    n, radius = scenario["N"], scenario["blockade_radius"]
    if n > 8:
        raise ValueError("Dense reference is bounded to N<=8.")
    coords = scenario["coordinates"]
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)
             if math.dist(coords[i], coords[j]) < radius]
    expected_basis = [s for s in range(2**n)
                      if not any((s >> i) & (s >> j) & 1 for i, j in edges)]
    if basis != expected_basis:
        raise AssertionError("Executed basis ordering differs from independent bit enumeration.")
    identity = np.eye(2)
    number, flip = np.diag([0., 1.]), np.array([[0., 1.], [1., 0.]])
    def local(operator, atom):
        result = np.ones((1, 1))
        for bit in reversed(range(n)):
            result = np.kron(result, operator if bit == atom else identity)
        return result
    populations = [local(number, atom) for atom in range(n)]
    full = sum(scenario["omega"] / 2 * local(flip, atom)
               - scenario["delta"] * populations[atom] for atom in range(n))
    for i in range(n):
        for j in range(i + 1, n):
            interaction = scenario["C6"] / math.dist(coords[i], coords[j])**6
            full += interaction * (populations[i] * populations[j])
    projected = full[np.ix_(basis, basis)]
    eigenvalues, eigenvectors = np.linalg.eigh(projected)
    states = eigenvectors @ (np.exp(-1j * eigenvalues[:, None] * np.array(times)[None, :])
                             * eigenvectors[0, :, None].conj())
    mask = np.array([bool(s & 1) for s in basis])
    values = np.sum(np.abs(states[mask])**2, axis=0)
    jl, _ = get_julia()
    actual = jl.seval("begin; using SparseArrays; (reg, omega, delta, radius) -> Matrix(sparse(Sagittarius.Physics.RydbergHamiltonian(reg, omega, delta; blockade_radius=radius))); end")(
        register.jl_obj, jl.Vector[jl.Float64]([scenario["omega"]] * n),
        jl.Vector[jl.Float64]([scenario["delta"]] * n), radius)
    error = float(np.max(np.abs(projected - np.asarray(actual))))
    return values, {"type": "independent_full_dense_projected_eigendecomposition",
                    "basis": basis, "t": times, "pop0": values.tolist(),
                    "hamiltonian_max_abs_error": error,
                    "hamiltonian_atol": 1e-12, "hamiltonian_passed": error <= 1e-12,
                    "limitations": "Verifies projected implementation, not physical full-space equivalence."}


def _save_result(result, directory, label):
    result_path = directory / f"{label}.result.json"
    manifest_path = directory / f"{label}.manifest.json"
    result.save(str(result_path))
    write_json(manifest_path, result.manifest)
    return {"result_artifact": str(result_path), "run_manifest": str(manifest_path)}


def _trajectory(result, times):
    t, values = np.asarray(result.data["t"]), np.asarray(result.data["pop0"])
    if t.shape != (len(times),) or not np.allclose(t, times, rtol=0, atol=1e-14):
        raise AssertionError("Effective output grid differs from the frozen grid.")
    if values.shape != t.shape or not np.all(np.isfinite(values)):
        raise AssertionError("Observable trajectory is missing or nonfinite.")
    return values


def _child(config_path, checkpoint_path):
    config = json.loads(Path(config_path).read_text())
    s, settings = config["scenario"], config["settings"]
    directory = Path(checkpoint_path).parent
    state = {"stage": "setup", "repeats": [], "warmups": [], "artifacts": {}, "timing": {}}
    def checkpoint(stage):
        state["stage"] = stage
        state["memory"] = linux_process_memory(os.getpid())
        state["memory_source"] = current_memory_usage()
        write_json(checkpoint_path, state)
    checkpoint("setup")
    try:
        for name, expected_hash in config.get("source_file_sha256", {}).items():
            if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != expected_hash:
                raise RuntimeError("Frozen benchmark implementation changed during campaign; start a new campaign.")
        started = time.perf_counter()
        diagnostics = doctor(backend="CPU", initialize_backend=True)
        state["doctor"] = diagnostics
        state["timing"]["initialized_doctor_seconds"] = time.perf_counter() - started
        if not diagnostics["available"] or not (diagnostics.get("backend_probe") or {}).get("available"):
            raise RuntimeError("Initialized CPU doctor failed; see retained diagnostics.")
        state["runtime_context"] = _runtime_context()
        runtime_project = state["runtime_context"]["environment"].get("PYTHON_JULIACALL_PROJECT")
        if runtime_project:
            state["runtime_context"]["project_files"] = {}
            for name in ("Project.toml", "Manifest.toml"):
                source = Path(runtime_project) / name
                if source.exists():
                    target = directory / f"juliacall-{name}"
                    shutil.copyfile(source, target)
                    state["runtime_context"]["project_files"][name] = {
                        "path": str(target), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
        state["memory_baseline"] = linux_process_memory(os.getpid())
        started = time.perf_counter()
        register = Register([Atom(*coord) for coord in s["coordinates"]], C6=s["C6"])
        sequence = PulseSequence(omega=s["omega"], delta=s["delta"])
        solver = SolverConfig(**settings["solver"], blockade_radius=s["blockade_radius"])
        simulation = Simulation(register, sequence, solver)
        state["timing"]["python_setup_seconds"] = time.perf_counter() - started
        started = time.perf_counter()
        dimension = simulation.validate()
        state["timing"]["basis_construction_seconds"] = time.perf_counter() - started
        basis = [int(value) for value in simulation._basis] if solver.blockade_radius > 0 else list(range(dimension))
        if dimension != s["basis_size"]:
            raise AssertionError("Preflight basis dimension differs from executed basis.")
        def solve(sim=simulation):
            initial = np.zeros(dimension, dtype=np.complex128)
            initial[0] = 1.
            started = time.perf_counter()
            result = sim.run(initial, 0., s["duration"], observables={"pop0": 0})
            elapsed = time.perf_counter() - started
            return result, elapsed
        checkpoint("solve")
        result, elapsed = solve()
        state["timing"]["first_solve_seconds"] = elapsed
        checkpoint("artifact")
        state["artifacts"]["first_solve"] = _save_result(result, directory, "first")
        for index in range(settings["warmups"]):
            result, elapsed = solve()
            _trajectory(result, TIMES)
            state["warmups"].append({"warmup_index": index, "warmup": True, "runtime_seconds": elapsed})
            checkpoint("solve")
        checkpoint("reference")
        started = time.perf_counter()
        if s["N"] <= 8:
            reference_values, reference = projected_dense_reference(register, s, basis, TIMES)
        else:
            tighter = SolverConfig(**{**settings["solver"], "reltol": 1e-11, "abstol": 1e-13},
                                   blockade_radius=s["blockade_radius"])
            reference_result, _ = solve(Simulation(register, sequence, tighter))
            reference_values = _trajectory(reference_result, TIMES)
            state["artifacts"]["reference_result"] = _save_result(reference_result, directory, "tighter")
            reference = {"type": "tighter_tolerance_sensitivity", "reltol": 1e-11, "abstol": 1e-13,
                         "t": TIMES, "pop0": reference_values.tolist(),
                         "limitations": "Same-method sensitivity only; independent dense implementation evidence is limited to N<=8."}
        state["timing"]["reference_seconds"] = time.perf_counter() - started
        reference_path = directory / "reference.json"
        write_json(reference_path, reference)
        state["reference"] = reference
        state["artifacts"]["reference_report"] = str(reference_path)
        checkpoint("validation")
        for index in range(settings["repeat_count"]):
            checkpoint("solve")
            result, elapsed = solve()
            repeat = {"row_id": f"{s['scenario_id']}-repeat-{index}", "repeat_index": index,
                      "warmup": False, "operation_count": 1,
                      "runtime_seconds": elapsed, "eligible": False, "gate_passed": False,
                      "artifacts": {}, "effective_solver": result.diagnostics.get("simulation", {})}
            state["repeats"].append(repeat)
            checkpoint("artifact")
            repeat["artifacts"] = _save_result(result, directory, f"repeat-{index}")
            repeat["artifacts"]["reference_report"] = str(reference_path)
            checkpoint("validation")
            values = _trajectory(result, TIMES)
            error = float(np.max(np.abs(values - reference_values)))
            repeat["max_abs_error"] = error
            repeat["output_sample_count"] = len(values)
            repeat["effective_times"] = np.asarray(result.data["t"]).tolist()
            effective = result.diagnostics["simulation"]
            expected = {"effective_method": "Tsit5", "effective_adaptive": True,
                        "effective_dt": None, "reltol": solver.reltol,
                        "abstol": solver.abstol, "basis_size": dimension, "use_gpu": False,
                        "effective_saveat": TIMES}
            if any(k not in effective or effective[k] != v for k, v in expected.items()):
                raise AssertionError("Effective solver differs from the frozen request.")
            repeat["gate_passed"] = error <= settings["observable_atol"] and reference.get("hamiltonian_passed", True)
            repeat["eligible"] = repeat["gate_passed"]
            checkpoint("validation")
        state["complete"] = True
        checkpoint("artifact")
    except Exception as exc:
        state["failure"] = benchmark_failure_context(exc, stage=state["stage"],
            timeout_seconds=settings["timeout_seconds"], backend_probe=state.get("doctor", {}).get("backend_probe"))
        checkpoint(state["stage"])


def _row(s, settings, state, supervision):
    repeats = state.get("repeats", [])
    summary = runtime_summary(repeats, settings["repeat_count"])
    failure = state.get("failure")
    status = "passed"
    if supervision.get("reason") == "interrupted":
        failure = {"stage": state.get("stage", "setup"), "code": "BENCHMARK_INTERRUPTED",
                   "message": "Campaign interrupted; completed measurements retained.",
                   "remediation": "Inspect partial evidence and rerun in a new output directory."}
        status = "incomplete"
    elif supervision.get("reason"):
        exc = TimeoutError("Scenario exceeded wall-time budget.") if supervision["reason"] == "timeout" else MemoryError("Scenario exceeded RSS budget.")
        failure = benchmark_failure_context(exc, stage=state.get("stage", "setup"), timeout_seconds=settings["timeout_seconds"])
        status = "incomplete" if supervision["reason"] == "timeout" else "failed"
    elif supervision.get("returncode", 0) != 0:
        failure = benchmark_failure_context(RuntimeError(f"Child exited with code {supervision['returncode']}"), stage=state.get("stage", "setup"))
        status = "failed"
    elif failure:
        status = "failed"
    elif not state.get("complete") or summary["completed"] < settings["repeat_count"]:
        status = "incomplete"
    elif summary["eligible"] != summary["completed"]:
        status = "failed"
    elif settings["repeat_count"] < 5 or settings["warmups"] < 2:
        status = "incomplete"
    if status != "passed" and failure is None:
        failure = {"stage": "validation", "code": "BENCHMARK_INSUFFICIENT_EVIDENCE" if status == "incomplete" else "BENCHMARK_REFERENCE_MISMATCH",
                   "message": "Campaign needs two warmups, five eligible repeats and all numerical gates.",
                   "remediation": "Retain diagnostic rows and rerun with the frozen acceptance counts and gates."}
    if failure:
        failure["process_memory"] = state.get("memory", {"reason": "Child memory unavailable; inspect supervisor samples."})
        failure["limits"] = {key: settings[key] for key in ("timeout_seconds", "memory_limit_bytes")}
        failure["backend_probe"] = state.get("doctor", {}).get("backend_probe")
    metrics = {"statistics": summary, "repeats": repeats, "warmups": state.get("warmups", []),
               "timing": state.get("timing", {}), "memory": state.get("memory"),
               "memory_baseline": state.get("memory_baseline"), "memory_source": state.get("memory_source"), "supervision": supervision,
               "runtime_context": state.get("runtime_context"),
               "reference": state.get("reference"), "cache_policy": "fresh process per scenario; doctor precedes validate; SDK basis cache reused by solves",
               "timer_scope": "Simulation.run end-to-end including validation, operator construction, collection and manifest; excludes reference, checks and writes"}
    artifacts = dict(state.get("artifacts", {}))
    if repeats:
        artifacts.update(repeats[-1]["artifacts"])
    row = make_benchmark_row(row_id=s["scenario_id"], scenario_id=s["scenario_id"], family=FAMILY, tier=TIER,
        status=status, stage=failure["stage"] if failure else "artifact", problem=s,
        solver={**settings["solver"], "blockade_radius": s["blockade_radius"]}, backend=BACKEND,
        observables=OBSERVABLES, metrics=metrics, artifacts=artifacts, failure=failure)
    memory = state.get("memory_source", {})
    row.update({key: s[key] for key in ("N", "basis_size", "full_dim", "pruned_fraction")})
    row.update(time_s=repeats[0]["runtime_seconds"] if repeats else None,
               max_rss=memory.get("max_rss"), max_rss_unit=memory.get("max_rss_unit"),
               median_time_s=summary["runtime_seconds"]["median"])
    return row


def benchmark_scaling(n_max=16, blockade_radius=5., output_dir=".", *, matrix=False,
                      sizes=None, geometries=None, radii=None, scenario_ids=None,
                      warmups=2, repeat_count=5, timeout_seconds=600., memory_limit_mb=4096,
                      observable_atol=1e-8):
    """Old positional calls keep consecutive chain N and absolute Rb.

    CLI defaults to the full v2 matrix. Short runs retain incomplete diagnostic
    evidence rather than passing the performance acceptance gate.
    """
    if isinstance(warmups, bool) or isinstance(repeat_count, bool) or not isinstance(warmups, int) or not isinstance(repeat_count, int) or warmups < 0 or repeat_count < 1:
        raise ValueError("Warmups must be nonnegative; repeats must be positive integers.")
    if not all(math.isfinite(v) and v > 0 for v in (timeout_seconds, memory_limit_mb, observable_atol)):
        raise ValueError("Limits and tolerance must be finite and positive.")
    if not matrix and sizes is None and not 2 <= n_max <= 20:
        raise ValueError("n_max must be in [2, 20].")
    selected = scenarios(tuple(sizes) if sizes is not None else SIZES if matrix else tuple(range(2, n_max + 1)),
                         tuple(geometries) if geometries is not None else ("chain", "rectangle") if matrix else ("chain",),
                         tuple(radii) if radii is not None else RADII if matrix else (blockade_radius / 4.,),
                         allow_zero_radius=not matrix and radii is None)
    if scenario_ids:
        unknown = set(scenario_ids) - {s["scenario_id"] for s in selected}
        if unknown:
            raise ValueError(f"Unknown scenario IDs: {sorted(unknown)}")
        selected = [s for s in selected if s["scenario_id"] in scenario_ids]
    settings = {"warmups": warmups, "repeat_count": repeat_count, "timeout_seconds": timeout_seconds,
                "memory_limit_bytes": int(memory_limit_mb * 1024**2), "observable_atol": observable_atol,
                "solver": {"method": "Tsit5", "adaptive": True, "dt": None,
                           "reltol": 1e-8, "abstol": 1e-10, "saveat": TIMES}}
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "campaign.json").exists():
        raise FileExistsError("Use a new output directory to preserve the previous campaign.")
    for s in selected:
        s["basis_size"] = basis_dimension(s)
        s["pruned_fraction"] = 1 - s["basis_size"] / s["full_dim"]
        s["estimated_peak_bytes"] = memory_estimate(s)
    freeze = {"scenarios": selected, "settings": settings}
    digest = hashlib.sha256(json.dumps(freeze, sort_keys=True).encode()).hexdigest()
    env = os.environ.copy()
    for key in ("JULIA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        env[key] = "1"
    campaign = {**freeze, "config_sha256": digest, "plan_version": "benchmark-implementation-plan/v2",
                "frozen_at": datetime.now(timezone.utc).isoformat(),
                "protocol_version": "benchmark-protocol/v1", "command": sys.argv, "cwd": str(Path.cwd()),
                "output_dir": str(output), "python_executable": sys.executable,
                "function_call": {"n_max": n_max, "blockade_radius": blockade_radius, "matrix": matrix},
                "thread_environment": {k: env[k] for k in ("JULIA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
                "source": version_info(initialize_backend=False), "stop_policy": "continue; retain every declared scenario",
                "seed": None, "seed_reason": "deterministic all-ground constant-H evolution; no randomness",
                "reference_policy": "N<=8 independent projected full dense; N>8 tighter Tsit5 1e-11/1e-13 sensitivity",
                "classification": "local_only; no physical approximation or public performance claim"}
    campaign["hardware"] = {"cpu_model": None, "physical_memory_bytes": None}
    try:
        campaign["hardware"]["cpu_model"] = next(line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name"))
        campaign["hardware"]["physical_memory_bytes"] = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (OSError, ValueError, StopIteration):
        campaign["hardware"]["unavailable_reason"] = "Host CPU/memory metadata unavailable."
    source_dir = output / "source"
    source_dir.mkdir()
    source_hashes = {}
    for source in (Path(__file__), Path(__file__).with_name("benchmark_measurement.py")):
        shutil.copyfile(source, source_dir / source.name)
        source_hashes[source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
    campaign["source_file_sha256"] = source_hashes
    write_json(output / "campaign.json", campaign)
    rows = []
    interrupted = False
    for s in selected:
        directory = output / s["scenario_id"]
        directory.mkdir()
        config_path, checkpoint_path = directory / "config.json", directory / "checkpoint.json"
        write_json(config_path, {"scenario": s, "settings": settings, "config_sha256": digest,
                                 "source_file_sha256": source_hashes})
        state, supervision = {}, {}
        if s["estimated_peak_bytes"] > settings["memory_limit_bytes"]:
            row = _row(s, settings, state, supervision)
            row.update(status="skipped", stage="setup", failure={"stage": "setup", "code": "BENCHMARK_RESOURCE_EXCLUDED",
                "message": "Construction/reference estimate exceeds declared memory budget.",
                "remediation": "Retain exclusion; choose an adequate host/budget before rerunning."})
        elif interrupted:
            row = _row(s, settings, state, supervision)
        else:
            command = [sys.executable, "-m", "sagittarius.scaling_benchmark", "--child", str(config_path), str(checkpoint_path)]
            write_json(directory / "command.json", {"argv": command, "cwd": str(Path.cwd())})
            try:
                supervision = supervise(command, cwd=str(Path.cwd()), env=env,
                    log_path=directory / "child.log", timeout_seconds=timeout_seconds,
                    memory_limit_bytes=settings["memory_limit_bytes"])
            except KeyboardInterrupt:
                interrupted = True
                supervision = {"reason": "interrupted"}
            except Exception as exc:
                state["failure"] = benchmark_failure_context(exc, stage="setup", timeout_seconds=timeout_seconds)
            if checkpoint_path.exists():
                try:
                    state = json.loads(checkpoint_path.read_text())
                except (OSError, ValueError) as exc:
                    state["failure"] = benchmark_failure_context(exc, stage="artifact")
            row = _row(s, settings, state, supervision)
        row["artifacts"]["checkpoint"] = str(checkpoint_path) if checkpoint_path.exists() else None
        row["artifacts"]["config"] = str(config_path)
        row["metrics"]["config_sha256"] = digest
        rows.append(row)
        write_json(output / "progress.json", {"rows": rows})
        print(f"{s['scenario_id']} D={s['basis_size']}: {row['status']}", flush=True)
    paths = write_benchmark_artifacts(output_dir=output, stem="scaling_results", name="Reduced-basis scaling benchmark",
        description="Plan v2 CPU matrix with numerical gates and independent repeats; local evidence only.",
        parameters=campaign, rows=rows, backend="CPU",
        diagnostics={"per_scenario_doctor": "see checkpoints; initialized independently in each child"},
        run_manifests=[{"label": repeat["row_id"], "path": repeat["artifacts"].get("run_manifest")}
                       for row in rows for repeat in row["metrics"]["repeats"]],
        columns=["row_id", "status", "N", "basis_size", "full_dim", "pruned_fraction", "time_s", "median_time_s", "max_rss", "max_rss_unit"],
        benchmark_context={"family": FAMILY, "tier": TIER, "config_sha256": digest, "disclosure_status": "local_only"})
    paths["suite"] = write_benchmark_suite_artifact(output_dir=output, stem="scaling_results_suite",
        suite_id="phase16-p0-scaling-v2", family=FAMILY, tier=TIER, rows=rows,
        source=campaign["source"], environment={"thread_environment": campaign["thread_environment"]},
        scenario_defaults={"campaign": str(output / "campaign.json"), "settings": settings})
    repeat_rows = []
    for row in rows:
        for repeat in row["metrics"]["repeats"]:
            repeat_rows.append(make_benchmark_row(row_id=repeat["row_id"], scenario_id=row["scenario_id"],
                family=FAMILY, tier=TIER, status="passed" if repeat["eligible"] else "failed", stage="validation",
                problem=row["problem"], solver=row["solver"], backend=BACKEND, observables=OBSERVABLES,
                metrics={k: v for k, v in repeat.items() if k != "artifacts"}, artifacts=repeat["artifacts"],
                failure=None if repeat["eligible"] else {"stage": "validation", "code": "BENCHMARK_REPEAT_INELIGIBLE",
                    "message": "Repeat did not finish its numerical/artifact gate.", "remediation": "Inspect scenario checkpoint and retained result."}))
    write_json(output / "scaling_repeats.json", repeat_rows)
    expected = scenarios()
    small_ids = {s["scenario_id"] for s in expected if s["N"] <= 8}
    extended_ids = {s["scenario_id"] for s in expected if s["N"] > 8}
    passed_ids = {r["scenario_id"] for r in rows if r["status"] == "passed"}
    declared_ids = {r["scenario_id"] for r in rows}
    write_json(output / "coverage.json", {
        "selected_campaign_passed": all(r["status"] == "passed" for r in rows),
        "full_v2_matrix_passed": {s["scenario_id"] for s in expected} <= passed_ids,
        "small_reference_group_passed": small_ids <= passed_ids,
        "extended_rows_accounted": sorted(extended_ids & declared_ids),
        "missing_successful_v2_scenarios": sorted({s["scenario_id"] for s in expected} - passed_ids),
        "successful_n20_scenarios": sorted(r["scenario_id"] for r in rows if r["N"] == 20 and r["status"] == "passed"),
        "evidence_class": "local_only; numerical/software verification, not scientific validation or release approval"})
    return paths


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--child":
        _child(sys.argv[2], sys.argv[3])
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="benchmark-output/scaling")
    parser.add_argument("--sizes", nargs="+", type=int, default=list(SIZES))
    parser.add_argument("--geometries", nargs="+", choices=["chain", "rectangle"], default=["chain", "rectangle"])
    parser.add_argument("--radii", nargs="+", type=float, default=list(RADII), help="Rb/a ratios")
    parser.add_argument("--scenario", action="append", dest="scenario_ids")
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--repeat-count", type=int, default=5)
    parser.add_argument("--timeout-seconds", type=float, default=600.)
    parser.add_argument("--memory-limit-mb", type=float, default=4096.)
    parser.add_argument("--observable-atol", type=float, default=1e-8)
    args = vars(parser.parse_args())
    paths = benchmark_scaling(matrix=True, **args)
    print(f"Results: {paths['json']}")
    return 0 if all(r["status"] == "passed" for r in paths["artifact"]["timings"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
