from __future__ import annotations

import csv
import json
from datetime import datetime, timezone

try:
    import resource as _resource
except ModuleNotFoundError:  # pragma: no cover - exercised on Windows runners
    _resource = None
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .api import _json_compatible
from .runtime import doctor, version_info

BENCHMARK_ARTIFACT_SCHEMA_VERSION = "benchmark-artifact/v1"
BENCHMARK_ARTIFACT_TYPE = "sagittarius.benchmark"


def current_memory_usage() -> Dict[str, Any]:
    """Return process memory metadata in a platform-stable shape."""
    if _resource is None:
        return {
            "max_rss": None,
            "max_rss_unit": None,
            "available": False,
            "reason": "The Python resource module is unavailable on this platform.",
        }

    usage = _resource.getrusage(_resource.RUSAGE_SELF)
    # Linux reports ru_maxrss in KiB; macOS reports bytes. Keep the source unit
    # explicit because benchmark artifacts are compared across platforms.
    return {
        "max_rss": int(usage.ru_maxrss),
        "max_rss_unit": "KiB on Linux, bytes on macOS",
        "available": True,
    }


def make_benchmark_artifact(
    *,
    name: str,
    description: str,
    parameters: Mapping[str, Any],
    rows: Iterable[Mapping[str, Any]],
    backend: str = "CPU",
    diagnostics: Optional[Mapping[str, Any]] = None,
    run_manifests: Optional[Iterable[Mapping[str, Any]]] = None,
    markdown_table: Optional[str] = None,
    csv_path: Optional[str] = None,
    markdown_path: Optional[str] = None,
) -> Dict[str, Any]:
    rows_list = [dict(row) for row in rows]
    diagnostics_payload = dict(diagnostics) if diagnostics is not None else doctor(backend=backend, initialize_backend=False)
    versions_payload = version_info(initialize_backend=False)
    hardware = {
        "platform": versions_payload.get("platform"),
        "container": versions_payload.get("container"),
        "gpu": diagnostics_payload.get("gpu", {}),
        "backend_devices": (diagnostics_payload.get("backend_probe") or {}).get("devices", []),
    }
    artifact = {
        "schema_version": BENCHMARK_ARTIFACT_SCHEMA_VERSION,
        "artifact_type": BENCHMARK_ARTIFACT_TYPE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "description": description,
        "parameters": dict(parameters),
        "timings": rows_list,
        "memory": current_memory_usage(),
        "versions": versions_payload,
        "hardware": hardware,
        "diagnostics": diagnostics_payload,
        "run_manifests": list(run_manifests or []),
        "artifacts": {
            "csv": csv_path,
            "markdown": markdown_path,
        },
    }
    if markdown_table is not None:
        artifact["markdown_table"] = markdown_table
    return _json_compatible(artifact)


def markdown_table(rows: Iterable[Mapping[str, Any]], *, columns: Optional[List[str]] = None) -> str:
    rows_list = [dict(row) for row in rows]
    if columns is None:
        columns = []
        for row in rows_list:
            for key in row:
                if key not in columns:
                    columns.append(key)
    if not columns:
        return ""

    def fmt(value: Any) -> str:
        if isinstance(value, float):
            return f"{value:.6g}"
        return str(value)

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = ["| " + " | ".join(fmt(row.get(column, "")) for column in columns) + " |" for row in rows_list]
    return "\n".join([header, separator, *body])


def write_benchmark_artifacts(
    *,
    output_dir: str | Path,
    stem: str,
    name: str,
    description: str,
    parameters: Mapping[str, Any],
    rows: Iterable[Mapping[str, Any]],
    backend: str = "CPU",
    diagnostics: Optional[Mapping[str, Any]] = None,
    run_manifests: Optional[Iterable[Mapping[str, Any]]] = None,
    columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rows_list = [dict(row) for row in rows]
    csv_file = output_path / f"{stem}.csv"
    markdown_file = output_path / f"{stem}.md"
    json_file = output_path / f"{stem}.json"

    if columns is None:
        columns = []
        for row in rows_list:
            for key in row:
                if key not in columns:
                    columns.append(key)

    with csv_file.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows_list)

    table = markdown_table(rows_list, columns=columns)
    markdown_file.write_text(table + "\n", encoding="utf-8")

    artifact = make_benchmark_artifact(
        name=name,
        description=description,
        parameters=parameters,
        rows=rows_list,
        backend=backend,
        diagnostics=diagnostics,
        run_manifests=run_manifests,
        markdown_table=table,
        csv_path=str(csv_file),
        markdown_path=str(markdown_file),
    )
    json_file.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "json": str(json_file),
        "csv": str(csv_file),
        "markdown": str(markdown_file),
        "artifact": artifact,
    }
