"""Frozen, supervised, per-instance AQC/ILP performance evidence (plan v2).

Source-checkout benchmark support, not a new optimization API or speedup claim.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import warnings

import numpy as np

from .benchmark_failures import benchmark_failure_context
from .benchmark_measurement import linux_process_memory, runtime_summary, supervise, write_json
from .benchmarking import make_benchmark_row, write_benchmark_artifacts
from .benchmark_suite import write_benchmark_suite_artifact

SIZES = (2, 4, 6, 8, 10, 12, 16, 20)
SEEDS = (101, 102, 103, 104, 105)
FAMILY, TIER = "optimization_aqc", "performance"
WORKLOAD_VERSION = "mwis-aqc-ilp-performance/v2"
THREAD_KEYS = ("JULIA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")


def project_modules():
    project = Path(__file__).resolve().parents[1] / "projects/mwis_udg"
    if str(project) not in sys.path:
        sys.path.insert(0, str(project))
    from batch_verify import generate_random_udg
    from mwis_solver import MWIS_AQC
    return generate_random_udg, MWIS_AQC


def graph_hash(s):
    payload = {key: s[key] for key in ("nodes", "edges")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def scenarios(sizes=SIZES, seeds=SEEDS, *, generation_timings=None):
    sizes, seeds = list(sizes), list(seeds)
    if not sizes or len(set(sizes)) != len(sizes) or any(type(n) is not int or not 1 <= n <= 20 for n in sizes):
        raise ValueError("Select unique integer sizes in [1,20]")
    if not seeds or len(set(seeds)) != len(seeds) or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("Select unique nonnegative integer seeds")
    generate, _ = project_modules()
    output = []
    for n in sizes:
        for seed in seeds:
            started = time.perf_counter()
            graph = generate(n, density=.8, blockade_radius=1., weight_range=(1., 1.5), seed=seed)
            elapsed = time.perf_counter() - started
            s = {"scenario_id": f"udg_weighted_n{n}_seed{seed}", "N": n, "atom_count": n, "seed": seed,
                 "density_parameter": .8, "blockade_radius": 1., "C6": 1., "duration": .15,
                 "omega_max": 2 * math.pi, "weight_range": [1., 1.5], "required": True,
                 "nodes": [{"node": int(i), "position": list(graph.nodes[i]["pos"]), "weight": float(graph.nodes[i]["weight"])} for i in graph],
                 "edges": [list(edge) for edge in sorted(graph.edges())],
                 "average_degree": 2 * graph.number_of_edges() / n,
                 "edge_density": 2 * graph.number_of_edges() / (n * (n - 1)) if n > 1 else 0.,
                 "units": {"length": "um", "time": "us", "angular_frequency": "rad/us", "C6": "rad*um^6/us"},
                 "atom_order": "node iteration order; atom i is bit i (LSB); labels in atom order"}
            s["graph_sha256"] = graph_hash(s)
            from .scaling_benchmark import basis_dimension
            s["basis_size"] = basis_dimension({"N": n, "coordinates": [node["position"] for node in s["nodes"]], "blockade_radius": 1.})
            s.update(full_dim=2**n, pruned_fraction=1 - s["basis_size"] / 2**n, basis="blockade_reduced")
            output.append(s)
            if generation_timings is not None:
                generation_timings[s["scenario_id"]] = elapsed
    return output


def graph_from_scenario(s):
    import networkx as nx
    if graph_hash(s) != s["graph_sha256"] or [node["node"] for node in s["nodes"]] != list(range(s["N"])):
        raise AssertionError("Frozen graph hash/node order mismatch")
    graph = nx.Graph()
    for node in s["nodes"]:
        graph.add_node(node["node"], pos=tuple(node["position"]), weight=node["weight"])
    graph.add_edges_from(s["edges"])
    edges = {tuple(edge) for edge in s["edges"]}
    physical_edges = {(i, j) for i in range(s["N"]) for j in range(i + 1, s["N"])
                      if math.dist(s["nodes"][i]["position"], s["nodes"][j]["position"]) < s["blockade_radius"]}
    if edges != physical_edges:
        raise AssertionError("UDG edges differ from executed strict-radius blockade graph")
    return graph


def independent_basis(s):
    neighbors = [0] * s["N"]
    for i, j in s["edges"]:
        neighbors[i] |= 1 << j
        neighbors[j] |= 1 << i
    basis = []
    def visit(i, bits):
        if i == s["N"]:
            basis.append(bits)
            return
        visit(i + 1, bits)
        if not neighbors[i] & bits:
            visit(i + 1, bits | (1 << i))
    visit(0, 0)
    return sorted(basis)


def basis_objectives(s, basis):
    return np.asarray([sum(node["weight"] for i, node in enumerate(s["nodes"]) if bits >> i & 1) for bits in basis])


def settings(*, repeat_count=5, warmups=2, timeout_seconds=600., memory_limit_mb=4096., ilp_time_limit=30., numerical_atol=1e-6):
    if type(repeat_count) is not int or repeat_count < 1 or type(warmups) is not int or warmups < 0:
        raise ValueError("repeat_count>=1 and warmups>=0 must be integers")
    if not all(math.isfinite(v) and v > 0 for v in (timeout_seconds, memory_limit_mb, ilp_time_limit, numerical_atol)):
        raise ValueError("Limits and numerical tolerance must be finite and positive")
    return {"repeat_count": repeat_count, "warmups": warmups, "timeout_seconds": timeout_seconds,
            "memory_limit_bytes": int(memory_limit_mb * 1024**2), "ilp_time_limit": ilp_time_limit,
            "numerical_atol": numerical_atol, "reference_stability_atol": 1e-9, "objective_atol": 1e-9,
            "solver": {"method": "Tsit5", "adaptive": True, "dt": None, "reltol": 1e-8, "abstol": 1e-10},
            "precision": "complex128", "initial_state": "all_ground", "output_count": 101,
            "observables": {"pop0": 0, "z0": {"type": "pauli_z", "atom": 0}},
            "readout_policy": "SDK normalized final probabilities; raw norm independently checked through Z0+2n0",
            "cbc_threads": 1, "cbc_seed": 1234, "cbc_gap_rel": 0., "cbc_gap_abs": 0.}


def independent_reference(s, *, rtol=1e-12, atol=1e-14):
    """Explicit independent reduced Hamiltonian action and SciPy DOP853.

    No SDK Hamiltonian, pulse compiler or Julia solver is used. Enumeration is
    over every graph-feasible state, not a truncated candidate set.
    """
    from scipy.integrate import solve_ivp
    from scipy.sparse import csr_matrix
    basis = independent_basis(s)
    lookup = {bits: i for i, bits in enumerate(basis)}
    rows, columns = [], []
    counts = np.asarray([bits.bit_count() for bits in basis])
    objective = basis_objectives(s, basis)
    interaction = np.zeros(len(basis))
    for row, bits in enumerate(basis):
        occupied = [i for i in range(s["N"]) if bits >> i & 1]
        interaction[row] = sum(s["C6"] / math.dist(s["nodes"][i]["position"], s["nodes"][j]["position"])**6
                               for k, i in enumerate(occupied) for j in occupied[k + 1:])
        for i in range(s["N"]):
            target = lookup.get(bits ^ (1 << i))
            if target is not None:
                rows.append(row)
                columns.append(target)
    adjacency = csr_matrix((np.ones(len(rows)), (rows, columns)), shape=(len(basis), len(basis)))
    def derivative(t, psi):
        fraction = t / s["duration"]
        omega = s["omega_max"] * math.sin(math.pi * fraction)**2
        diagonal = interaction + 2 * s["omega_max"] * (1 - fraction) * counts - 2 * math.pi * fraction * objective
        return -1j * (.5 * omega * (adjacency @ psi) + diagonal * psi)
    initial = np.zeros(len(basis), dtype=np.complex128)
    initial[0] = 1.
    times = np.linspace(0., s["duration"], 101)
    solution = solve_ivp(derivative, (0., s["duration"]), initial, method="DOP853", t_eval=times, rtol=rtol, atol=atol)
    if not solution.success or solution.y.shape != (len(basis), 101):
        raise AssertionError("Independent DOP853 reference failed")
    probabilities = np.abs(solution.y)**2
    pop0 = np.sum(probabilities[(np.asarray(basis) & 1) != 0], axis=0)
    return {"basis": np.asarray(basis), "t": times, "pop0": pop0, "probabilities": probabilities[:, -1].copy(),
            "nfev": solution.nfev, "method": "SciPy DOP853; independently enumerated sparse Hamiltonian", "rtol": rtol, "atol": atol}


def result_gate(result, s, cfg, reference):
    from .api import _pulse_manifest, validate_run_manifest
    _, adapter = project_modules()
    manifest = result.manifest
    validate_run_manifest(manifest)
    pulse = adapter(graph_from_scenario(s)).create_adiabatic_sequence(duration=s["duration"])
    expected_pulse = {key: _pulse_manifest(getattr(pulse, key)) for key in ("omega", "delta")}
    solver = manifest["solver"]
    if manifest["register"]["atoms"] != [node["position"] + [0.] for node in s["nodes"]] or manifest["register"]["C6"] != s["C6"] or manifest["pulse"] != expected_pulse:
        raise AssertionError("Executed register/pulse differs from frozen instance")
    for key, value in cfg["solver"].items():
        if solver[key] != value:
            raise AssertionError("Executed solver differs from freeze")
    if solver["effective_method"] != "Tsit5" or solver["effective_adaptive"] is not True or solver["effective_dt"] is not None or solver["use_gpu"] or manifest["backend_diagnostics"]["requested_backend"] != "CPU":
        raise AssertionError("Effective solver/backend mismatch")
    if solver["effective_saveat"] != reference["t"].tolist() or solver["observables"] != cfg["observables"] or solver["blockade_radius"] != s["blockade_radius"]:
        raise AssertionError("Effective grid/observable/basis mismatch")
    initial = manifest["initial_state"]
    if initial["basis_size"] != s["basis_size"] or (initial.get("preparation") or {}).get("bitstring") != "0" * s["N"] or abs(initial["norm"] - 1.) > 1e-14:
        raise AssertionError("Initial preparation/basis mismatch")
    distribution = result.final_bitstring_distribution()
    basis = independent_basis(s)
    labels = [format(bits, f"0{s['N']}b")[::-1] for bits in basis]
    if set(distribution) != set(labels) or manifest["readout"]["basis_bitstrings"] != labels:
        raise AssertionError("Graph/basis/LSB label mapping mismatch")
    values = np.asarray([distribution[key] for key in labels])
    actual_times, pop0 = np.asarray(result.data["t"]), np.asarray(result.data["pop0"])
    if actual_times.shape != (101,) or pop0.shape != (101,) or not np.allclose(actual_times, reference["t"], rtol=0, atol=1e-14):
        raise AssertionError("Saved output time/shape mismatch")
    finite = bool(np.isfinite(values).all() and np.isfinite(pop0).all())
    error = max(float(np.max(np.abs(values - reference["probabilities"]))), float(np.max(np.abs(pop0 - reference["pop0"])))) if finite else None
    norm_error = abs(float(np.sum(values)) - 1.) if finite else None
    gate = {"finite": finite, "numerical_max_abs_error": error, "probability_norm_error": norm_error,
            "passed": finite and error <= cfg["numerical_atol"] and norm_error <= cfg["numerical_atol"] and bool(np.min(values) >= -1e-12)}
    if "z0" in cfg["observables"]:
        z0 = np.asarray(result.data["z0"])
        if z0.shape != (101,) or not np.isfinite(z0).all():
            raise AssertionError("Raw-state norm observable is invalid")
        gate["raw_state_norm_error"] = float(np.max(np.abs(z0 + 2 * pop0 - 1.))) if finite else None
        gate["numerical_max_abs_error"] = max(error, float(np.max(np.abs(z0 - (1 - 2 * reference["pop0"]))))) if finite else None
        gate["passed"] = bool(gate["passed"] and gate["raw_state_norm_error"] is not None and gate["raw_state_norm_error"] <= cfg["numerical_atol"] and gate["numerical_max_abs_error"] <= cfg["numerical_atol"])
    return gate


def quality_metrics(s, distribution, exact_objective, *, objective_atol=1e-9):
    basis = independent_basis(s)
    objectives = basis_objectives(s, basis)
    # Ties select ascending integer basis order, matching the original adapter.
    probabilities = np.asarray([distribution[format(bits, f"0{s['N']}b")[::-1]] for bits in basis])
    candidates = sorted((int(label[::-1], 2), value) for label, value in distribution.items())
    bits = max(candidates, key=lambda item: item[1])[0]
    feasible = all(not ((bits >> i) & (bits >> j) & 1) for i, j in s["edges"])
    weight = sum(node["weight"] for i, node in enumerate(s["nodes"]) if bits >> i & 1)
    known = exact_objective is not None and feasible
    return {"candidate_bitstring": [(bits >> i) & 1 for i in range(s["N"])], "candidate_objective": weight, "feasible": feasible,
            "exact_objective": exact_objective, "objective_gap": max(0., exact_objective - weight) if known else None,
            "approximation_ratio": weight / exact_objective if known and exact_objective > 0 else None,
            "optimal_success_probability": float(np.sum(probabilities[np.abs(objectives - exact_objective) <= objective_atol])) if known else None,
            "unavailable_reason": None if known else "No proven ILP optimum (or infeasible candidate); an incumbent is not an exact optimum."}


def ilp_result(problem, variables, s, log_text):
    """PuLP 'Optimal' alone can mean a time-limited integer incumbent."""
    import pulp
    status = str(pulp.LpStatus[problem.status])
    solution_status = str(pulp.LpSolution[problem.sol_status])
    proven = problem.status == pulp.LpStatusOptimal and problem.sol_status == pulp.LpSolutionOptimal
    raw = [variable.value() for variable in variables]
    has_incumbent = problem.sol_status in (pulp.LpSolutionOptimal, pulp.LpSolutionIntegerFeasible)
    has_incumbent = has_incumbent and all(v is not None and math.isfinite(v) and abs(v - round(v)) <= 1e-6 and -1e-6 <= v <= 1 + 1e-6 for v in raw)
    bits = [int(round(v)) for v in raw] if has_incumbent else None
    feasible = bits is not None and all(not (bits[i] and bits[j]) for i, j in s["edges"])
    if has_incumbent and not feasible:
        raise AssertionError("ILP reported an infeasible integer incumbent")
    objective = sum(node["weight"] * bits[i] for i, node in enumerate(s["nodes"])) if feasible else None
    bound = re.search(r"Upper bound:\s*([-+0-9.eE]+)", log_text)
    return {"problem_status": status, "solution_status": solution_status, "proven_optimal": proven and feasible,
            "candidate_bitstring": bits, "incumbent_objective": objective, "exact_objective": objective if proven and feasible else None,
            "best_bound": float(bound.group(1)) if bound else None,
            "bound_source": "CBC log (printed precision)" if bound else "Unavailable: PuLP interface does not expose CBC best bound and log has none.",
            "termination": "optimal" if proven and feasible else "time_limit" if "time limit" in log_text.lower() or "stopped on time" in log_text.lower() else "not_optimal"}


def phases(cfg):
    return [("first", 0)] + [("warmup", i) for i in range(cfg["warmups"])] + [("measured", i) for i in range(cfg["repeat_count"])]


def save_result(result, directory, label):
    result_path, manifest_path = directory / f"{label}.result.json", directory / f"{label}.manifest.json"
    result.save(str(result_path))
    write_json(manifest_path, result.manifest)
    return {"result_artifact": str(result_path), "run_manifest": str(manifest_path)}


def _aqc(s, cfg, directory, state, checkpoint):
    from . import SolverConfig, doctor
    from .scaling_benchmark import _runtime_context
    from .ablation_benchmark import _blas_threads
    from .runtime import get_julia
    started = time.perf_counter()
    state["doctor"] = doctor(backend="CPU", initialize_backend=True)
    state["initialization_seconds"] = time.perf_counter() - started
    checkpoint("setup")
    if not state["doctor"].get("available") or not (state["doctor"].get("backend_probe") or {}).get("available"):
        raise RuntimeError("Initialized CPU doctor failed")
    state["runtime_context"] = _runtime_context()
    state["runtime_context"]["python_blas"] = _blas_threads()
    state["runtime_files"] = {}
    jl, _ = get_julia()
    project = Path(str(jl.seval("Base.active_project()")))
    for path in (project, project.with_name("Manifest.toml")):
        if path.is_file():
            shutil.copyfile(path, directory / path.name)
            state["runtime_files"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    state["memory_baseline"] = linux_process_memory(os.getpid())
    started = time.perf_counter()
    _, adapter = project_modules()
    aqc = adapter(graph_from_scenario(s), blockade_radius=s["blockade_radius"])
    times = np.linspace(0., s["duration"], cfg["output_count"]).tolist()
    simulation, initial = aqc.prepare_simulation(SolverConfig(**cfg["solver"], blockade_radius=s["blockade_radius"], saveat=times), s["duration"])
    if list(map(int, simulation._basis)) != independent_basis(s) or len(initial) != s["basis_size"]:
        raise AssertionError("SDK basis differs from independently enumerated graph basis")
    state["setup_seconds"] = time.perf_counter() - started
    reference = None
    for phase, index in phases(cfg):
        label = f"{phase}-{index}"
        record = {"row_id": f"{s['scenario_id']}-aqc-{label}", "phase": phase, "repeat_index": index,
                  "operation_count": 1, "eligible": False, "artifacts": {}}
        state["records"].append(record)
        from . import PreparedState
        reset = PreparedState(initial.amplitudes.copy(), dict(initial.metadata))
        checkpoint("solve")
        started = time.perf_counter()
        result = simulation.run(reset, 0., s["duration"], observables=cfg["observables"])
        record["runtime_seconds"] = time.perf_counter() - started
        checkpoint("artifact")
        started = time.perf_counter()
        record["artifacts"] = save_result(result, directory, label)
        record["serialization_seconds"] = time.perf_counter() - started
        checkpoint("reference" if reference is None else "validation")
        if reference is None:
            started = time.perf_counter()
            coarse = independent_reference(s, rtol=1e-10, atol=1e-12)
            reference = independent_reference(s)
            stability = max(float(np.max(np.abs(coarse[key] - reference[key]))) for key in ("pop0", "probabilities"))
            state["reference"] = {"method": reference["method"], "rtol": reference["rtol"], "atol": reference["atol"],
                "coarse_rtol": 1e-10, "coarse_atol": 1e-12, "stability_error": stability,
                "stability_atol": cfg["reference_stability_atol"], "nfev": int(reference["nfev"]),
                "limitations": "Independent verification of the executed reduced model, not finite-interaction/full-space physical equivalence."}
            state["reference_seconds"] = time.perf_counter() - started
            path = directory / "independent-reference.npz"
            np.savez_compressed(path, **{key: reference[key] for key in ("basis", "t", "pop0", "probabilities")})
            state["reference"]["arrays"] = str(path)
            checkpoint("validation")
            if not math.isfinite(stability) or stability > cfg["reference_stability_atol"]:
                raise AssertionError("Independent numerical reference is not stable under refinement")
        started = time.perf_counter()
        record["gate"] = result_gate(result, s, cfg, reference)
        bits, probabilities, basis = aqc.decode_result(result)
        record["candidate_bitstring"] = bits.tolist()
        record["postprocessing_seconds"] = time.perf_counter() - started
        record["eligible"] = record["gate"]["passed"]
        checkpoint("validation")
        if not record["eligible"]:
            raise AssertionError("AQC independent trajectory/probability gate failed")


def _ilp(s, cfg, directory, state, checkpoint):
    import pulp
    graph_from_scenario(s)
    state["memory_baseline"] = linux_process_memory(os.getpid())
    state["memory_scope"] = "Python ILP worker lifetime; CBC subprocess peak unavailable (not included in Python HWM or RSS polling)."
    basis = independent_basis(s)
    enumerated_optimum = float(np.max(basis_objectives(s, basis)))
    state["enumerated_optimum"] = enumerated_optimum
    # A second, full 2^N check is bounded to small graphs.
    if s["N"] <= 8:
        brute = [bits for bits in range(2**s["N"]) if all(not ((bits >> i) & (bits >> j) & 1) for i, j in s["edges"])]
        if brute != basis:
            raise AssertionError("Recursive graph enumeration differs from small full-bitstring reference")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        probe = pulp.PULP_CBC_CMD(msg=False)
    version = subprocess.run([probe.path, "-version"], capture_output=True, text=True, timeout=10)
    state["solver"] = {"name": "PuLP/CBC", "pulp_version": pulp.__version__, "binary": probe.path,
                       "binary_sha256": hashlib.sha256(Path(probe.path).read_bytes()).hexdigest(), "version_output": version.stdout + version.stderr,
                       "threads": cfg["cbc_threads"], "time_limit_seconds": cfg["ilp_time_limit"],
                       "gap_rel": 0., "gap_abs": 0., "random_seed": cfg["cbc_seed"], "warm_start": False}
    for phase, index in phases(cfg):
        label = f"{phase}-{index}"
        record = {"row_id": f"{s['scenario_id']}-ilp-{label}", "phase": phase, "repeat_index": index,
                  "operation_count": 1, "eligible": False, "artifacts": {}}
        state["records"].append(record)
        checkpoint("setup")
        started = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            model = pulp.LpProblem("Sagittarius_MWIS_Performance", pulp.LpMaximize)
            variables = [pulp.LpVariable(f"x_{i}", cat="Binary") for i in range(s["N"])]
            model += pulp.lpSum(node["weight"] * variables[i] for i, node in enumerate(s["nodes"]))
            for i, j in s["edges"]:
                model += variables[i] + variables[j] <= 1
            log_path = directory / f"{label}.cbc.log"
            solver = pulp.PULP_CBC_CMD(msg=False, threads=cfg["cbc_threads"], timeLimit=cfg["ilp_time_limit"],
                gapRel=0., gapAbs=0., warmStart=False, options=[f"randomSeed {cfg['cbc_seed']}"], logPath=str(log_path))
        record["model_construction_seconds"] = time.perf_counter() - started
        if phase == "first":
            model.writeLP(str(directory / "model.lp"))
        checkpoint("solve")
        started = time.perf_counter()
        model.solve(solver)
        record["runtime_seconds"] = time.perf_counter() - started
        checkpoint("validation")
        started = time.perf_counter()
        record["reference"] = ilp_result(model, variables, s, log_path.read_text())
        exact = record["reference"]["exact_objective"]
        if exact is not None and abs(exact - enumerated_optimum) > cfg["objective_atol"]:
            raise AssertionError("CBC optimum differs from independent exhaustive reference")
        record["eligible"] = bool(record["reference"]["proven_optimal"])
        record["postprocessing_seconds"] = time.perf_counter() - started
        report_path = directory / f"{label}.reference.json"
        record["artifacts"] = {"solver_log": str(log_path), "reference_report": str(report_path)}
        checkpoint("artifact")
        started = time.perf_counter()
        write_json(report_path, record["reference"])
        record["serialization_seconds"] = time.perf_counter() - started
        checkpoint("validation")


def _child(config_path, checkpoint_path):
    config = json.loads(Path(config_path).read_text())
    s, cfg, path = config["scenario"], config["settings"], config["path"]
    directory = Path(checkpoint_path).parent
    state = {"stage": "setup", "records": [], "complete": False, "path": path}
    def checkpoint(stage):
        state["stage"] = stage
        state["memory"] = linux_process_memory(os.getpid())
        write_json(checkpoint_path, state)
    checkpoint("setup")
    try:
        for name, digest in config["source_sha256"].items():
            if hashlib.sha256((Path(config["source_root"]) / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError("Frozen source changed during campaign")
        (_aqc if path == "aqc" else _ilp)(s, cfg, directory, state, checkpoint)
        state["complete"] = True
        checkpoint("validation")
    except BaseException as exc:
        state["failure"] = benchmark_failure_context(exc, stage=state["stage"], backend_probe=state.get("doctor"))
        checkpoint(state["stage"])


def path_summary(state, cfg):
    # Include stopped timers even when artifact writing or validation failed.
    records = [r for r in state.get("records", []) if r["phase"] == "measured" and "runtime_seconds" in r]
    return runtime_summary(records, cfg["repeat_count"])


def assemble_row(s, cfg, evidence, *, exclusion=None, generation_seconds=None):
    from . import SimulationResult
    aqc, ilp = (evidence.get(path, {}).get("state", {}) for path in ("aqc", "ilp"))
    failure = next((item["state"]["failure"] for item in evidence.values() if item.get("state", {}).get("failure")), None)
    summaries = {path: path_summary(evidence.get(path, {}).get("state", {}), cfg) for path in ("aqc", "ilp")}
    status = "passed"
    if exclusion:
        status = "incomplete" if exclusion == "Campaign interrupted" else "skipped"
        failure = {"stage": "setup", "code": "BENCHMARK_NOT_STARTED", "message": exclusion, "remediation": "Retain exclusion/progress and start a new campaign with explicit limits."}
    elif failure:
        status = "incomplete" if failure.get("code") == "BENCHMARK_TIMEOUT" or failure.get("exception_type") == "KeyboardInterrupt" else "failed"
    elif any(item.get("supervision", {}).get("reason") in ("timeout", "interrupted") for item in evidence.values()):
        status = "incomplete"
        failure = benchmark_failure_context(TimeoutError("Scenario path timed out or campaign interrupted"), stage="solve", timeout_seconds=cfg["timeout_seconds"])
    elif any(item.get("supervision", {}).get("reason") == "memory" for item in evidence.values()):
        status = "failed"
        failure = benchmark_failure_context(MemoryError("Path exceeded sampled RSS budget; inspect retained supervision/checkpoints"), stage="solve")
    elif any(item.get("supervision", {}).get("returncode", 0) != 0 for item in evidence.values()):
        status = "failed"
        failure = benchmark_failure_context(RuntimeError("Path exited unexpectedly; inspect supervision/logs"), stage="solve")
    elif cfg["warmups"] < 2 or cfg["repeat_count"] < 5 or not all(state.get("complete") for state in (aqc, ilp)) or any(summary["eligible"] != cfg["repeat_count"] for summary in summaries.values()):
        status = "incomplete"
        failure = {"stage": "validation", "code": "BENCHMARK_INCOMPLETE_EVIDENCE", "message": "Requires completed paths, two warmups, five eligible repeats and proven ILP optimality.", "remediation": "Inspect path checkpoints and exact termination status; run a new complete campaign."}
    exact_records = [r for r in ilp.get("records", []) if r.get("reference", {}).get("proven_optimal")]
    exact = exact_records[0]["reference"]["exact_objective"] if exact_records else None
    quality = {}
    for record in aqc.get("records", []):
        artifact = record.get("artifacts", {}).get("result_artifact")
        if artifact:
            try:
                result = SimulationResult.load(artifact)
                quality[record["row_id"]] = quality_metrics(s, result.final_bitstring_distribution(), exact, objective_atol=cfg["objective_atol"])
                if not quality[record["row_id"]]["feasible"]:
                    raise AssertionError("AQC candidate is infeasible")
            except Exception as exc:
                status = "failed"
                failure = benchmark_failure_context(exc, stage="validation")
    metrics = {"statistics": summaries, "paths": evidence, "quality_by_aqc_row_id": quality, "generation_seconds": generation_seconds,
               "exact_objective": exact, "exact_unavailable_reason": None if exact is not None else "No proven ILP optimum; retain AQC outputs but do not interpret incumbent as exact.",
               "basis_size": s["basis_size"], "full_dim": 2**s["N"]}
    row = make_benchmark_row(row_id=s["scenario_id"], scenario_id=s["scenario_id"], family=FAMILY, tier=TIER, status=status,
        stage="validation" if status == "passed" else failure["stage"], problem=s, solver=cfg,
        backend={"requested_backend": "CPU", "path": "separate_aqc_ilp_processes"},
        observables={"names": list(cfg["observables"]), "count": len(cfg["observables"]), "output_sample_count": 101,
                     "final_readout": "normalized final_basis_probabilities"},
        metrics=metrics, artifacts={"path_checkpoints": {p: item.get("checkpoint") for p, item in evidence.items()}}, failure=failure)
    row.update(N=s["N"], basis_size=s["basis_size"], average_degree=s["average_degree"], edge_density=s["edge_density"], exact_objective=exact)
    for path, summary in summaries.items():
        row[f"{path}_eligible"] = summary["eligible"]
        for name, value in summary["runtime_seconds"].items():
            row[f"{path}_{name}_s"] = value
    measured_quality = [quality[r["row_id"]] for r in aqc.get("records", []) if r["phase"] == "measured" and r["row_id"] in quality]
    representative = measured_quality[0] if measured_quality else {}
    for key in ("candidate_objective", "feasible", "objective_gap", "approximation_ratio", "optimal_success_probability"):
        row[key] = representative.get(key)
    row["numerical_max_abs_error"] = max((r["gate"]["numerical_max_abs_error"] for r in aqc.get("records", []) if r.get("gate", {}).get("numerical_max_abs_error") is not None), default=None)
    return row


def benchmark_mwis_performance(output_dir, *, sizes=SIZES, seeds=SEEDS, **options):
    from .runtime import version_info
    cfg = settings(**options)
    generation = {}
    selected = scenarios(sizes, seeds, generation_timings=generation)
    output = Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a new empty output directory; preserve previous evidence")
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    relative_sources = [f"sagittarius_py/sagittarius/{name}.py" for name in (
        "mwis_benchmark", "benchmark_measurement", "benchmarking", "benchmark_suite", "benchmark_failures",
        "api", "pulse", "runtime", "scaling_benchmark", "ablation_benchmark")]
    relative_sources += ["sagittarius_py/projects/mwis_udg/" + name + ".py" for name in ("mwis_solver", "batch_verify", "solution_verify")]
    relative_sources += ["sagittarius_py/tests/test_performance/benchmark_mwis_aqc.py", "sagittarius_py/uv.lock", "sagittarius_py/pyproject.toml", "Sagittarius.jl/Project.toml"]
    relative_sources += [str(p.relative_to(root)) for p in (root / "Sagittarius.jl/src").glob("*.jl")]
    relative_sources += [name for name in ("scripts/audit_mwis_campaign.py", "sagittarius_py/tests/test_mwis_performance.py") if (root / name).exists()]
    hashes = {}
    for name in relative_sources:
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
        hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    frozen = {"scenarios": selected, "settings": cfg, "source_sha256": hashes}
    env = os.environ.copy()
    env.update({key: "1" for key in THREAD_KEYS})
    campaign = {**frozen, "config_sha256": hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest(),
        "output_dir": str(output), "source_root": str(root), "source": version_info(initialize_backend=False),
        "plan_version": "benchmark-implementation-plan/v2", "workload_version": WORKLOAD_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(), "command": sys.argv, "cwd": str(Path.cwd()),
        "generation_seconds": generation, "thread_environment": {k: env[k] for k in THREAD_KEYS},
        "timer_policy": {"aqc": "Simulation.run including SDK validation/operator/pulse construction, pop0/Z0 collection and manifest. Setup/reset, references, validation, decoding and writes excluded.",
                         "ilp": "Fresh model.solve(CBC), including PuLP model-file writing, CBC subprocess startup/IPC and result parsing; model construction/validation/report writes excluded."},
        "cache_policy": "Fresh worker per graph/path; initialized CPU doctor before first AQC; first + two warmups + five independent calls; state reset, model rebuilt and CBC warmStart=False every time.",
        "stop_policy": "Continue after path failures; interruption prevents starting further paths but preserves every declared row.",
        "classification": "local_only; methods have different solution guarantees; no optimization speedup or scientific validation"}
    try:
        campaign["host"] = {"cpu_model": next(line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")),
            "logical_cpus": os.cpu_count(), "physical_memory_bytes": os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"), "isolation": "shared workstation, no affinity/exclusive-load controls"}
    except (OSError, ValueError, StopIteration):
        campaign["host"] = {"unavailable_reason": "CPU/memory metadata unavailable"}
    write_json(output / "campaign.json", campaign)
    rows, interrupted = [], False
    for s in selected:
        directory = output / s["scenario_id"]
        directory.mkdir()
        evidence = {}
        estimate = 2 * 1024**3 + s["basis_size"] * (256 * s["N"] + 128 * 16 + 2 * 101 * 16)
        exclusion = "Campaign interrupted" if interrupted else "Construction/reference estimate exceeds memory budget" if estimate > cfg["memory_limit_bytes"] else None
        for path in ("aqc", "ilp"):
            child_dir = directory / path
            child_dir.mkdir()
            config_path, checkpoint_path = child_dir / "config.json", child_dir / "checkpoint.json"
            write_json(config_path, {"scenario": s, "settings": cfg, "path": path, "source_root": str(root), "source_sha256": hashes})
            item = {"config": str(config_path), "checkpoint": None, "state": {}, "supervision": {}}
            evidence[path] = item
            if exclusion or interrupted:
                continue
            command = [sys.executable, "-m", "sagittarius.mwis_benchmark", "--child", str(config_path), str(checkpoint_path)]
            write_json(child_dir / "command.json", {"argv": command, "cwd": str(Path.cwd()), "threads": campaign["thread_environment"]})
            try:
                item["supervision"] = supervise(command, cwd=str(Path.cwd()), env=env, log_path=child_dir / "child.log",
                    timeout_seconds=cfg["timeout_seconds"], memory_limit_bytes=cfg["memory_limit_bytes"])
            except KeyboardInterrupt:
                interrupted = True
                item["supervision"] = {"reason": "interrupted"}
            except Exception as exc:
                item["state"]["failure"] = benchmark_failure_context(exc, stage="setup")
            if checkpoint_path.exists():
                item["checkpoint"] = str(checkpoint_path)
                try:
                    item["state"] = json.loads(checkpoint_path.read_text())
                except (OSError, ValueError) as exc:
                    item["state"]["failure"] = benchmark_failure_context(exc, stage="artifact")
        row = assemble_row(s, cfg, evidence, exclusion=exclusion, generation_seconds=generation[s["scenario_id"]])
        row["metrics"]["estimated_aqc_peak_bytes"] = estimate
        row["raw_records"] = f"[paths]({s['scenario_id']}/paths.json)"
        write_json(directory / "paths.json", evidence)
        rows.append(row)
        write_json(output / "progress.json", rows)
        print(f"{s['scenario_id']} D={s['basis_size']}: {row['status']}", flush=True)
    paths = write_benchmark_artifacts(output_dir=output, stem="mwis_aqc_performance", name="Frozen MWIS/UDG AQC and exact-reference performance",
        description=campaign["classification"], parameters=campaign, rows=rows, backend="CPU", diagnostics={"initialized_doctor": "AQC path checkpoints; ILP records CBC binary/version/status"},
        columns=["scenario_id", "status", "N", "basis_size", "average_degree", "edge_density", "aqc_eligible", "ilp_eligible",
                 "aqc_median_s", "aqc_min_s", "aqc_max_s", "aqc_p25_s", "aqc_p75_s",
                 "ilp_median_s", "ilp_min_s", "ilp_max_s", "ilp_p25_s", "ilp_p75_s", "exact_objective",
                 "candidate_objective", "feasible", "objective_gap", "approximation_ratio", "optimal_success_probability", "numerical_max_abs_error", "raw_records"],
        benchmark_context={"family": FAMILY, "tier": TIER, "disclosure_status": "local_only", "workload_version": WORKLOAD_VERSION})
    paths["suite"] = write_benchmark_suite_artifact(output_dir=output, stem="mwis_aqc_performance_suite", suite_id="phase16-p1-mwis-v2",
        family=FAMILY, tier=TIER, rows=rows, source=campaign["source"], environment={"threads": campaign["thread_environment"]}, scenario_defaults={"campaign": str(output / "campaign.json")})
    write_json(output / "mwis_repeats.json", [{"scenario_id": r["scenario_id"], "path": path, **record} for r in rows for path, item in r["metrics"]["paths"].items() for record in item["state"].get("records", [])])
    expected = scenarios()
    passed = {r["scenario_id"] for r in rows if r["status"] == "passed"}
    write_json(output / "coverage.json", {"declared_rows_accounted": len(rows) == len(selected),
        "all_p1_mwis_passed": all(s in selected for s in expected) and {s["scenario_id"] for s in expected} <= passed,
        "missing_successful_scenarios": sorted({s["scenario_id"] for s in expected} - passed), "classification": "local_only"})
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", nargs=2, help=argparse.SUPPRESS)
    parser.add_argument("--sizes", nargs="+", type=int, default=list(SIZES))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(SEEDS))
    parser.add_argument("--output-dir", default="benchmark-output/mwis-v2")
    parser.add_argument("--repeat-count", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=float, default=600.)
    parser.add_argument("--memory-limit-mb", type=float, default=4096.)
    parser.add_argument("--ilp-time-limit", type=float, default=30.)
    parser.add_argument("--numerical-atol", type=float, default=1e-6)
    args = parser.parse_args()
    if args.child:
        _child(*args.child)
    else:
        benchmark_mwis_performance(args.output_dir, sizes=args.sizes, seeds=args.seeds, repeat_count=args.repeat_count,
            warmups=args.warmups, timeout_seconds=args.timeout_seconds, memory_limit_mb=args.memory_limit_mb,
            ilp_time_limit=args.ilp_time_limit, numerical_atol=args.numerical_atol)


if __name__ == "__main__":
    main()
