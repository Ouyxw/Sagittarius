"""Phase 16 aggregate benchmark-suite artifact helpers.

The suite envelope aggregates fully structured ``benchmark-artifact/v1``
rows. It deliberately does not replace that single-scenario compatibility
contract.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from .api import _json_compatible
from .benchmarking import BENCHMARK_ROW_STATUSES, validate_benchmark_row
from .runtime import version_info

BENCHMARK_SUITE_ARTIFACT_SCHEMA_VERSION = "benchmark-suite-artifact/v1"
BENCHMARK_SUITE_ARTIFACT_TYPE = "benchmark.suite"
BENCHMARK_SUITE_PROTOCOL_VERSION = "benchmark-protocol/v1"
BENCHMARK_SUITE_STAGES = frozenset(
    {"setup", "reference", "solve", "validation", "artifact", "reporting", "teardown"}
)

_REQUIRED_SUITE_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_type",
        "suite_id",
        "family",
        "tier",
        "protocol_version",
        "generated_at",
        "source",
        "environment",
        "scenario_defaults",
        "rows",
        "summary",
        "diagnostics",
    }
)


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Benchmark suite field {field!r} must be a non-empty string.")
    return value


def _validate_suite_row(row: Mapping[str, Any], *, family: str, tier: str) -> dict[str, Any]:
    validate_benchmark_row(row)
    if row["stage"] not in BENCHMARK_SUITE_STAGES:
        allowed = ", ".join(sorted(BENCHMARK_SUITE_STAGES))
        raise ValueError(f"Benchmark suite row stage must be one of: {allowed}.")
    if row["family"] != family:
        raise ValueError("Benchmark suite rows must use the suite family.")
    if row["tier"] != tier:
        raise ValueError("Benchmark suite rows must use the suite tier.")
    return dict(row)


def summarize_benchmark_suite_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return stable status totals without dropping unsuccessful cases."""
    rows_list = list(rows)
    counts = {status: 0 for status in sorted(BENCHMARK_ROW_STATUSES)}
    for row in rows_list:
        counts[row["status"]] += 1
    completed = counts["passed"] + counts["failed"]
    return {
        "total_rows": len(rows_list),
        "status_counts": counts,
        "passed_count": counts["passed"],
        "failed_count": counts["failed"],
        "skipped_count": counts["skipped"],
        "incomplete_count": counts["incomplete"],
        "completed_count": completed,
        "pass_rate_completed": counts["passed"] / completed if completed else None,
    }


def make_benchmark_suite_artifact(
    *,
    suite_id: str,
    family: str,
    tier: str,
    rows: Iterable[Mapping[str, Any]],
    source: Optional[Mapping[str, Any]] = None,
    environment: Optional[Mapping[str, Any]] = None,
    scenario_defaults: Optional[Mapping[str, Any]] = None,
    diagnostics: Optional[Iterable[Mapping[str, Any]]] = None,
    protocol_version: str = BENCHMARK_SUITE_PROTOCOL_VERSION,
    generated_at: Optional[str] = None,
) -> dict[str, Any]:
    """Build and validate one family/tier aggregate artifact.

    Every expected scenario must appear as a row, including failures, skips,
    and incomplete work. Duplicate row IDs are rejected because they make
    scale-limit and success summaries ambiguous.
    """
    suite_id = _require_nonempty_string(suite_id, "suite_id")
    family = _require_nonempty_string(family, "family")
    tier = _require_nonempty_string(tier, "tier")
    protocol_version = _require_nonempty_string(protocol_version, "protocol_version")
    rows_list = [_validate_suite_row(row, family=family, tier=tier) for row in rows]
    row_ids = [row["row_id"] for row in rows_list]
    if len(row_ids) != len(set(row_ids)):
        raise ValueError("Benchmark suite rows must have unique row_id values.")
    artifact = {
        "schema_version": BENCHMARK_SUITE_ARTIFACT_SCHEMA_VERSION,
        "artifact_type": BENCHMARK_SUITE_ARTIFACT_TYPE,
        "suite_id": suite_id,
        "family": family,
        "tier": tier,
        "protocol_version": protocol_version,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "source": dict(source) if source is not None else version_info(initialize_backend=False),
        "environment": dict(environment or {}),
        "scenario_defaults": dict(scenario_defaults or {}),
        "rows": rows_list,
        "summary": summarize_benchmark_suite_rows(rows_list),
        "diagnostics": [dict(item) for item in diagnostics or []],
    }
    validate_benchmark_suite_artifact(artifact)
    return _json_compatible(artifact)


def validate_benchmark_suite_artifact(artifact: Mapping[str, Any]) -> None:
    """Validate an aggregate ``benchmark-suite-artifact/v1`` envelope."""
    if not isinstance(artifact, Mapping):
        raise ValueError("Benchmark suite artifact must be a mapping.")
    missing = sorted(_REQUIRED_SUITE_FIELDS - set(artifact))
    if missing:
        raise ValueError("Benchmark suite artifact is missing required fields: " + ", ".join(missing))
    if artifact["schema_version"] != BENCHMARK_SUITE_ARTIFACT_SCHEMA_VERSION:
        raise ValueError(
            "Expected benchmark suite schema_version "
            f"{BENCHMARK_SUITE_ARTIFACT_SCHEMA_VERSION!r}."
        )
    if artifact["artifact_type"] != BENCHMARK_SUITE_ARTIFACT_TYPE:
        raise ValueError(f"Expected benchmark suite artifact_type {BENCHMARK_SUITE_ARTIFACT_TYPE!r}.")
    for field in ("suite_id", "family", "tier", "protocol_version", "generated_at"):
        _require_nonempty_string(artifact[field], field)
    for field in ("source", "environment", "scenario_defaults", "summary"):
        if not isinstance(artifact[field], Mapping):
            raise ValueError(f"Benchmark suite field {field!r} must be a mapping.")
    if not isinstance(artifact["diagnostics"], list):
        raise ValueError("Benchmark suite diagnostics must be a list.")
    if not isinstance(artifact["rows"], list):
        raise ValueError("Benchmark suite rows must be a list.")
    rows = [
        _validate_suite_row(row, family=artifact["family"], tier=artifact["tier"])
        for row in artifact["rows"]
    ]
    if len({row["row_id"] for row in rows}) != len(rows):
        raise ValueError("Benchmark suite rows must have unique row_id values.")
    expected_summary = summarize_benchmark_suite_rows(rows)
    if dict(artifact["summary"]) != expected_summary:
        raise ValueError("Benchmark suite summary does not match its retained rows.")


def load_benchmark_suite_artifact(artifact: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    """Load and validate a suite artifact mapping or JSON path."""
    if isinstance(artifact, (str, Path)):
        with Path(artifact).open(encoding="utf-8") as handle:
            artifact = json.load(handle)
    validate_benchmark_suite_artifact(artifact)
    return dict(artifact)


def _csv_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    columns = ("row_id", "scenario_id", "family", "tier", "status", "stage", "disclosure_status")
    return [
        {
            **{column: str(row[column]) for column in columns},
            "problem": json.dumps(row["problem"], sort_keys=True),
            "solver": json.dumps(row["solver"], sort_keys=True),
            "backend": json.dumps(row["backend"], sort_keys=True),
            "observables": json.dumps(row["observables"], sort_keys=True),
            "metrics": json.dumps(row["metrics"], sort_keys=True),
            "artifacts": json.dumps(row["artifacts"], sort_keys=True),
            "failure": json.dumps(row["failure"], sort_keys=True),
        }
        for row in rows
    ]


def _markdown_summary(artifact: Mapping[str, Any]) -> str:
    summary = artifact["summary"]
    rows = [
        "# Benchmark Suite Summary",
        "",
        f"- Suite: `{artifact['suite_id']}`",
        f"- Family/tier: `{artifact['family']}` / `{artifact['tier']}`",
        f"- Total rows: {summary['total_rows']}",
        f"- Passed: {summary['passed_count']}; failed: {summary['failed_count']}; "
        f"skipped: {summary['skipped_count']}; incomplete: {summary['incomplete_count']}",
        "",
        "| Row ID | Scenario | Status | Stage |",
        "| --- | --- | --- | --- |",
    ]
    rows.extend(
        f"| {row['row_id']} | {row['scenario_id']} | {row['status']} | {row['stage']} |"
        for row in artifact["rows"]
    )
    return "\n".join(rows) + "\n"


def write_benchmark_suite_artifact(
    *,
    output_dir: str | Path,
    stem: str,
    suite_id: str,
    family: str,
    tier: str,
    rows: Iterable[Mapping[str, Any]],
    source: Optional[Mapping[str, Any]] = None,
    environment: Optional[Mapping[str, Any]] = None,
    scenario_defaults: Optional[Mapping[str, Any]] = None,
    diagnostics: Optional[Iterable[Mapping[str, Any]]] = None,
    protocol_version: str = BENCHMARK_SUITE_PROTOCOL_VERSION,
) -> dict[str, Any]:
    """Write JSON, flattened CSV, and Markdown companions for a suite run."""
    stem = _require_nonempty_string(stem, "stem")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    csv_file = output_path / f"{stem}.csv"
    markdown_file = output_path / f"{stem}.md"
    json_file = output_path / f"{stem}.json"
    artifact = make_benchmark_suite_artifact(
        suite_id=suite_id,
        family=family,
        tier=tier,
        rows=rows,
        source=source,
        environment=environment,
        scenario_defaults=scenario_defaults,
        diagnostics=diagnostics,
        protocol_version=protocol_version,
    )
    csv_rows = _csv_rows(artifact["rows"])
    with csv_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]) if csv_rows else ["row_id"])
        writer.writeheader()
        writer.writerows(csv_rows)
    markdown_file.write_text(_markdown_summary(artifact), encoding="utf-8")
    artifact["artifacts"] = {"json": str(json_file), "csv": str(csv_file), "markdown": str(markdown_file)}
    json_file.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"json": str(json_file), "csv": str(csv_file), "markdown": str(markdown_file), "artifact": artifact}
