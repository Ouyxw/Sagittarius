"""Independent formula, campaign and saved-output contracts for P1 observables."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import numpy as np
import pytest
from sagittarius import SolverConfig
from sagittarius.observable_benchmark import (SIZES, ORDERS, SEEDS, _scenario, basis, benchmark_observables,
    catalog, declarations, make_row, occupation_values, record_plan, reference, scenarios)
SPEC = importlib.util.spec_from_file_location("audit_observable_campaign", Path(__file__).resolve().parents[2] / "scripts/audit_observable_campaign.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
CFG = {"warmups": 2, "repeat_count": 5, "accuracy_atol": 1e-8, "reference_stability_atol": 1e-10,
       "stochastic_alpha": 1e-6, "timeout_seconds": 900., "memory_limit_bytes": 4096 * 1024**2}


def test_frozen_matrix_axes_and_duplicate_labels():
    matrix = scenarios()
    assert len(matrix) == len({s["scenario_id"] for s in matrix}) == 64
    costs = scenarios("performance")
    assert len(costs) == 52
    for n in SIZES:
        group = [s for s in costs if s["N"] == n and s["collection"] == "mixed"]
        assert {s["count"] for s in group} == {1, 4, 16, 64}
        assert {s["output_count"] for s in group} == {21, 101, 501}
        assert {s["order"] for s in group} == set(ORDERS)
    assert {s["collection"] for s in costs if s["collection"] != "mixed"} == {d["type"] for d in catalog(4)}
    assert basis(_scenario(20)) == [v for v in range(2**20) if not (v & (v << 1))]
    assert _scenario(20)["basis_size"] == 17711
    for s in matrix:
        SolverConfig(**s["solver"])
        assert s["estimated_peak_bytes"] < CFG["memory_limit_bytes"]
        assert len({d["name"] for d in s["declarations"]}) == s["count"]
        if s["count"] == 64:
            assert s["duplicate_outputs"] == 54
            assert "no additional physical information" in s["collection_label"]


def test_catalog_formulas_on_excited_bitstring_and_probability_distribution():
    bits = np.arange(8)
    p = np.zeros(8); p[5] = 1
    expected = [1., 2., 1., 0., 1., 1., -2., -1., 1., 1.]
    for d, value in zip(catalog(3), expected):
        assert occupation_values(p, bits, d)[0] == pytest.approx(value)
    p = np.arange(1., 9.) / 36
    d = catalog(3)
    assert occupation_values(p, bits, d[0])[0] == pytest.approx(20 / 36)
    assert occupation_values(p, bits, d[2])[0] == pytest.approx(14 / 36)
    assert occupation_values(p, bits, d[3])[0] == pytest.approx(14 / 36 - (20 / 36) * (26 / 36))
    # Density-matrix diagonal and pure-state probabilities use the same contract.
    psi = np.sqrt(p) * np.exp(1j * np.arange(8))
    rho = np.outer(psi, psi.conj())
    for declaration in d:
        np.testing.assert_allclose(occupation_values(np.diag(rho).real, bits, declaration), occupation_values(p, bits, declaration), atol=1e-15)


@pytest.mark.parametrize("fixture", ["ground", "excited", "distribution", "evolving", "lindblad", "mcwf"])
def test_references_and_mcwf_nonlinear_semantics(fixture):
    s = _scenario(3, kind="correctness", fixture=fixture, count=10, grid=21)
    ref, description = reference(s)
    assert description["stable"] and description["stability_error"] <= 1e-10
    np.testing.assert_allclose(ref["norm"], 1., atol=1e-12)
    if fixture == "mcwf":
        np.testing.assert_array_equal(ref["values"][3], np.zeros(21))
        assert ref["range_widths"][3] == 0
        assert len(record_plan(s, CFG)) == len(ORDERS) * len(SEEDS)
        assert ref["values"][5, -1] == pytest.approx(np.exp(-.4 * s["duration"])**2)


def test_extended_reference_has_independent_numerical_control():
    s = _scenario(12, grid=21)
    _, meta = reference(s)
    assert "DOP853" in meta["control"] and meta["stability_error"] < 1e-10


def completed_state(s):
    return {"complete": True, "records": [{"row_id": f"test-{p}-{i}", "phase": p, "repeat_index": i, "order": order, "seed": seed,
        "eligible": True, "runtime_seconds": float(i + 1), "gate": {"max_abs_error": 0., "value_passed": True, "order_passed": True}}
        for p, i, order, seed in record_plan(s, CFG)]}


def test_statistics_and_correctness_only_boundaries():
    s = _scenario(4)
    state = completed_state(s)
    state["records"][-1]["runtime_seconds"] = 100.
    row = make_row(s, CFG, state, {})
    assert row["status"] == "passed" and row["eligible"] == 5 and row["max_s"] == 100. and row["median_s"] == 3.
    state["records"][-1]["eligible"] = False
    state["records"][-1]["gate"]["value_passed"] = False
    row = make_row(s, CFG, state, {})
    assert row["status"] == "failed" and row["eligible"] == 4 and row["max_s"] == 4.
    assert row["metrics"]["state"]["records"][-1]["runtime_seconds"] == 100.
    small = _scenario(3, kind="correctness", fixture="ground", count=10, grid=21)
    row = make_row(small, CFG, completed_state(small), {})
    assert row["metrics"]["statistics"] is None and row["median_s"] is None


@pytest.mark.parametrize("reason,status", [("timeout", "incomplete"), ("interrupted", "incomplete"), ("memory", "failed"), ("unexpected", "failed")])
def test_supervision_retains_partial_measurements(reason, status):
    s = _scenario(4)
    row = make_row(s, CFG, completed_state(s), {"reason": reason})
    assert row["status"] == status and row["eligible"] == 5
    assert row["failure"]["limits"]["timeout_seconds"] == 900.


def test_resource_exclusions_are_auditable_and_do_not_replace_success(tmp_path):
    s = _scenario(4)
    paths = benchmark_observables(tmp_path, tier="performance", scenario_ids=[s["scenario_id"]], memory_limit_mb=1)
    assert paths["artifact"]["timings"][0]["status"] == "skipped"
    assert AUDIT.audit(tmp_path)["checked_results"] == 0
    with pytest.raises(FileExistsError): benchmark_observables(tmp_path)
    assert make_row(s, {**CFG, "warmups": 0}, completed_state(s), {})["status"] == "incomplete"


@pytest.mark.parametrize("options", [{"warmups": True}, {"repeat_count": 0}, {"memory_limit_mb": -1}, {"accuracy_atol": float("nan")},
    {"scenario_ids": []}, {"scenario_ids": ["unknown"]}, {"tier": "invalid"}, {"stochastic_alpha": 1.}])
def test_invalid_options_rejected_before_backend_or_output(tmp_path, options):
    with pytest.raises(ValueError): benchmark_observables(tmp_path / "new", **options)
    assert not (tmp_path / "new").exists()


@pytest.mark.requires_julia_backend
def test_real_cost_roundtrips_statistics_and_corruption(tmp_path):
    scenario = _scenario(4, count=64, grid=501, order="permuted")["scenario_id"]
    paths = benchmark_observables(tmp_path, scenario_ids=[scenario])
    row = paths["artifact"]["timings"][0]
    assert row["status"] == "passed", row["failure"]
    report = AUDIT.audit(tmp_path)
    assert report["checked_results"] == 8 and report["eligible_measured_count"] == 5
    import sagittarius.runtime as runtime
    original = runtime.get_julia
    try:
        runtime.get_julia = lambda: (_ for _ in ()).throw(AssertionError("audit initialized Julia"))
        assert AUDIT.audit(tmp_path) == report
    finally: runtime.get_julia = original
    for name, mutate, match in [
        ("observable_performance.csv", lambda text: text.replace("passed", "failed", 1), "CSV mismatch"),
        ("observable_performance.md", lambda text: text + "bad", "Markdown mismatch"),
        (f"{scenario}/measured-0.manifest.json", lambda text: text.replace('"method": "Tsit5"', '"method": "RK4"'), "Standalone manifest"),
    ]:
        path = tmp_path / name; before = path.read_text(); path.write_text(mutate(before))
        with pytest.raises((ValueError, AssertionError), match=match): AUDIT.audit(tmp_path)
        path.write_text(before)
    path = tmp_path / scenario / "measured-0.result.json"
    before = path.read_text(); data = json.loads(before)
    data["manifest"]["solver"]["observables"] = dict(reversed(list(data["manifest"]["solver"]["observables"].items())))
    path.write_text(json.dumps(data))
    with pytest.raises((ValueError, AssertionError), match="order mismatch"): AUDIT.audit(tmp_path)
    path.write_text(before)
    path = tmp_path / "source/sagittarius_py/sagittarius/observable_benchmark.py"
    path.write_text(path.read_text() + "\n# corrupted\n")
    with pytest.raises(ValueError, match="source hash"): AUDIT.audit(tmp_path)


@pytest.mark.requires_julia_backend
def test_real_lindblad_reference_and_all_order_controls(tmp_path):
    s = _scenario(3, kind="correctness", fixture="lindblad", count=10, grid=21, reduced=False)
    paths = benchmark_observables(tmp_path, scenario_ids=[s["scenario_id"]])
    row = paths["artifact"]["timings"][0]
    assert row["status"] == "passed", row["failure"]
    report = AUDIT.audit(tmp_path)
    assert report["deterministic_results"] == 3 and report["cross_order_pairs"] == 2
