"""P0 scaling acceptance, compatibility and retained failure evidence."""
import json
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from sagittarius import SimulationResult, validate_run_manifest
from sagittarius import scaling_benchmark as scaling
from sagittarius.benchmark_measurement import runtime_summary, supervise, write_json
from sagittarius.benchmark_suite import validate_benchmark_suite_artifact
from sagittarius.benchmarking import validate_benchmark_row


def test_complete_matrix_and_basis_counts():
    matrix = scaling.scenarios()
    assert len(matrix) == 42
    assert len({s["scenario_id"] for s in matrix}) == 42
    counts = {s["scenario_id"]: scaling.basis_dimension(s) for s in matrix}
    assert counts["chain-r1.1-n20"] == 17711
    assert counts["chain-r1.5-n20"] == 17711
    assert counts["chain-r2.1-n20"] == 2745
    for radius in scaling.RADII:
        assert counts[f"chain-r{radius:g}-n2"] == counts[f"rectangle-r{radius:g}-n2"] == 3
    assert next(s for s in matrix if s["scenario_id"] == "rectangle-r1.5-n20")["shape"] == [4, 5]


@pytest.mark.parametrize("kwargs", [{"sizes": [21]}, {"sizes": [3], "geometries": ["rectangle"]},
    {"geometries": ["other"]}, {"radii": [float("nan")]}, {"radii": [0]},
    {"sizes": []}, {"sizes": [2, 2]}])
def test_matrix_rejects_unsupported_or_ambiguous_inputs(kwargs):
    with pytest.raises(ValueError):
        scaling.scenarios(**kwargs)


def test_summary_uses_only_eligible_repeats_and_keeps_slow_values():
    repeats = [{"row_id": str(i), "eligible": eligible, "runtime_seconds": value}
               for i, (eligible, value) in enumerate([(True, 1), (True, 2), (False, 999), (True, 100)])]
    result = runtime_summary(repeats, 5)
    assert result["completed"] == 4 and result["eligible"] == 3 and result["requested"] == 5
    assert result["input_row_ids"] == ["0", "1", "3"]
    assert result["runtime_seconds"] == {"median": 2., "min": 1., "max": 100., "p25": 1.5, "p75": 51.}
    assert runtime_summary([], 5)["runtime_seconds"]["median"] is None


@pytest.mark.skipif(not Path('/proc/self/status').exists(), reason="Linux RSS supervisor")
@pytest.mark.parametrize("program, timeout, budget, reason, returncode", [
    ("import time; time.sleep(10)", .15, 1024**3, "timeout", None),
    ("import sys; sys.exit(7)", 5., 1024**3, None, 7),
    ("import time; a=bytearray(32*1024**2); time.sleep(10)", 5., 16*1024**2, "memory", None),
])
def test_supervisor_retains_timeout_crash_memory(tmp_path, program, timeout, budget, reason, returncode):
    checkpoint = tmp_path / "progress.json"
    program = f"from pathlib import Path; Path({str(checkpoint)!r}).write_text('partial'); " + program
    result = supervise([sys.executable, "-c", program], cwd=tmp_path, env=os.environ.copy(),
                       log_path=tmp_path / "child.log", timeout_seconds=timeout, memory_limit_bytes=budget)
    assert result["reason"] == reason
    if returncode is not None:
        assert result["returncode"] == returncode
    assert checkpoint.read_text() == "partial"
    assert result["sampled_peak_bytes"] > 0


def test_budget_exclusion_and_legacy_function_call(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Excluded allocations must not launch a child")
    monkeypatch.setattr(scaling, "supervise", forbidden)
    result = scaling.benchmark_scaling(3, 5., tmp_path, memory_limit_mb=1)
    rows = result["artifact"]["timings"]
    assert [r["N"] for r in rows] == [2, 3]
    assert all(r["problem"]["blockade_radius"] == 5. for r in rows)
    assert all(r["status"] == "skipped" and r["time_s"] is None for r in rows)
    assert Path(result["json"]).name == "scaling_results.json"
    validate_benchmark_suite_artifact(result["suite"]["artifact"])
    campaign = json.loads((tmp_path / "campaign.json").read_text())
    assert len(campaign["config_sha256"]) == 64
    assert len(campaign["source_file_sha256"]) == 2
    with pytest.raises(FileExistsError):
        scaling.benchmark_scaling(2, 5., tmp_path)


def test_parent_preserves_partial_repeats_on_timeout(tmp_path, monkeypatch):
    def timeout(command, **kwargs):
        state = {"stage": "solve", "repeats": [{"row_id": "partial-repeat-0", "runtime_seconds": .25,
                  "eligible": True, "gate_passed": True, "artifacts": {}}]}
        write_json(command[-1], state)
        return {"reason": "timeout", "returncode": -9}
    monkeypatch.setattr(scaling, "supervise", timeout)
    result = scaling.benchmark_scaling(2, 5., tmp_path)
    row = result["artifact"]["timings"][0]
    assert row["status"] == "incomplete"
    assert row["failure"]["code"] == "BENCHMARK_TIMEOUT"
    assert row["metrics"]["statistics"]["eligible"] == 1
    assert row["metrics"]["statistics"]["runtime_seconds"]["median"] == .25


def test_legacy_zero_radius_is_a_full_basis_budgeted_scenario(tmp_path):
    result = scaling.benchmark_scaling(2, 0., tmp_path, memory_limit_mb=1)
    assert result["artifact"]["timings"][0]["basis_size"] == 4


def test_archive_audit_detects_frozen_configuration_tampering(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts" / "audit_scaling_campaign.py"
    spec = importlib.util.spec_from_file_location("audit_scaling_campaign", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scaling.benchmark_scaling(2, 5., tmp_path, memory_limit_mb=1)
    report = module.audit(tmp_path)
    assert report["contract_audit_passed"] and not report["full_v2_matrix_passed"]
    campaign_path = tmp_path / "campaign.json"
    campaign = json.loads(campaign_path.read_text())
    campaign["scenarios"][0]["omega"] = 99.
    write_json(campaign_path, campaign)
    with pytest.raises(ValueError, match="hash mismatch"):
        module.audit(tmp_path)


def test_interruption_accounts_for_remaining_scenarios(tmp_path, monkeypatch):
    monkeypatch.setattr(scaling, "supervise", lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt()))
    result = scaling.benchmark_scaling(3, 5., tmp_path)
    rows = result["artifact"]["timings"]
    assert len(rows) == 2 and all(row["status"] == "incomplete" for row in rows)
    assert rows[0]["failure"]["code"] == "BENCHMARK_INTERRUPTED"


@pytest.mark.parametrize("reference_passed", [True, False])
def test_child_resets_state_and_excludes_checks_and_artifact_time(tmp_path, monkeypatch, reference_passed):
    scenario = scaling.scenarios([2], ["chain"], [1.1])[0]
    scenario["basis_size"] = 3
    settings = {"solver": {"method": "Tsit5", "adaptive": True, "dt": None,
                "reltol": 1e-8, "abstol": 1e-10, "saveat": scaling.TIMES},
                "warmups": 2, "repeat_count": 5, "observable_atol": 1e-8, "timeout_seconds": 10.,
                "memory_limit_bytes": 4 * 1024**3}
    config, checkpoint = tmp_path / "config.json", tmp_path / "checkpoint.json"
    write_json(config, {"scenario": scenario, "settings": settings})
    clock, inputs = [0.], []
    monkeypatch.setattr(scaling.time, "perf_counter", lambda: clock[0])
    monkeypatch.setattr(scaling, "doctor", lambda **kw: {"available": True, "backend_probe": {"available": True}})
    monkeypatch.setattr(scaling, "Register", lambda *a, **kw: None)
    monkeypatch.setattr(scaling, "_runtime_context", lambda: {"environment": {}, "threads": {}})
    class FakeSimulation:
        _basis = [0, 1, 2]
        def __init__(self, *args):
            pass
        def validate(self):
            return 3
        def run(self, initial, *args, **kwargs):
            inputs.append(initial.copy())
            initial[:] = 123  # A mutated input must never leak into the next repeat.
            clock[0] += 2.
            effective = {"effective_method": "Tsit5", "effective_adaptive": True, "effective_dt": None,
                         "reltol": 1e-8, "abstol": 1e-10, "basis_size": 3,
                         "use_gpu": False, "effective_saveat": scaling.TIMES}
            return SimpleNamespace(data={"t": scaling.TIMES, "pop0": np.zeros(101)},
                                   diagnostics={"simulation": effective}, manifest={})
    monkeypatch.setattr(scaling, "Simulation", FakeSimulation)
    def save(*args):
        clock[0] += 100.
        return {"result_artifact": "result", "run_manifest": "manifest"}
    monkeypatch.setattr(scaling, "_save_result", save)
    def reference(*args):
        clock[0] += 200.
        return np.zeros(101), {"type": "test", "hamiltonian_passed": reference_passed}
    monkeypatch.setattr(scaling, "projected_dense_reference", reference)
    scaling._child(config, checkpoint)
    state = json.loads(checkpoint.read_text())
    assert "failure" not in state
    assert state["complete"]
    assert len(inputs) == 8  # first + two warmups + five independent repeats
    assert all(np.array_equal(initial, [1, 0, 0]) for initial in inputs)
    assert all(r["runtime_seconds"] == 2. and r["eligible"] == reference_passed for r in state["repeats"])
    assert len(state["warmups"]) == 2
    scenario.update(full_dim=4, pruned_fraction=.25)
    row = scaling._row(scenario, settings, state, {"returncode": 0})
    assert row["status"] == ("passed" if reference_passed else "failed")
    assert row["metrics"]["statistics"]["eligible"] == (5 if reference_passed else 0)


def test_source_change_is_retained_before_backend_initialization(tmp_path, monkeypatch):
    config, checkpoint = tmp_path / "config.json", tmp_path / "checkpoint.json"
    write_json(config, {"scenario": {}, "settings": {"timeout_seconds": 10.},
                        "source_file_sha256": {"scaling_benchmark.py": "0" * 64}})
    monkeypatch.setattr(scaling, "doctor", lambda **kwargs: pytest.fail("Source drift must stop before backend setup"))
    scaling._child(config, checkpoint)
    failure = json.loads(checkpoint.read_text())["failure"]
    assert failure["stage"] == "setup" and "implementation changed" in failure["message"]


def test_nonfinite_and_wrong_grid_are_rejected():
    for data in ({"t": [0], "pop0": [0]}, {"t": scaling.TIMES, "pop0": [np.nan] * 101}):
        with pytest.raises(AssertionError):
            scaling._trajectory(SimpleNamespace(data=data), scaling.TIMES)


@pytest.mark.requires_julia_backend
@pytest.mark.parametrize("radius,dimension", [(4.4, 3), (0., 4)])
def test_real_backend_scaling_smoke(tmp_path, radius, dimension):
    paths = scaling.benchmark_scaling(2, radius, tmp_path)
    row = paths["artifact"]["timings"][0]
    assert row["status"] == "passed", row.get("failure")
    assert row["basis_size"] == dimension
    assert row["metrics"]["reference"]["hamiltonian_max_abs_error"] <= 1e-12
    assert row["metrics"]["statistics"]["eligible"] == 5
    repeats = json.loads((tmp_path / "scaling_repeats.json").read_text())
    for repeat in repeats:
        validate_benchmark_row(repeat)
        result = SimulationResult.load(repeat["artifacts"]["result_artifact"])
        validate_run_manifest(result.manifest)
        assert len(result.data["t"]) == 101
