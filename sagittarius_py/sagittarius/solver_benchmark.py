"""Plan v2 bounded CPU solver sensitivity; SDK/Julia solver semantics are unchanged."""
from __future__ import annotations

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

from .benchmark_measurement import linux_process_memory, runtime_summary, supervise, write_json
from .benchmark_failures import benchmark_failure_context
from .benchmarking import make_benchmark_row, write_benchmark_artifacts, current_memory_usage
from .benchmark_suite import write_benchmark_suite_artifact

WORKLOAD_VERSION = "solver-sensitivity/v1"
FAMILY, TIER = "backend_performance", "correctness"
THREAD_KEYS = ("JULIA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
OBSERVABLES = {"pop0": 0, "z0": {"type": "pauli_z", "atom": 0}}
TIMER_SCOPE = "Simulation.run including validation, pulse/operator construction, collection and manifest; reset, reference, checks and writes excluded"
COLUMNS = ["scenario_id", "status", "N", "basis_size", "method", "adaptive", "dt", "reltol", "abstol", "output_count", "eligible", "median_s", "min_s", "max_s", "p25_s", "p75_s", "max_abs_error", "raw_norm_error", "accuracy_atol", "reference_type", "peak_bytes", "raw_records"]


def scenarios():
    """One-axis scans around Tsit5/1e-8/1e-10/101, plus two combined cases.

    Both adaptive methods get all three tolerance pairs. RK4's 101-point anchor
    has three steps. Output-grid-only scans use the common Tsit5 anchor; two
    cross-axis controls use Vern9/tight/501 and RK4/T400/21. This is not a full
    Cartesian product, and grid refinement never means step refinement.
    """
    physics = [
        {"fixture": "rabi", "N": 1, "coordinates": [[0., 0., 0.]], "C6": 0.,
         "blockade_radius": 0., "duration": 1., "omega": [2 * math.pi], "delta": [0.], "pulse_kind": "constant"},
        {"fixture": "addressed", "N": 3, "coordinates": [[0., 0., 0.], [.5, 0., 0.], [1., 0., 0.]],
         "C6": 10., "blockade_radius": .6, "duration": .3,
         "omega": [.2, .3, .25], "delta": [-.1, 0., .1], "pulse_kind": "constant"},
        {"fixture": "ramp", "N": 3, "coordinates": [[0., 0., 0.], [4., 0., 0.], [8., 0., 0.]],
         "C6": 100., "blockade_radius": 4.4, "duration": 1., "pulse_kind": "linear_ramp",
         "omega_start": [0., 0., 0.], "omega_end": [4 * math.pi, 3 * math.pi, 2 * math.pi],
         "delta_start": [-4., -3., -2.], "delta_end": [4., 3., 2.]},
    ]
    result = []
    for p in physics:
        cases = []
        for method in ("Tsit5", "Vern9"):
            for power in (6, 8, 10):
                cases.append((f"{method.lower()}-tol{power}-g101", "tolerance", method, 10.**-power, 10.**-(power + 2), None, 101))
        for steps in (100, 200, 400):
            cases.append((f"rk4-s{steps}-g101", "step", "RK4", 1e-8, 1e-10, p["duration"] / steps, 101))
        for grid in (21, 501):
            cases.append((f"tsit5-tol8-g{grid}", "output_grid", "Tsit5", 1e-8, 1e-10, None, grid))
        cases += [("vern9-tol10-g501", "combined", "Vern9", 1e-10, 1e-12, None, 501),
                  ("rk4-s400-g21", "combined", "RK4", 1e-8, 1e-10, p["duration"] / 400, 21)]
        for label, axis, method, rtol, atol, dt, grid in cases:
            s = {**p, "scenario_id": f"{p['fixture']}-{label}", "axis": axis, "required": True,
                 "units": {"length": "um", "time": "us", "angular_frequency": "rad/us", "C6": "rad*um^6/us"},
                 "atom_order": "atom i is bit i (LSB); ascending integer basis", "initial_state": "all_ground",
                 "precision": "complex128", "output_count": grid, "full_dim": 2**p["N"]}
            s["solver"] = {"method": method, "adaptive": method != "RK4", "dt": dt, "reltol": rtol, "abstol": atol,
                           "blockade_radius": p["blockade_radius"], "saveat": np.linspace(0., p["duration"], grid).tolist()}
            s["basis_size"] = len(independent_basis(s))
            # Construction, reference and output allowances plus Julia/JIT reserve.
            s["estimated_peak_bytes"] = 2 * 1024**3 + s["basis_size"]**2 * 16 * 32 + grid * s["basis_size"] * 16 * 16
            result.append(s)
    return result


def independent_basis(s):
    edges = [(i, j) for i in range(s["N"]) for j in range(i + 1, s["N"])
             if math.dist(s["coordinates"][i], s["coordinates"][j]) < s["blockade_radius"]]
    return [b for b in range(2**s["N"]) if not any((b >> i) & (b >> j) & 1 for i, j in edges)]


def independent_hamiltonian(s, t):
    """Enumerate projected matrix directly, without the SDK Hamiltonian/compiler."""
    basis = independent_basis(s)
    index = {b: i for i, b in enumerate(basis)}
    if s["pulse_kind"] == "constant":
        omega, delta = s["omega"], s["delta"]
    else:
        u = t / s["duration"]
        omega, delta = [np.array(s[k + "_start"]) * (1 - u) + np.array(s[k + "_end"]) * u for k in ("omega", "delta")]
    h = np.zeros((len(basis), len(basis)), dtype=complex)
    for col, b in enumerate(basis):
        for i in range(s["N"]):
            h[col, col] -= delta[i] * ((b >> i) & 1)
            row = index.get(b ^ (1 << i))
            if row is not None:
                h[row, col] += omega[i] / 2
            for j in range(i + 1, s["N"]):
                if (b >> i) & (b >> j) & 1:
                    h[col, col] += s["C6"] / math.dist(s["coordinates"][i], s["coordinates"][j])**6
    return h


def independent_reference(s, *, method="DOP853", rtol=1e-12, atol=1e-14):
    times = np.asarray(s["solver"]["saveat"])
    basis = independent_basis(s)
    initial = np.zeros(len(basis), dtype=complex)
    initial[0] = 1
    if s["pulse_kind"] == "constant":
        eigenvalues, vectors = np.linalg.eigh(independent_hamiltonian(s, 0.))
        states = vectors @ (np.exp(-1j * eigenvalues[:, None] * times) * vectors[0, :, None].conj())
        kind = "analytic_rabi_and_independent_projected_eigendecomposition" if s["fixture"] == "rabi" else "independent_projected_eigendecomposition"
    else:
        from scipy.integrate import solve_ivp
        solution = solve_ivp(lambda t, psi: -1j * (independent_hamiltonian(s, t) @ psi),
            (0., s["duration"]), initial, method=method, rtol=rtol, atol=atol, t_eval=times)
        if not solution.success or solution.y.shape != (len(basis), len(times)):
            raise RuntimeError("Independent reference integration failed: " + solution.message)
        states, kind = solution.y, f"independent_scipy_{method}"
    probabilities = np.abs(states)**2
    pop0 = np.sum(probabilities[np.array(basis) & 1 != 0], axis=0)
    norm = probabilities.sum(axis=0)
    return {"type": kind, "basis": basis, "t": times.tolist(), "pop0": pop0.tolist(),
            "z0": (norm - 2 * pop0).tolist(), "raw_norm": norm.tolist(),
            "final_probabilities": (probabilities[:, -1] / norm[-1]).tolist(), "rtol": rtol, "atol": atol,
            "limitations": "Verifies reduced model implementation/numerics; no physical blockade equivalence or calibration."}


def stable_reference(s, stability_atol):
    reference = independent_reference(s)
    if s["fixture"] == "rabi":
        control = np.sin(np.asarray(reference["t"]) * s["omega"][0] / 2)**2
        error = float(np.max(np.abs(control - reference["pop0"])))
        check = "analytic sin(omega*t/2)^2 versus eigendecomposition"
    elif s["pulse_kind"] == "constant":
        from scipy.linalg import expm
        h = independent_hamiltonian(s, 0.)
        states = np.array([expm(-1j * h * t)[:, 0] for t in reference["t"]]).T
        control = np.sum(np.abs(states[np.array(reference["basis"]) & 1 != 0])**2, axis=0)
        error = float(np.max(np.abs(control - reference["pop0"])))
        check = "independent scipy matrix exponential versus eigendecomposition"
    else:
        second = independent_reference(s, method="RK45", rtol=1e-12, atol=1e-14)
        error = max(float(np.max(np.abs(np.array(reference[k]) - second[k]))) for k in ("pop0", "z0", "raw_norm", "final_probabilities"))
        check = "independent RK45 1e-12/1e-14 versus DOP853 1e-12/1e-14"
        reference["second_method"] = second
    reference.update(stability_error=error, stability_atol=stability_atol,
                     stability_check=check, stable=error <= stability_atol)
    if not reference["stable"]:
        raise AssertionError(f"Reference stability {error} exceeds {stability_atol}")
    return reference


def sdk_inputs(s):
    from . import Atom, Register, PulseSequence, Ramp
    register = Register([Atom(*coords) for coords in s["coordinates"]], C6=s["C6"])
    if s["pulse_kind"] == "constant":
        sequence = PulseSequence(omega=s["omega"], delta=s["delta"])
    else:
        sequence = PulseSequence(**{name: [Ramp(start, end, duration=s["duration"])
            for start, end in zip(s[name + "_start"], s[name + "_end"])] for name in ("omega", "delta")})
    return register, sequence


def result_gate(result, s, settings, reference):
    """Audit actual output and manifest; safe to run without initializing Julia."""
    from .api import _pulse_manifest, validate_run_manifest
    validate_run_manifest(result.manifest)
    manifest, solver = result.manifest, result.manifest["solver"]
    _, sequence = sdk_inputs(s)
    expected_pulse = {name: _pulse_manifest(getattr(sequence, name)) for name in ("omega", "delta")}
    if manifest["register"]["atoms"] != s["coordinates"] or manifest["register"]["C6"] != s["C6"] or manifest["pulse"] != expected_pulse:
        raise AssertionError("Executed register/pulse differs from freeze")
    expected = {**s["solver"], "effective_method": s["solver"]["method"], "effective_adaptive": s["solver"]["adaptive"],
                "effective_dt": s["solver"]["dt"], "effective_saveat": s["solver"]["saveat"], "use_gpu": False, "observables": OBSERVABLES}
    if any(solver.get(k) != v for k, v in expected.items()) or manifest["backend_diagnostics"]["requested_backend"] != "CPU":
        raise AssertionError("Executed solver/grid/backend/observables differs from freeze")
    initial = manifest["initial_state"]
    if initial["basis_size"] != s["basis_size"] or abs(initial["norm"] - 1) > 1e-14:
        raise AssertionError("Initial basis/norm mismatch")
    t = np.asarray(result.data["t"])
    if t.shape != (s["output_count"],) or not np.allclose(t, reference["t"], rtol=0, atol=1e-14):
        raise AssertionError("Actual output grid differs from reference")
    values = [np.asarray(result.data[k]) for k in ("pop0", "z0")]
    if any(v.shape != t.shape or not np.isfinite(v).all() for v in values):
        raise AssertionError("Invalid observable shape/values")
    errors = [float(np.max(np.abs(v - reference[k]))) for k, v in zip(("pop0", "z0"), values)]
    norm_error = float(np.max(np.abs(values[1] + 2 * values[0] - 1)))
    labels = [format(b, f"0{s['N']}b")[::-1] for b in reference["basis"]]
    if manifest["readout"]["basis_bitstrings"] != labels:
        raise AssertionError("Readout basis/bit order mismatch")
    distribution = result.final_bitstring_distribution()
    final = np.array([distribution[label] for label in labels])
    if not np.isfinite(final).all():
        raise AssertionError("Nonfinite final probabilities")
    final_error = float(np.max(np.abs(final - reference["final_probabilities"])))
    maximum = max(*errors, final_error)
    # Effective metadata must also describe actual backend execution.
    effective = result.diagnostics["simulation"]
    for k in ("effective_method", "effective_adaptive", "effective_dt", "effective_saveat", "reltol", "abstol", "use_gpu"):
        if effective.get(k) != expected[k]:
            raise AssertionError("Backend diagnostics differ from manifest/freeze")
    return {"max_abs_error": maximum, "observable_max_abs_error": max(errors), "final_probability_error": final_error,
            "raw_norm_error": norm_error, "accuracy_atol": settings["accuracy_atol"],
            "passed": bool(reference["stable"] and maximum <= settings["accuracy_atol"] and norm_error <= settings["accuracy_atol"])}


def phases(settings):
    return [("first", 0)] + [("warmup", i) for i in range(settings["warmups"])] + [("measured", i) for i in range(settings["repeat_count"])]


def _child(config_path, checkpoint_path):
    from . import Simulation, SolverConfig, doctor
    from .runtime import get_julia
    from .scaling_benchmark import _runtime_context
    from .ablation_benchmark import _blas_threads
    config = json.loads(Path(config_path).read_text())
    s, settings = config["scenario"], config["settings"]
    directory = Path(checkpoint_path).parent
    state = {"records": [], "timing": {}, "stage": "setup"}
    def checkpoint(stage):
        state.update(stage=stage, memory=linux_process_memory(os.getpid()), memory_source=current_memory_usage())
        write_json(checkpoint_path, state)
    checkpoint("setup")
    try:
        for name, digest in config["source_sha256"].items():
            if hashlib.sha256((Path(config["source_root"]) / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError("Frozen source changed during campaign")
        started = time.perf_counter()
        state["doctor"] = doctor(backend="CPU", initialize_backend=True)
        state["timing"]["initialized_doctor_seconds"] = time.perf_counter() - started
        if not state["doctor"].get("available") or not (state["doctor"].get("backend_probe") or {}).get("available"):
            raise RuntimeError("Initialized CPU doctor failed")
        state["runtime_context"] = _runtime_context()
        state["runtime_context"]["python_blas"] = _blas_threads()
        if any(state["runtime_context"]["threads"][k] != 1 for k in ("julia", "blas")):
            raise RuntimeError("Effective Julia/BLAS thread counts differ from freeze")
        jl, _ = get_julia()
        project = Path(str(jl.seval("Base.active_project()")))
        state["runtime_files"] = {}
        for path in (project, project.with_name("Manifest.toml")):
            if path.is_file():
                shutil.copyfile(path, directory / path.name)
                state["runtime_files"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        state["memory_baseline"] = linux_process_memory(os.getpid())
        checkpoint("setup")
        started = time.perf_counter()
        register, sequence = sdk_inputs(s)
        simulation = Simulation(register, sequence, SolverConfig(**s["solver"]))
        dimension = simulation.validate()
        actual_basis = list(range(2**s["N"])) if simulation._basis is None else list(map(int, simulation._basis))
        if dimension != s["basis_size"] or actual_basis != independent_basis(s):
            raise AssertionError("SDK basis differs from independent enumeration")
        initial = np.zeros(dimension, dtype=complex)
        initial[0] = 1
        state["timing"]["setup_basis_seconds"] = time.perf_counter() - started
        checkpoint("reference")
        started = time.perf_counter()
        reference = stable_reference(s, settings["reference_stability_atol"])
        state["timing"]["reference_seconds"] = time.perf_counter() - started
        state["reference"] = reference
        write_json(directory / "reference.json", reference)
        # Reference stability is established before any workload measurement.
        for phase, index in phases(settings):
            record = {"row_id": f"{s['scenario_id']}-{phase}-{index}", "phase": phase,
                      "repeat_index": index, "operation_count": 1, "eligible": False, "artifacts": {}}
            state["records"].append(record)
            reset = initial.copy()
            checkpoint("solve")
            started = time.perf_counter()
            result = simulation.run(reset, 0., s["duration"], observables=OBSERVABLES)
            record["runtime_seconds"] = time.perf_counter() - started
            checkpoint("artifact")
            started = time.perf_counter()
            label = f"{phase}-{index}"
            result_path, manifest_path = directory / f"{label}.result.json", directory / f"{label}.manifest.json"
            result.save(str(result_path))
            write_json(manifest_path, result.manifest)
            record["artifacts"] = {"result_artifact": str(result_path), "run_manifest": str(manifest_path), "reference_report": str(directory / "reference.json")}
            record["serialization_seconds"] = time.perf_counter() - started
            checkpoint("validation")
            started = time.perf_counter()
            record["gate"] = result_gate(result, s, settings, reference)
            record["effective_solver"] = result.diagnostics["simulation"]
            record["effective_times"] = np.asarray(result.data["t"]).tolist()
            record["output_sample_count"] = len(record["effective_times"])
            record["eligible"] = record["gate"]["passed"]
            record["validation_seconds"] = time.perf_counter() - started
            checkpoint("validation")
        state["complete"] = True
        checkpoint("artifact")
    except Exception as exc:
        state["failure"] = benchmark_failure_context(exc, stage=state["stage"], timeout_seconds=settings["timeout_seconds"], backend_probe=state.get("doctor", {}).get("backend_probe"))
        checkpoint(state["stage"])


def measured_records(state):
    return [r for r in state.get("records", []) if r["phase"] == "measured" and "runtime_seconds" in r]


def make_row(s, settings, state, supervision, *, exclusion=None):
    summary = runtime_summary(measured_records(state), settings["repeat_count"])
    failure = state.get("failure")
    if exclusion:
        status = "skipped"
        failure = {"stage": "setup", "code": "BENCHMARK_RESOURCE_EXCLUDED", "message": exclusion,
                   "remediation": "Retain exclusion and select adequate resources before a new campaign."}
    elif supervision.get("reason") == "interrupted":
        status = "incomplete"
        failure = {"stage": state.get("stage", "setup"), "code": "BENCHMARK_INTERRUPTED",
                   "message": "Campaign interrupted; partial measurements retained.",
                   "remediation": "Inspect retained evidence; rerun in a new output directory."}
    elif supervision.get("reason") == "timeout":
        status = "incomplete"
        failure = benchmark_failure_context(TimeoutError("Worker timed out"), stage=state.get("stage", "setup"), timeout_seconds=settings["timeout_seconds"])
    elif supervision.get("reason") == "memory":
        status = "failed"
        failure = benchmark_failure_context(MemoryError("Worker exceeded sampled RSS budget"), stage=state.get("stage", "setup"))
    elif supervision.get("reason") or supervision.get("returncode", 0) != 0:
        status = "failed"
        failure = benchmark_failure_context(RuntimeError("Worker terminated: " + str(supervision)), stage=state.get("stage", "setup"))
    elif failure:
        status = "failed"
    elif any(not r.get("eligible") for r in state.get("records", [])):
        status = "failed"
    elif not state.get("complete") or [(r["phase"], r["repeat_index"]) for r in state.get("records", [])] != phases(settings) or summary["completed"] != settings["repeat_count"] or settings["warmups"] < 2 or settings["repeat_count"] < 5:
        status = "incomplete"
    else:
        status = "passed"
    if status != "passed" and not failure:
        failure = {"stage": "validation", "code": "BENCHMARK_ACCURACY_FAILED" if status == "failed" else "BENCHMARK_INSUFFICIENT_EVIDENCE",
                   "message": "Acceptance needs all accuracy gates, two warmups and five eligible repeats.",
                   "remediation": "Inspect raw diagnostic times/errors; retain under-resolved or short runs."}
    if failure:
        failure = {**failure, "limits": {k: settings[k] for k in ("timeout_seconds", "memory_limit_bytes")}, "backend_probe": state.get("doctor", {}).get("backend_probe")}
    records = state.get("records", [])
    gates = [r["gate"] for r in records if "gate" in r]
    metrics = {"statistics": summary, "state": state, "supervision": supervision, "timer_scope": TIMER_SCOPE,
               "memory_scope": "one configuration process lifetime including initialization/references/writes; sampled RSS budget, kernel HWM retained"}
    row = make_benchmark_row(row_id=s["scenario_id"], scenario_id=s["scenario_id"], family=FAMILY, tier=TIER,
        status=status, stage=failure["stage"] if failure else "artifact", problem=s, solver=s["solver"],
        backend={"requested_backend": "CPU", "path": "cpu", "precision": "complex128"},
        observables={"names": list(OBSERVABLES), "declarations": OBSERVABLES, "count": len(OBSERVABLES), "output_sample_count": s["output_count"]},
        metrics=metrics, artifacts={}, failure=failure, disclosure_status="local_only")
    row.update(N=s["N"], basis_size=s["basis_size"], **{k: s["solver"][k] for k in ("method", "adaptive", "dt", "reltol", "abstol")},
        output_count=s["output_count"], eligible=summary["eligible"], accuracy_atol=settings["accuracy_atol"],
        max_abs_error=max((g["max_abs_error"] for g in gates), default=None), raw_norm_error=max((g["raw_norm_error"] for g in gates), default=None),
        reference_type=state.get("reference", {}).get("type"), peak_bytes=state.get("memory", {}).get("peak_bytes"), raw_records="solver_repeats.json")
    row.update({k + "_s": v for k, v in summary["runtime_seconds"].items()})
    return row


def coverage(rows):
    passed = {r["scenario_id"] for r in rows if r["status"] == "passed"}
    expected = {s["scenario_id"] for s in scenarios()}
    return {"selected_campaign_passed": all(r["status"] == "passed" for r in rows),
            "full_v2_matrix_passed": expected <= passed,
            "missing_successful_v2_scenarios": sorted(expected - passed),
            "declared": len(rows), "passed": len(passed),
            "classification": "local_only; software/numerical verification, not scientific validation or release/public approval"}


def benchmark_solver_sensitivity(output_dir, *, scenario_ids=None, warmups=2, repeat_count=5,
                                 timeout_seconds=600., memory_limit_mb=4096., accuracy_atol=1e-6,
                                 reference_stability_atol=1e-9):
    from .runtime import version_info
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (warmups, repeat_count)) or warmups < 0 or repeat_count < 1:
        raise ValueError("Warmups must be nonnegative and repeats positive integers")
    if not all(math.isfinite(v) and v > 0 for v in (timeout_seconds, memory_limit_mb, accuracy_atol, reference_stability_atol)):
        raise ValueError("Resource limits and accuracy tolerances must be finite positive values")
    selected = scenarios()
    if scenario_ids is not None:
        if not scenario_ids or len(set(scenario_ids)) != len(scenario_ids) or set(scenario_ids) - {s["scenario_id"] for s in selected}:
            raise ValueError("Select nonempty unique known scenario IDs")
        selected = [s for s in selected if s["scenario_id"] in scenario_ids]
    settings = {"warmups": warmups, "repeat_count": repeat_count, "timeout_seconds": timeout_seconds,
                "memory_limit_bytes": int(memory_limit_mb * 1024**2), "accuracy_atol": accuracy_atol,
                "reference_stability_atol": reference_stability_atol, "observables": OBSERVABLES}
    output = Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a new empty output directory to preserve evidence")
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    names = [f"sagittarius_py/sagittarius/{n}.py" for n in ("solver_benchmark", "benchmark_measurement", "benchmarking", "benchmark_suite", "benchmark_failures", "api", "pulse", "runtime", "scaling_benchmark", "ablation_benchmark")]
    names += ["sagittarius_py/tests/test_performance/benchmark_solver_performance.py", "sagittarius_py/uv.lock", "sagittarius_py/pyproject.toml", "Sagittarius.jl/Project.toml"]
    names += [str(p.relative_to(root)) for p in (root / "Sagittarius.jl/src").glob("*.jl")]
    names += [n for n in ("scripts/audit_solver_campaign.py", "sagittarius_py/tests/test_solver_sensitivity_benchmark.py") if (root / n).exists()]
    hashes = {}
    for name in names:
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
        hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    frozen = {"scenarios": selected, "settings": settings, "source_sha256": hashes}
    env = {**os.environ, **{k: "1" for k in THREAD_KEYS}}
    campaign = {**frozen, "config_sha256": hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest(),
                "workload_version": WORKLOAD_VERSION, "plan_version": "benchmark-implementation-plan/v2", "protocol_version": "benchmark-protocol/v1",
                "output_dir": str(output), "source_root": str(root), "source": version_info(initialize_backend=False),
                "created_at": datetime.now(timezone.utc).isoformat(), "command": sys.argv, "cwd": str(Path.cwd()), "python_executable": sys.executable,
                "thread_environment": {k: env[k] for k in THREAD_KEYS}, "timer_scope": TIMER_SCOPE,
                "cache_policy": "fresh process per configuration; initialized doctor and validate before first; reuse simulation/JIT, reset all-ground input each call",
                "stop_policy": "continue after failures; interruption prevents further workers, retaining all declared rows",
                "seed": None, "seed_reason": "deterministic evolution, no stochastic workload",
                "classification": "local_only; shared workstation; no affinity or exclusive-load controls"}
    try:
        campaign["host"] = {"cpu_model": next(line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")),
                            "physical_memory_bytes": os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"), "logical_cpus": os.cpu_count()}
    except (OSError, ValueError, StopIteration):
        campaign["host"] = {"unavailable_reason": "Host CPU/memory metadata unavailable"}
    write_json(output / "campaign.json", campaign)
    rows, interrupted = [], False
    for s in selected:
        directory = output / s["scenario_id"]
        directory.mkdir()
        config_path, checkpoint_path = directory / "config.json", directory / "checkpoint.json"
        write_json(config_path, {"scenario": s, "settings": settings, "source_root": str(root), "source_sha256": hashes})
        state, supervision = {}, {}
        exclusion = "Construction/reference estimate exceeds budget" if s["estimated_peak_bytes"] > settings["memory_limit_bytes"] else None
        if interrupted:
            supervision = {"reason": "interrupted"}
        elif not exclusion:
            command = [sys.executable, "-m", "sagittarius.solver_benchmark", "--child", str(config_path), str(checkpoint_path)]
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
                state = json.loads(checkpoint_path.read_text())
        row = make_row(s, settings, state, supervision, exclusion=exclusion)
        row["artifacts"] = {"config": str(config_path), "checkpoint": str(checkpoint_path) if checkpoint_path.exists() else None}
        rows.append(row)
        write_json(output / "progress.json", rows)
        print(f"{s['scenario_id']}: {row['status']} ({row['eligible']} eligible)", flush=True)
    raw = [{"scenario_id": row["scenario_id"], **r} for row in rows for r in row["metrics"]["state"].get("records", [])]
    write_json(output / "solver_repeats.json", raw)
    paths = write_benchmark_artifacts(output_dir=output, stem="solver_sensitivity", name="P1 CPU solver sensitivity",
        description="Plan v2 error-versus-runtime matrix; independent references and repeat statistics; local evidence only.",
        parameters=campaign, rows=rows, backend="CPU", diagnostics={"doctor": "see per-configuration checkpoints"},
        run_manifests=[{"label": r["row_id"], "path": r["artifacts"].get("run_manifest")} for r in raw if r["artifacts"].get("run_manifest")],
        columns=COLUMNS, benchmark_context={"family": FAMILY, "tier": TIER, "disclosure_status": "local_only", "config_sha256": campaign["config_sha256"]})
    paths["suite"] = write_benchmark_suite_artifact(output_dir=output, stem="solver_sensitivity_suite", suite_id="phase16-p1-solver-v2",
        family=FAMILY, tier=TIER, rows=rows, source=campaign["source"], environment={"thread_environment": campaign["thread_environment"]},
        scenario_defaults={"campaign": str(output / "campaign.json"), "settings": settings})
    write_json(output / "coverage.json", coverage(rows))
    return paths


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--child":
        _child(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit("Use tests/test_performance/benchmark_solver_performance.py --tier sensitivity")
