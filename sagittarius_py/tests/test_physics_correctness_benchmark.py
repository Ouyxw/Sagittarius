"""Acceptance coverage for the Phase 16 physics correctness runner."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from sagittarius import load_result, validate_run_manifest

_PATH = Path(__file__).parent / "test_performance" / "benchmark_physics_correctness.py"
_SPEC = importlib.util.spec_from_file_location("benchmark_physics_correctness", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
_RUNNER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RUNNER)

pytestmark = pytest.mark.requires_julia_backend


def test_physics_correctness_runner_retains_references_and_artifacts(tmp_path):
    paths = _RUNNER.benchmark_physics_correctness(tmp_path)
    rows = {row["scenario_id"]: row for row in json.loads(Path(paths["json"]).read_text(encoding="utf-8"))["timings"]}
    assert set(rows) == {"rabi_n1_cpu_seed_none", "blockade_n2_reduced_cpu_seed_none", "landau_zener_n1_cpu_seed_none", "small_chain_n3_dense_vs_reduced_cpu_seed_none"}
    assert all(row["status"] == "passed" and row["tier"] == "correctness" for row in rows.values())
    assert rows["rabi_n1_cpu_seed_none"]["metrics"]["max_abs_error"] <= 1e-6
    assert rows["blockade_n2_reduced_cpu_seed_none"]["metrics"]["max_double_excitation"] <= 1e-12
    assert rows["landau_zener_n1_cpu_seed_none"]["metrics"]["final_state_error"] <= 1.5e-2
    chain = rows["small_chain_n3_dense_vs_reduced_cpu_seed_none"]
    assert chain["metrics"]["max_hamiltonian_error"] <= 1e-10
    assert chain["metrics"]["max_state_error"] <= 1e-10
    assert Path(chain["artifacts"]["reference_report"]).is_file()
    for scenario_id in ("rabi_n1_cpu_seed_none", "blockade_n2_reduced_cpu_seed_none", "landau_zener_n1_cpu_seed_none"):
        artifacts = rows[scenario_id]["artifacts"]
        assert Path(artifacts["result_artifact"]).is_file()
        assert Path(artifacts["run_manifest"]).is_file()
        validate_run_manifest(load_result(artifacts["result_artifact"]).manifest)
