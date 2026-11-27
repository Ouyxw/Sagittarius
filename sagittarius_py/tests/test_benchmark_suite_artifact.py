"""Contract coverage for ``benchmark-suite-artifact/v1``."""

from __future__ import annotations

import csv

import pytest

from sagittarius.benchmark_suite import (
    BENCHMARK_SUITE_ARTIFACT_SCHEMA_VERSION,
    load_benchmark_suite_artifact,
    make_benchmark_suite_artifact,
    validate_benchmark_suite_artifact,
    write_benchmark_suite_artifact,
)
from sagittarius.benchmarking import make_benchmark_row


def _row(status: str, *, row_id: str) -> dict:
    failure = None
    if status != "passed":
        failure = {
            "stage": "validation",
            "code": f"{status.upper()}_ROW",
            "message": f"{status} evidence retained",
            "remediation": "Inspect the retained context.",
        }
    return make_benchmark_row(
        row_id=row_id,
        scenario_id=f"scenario-{row_id}",
        family="physics_baselines",
        tier="correctness",
        status=status,
        stage="validation",
        problem={"atom_count": 2},
        solver={"method": "Tsit5"},
        backend={"requested_backend": "CPU"},
        observables={"names": [], "count": 0, "output_sample_count": 0},
        metrics={"max_abs_error": 0.0},
        failure=failure,
    )


def test_suite_artifact_retains_all_statuses_and_derives_summary():
    artifact = make_benchmark_suite_artifact(
        suite_id="phase16-physics-correctness",
        family="physics_baselines",
        tier="correctness",
        rows=[
            _row("passed", row_id="pass"),
            _row("failed", row_id="fail"),
            _row("skipped", row_id="skip"),
            _row("incomplete", row_id="incomplete"),
        ],
        source={"commit": "abc123"},
        environment={"backend": "CPU"},
    )

    assert artifact["schema_version"] == BENCHMARK_SUITE_ARTIFACT_SCHEMA_VERSION
    assert artifact["summary"] == {
        "total_rows": 4,
        "status_counts": {"failed": 1, "incomplete": 1, "passed": 1, "skipped": 1},
        "passed_count": 1,
        "failed_count": 1,
        "skipped_count": 1,
        "incomplete_count": 1,
        "completed_count": 2,
        "pass_rate_completed": 0.5,
    }
    validate_benchmark_suite_artifact(artifact)


def test_suite_rejects_cross_family_rows_and_summary_drift():
    row = _row("passed", row_id="one")
    row["family"] = "optimization_aqc"
    with pytest.raises(ValueError, match="suite family"):
        make_benchmark_suite_artifact(
            suite_id="wrong-family",
            family="physics_baselines",
            tier="correctness",
            rows=[row],
            source={},
        )

    artifact = make_benchmark_suite_artifact(
        suite_id="summary-drift",
        family="physics_baselines",
        tier="correctness",
        rows=[_row("passed", row_id="one")],
        source={},
    )
    artifact["summary"]["passed_count"] = 0
    with pytest.raises(ValueError, match="summary"):
        validate_benchmark_suite_artifact(artifact)


def test_suite_writer_and_reader_round_trip_with_companion_reports(tmp_path):
    paths = write_benchmark_suite_artifact(
        output_dir=tmp_path,
        stem="physics-correctness",
        suite_id="phase16-physics-correctness",
        family="physics_baselines",
        tier="correctness",
        rows=[_row("passed", row_id="pass"), _row("failed", row_id="fail")],
        source={"commit": "abc123"},
        environment={"backend": "CPU"},
    )

    loaded = load_benchmark_suite_artifact(paths["json"])
    assert loaded["summary"]["failed_count"] == 1
    assert paths["artifact"]["artifacts"]["csv"] == paths["csv"]
    with open(paths["csv"], newline="", encoding="utf-8") as handle:
        assert [row["status"] for row in csv.DictReader(handle)] == ["passed", "failed"]
    assert "Benchmark Suite Summary" in open(paths["markdown"], encoding="utf-8").read()
