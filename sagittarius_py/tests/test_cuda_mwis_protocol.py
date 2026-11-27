"""CPU-only contract coverage for the opt-in CUDA/MWIS protocol."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


RUNNER_PATH = Path(__file__).parent / "test_performance" / "benchmark_cuda_mwis_protocol.py"
SPEC = importlib.util.spec_from_file_location("benchmark_cuda_mwis_protocol", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)


def _row(paths, family):
    key = "parity" if family == "backend_performance" else "mwis"
    artifact = json.loads(Path(paths[key]["json"]).read_text(encoding="utf-8"))
    suite = json.loads(Path(paths[key]["suite"]["json"]).read_text(encoding="utf-8"))
    assert suite["summary"]["total_rows"] == 1
    return artifact["timings"][0]


def test_cuda_protocol_normalizes_juliacall_style_device_mappings():
    class JuliaLikeDict:
        def items(self):
            return (("name", "test GPU"), ("nested", JuliaLikeDictLeaf()))

    class JuliaLikeDictLeaf:
        def items(self):
            return (("index", 0),)

    assert RUNNER._json_native(JuliaLikeDict()) == {
        "name": "test GPU",
        "nested": {"index": 0},
    }


def test_cuda_protocol_is_opt_in_and_retains_skipped_rows(tmp_path, monkeypatch):
    monkeypatch.delenv("SAGITTARIUS_ENABLE_GPU_TESTS", raising=False)
    calls = []

    def doctor_not_called(**kwargs):
        calls.append(kwargs)
        raise AssertionError("doctor must not run until CUDA opt-in is enabled")

    paths = RUNNER.benchmark_cuda_mwis_protocol(tmp_path, doctor_fn=doctor_not_called)

    assert calls == []
    for family in ("backend_performance", "optimization_aqc"):
        row = _row(paths, family)
        assert row["status"] == "skipped"
        assert row["failure"]["code"] == "BENCHMARK_GPU_OPT_IN_DISABLED"


def test_cuda_doctor_failure_is_preserved_for_both_families(tmp_path, monkeypatch):
    monkeypatch.setenv("SAGITTARIUS_ENABLE_GPU_TESTS", "1")
    report = {
        "available": False,
        "issues": ["GPU_DEVICE_NOT_FOUND"],
        "backend_probe": {"available": False, "runtime": {}, "versions": {}, "devices": []},
        "runtime": {"julia": {"version": "1.x"}},
        "gpu": {},
    }
    paths = RUNNER.benchmark_cuda_mwis_protocol(tmp_path, doctor_fn=lambda **kwargs: report)

    for family in ("backend_performance", "optimization_aqc"):
        row = _row(paths, family)
        assert row["status"] == "failed"
        assert row["failure"]["code"] == "BENCHMARK_CUDA_INITIALIZATION_FAILED"
        assert row["failure"]["backend_probe"]["issues"] == ["GPU_DEVICE_NOT_FOUND"]


@pytest.mark.requires_cuda_backend
def test_cuda_protocol_runs_real_parity_only_when_cuda_is_available(tmp_path, monkeypatch):
    monkeypatch.setenv("SAGITTARIUS_ENABLE_GPU_TESTS", "1")
    paths = RUNNER.benchmark_cuda_mwis_protocol(tmp_path)

    parity = _row(paths, "backend_performance")
    mwis = _row(paths, "optimization_aqc")
    assert parity["status"] == "passed"
    assert parity["metrics"]["parity_passed"] is True
    assert parity["metrics"]["cuda_cold_start_seconds"] >= 0.0
    assert parity["metrics"]["cuda_warm_seconds"] >= 0.0
    assert parity["backend"]["devices"]
    assert mwis["status"] == "passed"
    assert mwis["metrics"]["parity_passed"] is True
    assert mwis["metrics"]["cuda_feasible"] is True
    assert mwis["metrics"]["cuda_cold_start_seconds"] >= 0.0
    assert mwis["metrics"]["cuda_warm_seconds"] >= 0.0
