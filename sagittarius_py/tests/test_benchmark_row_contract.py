from sagittarius.benchmark_row_contract import structured_benchmark_rows


def test_legacy_rows_become_structured_rows_without_losing_flat_metrics():
    rows = structured_benchmark_rows(
        [{"N": 4, "basis_size": 8, "time_s": 0.1}, {"mode": "gpu", "status": "skipped", "reason": "CUDA unavailable"}],
        family="backend_performance", tier="scaling", problem_defaults={}, solver_defaults={},
        backend_defaults={"requested_backend": "CPU"}, observables={"names": [], "count": 0, "output_sample_count": 0},
    )
    assert rows[0]["status"] == "passed" and rows[0]["time_s"] == 0.1
    assert rows[1]["status"] == "skipped" and rows[1]["failure"]["code"] == "BENCHMARK_CASE_SKIPPED"
