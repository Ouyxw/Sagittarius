"""Fixed-input Python Hamiltonian ablations; timings are not Julia kernel costs."""
from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy.sparse import csr_matrix

from .api import (
    PulseSequence, Register, Simulation, SolverConfig, _constant_vector,
    _dense_hamiltonian_matrix, _interaction_matrix_python, _reduced_basis_python,
    _reduced_hamiltonian_matrix,
)
from .benchmarking import current_memory_usage
from .benchmark_failures import benchmark_failure_context
from .benchmark_measurement import runtime_summary
from .runtime import doctor

ABLATION_BENCHMARK_MODES = [
    {"mode": "full_dense", "representation": "full dense matrix", "backend": "CPU", "workload": "matvec"},
    {"mode": "full_sparse", "representation": "full sparse CSR matrix", "backend": "CPU", "workload": "matvec"},
    {"mode": "reduced_matrix_free", "representation": "blockade-reduced matrix-free operator", "backend": "CPU", "workload": "matvec"},
    {"mode": "reduced_sparse", "representation": "blockade-reduced sparse CSR matrix", "backend": "CPU", "workload": "matvec"},
    {"mode": "reduced_sparse_gpu_cached", "representation": "blockade-reduced cached sparse matrix", "backend": "CUDA", "workload": "ode_solve"},
]
WORKLOAD_VERSION = "fixed-normalized-input-matvec/v2"
CPU_MODES = tuple(item["mode"] for item in ABLATION_BENCHMARK_MODES[:-1])


def _descriptor(mode):
    return dict(next(item for item in ABLATION_BENCHMARK_MODES if item["mode"] == mode))


def _seeded_state(dim, seed):
    rng = np.random.default_rng(seed)
    state = rng.normal(size=dim) + 1j * rng.normal(size=dim)
    return (state / np.linalg.norm(state)).astype(np.complex128)


def _time_repeated_matvec(matrix_or_callable, state, repeats, warmups=0):
    """Every operation uses the same normalized input, never H**k @ state."""
    apply = matrix_or_callable if callable(matrix_or_callable) else matrix_or_callable.dot
    for _ in range(warmups):
        apply(state)
    start = time.perf_counter()
    for _ in range(repeats):
        result = apply(state)
    elapsed = time.perf_counter() - start
    return elapsed, result


def independent_reference(register, omega, delta, basis, state, *, reduced, radius):
    """Kronecker full/projected dense at N<=8; analytic bit action above N=8.

    Does not call production H, interaction, basis or matrix-free helpers.
    Larger checks independently enumerate the permitted bitstrings and apply
    analytic transitions; they are not large full-dense reference evidence.
    """
    n = len(register.atoms)
    coords = np.array([[a.x, a.y, a.z] for a in register.atoms])
    distances = {(i, j): float(np.linalg.norm(coords[i] - coords[j]))
                 for i in range(n) for j in range(i + 1, n)}
    candidates = np.arange(2**n, dtype=np.int64)
    if reduced:
        allowed = np.ones(len(candidates), dtype=bool)
        for (i, j), distance in distances.items():
            if distance < radius:
                allowed &= ~(((candidates >> i) & (candidates >> j) & 1).astype(bool))
        candidates = candidates[allowed]
    if not np.array_equal(candidates, basis):
        raise AssertionError("Basis differs from independent bitstring enumeration.")
    if n <= 8:
        def local(operator, atom):
            result = np.ones((1, 1))
            for bit in reversed(range(n)):
                result = np.kron(result, operator if bit == atom else np.eye(2))
            return result
        populations = [local(np.diag([0., 1.]), i) for i in range(n)]
        full = sum(omega[i] / 2 * local(np.array([[0., 1.], [1., 0.]]), i)
                   - delta[i] * populations[i] for i in range(n))
        for (i, j), distance in distances.items():
            full += (0. if distance == 0 else register.C6 / distance**6) * populations[i] * populations[j]
        return full[np.ix_(candidates, candidates)] @ state, "independent_kronecker_full_projected_dense"
    occupations = [(candidates >> i) & 1 for i in range(n)]
    diagonal = -sum(delta[i] * occupations[i] for i in range(n))
    for (i, j), distance in distances.items():
        diagonal += (0. if distance == 0 else register.C6 / distance**6) * occupations[i] * occupations[j]
    result = diagonal * state
    for i in range(n):
        targets = candidates ^ (1 << i)
        indices = np.searchsorted(candidates, targets)
        valid = indices < len(candidates)
        valid[valid] &= candidates[indices[valid]] == targets[valid]
        result[indices[valid]] += omega[i] / 2 * state[valid]
    return result, "independent_enumerated_bit_transition_action"


def output_gate(actual, expected, *, full, full_rtol, reduced_atol):
    finite = bool(np.all(np.isfinite(actual)) and np.all(np.isfinite(expected)))
    scale = float(max(np.max(np.abs(expected)), 1.)) if np.all(np.isfinite(expected)) else None
    error = float(np.max(np.abs(actual - expected))) if finite else None
    relative = error / scale if finite else None
    return {"finite": finite, "reference_error": error, "reference_scale": scale,
            "reference_relative_error": relative,
            "output_norm": float(np.linalg.norm(actual)) if finite else None,
            "passed": finite and (relative <= full_rtol if full else error <= reduced_atol)}


def construction_estimate(mode, n, d):
    """Conservative allocation preflight, including existing dense CSR intermediate.

    2 GiB runtime/doctor reserve, dense storage + 30% CSR/transient allowance,
    Python basis/mapping allowances, vectors and small independent references.
    """
    dense = mode in {"full_dense", "full_sparse", "reduced_sparse"}
    return int(2 * 1024**3 + (1.3 * 16 * d*d if dense else 0)
               + d * (256 * n + 16 * 16) + (8 * 16 * (2**n)**2 if n <= 8 else 0))
def _reduced_matrix_free_callable(register: Register, omega: List[float], delta: List[float], basis: List[int]):
    n_atoms = len(register.atoms)
    interactions = _interaction_matrix_python(register)
    mapping = {state: idx for idx, state in enumerate(basis)}

    def matvec(state_vector: np.ndarray) -> np.ndarray:
        result = np.zeros_like(state_vector)
        for idx, state in enumerate(basis):
            amplitude = state_vector[idx]
            if amplitude == 0:
                continue
            diagonal = 0.0
            for j in range(n_atoms):
                if state & (1 << j):
                    diagonal -= delta[j]
                    for k in range(j + 1, n_atoms):
                        if state & (1 << k):
                            diagonal += interactions[j, k]
            result[idx] += diagonal * amplitude
            for j in range(n_atoms):
                target_idx = mapping.get(state ^ (1 << j))
                if target_idx is not None:
                    result[target_idx] += (omega[j] / 2.0) * amplitude
        return result

    return matvec



def _benchmark_mode(register, sequence, mode, *, blockade_radius, repeats, warmups,
                    repeat_count, seed, max_full_dim, include_gpu, gpu_duration,
                    memory_limit_bytes, full_rtol, reduced_atol,
                    directory=None, checkpoint=None):
    """One path, with checkpointed timing progress and validation after timing."""
    n = len(register.atoms)
    full = mode.startswith("full_")
    row = {**_descriptor(mode), "status": "ok", "reason": "", "atom_count": n,
           "full_dim": 2**n, "basis_size": 2**n if full else None,
           "repeats": repeats if mode in CPU_MODES else 1,
           "repeat_count": repeat_count, "warmup_count": warmups,
           "total_time_s": None, "time_per_operation_s": None,
           "duration_s": gpu_duration if mode not in CPU_MODES else None,
           "measurement_status": "incomplete", "stage": "setup", "timing": {},
           "measurements": [], "warmups": [], "artifacts": {}, "run_manifests": [],
           "implementation": "Python/NumPy/SciPy" if mode in CPU_MODES else "Julia CUDA ODE through Python SDK",
           "workload_version": WORKLOAD_VERSION if mode in CPU_MODES else "sdk-ode-solve/v1",
           "memory_scope": "shared caller process; use supervised campaign for attributable per-path peaks",
           "dense_construction_intermediate": mode in {"full_sparse", "reduced_sparse"}}
    def save(stage):
        row["stage"] = stage
        row.update(current_memory_usage())
        row["statistics"] = runtime_summary(row["measurements"], repeat_count)
        if checkpoint:
            checkpoint(row)
    def skip(reason):
        row.update(status="skipped", reason=reason, measurement_status="skipped")
        save("setup")
        return row
    save("setup")
    if mode not in CPU_MODES:
        if not include_gpu or os.environ.get("SAGITTARIUS_ENABLE_GPU_TESTS") != "1":
            return skip("CUDA requires include_gpu=True and SAGITTARIUS_ENABLE_GPU_TESTS=1")
    if full and 2**n > max_full_dim:
        return skip(f"full_dim {2**n} exceeds max_full_dim {max_full_dim}")
    try:
        started = time.perf_counter()
        basis = list(range(2**n)) if full else _reduced_basis_python(register, blockade_radius)
        row["timing"]["basis_construction_seconds"] = time.perf_counter() - started
        d = len(basis)
        row.update(basis_size=d, pruned_fraction=1 - d / 2**n,
                   estimated_peak_bytes=construction_estimate(mode, n, d))
        if row["estimated_peak_bytes"] > memory_limit_bytes:
            return skip("Construction/reference estimate exceeds declared memory budget")
        omega = _constant_vector(sequence.omega, n, field_name="omega")
        delta = _constant_vector(sequence.delta, n, field_name="delta")
        if mode not in CPU_MODES:
            return _gpu_measure(register, sequence, basis, row, save, directory,
                                blockade_radius, gpu_duration, warmups, repeat_count)
        state = _seeded_state(d, seed)
        state.setflags(write=False)
        row["input"] = {"seed": seed, "norm": float(np.linalg.norm(state)), "precision": "complex128",
                        "sha256": hashlib.sha256(state.tobytes()).hexdigest(),
                        "policy": "same read-only normalized vector for every operation and repeat"}
        save("setup")
        started = time.perf_counter()
        if mode == "full_dense":
            operator = _dense_hamiltonian_matrix(register, omega, delta)
        elif mode == "full_sparse":
            operator = csr_matrix(_dense_hamiltonian_matrix(register, omega, delta))
        elif mode == "reduced_sparse":
            operator = csr_matrix(_reduced_hamiltonian_matrix(register, omega, delta, basis))
        else:
            operator = _reduced_matrix_free_callable(register, omega, delta, basis)
        row["timing"]["operator_construction_seconds"] = time.perf_counter() - started
        save("reference")
        started = time.perf_counter()
        expected, reference_type = independent_reference(register, omega, delta, basis, state,
                                                         reduced=not full, radius=blockade_radius)
        row["timing"]["reference_seconds"] = time.perf_counter() - started
        row["reference"] = {"type": reference_type, "full_rtol": full_rtol, "reduced_atol": reduced_atol,
                            "relative_scale": "max(1, max(abs(independent H*psi)))",
                            "limitations": "Projected implementation verification; no physical approximation validation. N>8 uses analytic action, not dense reference."}
        if directory:
            reference_path = Path(directory) / "reference.npz"
            np.savez_compressed(reference_path, basis=basis, input=state, expected=expected)
            row["artifacts"]["reference_arrays"] = str(reference_path)
        save("solve")
        elapsed, first = _time_repeated_matvec(operator, state, 1)
        row["timing"]["first_operation_seconds"] = elapsed
        gate = lambda actual: output_gate(actual, expected, full=full, full_rtol=full_rtol, reduced_atol=reduced_atol)
        row["first_gate"] = gate(first)
        if not row["first_gate"]["passed"]:
            raise AssertionError("First operation failed independent reference/finite-value gate")
        for index in range(warmups):
            elapsed, output = _time_repeated_matvec(operator, state, repeats)
            checked = gate(output)
            row["warmups"].append({"warmup_index": index, "warmup": True, "runtime_seconds": elapsed, **checked})
            save("validation")
            if not checked["passed"]:
                raise AssertionError("Warmup failed independent reference/finite-value gate")
        for index in range(repeat_count):
            save("solve")
            elapsed, output = _time_repeated_matvec(operator, state, repeats)
            measurement = {"row_id": f"{mode}-repeat-{index}", "repeat_index": index,
                           "warmup": False, "operation_count": repeats, "runtime_seconds": elapsed,
                           "time_per_operation_s": elapsed / repeats, "eligible": False, "artifacts": {}}
            row["measurements"].append(measurement)
            save("validation")
            checked = gate(output)
            measurement.update(checked)
            if directory:
                output_path = Path(directory) / f"repeat-{index}.npy"
                np.save(output_path, output)
                measurement["artifacts"]["output_array"] = str(output_path)
            measurement["eligible"] = checked["passed"]
            row.update({key: checked[key] for key in ("reference_error", "reference_scale", "reference_relative_error")})
            row.update(total_time_s=row["measurements"][0]["runtime_seconds"],
                       time_per_operation_s=row["measurements"][0]["time_per_operation_s"])
            save("validation")
            if not checked["passed"]:
                raise AssertionError("Measured output failed independent reference/finite-value gate")
        row["measurement_status"] = "passed" if warmups >= 2 and repeat_count >= 5 else "incomplete"
        row["complete"] = True
        save("artifact")
    except Exception as exc:
        row.update(status="failed", measurement_status="failed", reason=str(exc),
                   failure=benchmark_failure_context(exc, stage=row["stage"]))
        save(row["stage"])
    return row


def _gpu_measure(register, sequence, basis, row, save, directory, radius, duration, warmups, repeat_count):
    started = time.perf_counter()
    diagnostics = doctor(backend="CUDA", initialize_backend=True)
    row["doctor"] = diagnostics
    row["timing"]["initialized_cuda_doctor_seconds"] = time.perf_counter() - started
    if not diagnostics.get("available") or not (diagnostics.get("backend_probe") or {}).get("available"):
        raise RuntimeError("Initialized CUDA diagnostics failed")
    times = np.linspace(0., duration, 101).tolist()
    config = SolverConfig(blockade_radius=radius, use_gpu=True, gpu_backend="CUDA",
                          method="Tsit5", reltol=1e-8, abstol=1e-10, saveat=times)
    sim = Simulation(register, sequence, config)
    row["solver"] = {"method": "Tsit5", "reltol": 1e-8, "abstol": 1e-10, "saveat": times,
                     "blockade_radius": radius, "use_gpu": True, "gpu_backend": "CUDA"}
    row["gpu_memory"] = {"peak_bytes": None, "reason": "No supported GPU peak collector; process RSS is CPU memory."}
    row["reference"] = {"type": "finite_and_output_grid_only", "limitations": "Matched CPU/CUDA numerical parity belongs to the GPU suite; no solve ratio or qualified CUDA performance evidence."}
    # Simulation.run converts observable data back to CPU before returning.
    # Explicit device synchronization also brackets every timed end-to-end solve.
    from .runtime import get_julia
    jl, _ = get_julia()
    def solve():
        initial = np.zeros(len(basis), dtype=np.complex128)
        initial[0] = 1.
        jl.seval("using CUDA; CUDA.synchronize()")
        started = time.perf_counter()
        result = sim.run(initial, 0., duration, observables={"pop0": 0})
        jl.seval("using CUDA; CUDA.synchronize()")
        elapsed = time.perf_counter() - started
        values = np.asarray(result.data["pop0"])
        if values.shape != (101,) or not np.all(np.isfinite(values)) or not np.allclose(result.data["t"], times, rtol=0, atol=1e-14):
            raise AssertionError("CUDA output is nonfinite or differs from frozen output grid")
        return result, elapsed
    def retain(result, label):
        row["run_manifests"].append({"label": label, "manifest": result.manifest})
        if not directory:
            return {}
        result_path, manifest_path = Path(directory) / f"{label}.result.json", Path(directory) / f"{label}.manifest.json"
        from .benchmark_measurement import write_json
        result.save(str(result_path))
        write_json(manifest_path, result.manifest)
        return {"result_artifact": str(result_path), "run_manifest": str(manifest_path)}
    save("solve")
    result, elapsed = solve()
    row["timing"]["first_solve_seconds"] = elapsed
    row["artifacts"]["first_solve"] = retain(result, "first")
    for index in range(warmups):
        result, elapsed = solve()
        row["warmups"].append({"warmup_index": index, "warmup": True, "runtime_seconds": elapsed})
        save("solve")
    for index in range(repeat_count):
        result, elapsed = solve()
        item = {"row_id": f"{row['mode']}-repeat-{index}", "repeat_index": index, "warmup": False,
                "operation_count": 1, "runtime_seconds": elapsed, "time_per_operation_s": elapsed,
                "eligible": False, "finite": True, "artifacts": retain(result, f"repeat-{index}")}
        row["measurements"].append(item)
        save("validation")
    row.update(total_time_s=row["measurements"][0]["runtime_seconds"],
               time_per_operation_s=row["measurements"][0]["runtime_seconds"],
               measurement_status="incomplete", complete=True,
               reason="CUDA timings diagnostic until matched GPU-suite parity evidence is retained")
    save("artifact")
    return row


def benchmark_ablation_modes(register: Register, sequence: PulseSequence, *, blockade_radius: float,
                             repeats: int = 50, warmups: int = 2, seed: int = 1234,
                             max_full_dim: int = 4096, include_gpu: bool = False,
                             gpu_duration: float = .2, repeat_count: int = 5,
                             memory_limit_mb: float = 8192, full_rtol: float = 1e-12,
                             reduced_atol: float = 1e-10, modes=None,
                             directory=None, checkpoint=None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Benchmark fixed-input batches. ``repeats`` remains operations per batch.

    ``repeat_count`` counts independent measured batches; ``total_time_s`` and
    ``time_per_operation_s`` retain first-batch semantics. ``statistics`` uses
    eligible independent batches. Direct calls share caller-process memory;
    use benchmark_ablation's supervised CLI for per-path memory attribution.
    Raw ``status=ok`` denotes numerical success; ``measurement_status`` also
    requires >=2 warmups and >=5 measured batches for CPU performance evidence.
    """
    for name, value, minimum in (("repeats", repeats, 1), ("repeat_count", repeat_count, 1),
                                 ("warmups", warmups, 0), ("max_full_dim", max_full_dim, 1), ("seed", seed, 0)):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    if not 1 <= len(register.atoms) <= 20:
        raise ValueError("Ablation fixtures support 1..20 atoms")
    if not math.isfinite(blockade_radius) or blockade_radius < 0:
        raise ValueError("blockade_radius must be finite and nonnegative")
    if not all(math.isfinite(v) and v > 0 for v in (memory_limit_mb, full_rtol, reduced_atol, gpu_duration)):
        raise ValueError("Memory limit, tolerances and duration must be finite and positive")
    selected = [item["mode"] for item in ABLATION_BENCHMARK_MODES] if modes is None else list(modes)
    if not selected or len(set(selected)) != len(selected) or set(selected) - {item["mode"] for item in ABLATION_BENCHMARK_MODES}:
        raise ValueError("Select nonempty unique supported modes")
    rows = [_benchmark_mode(register, sequence, mode, blockade_radius=blockade_radius,
                repeats=repeats, warmups=warmups, repeat_count=repeat_count, seed=seed,
                max_full_dim=max_full_dim, include_gpu=include_gpu, gpu_duration=gpu_duration,
                memory_limit_bytes=int(memory_limit_mb * 1024**2), full_rtol=full_rtol,
                reduced_atol=reduced_atol, directory=directory, checkpoint=checkpoint)
            for mode in selected]
    return rows, [manifest for row in rows for manifest in row["run_manifests"]]
