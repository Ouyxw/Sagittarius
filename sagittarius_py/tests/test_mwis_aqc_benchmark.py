"""Acceptance coverage for the Phase 16 MWIS/UDG benchmark family."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


RUNNER_PATH = Path(__file__).parent / "test_performance" / "benchmark_mwis_aqc.py"
SPEC = importlib.util.spec_from_file_location("benchmark_mwis_aqc", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)

pytestmark = pytest.mark.requires_julia_backend


class FailingSolver:
    def __init__(self, graph, blockade_radius=1.0):
        self.graph = graph

    def solve_full(self, config=None, duration=1.0):
        raise RuntimeError("intentional AQC execution failure")


def test_mwis_aqc_family_emits_seeded_exact_reference_rows(tmp_path):
    paths_by_tier = RUNNER.benchmark_mwis_aqc(tmp_path)

    for tier, paths in paths_by_tier.items():
        artifact = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
        suite = json.loads(Path(paths["suite"]["json"]).read_text(encoding="utf-8"))
        rows = artifact["timings"]
        assert rows
        assert suite["summary"]["passed_count"] == len(rows)
        assert all(row["status"] == "passed" for row in rows)
        assert all(row["tier"] == tier and row["family"] == "optimization_aqc" for row in rows)
        assert all(row["problem"]["instance_seed"] is not None for row in rows)
        assert all(row["problem"]["graph_sha256"] for row in rows)
        assert all(isinstance(row["problem"]["edge_list"], list) for row in rows)
        assert all(len(row["problem"]["node_weights"]) == row["problem"]["atom_count"] for row in rows)
        assert all(row["solver"]["schedule"]["duration"] > 0 for row in rows)
        assert all(row["metrics"]["ilp_status"] == "Optimal" for row in rows)
        assert all(row["metrics"]["feasible"] is True for row in rows)
        assert all(row["metrics"]["objective_gap"] >= 0.0 for row in rows)
        assert all(0.0 <= row["metrics"]["approximation_ratio"] <= 1.0 for row in rows)
        assert all(0.0 <= row["metrics"]["optimal_success_probability"] <= 1.0 for row in rows)
        assert all(Path(row["artifacts"]["reference_report"]).is_file() for row in rows)

    scaling = json.loads(Path(paths_by_tier["scaling"]["json"]).read_text(encoding="utf-8"))["timings"]
    assert [row["problem"]["atom_count"] for row in scaling] == [2, 4, 6]


def test_mwis_aqc_tier_retains_solver_failure_row(tmp_path):
    paths = RUNNER.benchmark_mwis_aqc_tier("smoke", tmp_path, solver_factory=FailingSolver)
    row = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))["timings"][0]

    assert row["status"] == "failed"
    assert row["failure"]["stage"] == "solve"
    assert row["failure"]["code"] == "BENCHMARK_EXECUTION_FAILED"
    assert Path(row["artifacts"]["reference_report"]).is_file()
