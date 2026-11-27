"""End-to-end suite-artifact coverage for the physics smoke runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from sagittarius import load_benchmark_suite_artifact

_PATH = Path(__file__).parent / "test_performance" / "benchmark_physics_smoke.py"
_SPEC = importlib.util.spec_from_file_location("benchmark_physics_smoke", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
_RUNNER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RUNNER)

pytestmark = pytest.mark.requires_julia_backend


def test_physics_smoke_runner_writes_a_valid_suite_artifact(tmp_path):
    paths = _RUNNER.benchmark_physics_smoke(tmp_path)
    suite = load_benchmark_suite_artifact(paths["suite"]["json"])

    assert suite["suite_id"] == "phase16-physics-baselines-smoke"
    assert suite["summary"]["total_rows"] == 2
    assert suite["summary"]["passed_count"] == 2
