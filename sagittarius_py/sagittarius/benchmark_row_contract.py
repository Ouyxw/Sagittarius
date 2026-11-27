"""Compatibility adapter from legacy benchmark measurements to Phase 16 rows."""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from .benchmarking import make_benchmark_row


def structured_benchmark_rows(
    rows: Iterable[Mapping[str, Any]], *, family: str, tier: str,
    problem_defaults: Mapping[str, Any], solver_defaults: Mapping[str, Any],
    backend_defaults: Mapping[str, Any], observables: Mapping[str, Any],
    disclosure_status: str = "local_only",
) -> list[dict[str, Any]]:
    """Return validated rows while retaining legacy flat measurement columns."""
    output: list[dict[str, Any]] = []
    for index, legacy in enumerate(rows):
        legacy = dict(legacy)
        execution_status = str(legacy.get("status", "ok"))
        status = {"ok": "passed", "passed": "passed", "skipped": "skipped", "failed": "failed", "incomplete": "incomplete"}.get(execution_status, "incomplete")
        scenario_id = str(legacy.get("scenario_id") or legacy.get("mode") or legacy.get("N") or legacy.get("workers") or index)
        failure = None if status == "passed" else {
            "stage": "setup" if status == "skipped" else "validation",
            "code": "BENCHMARK_CASE_" + status.upper(),
            "message": str(legacy.get("reason") or f"Legacy benchmark case recorded as {status}."),
            "remediation": "Inspect the retained row fields and backend diagnostics before retrying.",
        }
        problem = dict(problem_defaults)
        for key in ("N", "atom_count", "basis_size", "full_dim", "workers", "parameter_count"):
            if key in legacy:
                problem[key] = legacy[key]
        metrics = {key: value for key, value in legacy.items() if key not in {"status", "backend", "reason", "mode", "scenario_id"}}
        row = make_benchmark_row(
            row_id=f"{family}-{tier}-{scenario_id}", scenario_id=f"{family}-{scenario_id}",
            family=family, tier=tier, status=status,
            stage="artifact" if status == "passed" else "setup",
            problem=problem, solver=solver_defaults, backend=backend_defaults,
            observables=observables, metrics=metrics, failure=failure,
            disclosure_status=disclosure_status,
        )
        for key, value in legacy.items():
            if key not in {"status", "backend"}:
                row[key] = value
        row["execution_status"] = execution_status
        if "backend" in legacy:
            row["execution_backend"] = legacy["backend"]
        output.append(row)
    return output
