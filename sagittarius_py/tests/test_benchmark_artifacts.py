import csv
import json

import pytest

import sagittarius.benchmarking as benchmarking
from sagittarius import (
    BENCHMARK_ARTIFACT_SCHEMA_VERSION,
    BENCHMARK_ARTIFACT_TYPE,
    benchmark_failure_from_exception,
    make_benchmark_artifact,
    make_benchmark_row,
    markdown_table,
    validate_benchmark_row,
    write_benchmark_artifacts,
)


def test_make_benchmark_artifact_contains_reproducibility_metadata():
    artifact = make_benchmark_artifact(
        name="unit benchmark",
        description="metadata shape test",
        parameters={"N": 2, "duration": 0.1},
        rows=[{"N": 2, "time_s": 0.01, "max_rss": 123}],
        diagnostics={"requested_backend": "CPU", "available": True},
        run_manifests=[{"label": "case", "manifest": {"schema_version": "run-manifest/v1"}}],
    )

    assert artifact["schema_version"] == BENCHMARK_ARTIFACT_SCHEMA_VERSION
    assert artifact["artifact_type"] == BENCHMARK_ARTIFACT_TYPE
    assert artifact["parameters"] == {"N": 2, "duration": 0.1}
    assert artifact["timings"][0]["time_s"] == 0.01
    assert artifact["memory"]["max_rss"] >= 0
    assert artifact["versions"]["schema_version"] == "version-info/v1"
    assert "platform" in artifact["hardware"]
    assert artifact["diagnostics"]["requested_backend"] == "CPU"
    assert artifact["run_manifests"][0]["manifest"]["schema_version"] == "run-manifest/v1"


def test_current_memory_usage_handles_missing_resource_module(monkeypatch):
    monkeypatch.setattr(benchmarking, "_resource", None)

    memory = benchmarking.current_memory_usage()

    assert memory["max_rss"] is None
    assert memory["max_rss_unit"] is None
    assert memory["available"] is False
    assert "resource module" in memory["reason"]


def test_markdown_table_formats_rows():
    table = markdown_table([{"N": 2, "time_s": 0.012345678}], columns=["N", "time_s"])

    assert table.splitlines()[0] == "| N | time_s |"
    assert "| 2 | 0.0123457 |" in table


def test_structured_benchmark_row_retains_single_scenario_evidence():
    row = make_benchmark_row(
        row_id="physics-smoke-rabi",
        scenario_id="rabi_n1_cpu_seed_none",
        family="physics_baselines",
        tier="smoke",
        status="passed",
        stage="artifact",
        problem={"type": "single_atom_rabi", "seed": None},
        solver={"method": "Tsit5", "reltol": 1e-9},
        backend={"requested_backend": "CPU"},
        observables={"names": ["rydberg_population"], "count": 1, "output_sample_count": 3},
        metrics={"max_abs_error": 1e-9, "runtime_seconds": 0.1},
        artifacts={"run_manifest": "rabi.manifest.json", "result_artifact": "rabi.result.json"},
    )

    validate_benchmark_row(row)
    assert row["artifacts"]["run_manifest"] == "rabi.manifest.json"
    assert row["metrics"]["max_abs_error"] == 1e-9
    assert row["failure"] is None


def test_structured_benchmark_row_requires_a_failure_for_nonpassed_status():
    with pytest.raises(ValueError, match="structured failure"):
        make_benchmark_row(
            row_id="physics-smoke-failure",
            scenario_id="broken",
            family="physics_baselines",
            tier="smoke",
            status="failed",
            stage="solve",
            problem={},
            solver={},
            backend={},
            observables={},
        )

    failure = benchmark_failure_from_exception(ValueError("bad pulse"), stage="validation")
    assert failure["code"] == "ValueError"
    assert failure["stage"] == "validation"


def test_write_benchmark_artifacts_writes_json_csv_and_markdown(tmp_path):
    paths = write_benchmark_artifacts(
        output_dir=tmp_path,
        stem="bench",
        name="write test",
        description="writes all artifact views",
        parameters={"sweep": [1, 2]},
        rows=[{"N": 1, "time_s": 0.1}, {"N": 2, "time_s": 0.2}],
        diagnostics={"requested_backend": "CPU", "available": True},
        run_manifests=[{"label": "N=1", "manifest": {"schema_version": "run-manifest/v1"}}],
        columns=["N", "time_s"],
        benchmark_context={"protocol_version": "benchmark-protocol/v1", "tier": "smoke"},
    )

    with open(paths["json"], encoding="utf-8") as fh:
        payload = json.load(fh)
    assert payload["schema_version"] == BENCHMARK_ARTIFACT_SCHEMA_VERSION
    assert payload["artifacts"]["csv"] == paths["csv"]
    assert payload["artifacts"]["markdown"] == paths["markdown"]
    assert payload["markdown_table"].startswith("| N | time_s |")
    assert payload["benchmark_context"]["tier"] == "smoke"

    with open(paths["csv"], newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows == [{"N": "1", "time_s": "0.1"}, {"N": "2", "time_s": "0.2"}]

    with open(paths["markdown"], encoding="utf-8") as fh:
        assert "| 2 | 0.2 |" in fh.read()
