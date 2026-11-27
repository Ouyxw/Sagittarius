"""First-class failure rows for governed benchmark evidence."""
from __future__ import annotations

from typing import Any, Mapping, Optional

from .benchmarking import current_memory_usage, make_benchmark_row


def classify_benchmark_failure(exc: BaseException) -> tuple[str, str]:
    """Map common benchmark failures to stable codes and remediation."""
    text = f"{type(exc).__name__}: {exc}".lower()
    if isinstance(exc, TimeoutError) or "timeout" in text or "timed out" in text:
        return "BENCHMARK_TIMEOUT", "Increase the documented timeout only after retaining this boundary row."
    if isinstance(exc, MemoryError) or "out of memory" in text or "oom" in text:
        return "BENCHMARK_MEMORY_EXHAUSTED", "Reduce the workload or increase the documented memory limit and retain this row."
    if "cuda" in text and ("initial" in text or "device" in text or "driver" in text or "unavailable" in text):
        return "BENCHMARK_CUDA_INITIALIZATION_FAILED", "Run doctor(backend='CUDA', initialize_backend=True) and retain its diagnostics."
    if isinstance(exc, AssertionError) or "reference" in text or "mismatch" in text:
        return "BENCHMARK_REFERENCE_MISMATCH", "Inspect the retained reference, tolerances, solver settings, and result artifacts."
    if "ilp" in text or "pulp" in text or "cbc" in text:
        return "BENCHMARK_ILP_FAILED", "Check the exact-solver installation and retain the solver status and instance metadata."
    return "BENCHMARK_EXECUTION_FAILED", "Inspect the retained exception and backend diagnostics before retrying."


def benchmark_failure_context(
    exc: BaseException,
    *,
    stage: str,
    timeout_seconds: Optional[float] = None,
    backend_probe: Optional[Mapping[str, Any]] = None,
    gpu_memory_peak_mb: Optional[float] = None,
) -> dict[str, Any]:
    """Capture serializable context for a failed benchmark case."""
    code, remediation = classify_benchmark_failure(exc)
    memory = current_memory_usage()
    return {
        "stage": stage,
        "exception_type": type(exc).__name__,
        "code": code,
        "message": str(exc) or type(exc).__name__,
        "remediation": remediation,
        "deterministic": True,
        "timeout_seconds": timeout_seconds,
        "process_memory": memory,
        "gpu_memory_peak_mb": gpu_memory_peak_mb,
        "backend_probe": dict(backend_probe or {}),
    }


def make_benchmark_failure_row(
    *,
    row_id: str,
    scenario_id: str,
    family: str,
    tier: str,
    stage: str,
    exc: BaseException,
    problem: Mapping[str, Any],
    solver: Mapping[str, Any],
    backend: Mapping[str, Any],
    observables: Mapping[str, Any],
    timeout_seconds: Optional[float] = None,
    backend_probe: Optional[Mapping[str, Any]] = None,
    gpu_memory_peak_mb: Optional[float] = None,
    disclosure_status: str = "local_only",
) -> dict[str, Any]:
    """Build a validated failed row without discarding the failed scenario."""
    failure = benchmark_failure_context(
        exc, stage=stage, timeout_seconds=timeout_seconds,
        backend_probe=backend_probe, gpu_memory_peak_mb=gpu_memory_peak_mb,
    )
    return make_benchmark_row(
        row_id=row_id, scenario_id=scenario_id, family=family, tier=tier,
        status="failed", stage=stage, problem=problem, solver=solver,
        backend=backend, observables=observables,
        metrics={"process_memory": failure["process_memory"], "gpu_memory_peak_mb": gpu_memory_peak_mb},
        failure=failure, disclosure_status=disclosure_status,
    )
