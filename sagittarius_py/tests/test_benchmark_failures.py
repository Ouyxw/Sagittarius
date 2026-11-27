import pytest

from sagittarius.benchmark_failures import (
    benchmark_failure_context,
    classify_benchmark_failure,
    make_benchmark_failure_row,
)


@pytest.mark.parametrize("exc, code", [
    (TimeoutError("timed out"), "BENCHMARK_TIMEOUT"),
    (MemoryError(), "BENCHMARK_MEMORY_EXHAUSTED"),
    (RuntimeError("CUDA device unavailable"), "BENCHMARK_CUDA_INITIALIZATION_FAILED"),
    (AssertionError("reference mismatch"), "BENCHMARK_REFERENCE_MISMATCH"),
    (RuntimeError("ILP CBC failed"), "BENCHMARK_ILP_FAILED"),
])
def test_failure_classification_is_stable(exc, code):
    assert classify_benchmark_failure(exc)[0] == code


def test_failure_row_retains_resource_and_probe_context():
    row = make_benchmark_failure_row(
        row_id="gpu-n10", scenario_id="n10", family="backend_performance", tier="parity",
        stage="setup", exc=RuntimeError("CUDA device unavailable"), problem={"N": 10},
        solver={"method": "Tsit5"}, backend={"requested_backend": "CUDA"},
        observables={"names": [], "count": 0, "output_sample_count": 0}, timeout_seconds=30,
        backend_probe={"available": False}, gpu_memory_peak_mb=None,
    )
    assert row["status"] == "failed"
    assert row["failure"]["code"] == "BENCHMARK_CUDA_INITIALIZATION_FAILED"
    assert row["failure"]["timeout_seconds"] == 30
    assert row["failure"]["backend_probe"] == {"available": False}
    assert "process_memory" in row["failure"]
