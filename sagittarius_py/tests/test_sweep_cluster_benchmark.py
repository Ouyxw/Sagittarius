"""Acceptance coverage for Phase 16 ParallelSimulation sweep evidence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from sagittarius import load_sweep_artifact, make_sweep_artifact, save_sweep_artifact


RUNNER_PATH = Path(__file__).parent / "test_performance" / "benchmark_sweep_cluster.py"
SPEC = importlib.util.spec_from_file_location("benchmark_sweep_cluster", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)

pytestmark = pytest.mark.requires_julia_backend


def test_parallel_sweep_runner_retains_aggregate_and_resumes_failed_item(tmp_path):
    paths = RUNNER.benchmark_sweep_cluster(tmp_path, worker_counts=(1,), values=(0.1, 0.2))
    artifact = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    row = artifact["timings"][0]
    sweep = load_sweep_artifact(row["artifacts"]["sweep_artifact"])

    assert row["status"] == "passed"
    assert row["metrics"]["completed_count"] == 2
    assert row["metrics"]["max_abs_error"] <= 1e-12
    assert all(item["status"] == "succeeded" for item in sweep["items"])

    failed_items = [dict(item) for item in sweep["items"]]
    failed_items[0].update({"status": "failed", "attempts": 1, "result_path": None, "manifest_path": None, "failure": {"code": "SYNTHETIC_INTERRUPTION", "message": "resume test", "remediation": "retry"}})
    failed = make_sweep_artifact(axes=sweep["axes"], items=failed_items, base_config=sweep["base_config"])
    failed_path = tmp_path / "failed-sweep.json"
    save_sweep_artifact(failed, failed_path)

    resumed = RUNNER.benchmark_sweep_cluster(tmp_path / "resume", worker_counts=(1,), resume_from=failed_path)
    resumed_row = json.loads(Path(resumed["json"]).read_text(encoding="utf-8"))["timings"][0]
    resumed_sweep = load_sweep_artifact(resumed_row["artifacts"]["sweep_artifact"])
    assert resumed_row["status"] == "passed"
    assert resumed_row["metrics"]["resumed_item_count"] == 1
    assert all(item["status"] == "succeeded" for item in resumed_sweep["items"])
    assert resumed_sweep["items"][0]["attempts"] == 2
