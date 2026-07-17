"""Governed benchmark-artifact/v1 plotting entry points."""

import json
from pathlib import Path
from typing import Any, Mapping, Union

from matplotlib.axes import Axes

from sagittarius.benchmarking import (
    BENCHMARK_ARTIFACT_SCHEMA_VERSION,
    BENCHMARK_ARTIFACT_TYPE,
)
from sagittarius.viz.benchmark_perf import (
    plot_diagnostic_cpu_gpu_error_comparison,
    plot_diagnostic_memory_scaling,
    plot_diagnostic_runtime_scaling,
    plot_diagnostic_solver_comparison,
    plot_diagnostic_success_failure_summary,
)

BenchmarkArtifactInput = Union[Mapping[str, Any], str, Path]
_REQUIRED_ARTIFACT_FIELDS = {
    "schema_version",
    "artifact_type",
    "name",
    "parameters",
    "timings",
    "versions",
    "hardware",
    "diagnostics",
    "run_manifests",
    "artifacts",
}


def validate_benchmark_artifact(artifact: BenchmarkArtifactInput) -> dict[str, Any]:
    """Validate and normalize a governed ``benchmark-artifact/v1`` envelope."""
    if isinstance(artifact, (str, Path)):
        with Path(artifact).open("r", encoding="utf-8") as handle:
            artifact = json.load(handle)
    if not isinstance(artifact, Mapping):
        raise ValueError("Expected a benchmark-artifact/v1 mapping or JSON path.")

    missing = sorted(_REQUIRED_ARTIFACT_FIELDS - set(artifact))
    if missing:
        raise ValueError(
            "Benchmark artifact is missing required governance fields: "
            + ", ".join(missing)
        )
    if artifact["schema_version"] != BENCHMARK_ARTIFACT_SCHEMA_VERSION:
        raise ValueError(
            "Expected schema_version "
            f"{BENCHMARK_ARTIFACT_SCHEMA_VERSION!r}, got {artifact['schema_version']!r}."
        )
    if artifact["artifact_type"] != BENCHMARK_ARTIFACT_TYPE:
        raise ValueError(
            "Expected artifact_type "
            f"{BENCHMARK_ARTIFACT_TYPE!r}, got {artifact['artifact_type']!r}."
        )
    if not isinstance(artifact["timings"], list) or not artifact["timings"]:
        raise ValueError("Benchmark artifact timings must be a non-empty list of rows.")
    for field in ("parameters", "versions", "hardware", "diagnostics", "artifacts"):
        if not isinstance(artifact[field], Mapping):
            raise ValueError(f"Benchmark artifact field {field!r} must be a mapping.")
    if not isinstance(artifact["run_manifests"], list):
        raise ValueError("Benchmark artifact run_manifests must be a list.")
    if not all(isinstance(row, Mapping) for row in artifact["timings"]):
        raise ValueError("Benchmark artifact timings must contain mapping rows.")
    return dict(artifact)


def _rows(artifact: BenchmarkArtifactInput) -> list[dict[str, Any]]:
    validated = validate_benchmark_artifact(artifact)
    return [dict(row) for row in validated["timings"]]


def plot_runtime_scaling(artifact: BenchmarkArtifactInput, **kwargs: Any) -> Axes:
    """Plot runtime scaling from one validated ``benchmark-artifact/v1``."""
    return plot_diagnostic_runtime_scaling(_rows(artifact), **kwargs)


def plot_memory_scaling(artifact: BenchmarkArtifactInput, **kwargs: Any) -> Axes:
    """Plot memory scaling from one validated ``benchmark-artifact/v1``."""
    return plot_diagnostic_memory_scaling(_rows(artifact), **kwargs)


def plot_solver_comparison(artifact: BenchmarkArtifactInput, **kwargs: Any) -> Axes:
    """Plot solver comparison from one validated ``benchmark-artifact/v1``."""
    return plot_diagnostic_solver_comparison(_rows(artifact), **kwargs)


def plot_success_failure_summary(artifact: BenchmarkArtifactInput, **kwargs: Any) -> Axes:
    """Plot success and failure rows from one validated ``benchmark-artifact/v1``."""
    return plot_diagnostic_success_failure_summary(_rows(artifact), **kwargs)


def plot_cpu_gpu_error_comparison(
    cpu_artifact: BenchmarkArtifactInput,
    gpu_artifact: BenchmarkArtifactInput,
    **kwargs: Any,
) -> Axes:
    """Plot CPU/GPU errors from two validated ``benchmark-artifact/v1`` envelopes."""
    return plot_diagnostic_cpu_gpu_error_comparison(
        _rows(cpu_artifact), _rows(gpu_artifact), **kwargs
    )
