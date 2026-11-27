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
BENCHMARK_ROW_STATUSES = frozenset({"passed", "failed", "skipped", "incomplete"})
BENCHMARK_DISCLOSURE_STATUSES = frozenset({"local_only", "reviewable", "release_grade"})


def benchmark_failure_from_exception(
    exc: BaseException,
    *,
    stage: str,
    deterministic: bool = True,
) -> Dict[str, Any]:
    """Normalize an exception into a benchmark-row failure payload."""
    issue = getattr(exc, "issue", None)
    if issue is not None:
        code = getattr(issue, "code", type(exc).__name__)
        message = getattr(issue, "message", str(exc))
        remediation = getattr(
            issue,
            "remediation",
            "Inspect the linked diagnostics and retry after correcting the reported condition.",
        )
    else:
        code = type(exc).__name__
        message = str(exc) or type(exc).__name__
        remediation = "Inspect the linked diagnostics and retry after correcting the reported condition."
    return {
        "stage": stage,
        "exception_type": type(exc).__name__,
        "code": str(code),
        "message": str(message),
        "remediation": str(remediation),
        "deterministic": bool(deterministic),
    }


def make_benchmark_row(
    *,
    row_id: str,
    scenario_id: str,
    family: str,
    tier: str,
    status: str,
    stage: str,
    problem: Mapping[str, Any],
    solver: Mapping[str, Any],
    backend: Mapping[str, Any],
    observables: Mapping[str, Any],
    metrics: Optional[Mapping[str, Any]] = None,
    artifacts: Optional[Mapping[str, Any]] = None,
    failure: Optional[Mapping[str, Any]] = None,
    disclosure_status: str = "local_only",
) -> Dict[str, Any]:
    """Build one structured Phase 16 row inside ``benchmark-artifact/v1``.

    The existing artifact envelope remains the compatibility boundary. These
    optional row fields make a single scenario independently auditable while
    preserving legacy benchmark rows used by older scripts.
    """
    row = {
        "row_id": row_id,
        "scenario_id": scenario_id,
        "family": family,
        "tier": tier,
        "status": status,
        "stage": stage,
        "problem": dict(problem),
        "solver": dict(solver),
        "backend": dict(backend),
        "observables": dict(observables),
        "metrics": dict(metrics or {}),
        "artifacts": {
            "run_manifest": None,
            "result_artifact": None,
            **dict(artifacts or {}),
        },
        "failure": None if failure is None else dict(failure),
        "disclosure_status": disclosure_status,
    }
    validate_benchmark_row(row)
    return _json_compatible(row)


def validate_benchmark_row(row: Mapping[str, Any]) -> None:
    """Validate the optional structured-row profile for ``benchmark-artifact/v1``."""
    required = {
        "row_id", "scenario_id", "family", "tier", "status", "stage",
        "problem", "solver", "backend", "observables", "metrics",
        "artifacts", "failure", "disclosure_status",
    }
    missing = sorted(required - set(row))
    if missing:
        raise ValueError("Benchmark row is missing required fields: " + ", ".join(missing))
    for name in ("row_id", "scenario_id", "family", "tier", "stage"):
        if not isinstance(row[name], str) or not row[name]:
            raise ValueError(f"Benchmark row field {name!r} must be a non-empty string.")
    if row["status"] not in BENCHMARK_ROW_STATUSES:
        raise ValueError("Benchmark row status must be passed, failed, skipped, or incomplete.")
    if row["disclosure_status"] not in BENCHMARK_DISCLOSURE_STATUSES:
        raise ValueError("Benchmark row disclosure_status must be local_only, reviewable, or release_grade.")
    for name in ("problem", "solver", "backend", "observables", "metrics", "artifacts"):
        if not isinstance(row[name], Mapping):
            raise ValueError(f"Benchmark row field {name!r} must be a mapping.")
    if row["status"] == "passed":
        if row["failure"] is not None:
            raise ValueError("Passed benchmark rows must have failure=None.")
    else:
        if not isinstance(row["failure"], Mapping):
            raise ValueError("Non-passed benchmark rows require a structured failure mapping.")
        for name in ("stage", "code", "message", "remediation"):
            if not isinstance(row["failure"].get(name), str) or not row["failure"][name]:
                raise ValueError(f"Benchmark failure field {name!r} must be a non-empty string.")


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
    benchmark_context: Optional[Mapping[str, Any]] = None,
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
    if benchmark_context is not None:
        artifact["benchmark_context"] = dict(benchmark_context)
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
    benchmark_context: Optional[Mapping[str, Any]] = None,
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
        benchmark_context=benchmark_context,
    )
    json_file.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "json": str(json_file),
        "csv": str(csv_file),
        "markdown": str(markdown_file),
        "artifact": artifact,
    }
