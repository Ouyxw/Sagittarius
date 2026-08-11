"""Public SDK exports for aggregate benchmark suite artifacts."""

from sagittarius import (
    BENCHMARK_SUITE_ARTIFACT_SCHEMA_VERSION,
    load_benchmark_suite_artifact,
    make_benchmark_suite_artifact,
    validate_benchmark_suite_artifact,
    write_benchmark_suite_artifact,
)


def test_benchmark_suite_contract_is_exported_from_the_sdk():
    assert BENCHMARK_SUITE_ARTIFACT_SCHEMA_VERSION == "benchmark-suite-artifact/v1"
    assert callable(make_benchmark_suite_artifact)
    assert callable(validate_benchmark_suite_artifact)
    assert callable(load_benchmark_suite_artifact)
    assert callable(write_benchmark_suite_artifact)
