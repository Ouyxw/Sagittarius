"""CPU contract checks and opt-in hardware verification for the P1 GPU scan."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from sagittarius import gpu_benchmark as gpu


def test_frozen_matrix_and_independent_basis():
    matrix = gpu.scenarios()
    assert len(matrix) == 8
    assert [len(gpu.basis_values(s)) for s in matrix] == [3, 8, 55, 377, 2584, 17711, 7, 3]
    assert matrix[-1]["seed"] == 3
    for sizes in ([], [True], [2, 2], [21]):
        with pytest.raises(ValueError):
            gpu.scenarios(sizes)


def test_timer_brackets_sync_and_resets_inputs():
    events = []
    initial = np.array([1., 0.])
    class Simulation:
        def run(self, state, *args, **kwargs):
            assert state is not initial
            np.testing.assert_array_equal(state, initial)
            state[:] = 0
            events.append("solve")
            return "result"
    ticks = iter([10., 13.])
    def clock():
        events.append("clock")
        return next(ticks)
    result, seconds = gpu.timed_solve(Simulation(), initial, .5, {"pop0": 0},
        synchronize=lambda: events.append("sync"), clock=clock)
    assert (result, seconds) == ("result", 3.)
    assert events == ["sync", "clock", "solve", "sync", "clock"]
    np.testing.assert_array_equal(initial, [1., 0.])


def _pairs():
    return [{"row_id": f"pair-{i}", "phase": "measured", "paths": {
        "CPU": {"runtime_seconds": value * 2}, "CUDA": {"runtime_seconds": value}},
        "gate": {"passed": True}} for i, value in enumerate([1., 2., 3., 4., 100.])]


def test_ratio_uses_independent_medians_and_retains_slow_valid_repeat():
    pairs = _pairs()
    pairs.append({**deepcopy(pairs[0]), "row_id": "warm", "phase": "warmup"})
    result = gpu.pair_statistics(pairs, gpu.settings())
    assert result["median_cpu_over_cuda"] == 2.
    assert result["statistics"]["CUDA"]["runtime_seconds"] == {"median": 3., "min": 1., "max": 100., "p25": 2., "p75": 4.}
    assert result["statistics"]["CPU"]["eligible"] == 5
    assert "warm" not in result["statistics"]["CPU"]["input_row_ids"]
    pairs[0]["gate"]["passed"] = False
    assert gpu.pair_statistics(pairs, gpu.settings())["median_cpu_over_cuda"] is None
    assert gpu.pair_statistics(_pairs(), gpu.settings(warmups=1))["median_cpu_over_cuda"] is None
    assert gpu.pair_statistics(_pairs(), gpu.settings(), valid_campaign=False)["median_cpu_over_cuda"] is None


def test_opt_in_and_budget_exclusions_do_not_start_workers(tmp_path, monkeypatch):
    monkeypatch.setattr(gpu._Workers, "start", lambda *args: pytest.fail("worker must not start"))
    monkeypatch.delenv("SAGITTARIUS_ENABLE_GPU_TESTS", raising=False)
    s = gpu.chain_scenario(2)
    row = gpu.measure_row(s, gpu.settings(), tmp_path / "disabled", {})
    assert row["status"] == "skipped"
    assert row["failure"]["code"] == "BENCHMARK_GPU_OPT_IN_DISABLED"
    assert row["metrics"]["median_cpu_over_cuda"] is None
    monkeypatch.setenv("SAGITTARIUS_ENABLE_GPU_TESTS", "1")
    row = gpu.measure_row(s, gpu.settings(memory_limit_mb=1), tmp_path / "budget", {})
    assert row["status"] == "skipped"
    assert row["failure"]["code"] == "BENCHMARK_MEMORY_BUDGET_EXCLUSION"


@pytest.mark.parametrize("error,status", [(TimeoutError("deadline"), "incomplete"), (MemoryError("budget"), "failed"), (RuntimeError("CUDA initialization failed"), "failed")])
def test_attempted_failures_preserve_row(tmp_path, monkeypatch, error, status):
    monkeypatch.setenv("SAGITTARIUS_ENABLE_GPU_TESTS", "1")
    def start(*args):
        raise error
    monkeypatch.setattr(gpu._Workers, "start", start)
    row = gpu.measure_row(gpu.chain_scenario(2), gpu.settings(), tmp_path, {})
    assert row["status"] == status
    assert row["failure"]["message"]
    assert row["metrics"]["median_cpu_over_cuda"] is None


def test_saved_full_grid_gate_checks_every_named_observable(monkeypatch):
    from sagittarius import cuda_parity
    monkeypatch.setattr(cuda_parity, "validate_run_manifest", lambda _: None)
    times = [0., .5, 1.]
    solver = dict.fromkeys(cuda_parity.MATCHED_SOLVER_FIELDS)
    solver.update(use_gpu=False, gpu_backend="CUDA", effective_method="Tsit5", effective_adaptive=True, effective_saveat=times)
    cpu = SimpleNamespace(data={"t": times, "pop0": [0., .1, .2], "pop1": [0., .2, .3]},
        manifest={"solver": solver, "backend_diagnostics": {"requested_backend": "CPU"}, "register": {}, "pulse": {}, "initial_state": {}})
    cuda = deepcopy(cpu)
    cuda.manifest["solver"]["use_gpu"] = True
    cuda.manifest["backend_diagnostics"]["requested_backend"] = "CUDA"
    assert cuda_parity.solve_pair_gate(cpu, cuda, times, 1e-6, ("pop0", "pop1"))["passed"]
    cuda.data["pop1"][1] += .01
    assert not cuda_parity.solve_pair_gate(cpu, cuda, times, 1e-6, ("pop0", "pop1"))["passed"]
    cuda.data["pop1"][1] = float("nan")
    assert not cuda_parity.solve_pair_gate(cpu, cuda, times, 1e-6, ("pop0", "pop1"))["finite"]


def test_serialization_failure_keeps_completed_solve_time(tmp_path, monkeypatch):
    monkeypatch.setenv("SAGITTARIUS_ENABLE_GPU_TESTS", "1")
    def start(self, backend):
        self.states[backend] = {"records": []}
    def solve(self, backend, label):
        self.states[backend]["records"].append({"label": label, "runtime_seconds": 1.25, "artifacts": {}})
        raise OSError("artifact write failed")
    monkeypatch.setattr(gpu._Workers, "start", start)
    monkeypatch.setattr(gpu._Workers, "solve", solve)
    row = gpu.measure_row(gpu.chain_scenario(2), gpu.settings(), tmp_path, {})
    assert row["status"] == "failed"
    assert row["metrics"]["paths"]["CPU"]["records"][0]["runtime_seconds"] == 1.25
    assert row["metrics"]["median_cpu_over_cuda"] is None


def test_backend_free_audit_detects_companion_and_source_tampering(tmp_path, monkeypatch):
    import importlib.util
    monkeypatch.delenv("SAGITTARIUS_ENABLE_GPU_TESTS", raising=False)
    script = Path(__file__).resolve().parents[2] / "scripts/audit_gpu_campaign.py"
    spec = importlib.util.spec_from_file_location("audit_gpu_campaign", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    directory = tmp_path / "campaign"
    gpu.benchmark_gpu([2], directory, include_fixtures=False)
    result = module.audit(directory)
    assert result["contract_audit_passed"] and not result["all_p1_gpu_passed"]
    csv = directory / "gpu_bench_results.csv"
    original = csv.read_text()
    csv.write_text(original.replace("skipped", "passed"))
    with pytest.raises(ValueError, match="CSV"):
        module.audit(directory)
    csv.write_text(original)
    source = directory / "source/sagittarius_py/sagittarius/gpu_benchmark.py"
    source.write_text(source.read_text() + "\n# changed\n")
    with pytest.raises(ValueError, match="source hash"):
        module.audit(directory)


def test_interruption_retains_remaining_scenarios_without_starting_them(tmp_path, monkeypatch):
    monkeypatch.setenv("SAGITTARIUS_ENABLE_GPU_TESTS", "1")
    calls = []
    def start(self, backend):
        calls.append(backend)
        raise KeyboardInterrupt()
    monkeypatch.setattr(gpu._Workers, "start", start)
    paths = gpu.benchmark_gpu([2, 4], tmp_path, include_fixtures=False)
    rows = json.loads(Path(paths["json"]).read_text())["timings"]
    assert calls == ["CPU"]
    assert [r["status"] for r in rows] == ["incomplete", "incomplete"]
    assert rows[1]["failure"]["code"] == "BENCHMARK_CAMPAIGN_INTERRUPTED"


@pytest.mark.requires_cuda_backend
def test_small_real_scan_retains_separate_backend_memory_and_saved_results(tmp_path):
    paths = gpu.benchmark_gpu([2], tmp_path / "campaign", include_fixtures=False, warmups=1, repeat_count=1)
    row = json.loads(Path(paths["json"]).read_text())["timings"][0]
    assert row["status"] == "incomplete"  # A pilot cannot qualify a ratio.
    assert row["metrics"]["median_cpu_over_cuda"] is None
    assert all(p["gate"]["passed"] for p in row["metrics"]["pairs"])
    for backend in ("CPU", "CUDA"):
        state = row["metrics"]["paths"][backend]
        assert state["doctor"]["available"]
        assert state["memory"]["peak_bytes"] > 0
        assert state["runtime_context"]["threads"]["julia"] == 1
        assert all(Path(r["artifacts"]["result_artifact"]).is_file() for r in state["records"])
    import importlib.util
    script = Path(__file__).resolve().parents[2] / "scripts/audit_gpu_campaign.py"
    spec = importlib.util.spec_from_file_location("audit_gpu_campaign", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.audit(tmp_path / "campaign")["checked_pairs"] == 3
    manifest = Path(row["metrics"]["pairs"][0]["paths"]["CPU"]["artifacts"]["run_manifest"])
    payload = json.loads(manifest.read_text())
    payload["solver"]["reltol"] = .01
    manifest.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="manifest differs"):
        module.audit(tmp_path / "campaign")
