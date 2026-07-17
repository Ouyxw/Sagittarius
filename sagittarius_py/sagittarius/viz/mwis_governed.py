"""Governed MWIS benchmark figure export."""

from pathlib import Path
from typing import Any

from sagittarius.viz.benchmark_governed import (
    BenchmarkArtifactInput,
    validate_benchmark_artifact,
)
from sagittarius.viz.mwis_viz import save_diagnostic_mwis_figure


def save_mwis_benchmark_figure(
    fig: Any,
    output_path: str | Path,
    artifact: BenchmarkArtifactInput,
    *,
    dpi: int = 150,
    save_metadata_sidecar: bool = True,
) -> None:
    """Export an MWIS figure linked to a validated ``benchmark-artifact/v1``."""
    validated = validate_benchmark_artifact(artifact)
    sidecar = {
        "schema_version": validated["schema_version"],
        "artifact_type": validated["artifact_type"],
        "source_benchmark_artifact": validated,
    }
    save_diagnostic_mwis_figure(
        fig,
        str(output_path),
        sidecar,
        dpi=dpi,
        save_metadata_sidecar=save_metadata_sidecar,
    )
