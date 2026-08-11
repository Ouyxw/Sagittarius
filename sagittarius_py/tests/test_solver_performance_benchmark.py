"""Acceptance coverage for Phase 16 solver/performance evidence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


RUNNER_PATH = Path(__file__).parent / "test_performance" / "benchmark_solver_performance.py"
SPEC = importlib.util.spec_from_file_location("benchmark_solver_performance", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)

pytestmark = pytest.mark.requires_julia_backend


def test_solver_performance_runner_retains_repeated_correctness_rows(tmp_path):
    paths = RUNNER.benchmark_solver_performance(tmp_path, repeat_count=1, ablation_repeats=2)
    artifact = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    suite = json.loads(Path(paths["suite"]["json"]).read_text(encoding="utf-8"))
    rows = artifact["timings"]

    by_scenario = {row["scenario_id"]: row for row in rows}
    assert suite["summary"]["total_rows"] == len(rows)
    for scenario_id in ("path-full_dense-repeat-0", "path-full_sparse-repeat-0", "path-reduced_matrix_free-repeat-0", "path-reduced_sparse-repeat-0"):
        row = by_scenario[scenario_id]
        assert row["metrics"]["reference_error"] <= row["metrics"]["reference_atol"]
    assert by_scenario["path-reduced_sparse_gpu_cached-repeat-0"]["status"] == "skipped"
    for method in ("tsit5", "vern9", "rk4"):
        row = by_scenario[f"solver-{method}-repeat-0"]
        assert row["status"] == "passed"
        assert row["metrics"]["max_abs_error"] <= row["metrics"]["reference_atol"]
        assert Path(row["artifacts"]["result_artifact"]).is_file()
        assert Path(row["artifacts"]["run_manifest"]).is_file()
