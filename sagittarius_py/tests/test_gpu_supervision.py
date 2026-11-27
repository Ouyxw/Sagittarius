"""Resource and crash handling for the persistent GPU benchmark workers."""
from types import SimpleNamespace

import pytest

from sagittarius import gpu_benchmark as gpu


def _workers(tmp_path):
    workers = gpu._Workers(tmp_path / "config.json", gpu.settings(memory_limit_mb=1))
    workers.children["CPU"] = (SimpleNamespace(pid=123, poll=lambda: None), None)
    return workers


def test_worker_rss_limit_and_peak_are_per_backend(tmp_path, monkeypatch):
    workers = _workers(tmp_path)
    monkeypatch.setattr(gpu, "linux_process_memory", lambda _: {"rss_bytes": 2 * 1024**2, "peak_bytes": 3 * 1024**2})
    with pytest.raises(MemoryError, match="CPU"):
        workers.refresh()
    assert workers.peaks == {"CPU": 3 * 1024**2}


def test_scenario_deadline_still_applies_when_memory_probe_is_unavailable(tmp_path, monkeypatch):
    workers = _workers(tmp_path)
    monkeypatch.setattr(gpu, "linux_process_memory", lambda _: {"rss_bytes": None, "peak_bytes": None})
    monkeypatch.setattr(gpu.time, "monotonic", lambda: workers.started + workers.cfg["timeout_seconds"] + 1)
    with pytest.raises(TimeoutError):
        workers.refresh()


def test_unexpected_worker_exit_retains_exit_code(tmp_path, monkeypatch):
    workers = _workers(tmp_path)
    workers.children["CPU"][0].poll = lambda: 42
    workers.children["CPU"][0].returncode = 42
    monkeypatch.setattr(gpu, "linux_process_memory", lambda _: {"rss_bytes": None, "peak_bytes": None})
    with pytest.raises(RuntimeError, match="CPU worker exited 42"):
        workers.wait("CPU")
