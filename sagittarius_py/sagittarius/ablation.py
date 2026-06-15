from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy.sparse import csr_matrix

from .api import (
    PulseSequence,
    Register,
    SagittariusSolverError,
    Simulation,
    SolverConfig,
    _constant_vector,
    _dense_hamiltonian_matrix,
    _interaction_matrix_python,
    _reduced_basis_python,
    _reduced_hamiltonian_matrix,
)
from .benchmarking import current_memory_usage

ABLATION_BENCHMARK_MODES = [
    {"mode": "full_dense", "representation": "full dense matrix", "backend": "CPU", "workload": "matvec"},
    {"mode": "full_sparse", "representation": "full sparse CSR matrix", "backend": "CPU", "workload": "matvec"},
    {"mode": "reduced_matrix_free", "representation": "blockade-reduced matrix-free operator", "backend": "CPU", "workload": "matvec"},
    {"mode": "reduced_sparse", "representation": "blockade-reduced sparse CSR matrix", "backend": "CPU", "workload": "matvec"},
    {"mode": "reduced_sparse_gpu_cached", "representation": "blockade-reduced cached sparse matrix", "backend": "CUDA", "workload": "ode_solve"},
]


def _descriptor(mode: str) -> Dict[str, str]:
    for item in ABLATION_BENCHMARK_MODES:
        if item["mode"] == mode:
            return dict(item)
    raise KeyError(mode)


def _seeded_state(dim: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    state = rng.normal(size=dim) + 1j * rng.normal(size=dim)
    return (state / np.linalg.norm(state)).astype(np.complex128)


def _time_repeated_matvec(matrix_or_callable: Any, state: np.ndarray, repeats: int, warmups: int) -> Tuple[float, np.ndarray]:
    vector = state.copy()
    for _ in range(warmups):
        vector = matrix_or_callable(vector) if callable(matrix_or_callable) else matrix_or_callable @ vector
    start = time.perf_counter()
    for _ in range(repeats):
        vector = matrix_or_callable(vector) if callable(matrix_or_callable) else matrix_or_callable @ vector
    return time.perf_counter() - start, vector


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


def _row(
    *,
    mode: str,
    status: str,
    atom_count: int,
    full_dim: int,
    basis_size: int,
    repeats: int,
    total_time_s: float | None = None,
    reason: str = "",
    duration_s: float | None = None,
) -> Dict[str, Any]:
    descriptor = _descriptor(mode)
    memory = current_memory_usage()
    per_operation = None if total_time_s is None else total_time_s / max(repeats, 1)
    return {
        "mode": mode,
        "status": status,
        "backend": descriptor["backend"],
        "workload": descriptor["workload"],
        "representation": descriptor["representation"],
        "atom_count": atom_count,
        "full_dim": full_dim,
        "basis_size": basis_size,
        "repeats": repeats,
        "duration_s": duration_s,
        "total_time_s": total_time_s,
        "time_per_operation_s": per_operation,
        "max_rss": memory["max_rss"],
        "max_rss_unit": memory["max_rss_unit"],
        "reason": reason,
    }


def benchmark_ablation_modes(
    register: Register,
    sequence: PulseSequence,
    *,
    blockade_radius: float,
    repeats: int = 25,
    warmups: int = 2,
    seed: int = 1234,
    max_full_dim: int = 4096,
    include_gpu: bool = False,
    gpu_duration: float = 0.2,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Benchmark dense/sparse/reduced/GPU-cached Hamiltonian execution paths."""
    atom_count = len(register.atoms)
    full_dim = 2 ** atom_count
    omega = _constant_vector(sequence.omega, atom_count, field_name="omega")
    delta = _constant_vector(sequence.delta, atom_count, field_name="delta")
    basis = _reduced_basis_python(register, float(blockade_radius))
    basis_size = len(basis)
    rows: List[Dict[str, Any]] = []
    run_manifests: List[Dict[str, Any]] = []

    if full_dim <= max_full_dim:
        full_state = _seeded_state(full_dim, seed)
        full_dense = _dense_hamiltonian_matrix(register, omega, delta)
        elapsed, _ = _time_repeated_matvec(full_dense, full_state, repeats, warmups)
        rows.append(_row(mode="full_dense", status="ok", atom_count=atom_count, full_dim=full_dim, basis_size=full_dim, repeats=repeats, total_time_s=elapsed))

        full_sparse = csr_matrix(full_dense)
        elapsed, _ = _time_repeated_matvec(full_sparse, full_state, repeats, warmups)
        rows.append(_row(mode="full_sparse", status="ok", atom_count=atom_count, full_dim=full_dim, basis_size=full_dim, repeats=repeats, total_time_s=elapsed))
    else:
        reason = f"full_dim {full_dim} exceeds max_full_dim {max_full_dim}"
        rows.append(_row(mode="full_dense", status="skipped", atom_count=atom_count, full_dim=full_dim, basis_size=full_dim, repeats=repeats, reason=reason))
        rows.append(_row(mode="full_sparse", status="skipped", atom_count=atom_count, full_dim=full_dim, basis_size=full_dim, repeats=repeats, reason=reason))

    reduced_state = _seeded_state(basis_size, seed)
    reduced_matrix_free = _reduced_matrix_free_callable(register, omega, delta, basis)
    elapsed, matrix_free_result = _time_repeated_matvec(reduced_matrix_free, reduced_state, repeats, warmups)
    rows.append(_row(mode="reduced_matrix_free", status="ok", atom_count=atom_count, full_dim=full_dim, basis_size=basis_size, repeats=repeats, total_time_s=elapsed))

    reduced_sparse = csr_matrix(_reduced_hamiltonian_matrix(register, omega, delta, basis))
    elapsed, sparse_result = _time_repeated_matvec(reduced_sparse, reduced_state, repeats, warmups)
    rows.append(_row(mode="reduced_sparse", status="ok", atom_count=atom_count, full_dim=full_dim, basis_size=basis_size, repeats=repeats, total_time_s=elapsed))

    reference_error = float(np.max(np.abs(matrix_free_result - sparse_result))) if basis_size else 0.0
    rows[-2]["reference_error"] = reference_error
    rows[-1]["reference_error"] = reference_error

    if include_gpu:
        psi0 = np.zeros(basis_size, dtype=np.complex128)
        psi0[0] = 1.0
        config = SolverConfig(blockade_radius=float(blockade_radius), use_gpu=True, gpu_backend="CUDA")
        sim = Simulation(register, sequence, config)
        try:
            start = time.perf_counter()
            result = sim.run(psi0, 0.0, float(gpu_duration), observables={"pop0": 0})
            elapsed = time.perf_counter() - start
            rows.append(_row(mode="reduced_sparse_gpu_cached", status="ok", atom_count=atom_count, full_dim=full_dim, basis_size=basis_size, repeats=1, total_time_s=elapsed, duration_s=float(gpu_duration)))
            run_manifests.append({"label": "reduced_sparse_gpu_cached", "manifest": result.manifest})
        except SagittariusSolverError as exc:
            rows.append(_row(mode="reduced_sparse_gpu_cached", status="skipped", atom_count=atom_count, full_dim=full_dim, basis_size=basis_size, repeats=1, reason=exc.issue.code, duration_s=float(gpu_duration)))
    else:
        rows.append(_row(mode="reduced_sparse_gpu_cached", status="skipped", atom_count=atom_count, full_dim=full_dim, basis_size=basis_size, repeats=1, reason="set include_gpu=True and provide a working CUDA backend", duration_s=float(gpu_duration)))

    return rows, run_manifests
