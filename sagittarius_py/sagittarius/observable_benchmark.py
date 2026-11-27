"""Bounded plan-v2 diagonal-observable correctness and SDK collection costs."""
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
from .benchmarking import current_memory_usage, make_benchmark_row, write_benchmark_artifacts
from .benchmark_suite import write_benchmark_suite_artifact

WORKLOAD_VERSION = "observable-performance/v1"
FAMILY, TIER = "backend_performance", "correctness"
SIZES = (4, 8, 12, 16, 20)
SEEDS = (20260811, 20260812, 20260813, 20260814, 20260815)
ORDERS = ("original", "reverse", "permuted")
THREAD_KEYS = ("JULIA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
STORAGE = "observable series at explicit times plus final normalized readout where supported; no exposed state history; no raw trajectories for cost runs"
TIMER = "Simulation.run including validation, operator/observable construction, collection and manifest; excludes reset, reference, checks, round trips and writes"
COLUMNS = ["scenario_id", "status", "kind", "N", "basis_size", "collection", "count", "order", "output_count", "duplicate_outputs", "eligible", "median_s", "min_s", "max_s", "p25_s", "p75_s", "max_abs_error", "value_gate", "order_gate", "peak_bytes", "storage_policy", "raw_records"]


def catalog(n):
    pair = [0, n - 1]
    edges = [[0, 1], pair]
    return [
        {"type": "rydberg_population", "atom": 0},
        {"type": "total_rydberg_population"},
        {"type": "pair_correlation", "atoms": pair},
        {"type": "connected_pair_correlation", "atoms": pair},
        {"type": "blockade_violation", "edges": edges},
        {"type": "bitstring_probability", "bitstring": 1 | (1 << (n - 1))},
        {"type": "mwis_cost", "weights": [1. + .125 * i for i in range(n)], "edges": edges, "penalty": 4.25},
        {"type": "pauli_z", "atom": n - 1, "convention": "ground_plus"},
        {"type": "pauli_zz", "atoms": pair, "convention": "ground_plus"},
        {"type": "parity", "atoms": sorted({0, n // 2, n - 1}), "convention": "ground_plus"},
    ]


def declarations(n, count, order, single_type=None):
    choices = catalog(n)
    if single_type:
        choices = [d for d in choices if d["type"] == single_type]
        if not choices:
            raise ValueError("Unsupported observable type")
    values = [{"name": f"obs_{i:02d}_{choices[i % len(choices)]['type']}", "declaration": choices[i % len(choices)]} for i in range(count)]
    if order == "reverse":
        values.reverse()
    elif order == "permuted":
        values = [values[int(i)] for i in np.random.default_rng(1234).permutation(count)]
    elif order != "original":
        raise ValueError("Unknown order")
    return values


def basis(s):
    n = s["N"]
    neighbors = [sum(1 << j for j in range(i) if math.dist(s["coordinates"][i], s["coordinates"][j]) < s["blockade_radius"]) for i in range(n)]
    values = [0]
    for i in range(n):
        values += [b | (1 << i) for b in values if not b & neighbors[i]]
    return values


def _scenario(n, *, kind="performance", fixture="evolving", count=4, grid=101, order="original", single_type=None, reduced=True):
    s = {"N": n, "kind": kind, "fixture": fixture, "coordinates": [[4. * i, 0., 0.] for i in range(n)],
         "C6": 100. if fixture == "evolving" else 0., "blockade_radius": 4.4 if reduced else 0.,
         "omega": 2 * math.pi if fixture == "evolving" else 0., "delta": .3 if fixture == "evolving" else 0.,
         "duration": .15 if fixture == "evolving" else .5, "basis_mode": "reduced" if reduced else "full",
         "count": count, "output_count": grid, "order": order, "collection": single_type or "mixed",
         "units": {"length": "um", "time": "us", "angular_frequency": "rad/us", "C6": "rad*um^6/us"},
         "atom_order": "Python atom i is bit i (LSB); Julia atom i+1; ascending basis integers", "required": True,
         "precision": "complex128", "full_dim": 2**n, "initial_state": "all_ground" if fixture in ("ground", "evolving") else fixture,
         "storage_policy": STORAGE if kind == "performance" else "observable correctness; MCWF raw samples retained"}
    s["declarations"] = declarations(n, count, order, single_type)
    distinct = len({json.dumps(d["declaration"], sort_keys=True) for d in s["declarations"]})
    s["duplicate_outputs"] = count - distinct
    s["collection_label"] = "duplicate-output collection workload; no additional physical information" if count > distinct else "distinct declarations"
    s["basis_size"] = len(basis(s))
    s["solver"] = {"method": "Tsit5", "adaptive": True, "dt": None, "reltol": 1e-11, "abstol": 1e-13,
        "blockade_radius": s["blockade_radius"], "saveat": np.linspace(0., s["duration"], grid).tolist(),
        "gamma": .4 if fixture in ("lindblad", "mcwf") else 0., "gamma_phi": 0., "use_mc": fixture == "mcwf",
        "n_trajectories": 500, "store_trajectories": fixture == "mcwf"}
    label = f"{kind}-n{n}-{s['basis_mode']}-{fixture}-{s['collection']}-c{count}-g{grid}-{order}"
    s["scenario_id"] = label
    s["estimated_peak_bytes"] = 2 * 1024**3 + s["basis_size"] * (256 * n + 128 * 16 + grid * 16 * 6) + count * grid * 500 * 16
    return s


def scenarios(tier="all"):
    if tier not in ("all", "performance", "correctness"):
        raise ValueError("Tier must be all, performance or correctness")
    rows = []
    if tier in ("all", "correctness"):
        for reduced in (False, True):
            for fixture in ("ground", "excited", "distribution", "evolving", "lindblad", "mcwf"):
                rows.append(_scenario(3, kind="correctness", fixture=fixture, count=10, grid=21, reduced=reduced))
    if tier in ("all", "performance"):
        for n in SIZES:
            for count, grid, order in [(4, 101, "original"), (1, 101, "original"), (16, 101, "original"), (64, 101, "original"),
                (4, 21, "original"), (4, 501, "original"), (4, 101, "reverse"), (4, 101, "permuted")]:
                rows.append(_scenario(n, count=count, grid=grid, order=order))
        for d in catalog(4):
            rows.append(_scenario(4, count=1, single_type=d["type"]))
        rows += [_scenario(4, count=64, grid=501, order="permuted"), _scenario(20, count=16, grid=501, order="reverse")]
    return rows


def initial_state(s):
    b = basis(s)
    psi = np.zeros(len(b), dtype=complex)
    if s["fixture"] == "distribution":
        p = np.arange(1., len(b) + 1)
        psi = np.sqrt(p / p.sum()) * np.exp(.3j * np.arange(len(b)))
    else:
        target = 0 if s["fixture"] in ("ground", "evolving") else 1 | (1 << (s["N"] - 1))
        psi[b.index(target)] = 1
    return psi


def occupation_values(probabilities, bits, declaration):
    """Independent NumPy semantics, including nonlinear connected subtraction."""
    p = np.asarray(probabilities)
    if p.ndim == 1:
        p = p[:, None]
    bits = np.asarray(bits, dtype=np.int64)
    n = lambda i: ((bits >> i) & 1).astype(float)
    average = lambda v: np.asarray(v) @ p
    d, t = declaration, declaration["type"]
    if t == "rydberg_population": return average(n(d["atom"]))
    if t == "total_rydberg_population": return average(sum(n(i) for i in d.get("atoms", range(max(1, int(bits.max()).bit_length())))))
    if t in ("pair_correlation", "connected_pair_correlation"):
        i, j = d["atoms"]
        pair = average(n(i) * n(j))
        return pair if t == "pair_correlation" else pair - average(n(i)) * average(n(j))
    if t == "blockade_violation": return average(sum(n(i) * n(j) for i, j in d["edges"]))
    if t == "bitstring_probability": return average(bits == d["bitstring"])
    if t == "mwis_cost": return average(sum(w * n(i) for i, w in enumerate(d["weights"])) - d["penalty"] * sum(n(i) * n(j) for i, j in d["edges"]))
    if t == "pauli_z": return average(1 - 2 * n(d["atom"]))
    if t in ("pauli_zz", "parity"): return average(np.prod([1 - 2 * n(i) for i in d["atoms"]], axis=0))
    raise ValueError("Unsupported reference type")


def hamiltonian(s):
    from scipy.sparse import coo_matrix
    b = basis(s)
    index = {v: i for i, v in enumerate(b)}
    bits = np.array(b)
    occupation = [((bits >> i) & 1).astype(float) for i in range(s["N"])]
    diagonal = -s["delta"] * sum(occupation)
    for i in range(s["N"]):
        for j in range(i + 1, s["N"]):
            diagonal += s["C6"] / math.dist(s["coordinates"][i], s["coordinates"][j])**6 * occupation[i] * occupation[j]
    rows, cols, values = list(range(len(b))), list(range(len(b))), diagonal.tolist()
    for col, bitstring in enumerate(b):
        for i in range(s["N"]):
            row = index.get(bitstring ^ (1 << i))
            if row is not None:
                rows.append(row); cols.append(col); values.append(s["omega"] / 2)
    return coo_matrix((values, (rows, cols)), shape=(len(b), len(b)), dtype=complex).tocsr()


def reference(s, stability_atol=1e-10):
    """Independent static probabilities, projected exponential or analytic decay."""
    b, times = basis(s), np.array(s["solver"]["saveat"])
    initial = initial_state(s)
    stability = 0.
    if s["fixture"] == "evolving":
        from scipy.sparse.linalg import expm_multiply
        h = hamiltonian(s)
        states = expm_multiply(-1j * h, initial, start=0., stop=s["duration"], num=len(times), traceA=-1j * h.diagonal().sum()).T
        probabilities = np.abs(states)**2
        if s["N"] <= 8:
            eigenvalues, vectors = np.linalg.eigh(h.toarray())
            control = vectors @ (np.exp(-1j * eigenvalues[:, None] * times) * (vectors.conj().T @ initial)[:, None])
            control_type = "independent dense eigendecomposition"
        else:
            from scipy.integrate import solve_ivp
            sol = solve_ivp(lambda t, y: -1j * (h @ y), (0., s["duration"]), initial,
                            method="DOP853", rtol=1e-12, atol=1e-14, t_eval=times)
            if not sol.success: raise RuntimeError("Independent DOP853 control failed")
            control, control_type = sol.y, "independent sparse DOP853 1e-12/1e-14"
        stability = float(np.max(np.abs(states - control)))
        kind = "independent projected sparse exponential"
    elif s["fixture"] in ("lindblad", "mcwf"):
        survival = np.exp(-.4 * times)
        support = [0, 1, 1 << (s["N"] - 1), 1 | (1 << (s["N"] - 1))]
        probabilities = np.zeros((len(b), len(times)))
        for bitstring in support:
            count = bitstring.bit_count()
            probabilities[b.index(bitstring)] = survival**count * (1 - survival)**(2 - count)
        kind, control_type = "analytic independent local decay from two excitations", "exact product Bernoulli probabilities"
    else:
        probabilities = np.repeat(np.abs(initial[:, None])**2, len(times), axis=1)
        kind, control_type = "independent static occupation probabilities", "declared bitstring or normalized nontrivial distribution"
    ds = s["declarations"]
    values = np.array([occupation_values(probabilities, b, d["declaration"]) for d in ds])
    widths = np.zeros(len(ds))
    if s["fixture"] == "mcwf":
        # Each trajectory stays a bitstring. Connected covariance is exactly
        # zero per trajectory, before averaging; do not subtract ensemble means.
        support = [0, 1, 1 << (s["N"] - 1), 1 | (1 << (s["N"] - 1))]
        for i, d in enumerate(ds):
            vals = occupation_values(np.eye(len(support)), support, d["declaration"])
            widths[i] = float(np.ptp(vals))
            if d["declaration"]["type"] == "connected_pair_correlation":
                values[i] = 0.
    norm = probabilities.sum(axis=0)
    if stability > stability_atol or np.max(np.abs(norm - 1)) > stability_atol:
        raise AssertionError("Independent reference stability/norm gate failed")
    arrays = {"basis": np.array(b), "t": times, "values": values, "norm": norm,
              "final_probabilities": probabilities[:, -1], "range_widths": widths}
    return arrays, {"type": kind, "control": control_type, "stability_error": stability, "stability_atol": stability_atol,
                    "stable": True, "limitations": "Projected-model verification; no physical blockade equivalence or calibration"}


def ordered_declarations(s, order=None):
    items = s["declarations"]
    if order is not None:
        items = declarations(s["N"], s["count"], order, None if s["collection"] == "mixed" else s["collection"])
    return {item["name"]: item["declaration"] for item in items}


def expected_metadata(s, ds):
    result = []
    for i, (name, d) in enumerate(ds.items()):
        params = {k: v for k, v in d.items() if k != "type"}
        if d["type"] in ("pauli_z", "pauli_zz", "parity"):
            params.setdefault("convention", "ground_plus")
        result.append({"name": name, "type": d["type"], "parameters": params, "basis_mode": s["basis_mode"], "declaration_index": i})
    return result


def result_gate(result, s, cfg, ref, *, order=None, seed=None):
    from .api import validate_run_manifest
    validate_run_manifest(result.manifest)
    ds = ordered_declarations(s, order)
    names, solver = list(ds), result.manifest["solver"]
    if list(result.data) != names + ["t"]:
        raise AssertionError("Result declaration order mismatch")
    shared = result.to_shared_result()
    if shared["observable_names"] != names or list(shared["series"])[:len(names)] != names:
        raise AssertionError("Shared-result declaration order mismatch")
    if list(solver["observables"]) != names or solver["observables"] != ds or solver["observable_metadata"] != expected_metadata(s, ds):
        raise AssertionError("Manifest declaration/type/parameter/order mismatch")
    expected = {**s["solver"], "effective_method": "Tsit5", "effective_adaptive": True, "effective_dt": None,
                "effective_saveat": s["solver"]["saveat"], "use_gpu": False, "t_span": [0., s["duration"]]}
    if any(solver.get(k) != v for k, v in expected.items()): raise AssertionError("Executed solver differs from frozen configuration")
    effective = result.diagnostics["simulation"]
    for k in ("effective_method", "effective_adaptive", "effective_dt", "effective_saveat", "reltol", "abstol"):
        if effective.get(k) != expected[k]: raise AssertionError("Backend effective solver mismatch")
    manifest = result.manifest
    if manifest["backend_diagnostics"]["requested_backend"] != "CPU" or abs(manifest["initial_state"]["norm"] - 1.) > 1e-12:
        raise AssertionError("Executed initial norm/backend mismatch")
    if manifest["register"]["atoms"] != s["coordinates"] or manifest["register"]["C6"] != s["C6"] or manifest["initial_state"]["basis_size"] != s["basis_size"]:
        raise AssertionError("Executed register/basis mismatch")
    from .api import _pulse_manifest
    if manifest["pulse"] != {"omega": _pulse_manifest(s["omega"]), "delta": _pulse_manifest(s["delta"])}:
        raise AssertionError("Executed pulse mismatch")
    t = np.asarray(result.data["t"])
    if t.shape != ref["t"].shape or not np.allclose(t, ref["t"], rtol=0, atol=1e-14): raise AssertionError("Output grid mismatch")
    canonical = [item["name"] for item in s["declarations"]]
    values = np.array([result.data[name] for name in canonical], dtype=float)
    if values.shape != ref["values"].shape or not np.isfinite(values).all(): raise AssertionError("Invalid observable output")
    error = np.max(np.abs(values - ref["values"]), axis=1)
    bounds = np.full(len(canonical), cfg["accuracy_atol"])
    sample_error = None
    if s["fixture"] == "mcwf":
        if manifest["random"]["effective_seed"] != seed: raise AssertionError("Effective MCWF seed mismatch")
        samples = result.trajectories
        if samples is None or list(samples) != names: raise AssertionError("Raw MCWF trajectory order missing")
        sample_error = 0.
        for i, name in enumerate(canonical):
            a = np.asarray(samples[name])
            if a.shape != (s["solver"]["n_trajectories"], len(t)) or not np.isfinite(a).all(): raise AssertionError("Invalid raw MCWF trajectory shape")
            sample_error = max(sample_error, float(np.max(np.abs(a.mean(axis=0) - values[i]))))
        comparisons = len(canonical) * len(t) * len(SEEDS) * len(ORDERS) * 2
        bounds += ref["range_widths"] * np.sqrt(np.log(2 * comparisons / cfg["stochastic_alpha"]) / (2 * s["solver"]["n_trajectories"]))
    return {"max_abs_error": float(error.max()), "per_observable_error": error.tolist(), "per_observable_bound": bounds.tolist(),
            "value_passed": bool(np.all(error <= bounds) and (sample_error is None or sample_error <= 1e-12)),
            "order_passed": True, "sample_mean_error": sample_error,
            "uncertainty": "Simultaneous Hoeffding absolute bounds over types/times/orders/seeds/bases; trajectory-wise connected covariance" if s["fixture"] == "mcwf" else "deterministic absolute gate",
            "passed": bool(np.all(error <= bounds) and (sample_error is None or sample_error <= 1e-12))}


def ordered_write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def record_plan(s, cfg):
    if s["kind"] == "performance":
        return [("first", 0, s["order"], None)] + [("warmup", i, s["order"], None) for i in range(cfg["warmups"])] + [("measured", i, s["order"], None) for i in range(cfg["repeat_count"])]
    seeds = SEEDS if s["fixture"] == "mcwf" else (None,)
    return [("correctness", i, order, seed) for i, (order, seed) in enumerate((o, seed) for o in ORDERS for seed in seeds)]


def _child(config_path, checkpoint_path):
    from . import Atom, Register, PulseSequence, Simulation, SimulationResult, SolverConfig, doctor
    from .runtime import get_julia
    from .scaling_benchmark import _runtime_context
    from .ablation_benchmark import _blas_threads
    config = json.loads(Path(config_path).read_text())
    s, cfg = config["scenario"], config["settings"]
    directory = Path(checkpoint_path).parent
    state = {"records": [], "timing": {}, "stage": "setup"}
    def checkpoint(stage):
        state.update(stage=stage, memory=linux_process_memory(os.getpid()), memory_source=current_memory_usage())
        write_json(checkpoint_path, state)
    checkpoint("setup")
    try:
        for name, digest in config["source_sha256"].items():
            if hashlib.sha256((Path(config["source_root"]) / name).read_bytes()).hexdigest() != digest: raise RuntimeError("Frozen source changed")
        started = time.perf_counter()
        state["doctor"] = doctor(backend="CPU", initialize_backend=True)
        state["timing"]["initialized_doctor_seconds"] = time.perf_counter() - started
        if not state["doctor"].get("available") or not (state["doctor"].get("backend_probe") or {}).get("available"): raise RuntimeError("Initialized CPU doctor failed")
        state["runtime_context"] = _runtime_context()
        state["runtime_context"]["python_blas"] = _blas_threads()
        if any(state["runtime_context"]["threads"][k] != 1 for k in ("julia", "blas")):
            raise RuntimeError("Effective Julia/BLAS thread counts differ from freeze")
        jl, _ = get_julia()
        project = Path(str(jl.seval("Base.active_project()")))
        state["runtime_files"] = {}
        for p in (project, project.with_name("Manifest.toml")):
            shutil.copyfile(p, directory / p.name)
            state["runtime_files"][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
        state["memory_baseline"] = linux_process_memory(os.getpid())
        started = time.perf_counter()
        reg = Register([Atom(*coords) for coords in s["coordinates"]], C6=s["C6"])
        seq = PulseSequence(omega=s["omega"], delta=s["delta"])
        sim = Simulation(reg, seq, SolverConfig(**s["solver"]))
        dimension = sim.validate()
        actual_basis = list(map(int, sim._basis)) if sim._basis is not None else list(range(2**s["N"]))
        if actual_basis != basis(s) or dimension != s["basis_size"]: raise AssertionError("Independent/SDK basis mismatch")
        initial = initial_state(s)
        state["timing"]["setup_basis_seconds"] = time.perf_counter() - started
        # An inexpensive bounded control establishes actual SDK output retention
        # before any cost interpretation; never subtract this from cost timings.
        if s["kind"] == "correctness" and s["fixture"] == "ground":
            empty = sim.run(initial.copy(), 0., s["duration"], observables={})
            empty_path = directory / "empty-history.npz"
            np.savez_compressed(empty_path, t=np.array(list(empty.t)), states=np.array([np.asarray(v, dtype=complex) for v in empty.u]))
            state["empty_observables"] = {"arrays": str(empty_path), "python_type": type(empty).__name__, "state_count": len(empty.u),
                "state_dimension": len(empty.u[0]), "time_count": len(empty.t), "times": list(empty.t),
                "policy": "raw ODE solution exposes state history; observable SDK results expose series/final readout; no matched baseline/no incremental-overhead subtraction"}
            if len(empty.u) != s["output_count"]: raise AssertionError("Empty-observable output policy changed")
        checkpoint("reference")
        started = time.perf_counter()
        ref, description = reference(s, cfg["reference_stability_atol"])
        state["timing"]["reference_seconds"] = time.perf_counter() - started
        np.savez_compressed(directory / "reference.npz", **ref)
        state["reference"] = description
        write_json(directory / "reference.json", description)
        for phase, index, order, seed in record_plan(s, cfg):
            record = {"row_id": f"{s['scenario_id']}-{phase}-{index}", "phase": phase, "repeat_index": index,
                      "order": order, "seed": seed, "operation_count": 1, "eligible": False, "artifacts": {}}
            state["records"].append(record)
            options = {**s["solver"], **({"seed": seed} if seed is not None else {})}
            simulation = sim if seed is None else Simulation(reg, seq, SolverConfig(**options))
            reset, ds = initial.copy(), ordered_declarations(s, order)
            checkpoint("solve")
            started = time.perf_counter()
            result = simulation.run(reset, 0., s["duration"], observables=ds)
            record["runtime_seconds"] = time.perf_counter() - started
            checkpoint("artifact")
            started = time.perf_counter()
            label = f"{phase}-{index}"
            result_path, manifest_path = directory / f"{label}.result.json", directory / f"{label}.manifest.json"
            result.save(str(result_path))
            ordered_write(manifest_path, result.manifest)
            record["artifacts"] = {"result_artifact": str(result_path), "run_manifest": str(manifest_path),
                                   "reference_arrays": str(directory / "reference.npz"), "reference_report": str(directory / "reference.json")}
            record["serialization_seconds"] = time.perf_counter() - started
            checkpoint("validation")
            started = time.perf_counter()
            record["gate"] = result_gate(result, s, cfg, ref, order=order, seed=seed)
            loaded = SimulationResult.load(str(result_path))
            if loaded.manifest != result.manifest or result_gate(loaded, s, cfg, ref, order=order, seed=seed) != record["gate"]:
                raise AssertionError("Saved/reloaded observable result changed")
            saved_envelope = json.loads(result_path.read_text())
            if saved_envelope["shared_result"]["observable_names"] != list(ds) or list(saved_envelope["data"]) != list(ds) + ["t"] or list(saved_envelope["manifest"]["solver"]["observables"]) != list(ds):
                raise AssertionError("Serialized declaration order mismatch")
            record["eligible"] = record["gate"]["passed"]
            record["effective_solver"] = result.diagnostics["simulation"]
            record["validation_seconds"] = time.perf_counter() - started
            checkpoint("validation")
        state["complete"] = True
        checkpoint("artifact")
    except Exception as exc:
        state["failure"] = benchmark_failure_context(exc, stage=state["stage"], timeout_seconds=cfg["timeout_seconds"], backend_probe=state.get("doctor", {}).get("backend_probe"))
        checkpoint(state["stage"])


def make_row(s, cfg, state, supervision, exclusion=None):
    records = state.get("records", [])
    measured = [r for r in records if r["phase"] == "measured" and "runtime_seconds" in r]
    summary = runtime_summary(measured, cfg["repeat_count"]) if s["kind"] == "performance" else None
    failure = state.get("failure")
    status = "passed"
    reason = supervision.get("reason")
    if exclusion:
        status, failure = "skipped", {"stage": "setup", "code": "BENCHMARK_RESOURCE_EXCLUDED", "message": exclusion, "remediation": "Retain exclusion; choose adequate resources before a new campaign"}
    elif reason in ("timeout", "interrupted"):
        status, failure = "incomplete", {"stage": state.get("stage", "setup"), "code": "BENCHMARK_" + reason.upper(), "message": "Worker stopped; partial evidence retained", "remediation": "Inspect checkpoints; rerun in a new directory"}
    elif reason or supervision.get("returncode", 0) != 0:
        status = "failed"
        exc = MemoryError("RSS budget exceeded") if reason == "memory" else RuntimeError("Unexpected worker exit")
        failure = benchmark_failure_context(exc, stage=state.get("stage", "setup"))
    elif failure or any(not r.get("eligible") for r in records): status = "failed"
    elif not state.get("complete") or [(r["phase"], r["repeat_index"], r["order"], r["seed"]) for r in records] != record_plan(s, cfg): status = "incomplete"
    elif s["kind"] == "performance" and (cfg["warmups"] < 2 or cfg["repeat_count"] < 5): status = "incomplete"
    if status != "passed" and not failure:
        failure = {"stage": "validation", "code": "BENCHMARK_VALUE_ORDER_FAILED" if status == "failed" else "BENCHMARK_INSUFFICIENT_EVIDENCE", "message": "All declared calls/value/order gates required; costs need two warmups/five repeats", "remediation": "Retain diagnostics and resolve gates before comparison"}
    if failure: failure = {**failure, "limits": {k: cfg[k] for k in ("timeout_seconds", "memory_limit_bytes")}, "backend_probe": state.get("doctor", {}).get("backend_probe")}
    gates = [r["gate"] for r in records if "gate" in r]
    metrics = {"state": state, "supervision": supervision, "statistics": summary,
               "statistics_reason": None if summary else "Correctness-only control; no performance distribution claimed",
               "timer_scope": TIMER, "memory_scope": "configuration worker lifetime including doctor/reference/writes; /proc HWM and sampled RSS budget"}
    row = make_benchmark_row(row_id=s["scenario_id"], scenario_id=s["scenario_id"], family=FAMILY, tier=TIER,
        status=status, stage=failure["stage"] if failure else "artifact", problem=s, solver=s["solver"],
        backend={"requested_backend": "CPU", "path": s["fixture"], "precision": "complex128"},
        observables={"names": [d["name"] for d in s["declarations"]], "declarations": s["declarations"], "count": s["count"], "output_sample_count": s["output_count"]},
        metrics=metrics, artifacts={}, failure=failure, disclosure_status="local_only")
    row.update({k: s[k] for k in ("kind", "N", "basis_size", "collection", "count", "order", "output_count", "duplicate_outputs", "storage_policy")})
    row.update(eligible=summary["eligible"] if summary else None,
        max_abs_error=max((g["max_abs_error"] for g in gates), default=None), value_gate=all(g["value_passed"] for g in gates) if gates else None,
        order_gate=all(g["order_passed"] for g in gates) if gates else None, peak_bytes=state.get("memory", {}).get("peak_bytes"), raw_records="observable_repeats.json")
    row.update({k + "_s": v for k, v in (summary["runtime_seconds"] if summary else dict.fromkeys(("median", "min", "max", "p25", "p75"))).items()})
    return row


def coverage(rows):
    passed = {r["scenario_id"] for r in rows if r["status"] == "passed"}
    expected = scenarios()
    return {"selected_campaign_passed": all(r["status"] == "passed" for r in rows),
        "full_matrix_passed": {s["scenario_id"] for s in expected} <= passed,
        "correctness_matrix_passed": {s["scenario_id"] for s in expected if s["kind"] == "correctness"} <= passed,
        "performance_matrix_passed": {s["scenario_id"] for s in expected if s["kind"] == "performance"} <= passed,
        "missing_successful_scenarios": [s["scenario_id"] for s in expected if s["scenario_id"] not in passed],
        "classification": "local_only; software/numerical verification, not physical validation or public/release approval"}


def benchmark_observables(output_dir, *, tier="all", scenario_ids=None, warmups=2, repeat_count=5,
                          timeout_seconds=900., memory_limit_mb=4096., accuracy_atol=1e-8,
                          reference_stability_atol=1e-10, stochastic_alpha=1e-6):
    from .runtime import version_info
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (warmups, repeat_count)) or warmups < 0 or repeat_count < 1: raise ValueError("Invalid warmup/repeat counts")
    if not all(math.isfinite(v) and v > 0 for v in (timeout_seconds, memory_limit_mb, accuracy_atol, reference_stability_atol, stochastic_alpha)) or stochastic_alpha >= 1: raise ValueError("Limits/tolerances must be finite positive, alpha below one")
    selected = scenarios(tier)
    if scenario_ids is not None:
        if not scenario_ids or len(set(scenario_ids)) != len(scenario_ids) or set(scenario_ids) - {s["scenario_id"] for s in selected}: raise ValueError("Select unique known nonempty scenario IDs")
        selected = [s for s in selected if s["scenario_id"] in scenario_ids]
    cfg = {"tier": tier, "warmups": warmups, "repeat_count": repeat_count, "timeout_seconds": timeout_seconds,
        "memory_limit_bytes": int(memory_limit_mb * 1024**2), "accuracy_atol": accuracy_atol,
        "reference_stability_atol": reference_stability_atol, "stochastic_alpha": stochastic_alpha}
    output = Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()): raise FileExistsError("Use a new empty output directory")
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    names = [f"sagittarius_py/sagittarius/{n}.py" for n in ("observable_benchmark", "benchmark_measurement", "benchmarking", "benchmark_suite", "benchmark_failures", "api", "pulse", "runtime", "scaling_benchmark", "ablation_benchmark")]
    names += ["sagittarius_py/pyproject.toml", "sagittarius_py/uv.lock", "Sagittarius.jl/Project.toml", "sagittarius_py/tests/test_performance/benchmark_observables.py"]
    names += [str(p.relative_to(root)) for p in (root / "Sagittarius.jl/src").glob("*.jl")]
    names += [n for n in ("scripts/audit_observable_campaign.py", "sagittarius_py/tests/test_observable_benchmark.py") if (root / n).exists()]
    hashes = {}
    for name in names:
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
        hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    frozen = {"scenarios": selected, "settings": cfg, "source_sha256": hashes}
    env = {**os.environ, **{key: "1" for key in THREAD_KEYS}}
    campaign = {**frozen, "config_sha256": hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest(),
        "output_dir": str(output), "source_root": str(root), "source": version_info(initialize_backend=False),
        "workload_version": WORKLOAD_VERSION, "plan_version": "benchmark-implementation-plan/v2", "protocol_version": "benchmark-protocol/v1",
        "created_at": datetime.now(timezone.utc).isoformat(), "command": sys.argv, "cwd": str(Path.cwd()), "python_executable": sys.executable,
        "thread_environment": {k: env[k] for k in THREAD_KEYS}, "timer_scope": TIMER,
        "cache_policy": "fresh worker per configuration; doctor/setup/reference before first; reset initial state; reuse simulation/JIT within worker",
        "stop_policy": "continue after failures; interruption retains unstarted rows as incomplete", "permutation_seed": 1234,
        "correctness_seed_set": list(SEEDS), "performance_seed": None,
        "classification": "shared-workstation local_only; no affinity/exclusive-load controls; no incremental observable-overhead estimator"}
    try:
        campaign["host"] = {"cpu_model": next(line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")), "logical_cpus": os.cpu_count(), "memory_bytes": os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")}
    except (OSError, ValueError, StopIteration): campaign["host"] = {"unavailable_reason": "Host metadata unavailable"}
    write_json(output / "campaign.json", campaign)
    rows, interrupted = [], False
    for s in selected:
        directory = output / s["scenario_id"]
        directory.mkdir()
        config_path, checkpoint_path = directory / "config.json", directory / "checkpoint.json"
        write_json(config_path, {"scenario": s, "settings": cfg, "source_root": str(root), "source_sha256": hashes})
        state, supervision = {}, {}
        exclusion = "Construction/reference estimate exceeds budget" if s["estimated_peak_bytes"] > cfg["memory_limit_bytes"] else None
        if interrupted: supervision = {"reason": "interrupted"}
        elif not exclusion:
            command = [sys.executable, "-m", "sagittarius.observable_benchmark", "--child", str(config_path), str(checkpoint_path)]
            write_json(directory / "command.json", {"argv": command, "cwd": str(Path.cwd())})
            try:
                supervision = supervise(command, cwd=str(Path.cwd()), env=env, log_path=directory / "child.log", timeout_seconds=timeout_seconds, memory_limit_bytes=cfg["memory_limit_bytes"])
            except KeyboardInterrupt: interrupted, supervision = True, {"reason": "interrupted"}
            except Exception as exc: state["failure"] = benchmark_failure_context(exc, stage="setup")
            if checkpoint_path.exists(): state = json.loads(checkpoint_path.read_text())
        row = make_row(s, cfg, state, supervision, exclusion)
        row["artifacts"] = {"config": str(config_path), "checkpoint": str(checkpoint_path) if checkpoint_path.exists() else None}
        rows.append(row)
        write_json(output / "progress.json", rows)
        print(f"{s['scenario_id']}: {row['status']}", flush=True)
    raw = [{"scenario_id": row["scenario_id"], **record} for row in rows for record in row["metrics"]["state"].get("records", [])]
    write_json(output / "observable_repeats.json", raw)
    paths = write_benchmark_artifacts(output_dir=output, stem="observable_performance", name="P1 observable collection and correctness",
        description="Declared diagonal types/order/value gates and per-configuration SDK solve/collection costs; no incremental-overhead claim",
        parameters=campaign, rows=rows, backend="CPU", diagnostics={"doctor": "per-worker checkpoints"},
        run_manifests=[{"label": r["row_id"], "path": r["artifacts"]["run_manifest"]} for r in raw if r["artifacts"].get("run_manifest")],
        columns=COLUMNS, benchmark_context={"family": FAMILY, "tier": TIER, "config_sha256": campaign["config_sha256"], "disclosure_status": "local_only"})
    paths["suite"] = write_benchmark_suite_artifact(output_dir=output, stem="observable_performance_suite", suite_id="phase16-p1-observables-v2",
        family=FAMILY, tier=TIER, rows=rows, source=campaign["source"], environment={"thread_environment": campaign["thread_environment"]},
        scenario_defaults={"settings": cfg, "campaign": str(output / "campaign.json")})
    write_json(output / "coverage.json", coverage(rows))
    return paths


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--child": _child(sys.argv[2], sys.argv[3])
    else: raise SystemExit("Use tests/test_performance/benchmark_observables.py")
