import os

import pytest


JULIA_BACKEND_TEST_MODULES = (
    "tests/test_api_v2.py",
    "tests/test_benchmarks.py",
    "tests/test_cluster.py",
    "tests/test_cross_language_golden.py",
    "tests/test_gpu_acceleration.py",
    "tests/test_invariants.py",
    "tests/test_local_pulses.py",
    "tests/test_mc_trajectories.py",
    "tests/test_physics.py",
    "tests/test_pulse.py",
)

_julia_backend_skip_reason = None
_julia_backend_checked = False


def pytest_collection_modifyitems(config, items):
    julia_marker = pytest.mark.requires_julia_backend
    cuda_marker = pytest.mark.requires_cuda_backend
    for item in items:
        if item.nodeid.startswith(JULIA_BACKEND_TEST_MODULES):
            item.add_marker(julia_marker)
        if item.nodeid.startswith("tests/test_gpu_acceleration.py"):
            item.add_marker(cuda_marker)


def pytest_runtest_setup(item):
    if item.get_closest_marker("requires_cuda_backend") is not None:
        if os.environ.get("SAGITTARIUS_ENABLE_GPU_TESTS") != "1":
            pytest.skip("CUDA backend tests require SAGITTARIUS_ENABLE_GPU_TESTS=1")
        reason = _check_cuda_backend()
        if reason is not None:
            pytest.skip(reason)
        return

    if item.get_closest_marker("requires_julia_backend") is None:
        return

    reason = _check_julia_backend()
    if reason is not None:
        pytest.skip(reason)


def _check_julia_backend():
    global _julia_backend_checked, _julia_backend_skip_reason
    if _julia_backend_checked:
        return _julia_backend_skip_reason

    _julia_backend_checked = True
    try:
        from sagittarius.runtime import get_julia

        get_julia()
    except Exception as exc:
        _julia_backend_skip_reason = f"Julia backend unavailable: {exc}"
    return _julia_backend_skip_reason


def _check_cuda_backend():
    reason = _check_julia_backend()
    if reason is not None:
        return reason
    try:
        from sagittarius import doctor

        report = doctor(backend="CUDA", initialize_backend=True)
    except Exception as exc:
        return f"CUDA backend diagnostics failed: {exc}"
    if not report.get("available"):
        return f"CUDA backend unavailable: {report.get('issues', [])}"
    return None
