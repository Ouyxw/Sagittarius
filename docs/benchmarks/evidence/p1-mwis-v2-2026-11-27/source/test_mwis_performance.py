"""Frozen graph, exact-status, numerical-reference and retention acceptance."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from sagittarius import mwis_benchmark as mwis


def test_matrix_freezes_five_actual_graphs_per_size_and_hashes():
    selected = mwis.scenarios()
    assert len(selected) == 40
    assert [(s["N"], s["seed"]) for s in selected] == [(n, seed) for n in mwis.SIZES for seed in mwis.SEEDS]
    for s in selected:
        mwis.graph_from_scenario(s)
        assert s["graph_sha256"] == mwis.graph_hash(s)
        assert s["basis_size"] == len(mwis.independent_basis(s))
        assert 0 <= s["edge_density"] <= 1
    assert max(s["basis_size"] for s in selected if s["N"] == 20) == 53760
    changed = deepcopy(selected[0])
    changed["nodes"][0]["weight"] += .01
    with pytest.raises(AssertionError, match="hash"):
        mwis.graph_from_scenario(changed)
    for sizes in ([], [2, 2], [True], [21]):
        with pytest.raises(ValueError):
            mwis.scenarios(sizes)


def test_independent_dop853_matches_small_dense_time_dependent_reference():
    from scipy.integrate import solve_ivp
    from sagittarius import Atom, Register
    from sagittarius.api import _dense_hamiltonian_matrix
    s = mwis.scenarios([3], [101])[0]
    independent = mwis.independent_reference(s)
    basis = mwis.independent_basis(s)
    register = Register([Atom(*node["position"]) for node in s["nodes"]], C6=s["C6"])
    def derivative(t, state):
        fraction = t / s["duration"]
        omega = [s["omega_max"] * np.sin(np.pi * fraction)**2] * s["N"]
        delta = [-2 * s["omega_max"] * (1 - fraction) + 2 * np.pi * node["weight"] * fraction for node in s["nodes"]]
        full = _dense_hamiltonian_matrix(register, omega, delta)
        return -1j * (full[np.ix_(basis, basis)] @ state)
    initial = np.zeros(len(basis), dtype=complex)
    initial[0] = 1
    dense = solve_ivp(derivative, (0., s["duration"]), initial, method="DOP853", t_eval=independent["t"], rtol=1e-12, atol=1e-14)
    np.testing.assert_allclose(independent["probabilities"], np.abs(dense.y[:, -1])**2, rtol=1e-10, atol=1e-12)
    expected = np.sum(np.abs(dense.y[np.asarray(basis) & 1 != 0])**2, axis=0)
    np.testing.assert_allclose(independent["pop0"], expected, rtol=1e-10, atol=1e-12)


def _equal_weight_edge():
    s = mwis.scenarios([2], [101])[0]
    for node in s["nodes"]:
        node["weight"] = 1.
    s["graph_sha256"] = mwis.graph_hash(s)
    return s


def test_optimal_mass_includes_all_optima_and_poor_feasible_objective_is_valid():
    s = _equal_weight_edge()
    quality = mwis.quality_metrics(s, {"00": .5, "10": .2, "01": .3}, 1.)
    assert quality["feasible"] and quality["candidate_objective"] == 0
    assert quality["objective_gap"] == 1 and quality["approximation_ratio"] == 0
    assert quality["optimal_success_probability"] == .5
    unknown = mwis.quality_metrics(s, {"00": .5, "10": .2, "01": .3}, None)
    assert all(unknown[k] is None for k in ("objective_gap", "approximation_ratio", "optimal_success_probability"))
    infeasible = mwis.quality_metrics(s, {"00": .1, "10": .05, "01": .05, "11": .8}, 1.)
    assert not infeasible["feasible"] and infeasible["candidate_objective"] == 2
    assert infeasible["approximation_ratio"] is None


def test_pulp_optimal_problem_with_integer_incumbent_is_not_proven_optimal():
    import pulp
    s = _equal_weight_edge()
    variables = [SimpleNamespace(value=lambda v=v: v) for v in (1., 0.)]
    problem = SimpleNamespace(status=pulp.LpStatusOptimal, sol_status=pulp.LpSolutionIntegerFeasible)
    result = mwis.ilp_result(problem, variables, s, "Stopped on time limit\nUpper bound: 1.2\n")
    assert result["problem_status"] == "Optimal" and not result["proven_optimal"]
    assert result["exact_objective"] is None and result["incumbent_objective"] == 1
    assert result["best_bound"] == 1.2 and result["termination"] == "time_limit"
    problem.sol_status = pulp.LpSolutionOptimal
    assert mwis.ilp_result(problem, variables, s, "Result - Optimal solution found")["proven_optimal"]


def test_independent_path_statistics_do_not_pool_graphs_or_warmups():
    records = [{"row_id": f"repeat-{i}", "phase": "measured", "eligible": True, "runtime_seconds": t} for i, t in enumerate((1., 2., 3., 4., 100.))]
    records.append({"row_id": "warm", "phase": "warmup", "eligible": True, "runtime_seconds": 999.})
    summary = mwis.path_summary({"records": records}, mwis.settings())
    assert summary["runtime_seconds"] == {"median": 3., "min": 1., "max": 100., "p25": 2., "p75": 4.}
    assert summary["eligible"] == 5 and "warm" not in summary["input_row_ids"]
    records[0]["eligible"] = False
    assert mwis.path_summary({"records": records}, mwis.settings())["eligible"] == 4


def test_timeout_and_budget_rows_keep_requested_scenario_and_partial_timing():
    s, cfg = mwis.scenarios([2], [101])[0], mwis.settings()
    record = {"row_id": "partial", "phase": "measured", "eligible": False, "runtime_seconds": 1.25, "artifacts": {}}
    evidence = {"aqc": {"state": {"records": [record]}, "supervision": {"reason": "timeout"}}, "ilp": {"state": {}, "supervision": {}}}
    row = mwis.assemble_row(s, cfg, evidence)
    assert row["status"] == "incomplete"
    assert row["metrics"]["statistics"]["aqc"]["completed"] == 1
    assert row["metrics"]["statistics"]["aqc"]["eligible"] == 0
    assert row["metrics"]["exact_objective"] is None
    excluded = mwis.assemble_row(s, cfg, {}, exclusion="Construction estimate over budget")
    assert excluded["status"] == "skipped" and excluded["problem"] == s
    evidence["aqc"]["supervision"]["reason"] = "memory"
    exhausted = mwis.assemble_row(s, cfg, evidence)
    assert exhausted["status"] == "failed" and exhausted["failure"]["code"] == "BENCHMARK_MEMORY_EXHAUSTED"


def test_model_rebuild_and_ilp_proof_control_on_real_cbc(tmp_path):
    s, cfg = mwis.scenarios([2], [101])[0], mwis.settings(warmups=1, repeat_count=1)
    state = {"records": []}
    mwis._ilp(s, cfg, tmp_path, state, lambda stage: None)
    assert len(state["records"]) == 3
    for record in state["records"]:
        assert record["reference"]["proven_optimal"] and record["eligible"]
        assert record["runtime_seconds"] >= 0 and record["model_construction_seconds"] >= 0
        assert Path(record["artifacts"]["solver_log"]).is_file()


@pytest.mark.requires_julia_backend
def test_small_real_performance_and_saved_evidence_audit(tmp_path):
    paths = mwis.benchmark_mwis_performance(tmp_path / "campaign", sizes=[2], seeds=[101], warmups=1, repeat_count=1)
    row = json.loads(Path(paths["json"]).read_text())["timings"][0]
    assert row["status"] == "incomplete"
    assert row["aqc_eligible"] == row["ilp_eligible"] == 1
    assert row["numerical_max_abs_error"] < 1e-6
    assert row["feasible"]
    script = Path(__file__).resolve().parents[2] / "scripts/audit_mwis_campaign.py"
    spec = importlib.util.spec_from_file_location("audit_mwis_campaign", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.audit(tmp_path / "campaign")["checked_aqc_results"] == 3
    actual_file = Path(row["metrics"]["paths"]["aqc"]["state"]["records"][0]["artifacts"]["result_artifact"])
    from sagittarius import SimulationResult
    result = SimulationResult.load(str(actual_file))
    s = row["problem"]
    reference = mwis.independent_reference(s)
    result.data["pop0"][2] = float("nan")
    invalid = mwis.result_gate(result, s, row["solver"], reference)
    assert invalid["passed"] is False and invalid["raw_state_norm_error"] is None
    json.dumps(invalid, allow_nan=False)
    file = Path(row["metrics"]["paths"]["aqc"]["state"]["records"][0]["artifacts"]["run_manifest"])
    manifest = json.loads(file.read_text())
    manifest["solver"]["reltol"] = .01
    file.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Standalone manifest"):
        module.audit(tmp_path / "campaign")
