"""Contract and saved-evidence acceptance for the bounded P1 solver matrix."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np
import pytest
from sagittarius import SolverConfig
from sagittarius.solver_benchmark import (benchmark_solver_sensitivity, independent_basis,
    independent_hamiltonian, make_row, phases, scenarios, stable_reference)

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("audit_solver_campaign", ROOT / "scripts/audit_solver_campaign.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
CFG = {"warmups": 2, "repeat_count": 5, "accuracy_atol": 1e-6, "reference_stability_atol": 1e-9,
       "timeout_seconds": 600., "memory_limit_bytes": 4096 * 1024**2}


def test_matrix_is_one_axis_scans_with_explicit_combined_controls():
    matrix = scenarios()
    assert len(matrix) == len({s["scenario_id"] for s in matrix}) == 39
    for fixture in ("rabi", "addressed", "ramp"):
        group = [s for s in matrix if s["fixture"] == fixture]
        assert len(group) == 13
        for method in ("Tsit5", "Vern9"):
            adaptive = [s for s in group if s["solver"]["method"] == method and s["axis"] == "tolerance"]
            assert {(s["solver"]["reltol"], s["solver"]["abstol"]) for s in adaptive} == {(1e-6, 1e-8), (1e-8, 1e-10), (1e-10, 1e-12)}
        assert {s["duration"] / s["solver"]["dt"] for s in group if s["axis"] == "step"} == {100, 200, 400}
        assert {s["output_count"] for s in group} == {21, 101, 501}
        assert sum(s["axis"] == "combined" for s in group) == 2
    for s in matrix:
        SolverConfig(**s["solver"])
        assert s["solver"]["saveat"][0] == 0 and s["solver"]["saveat"][-1] == s["duration"]
        assert len(s["solver"]["saveat"]) == s["output_count"]
        assert s["basis_size"] == len(independent_basis(s))


@pytest.mark.parametrize("index", [0, 13, 26])
def test_independent_references_are_stable_and_normalized(index):
    ref = stable_reference(scenarios()[index], 1e-9)
    assert ref["stable"] and ref["stability_error"] < 1e-9
    np.testing.assert_allclose(ref["raw_norm"], 1., rtol=0, atol=1e-10)
    assert sum(ref["final_probabilities"]) == pytest.approx(1.)
    np.testing.assert_allclose(np.array(ref["z0"]) + 2 * np.array(ref["pop0"]), ref["raw_norm"], rtol=0, atol=1e-14)


def test_independent_hamiltonian_uses_lsb_pulses_and_finite_interactions():
    s = scenarios()[13]
    assert independent_basis(s) == [0, 1, 2, 4, 5]
    h = independent_hamiltonian(s, 0.)
    np.testing.assert_allclose(h, h.conj().T)
    np.testing.assert_allclose(h[:, 0], [0, .1, .15, .125, 0])
    assert h[4, 4] == pytest.approx(10.)
    ramp = scenarios()[26]
    assert not np.allclose(independent_hamiltonian(ramp, 0), independent_hamiltonian(ramp, 1))


def complete_state():
    return {"complete": True, "records": [{"row_id": f"test-{p}-{i}", "phase": p, "repeat_index": i,
            "runtime_seconds": float(i + 1), "eligible": True, "gate": {"max_abs_error": 0., "raw_norm_error": 0.}} for p, i in phases(CFG)]}


def test_summary_keeps_slow_valid_repeats_and_under_resolved_diagnostics():
    s, state = scenarios()[0], complete_state()
    state["records"][-1]["runtime_seconds"] = 100.
    row = make_row(s, CFG, state, {})
    assert row["status"] == "passed" and row["eligible"] == 5
    assert row["max_s"] == 100. and row["median_s"] == 3.
    state["records"][-1]["eligible"] = False
    state["records"][-1]["gate"]["max_abs_error"] = .01
    row = make_row(s, CFG, state, {})
    assert row["status"] == "failed" and row["eligible"] == 4
    assert row["metrics"]["state"]["records"][-1]["runtime_seconds"] == 100.
    assert row["max_s"] == 4. and row["max_abs_error"] == .01


@pytest.mark.parametrize("supervision,status", [({"reason": "timeout"}, "incomplete"), ({"reason": "interrupted"}, "incomplete"),
    ({"reason": "memory"}, "failed"), ({"returncode": 9}, "failed")])
def test_supervisor_failures_keep_partial_measurements(supervision, status):
    row = make_row(scenarios()[0], CFG, complete_state(), supervision)
    assert row["status"] == status and row["eligible"] == 5
    assert row["failure"]["limits"]["timeout_seconds"] == 600


def test_short_and_resource_excluded_runs_cannot_pass_acceptance(tmp_path):
    assert make_row(scenarios()[0], {**CFG, "warmups": 0}, complete_state(), {})["status"] == "incomplete"
    paths = benchmark_solver_sensitivity(tmp_path, scenario_ids=[scenarios()[0]["scenario_id"]], memory_limit_mb=1)
    assert paths["artifact"]["timings"][0]["status"] == "skipped"
    assert AUDIT.audit(tmp_path)["checked_results"] == 0
    assert not AUDIT.audit(tmp_path)["full_v2_matrix_passed"]
    with pytest.raises(FileExistsError):
        benchmark_solver_sensitivity(tmp_path)


@pytest.mark.parametrize("options", [{"warmups": True}, {"repeat_count": 0}, {"accuracy_atol": float("nan")},
    {"memory_limit_mb": -1}, {"scenario_ids": []}, {"scenario_ids": ["unknown"]}])
def test_invalid_options_rejected_before_backend_or_output(tmp_path, options):
    with pytest.raises(ValueError):
        benchmark_solver_sensitivity(tmp_path / "new", **options)
    assert not (tmp_path / "new").exists()


@pytest.mark.requires_julia_backend
def test_real_ramp_audit_and_corruption_detection(tmp_path):
    scenario = "ramp-vern9-tol10-g501"
    paths = benchmark_solver_sensitivity(tmp_path, scenario_ids=[scenario])
    row = paths["artifact"]["timings"][0]
    assert row["status"] == "passed", row["failure"]
    assert row["eligible"] == 5
    report = AUDIT.audit(tmp_path)
    assert report["contract_audit_passed"] and report["checked_results"] == 8
    assert not report["full_v2_matrix_passed"]
    import sagittarius.runtime as runtime
    original = runtime.get_julia
    try:
        runtime.get_julia = lambda: (_ for _ in ()).throw(AssertionError("audit initialized Julia"))
        assert AUDIT.audit(tmp_path) == report
    finally:
        runtime.get_julia = original
    for name, mutate, match in [
        ("solver_sensitivity.csv", lambda text: text.replace("Vern9", "Tsit5", 1), "CSV mismatch"),
        ("solver_sensitivity.md", lambda text: text + "corrupt", "Markdown mismatch"),
        (f"{scenario}/reference.json", lambda text: text.replace('"stable": true', '"stable": false'), "Reference companion mismatch"),
        (f"{scenario}/measured-0.manifest.json", lambda text: text.replace('"method": "Vern9"', '"method": "Tsit5"'), "standalone manifest differ"),
    ]:
        path = tmp_path / name
        original_text = path.read_text()
        path.write_text(mutate(original_text))
        with pytest.raises((ValueError, AssertionError), match=match):
            AUDIT.audit(tmp_path)
        path.write_text(original_text)
    path = tmp_path / "source/sagittarius_py/sagittarius/solver_benchmark.py"
    path.write_text(path.read_text() + "\n# corruption\n")
    with pytest.raises(ValueError, match="source hash"):
        AUDIT.audit(tmp_path)
