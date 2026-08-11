"""Regression checks for Phase 16 benchmark documentation references."""

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_phase16_tier_commands_and_outputs_are_documented() -> None:
    readme = (REPOSITORY_ROOT / "docs/benchmarks/README.md").read_text()
    tiers = (REPOSITORY_ROOT / "docs/benchmarks/tiers.md").read_text()

    for text in (readme, tiers):
        for tier in ("Smoke", "Correctness", "Parity", "Scaling", "Stress"):
            assert tier in text

    for command in (
        "benchmark_physics_smoke.py",
        "benchmark_phase16_validation.py",
        "benchmark_mwis_aqc.py",
        "benchmark_cuda_mwis_protocol.py",
        "benchmark_scaling.py",
        "benchmark_ablation.py",
    ):
        assert command in tiers

    assert "SAGITTARIUS_ENABLE_GPU_TESTS=1" in tiers
    assert "physics_smoke_suite" in readme
    assert "mwis_aqc_correctness" in tiers
    assert "cuda_parity" in tiers
    assert "scaling_results" in tiers
    assert "ablation_bench_results" in tiers


def test_governance_stems_and_mwis_paths_match_current_runners() -> None:
    requirements = (REPOSITORY_ROOT / "docs/development/requirements.md").read_text()
    claims = (
        REPOSITORY_ROOT / "docs/governance/SPEC-GOV-001-performance-claims.md"
    ).read_text()
    plan = (REPOSITORY_ROOT / "docs/governance/SPEC-GOV-004-benchmarking-plan.md").read_text()

    runner_directory = REPOSITORY_ROOT / "sagittarius_py/tests/test_performance"
    expected_stems = {
        "benchmark_gpu.py": "gpu_bench_results",
        "benchmark_cluster.py": "cluster_bench_results",
        "benchmark_ablation.py": "ablation_bench_results",
    }

    for script, stem in expected_stems.items():
        assert stem in (runner_directory / script).read_text()
        assert f"`{stem}`" in claims

    assert "sagittarius_py/projects/mwis_udg/batch_verify.py" in requirements
    assert "`gpu_results`" not in claims
    assert "`cluster_results`" not in claims
    assert "`ablation_results`" not in claims
    assert "benchmark_mwis_aqc.py" in claims
    assert "benchmark_mwis_aqc.py" in plan
