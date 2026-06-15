import pytest


JULIA_BACKEND_TEST_MODULES = (
    "tests/test_api_v2.py",
    "tests/test_benchmarks.py",
    "tests/test_cluster.py",
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
    marker = pytest.mark.requires_julia_backend
    for item in items:
        if item.nodeid.startswith(JULIA_BACKEND_TEST_MODULES):
            item.add_marker(marker)


def pytest_runtest_setup(item):
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
