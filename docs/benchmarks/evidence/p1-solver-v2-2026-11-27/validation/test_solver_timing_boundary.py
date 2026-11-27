"""The legacy solver timer excludes reference generation and result writes."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np


def test_legacy_method_timer_excludes_slow_serialization(monkeypatch, tmp_path):
    path = Path(__file__).parent / "test_performance/benchmark_solver_performance.py"
    spec = importlib.util.spec_from_file_location("legacy_solver_timer", path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    clock, saved = [0.], []

    class Simulation:
        def __init__(self, *args):
            clock[0] += 1.

        def validate(self):
            return 2

        def run(self, *args, **kwargs):
            clock[0] += 2.
            return SimpleNamespace(data={"pop0": np.zeros(9)}, diagnostics={"simulation": {}})

    def slow_save(result, directory, label):
        clock[0] += 100.
        saved.append(label)
        return {"result_artifact": str(directory / label)}, {"label": label}

    monkeypatch.setattr(runner, "Simulation", Simulation)
    monkeypatch.setattr(runner, "time", SimpleNamespace(perf_counter=lambda: clock[0]))
    monkeypatch.setattr(runner, "_save_result", slow_save)
    rows, _ = runner._method_rows(tmp_path, repeat_count=1)
    assert len(rows) == 3 and len(saved) == 4  # reference plus three method results
    assert all(r["status"] == "passed" for r in rows)
    assert [r["metrics"]["runtime_seconds"] for r in rows] == [3., 3., 3.]
