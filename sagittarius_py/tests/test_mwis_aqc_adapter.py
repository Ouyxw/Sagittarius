"""Backend coverage for the default MWIS AQC verification adapter."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1] / "projects" / "mwis_udg"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from batch_verify import verify_mwis_batch  # noqa: E402


pytestmark = pytest.mark.requires_julia_backend


def test_default_aqc_adapter_returns_a_feasible_small_udg_solution():
    report = verify_mwis_batch(
        n_instances=1,
        n_nodes=2,
        densities=(1.0,),
        seed=3,
        duration=0.1,
    )

    instance = report.instances[0]
    assert report.schema_version == "mwis-batch-verification/v1"
    assert instance.ilp_status == "Optimal"
    assert instance.aqc_valid_independent_set is True
    assert 0.0 <= instance.approximation_ratio <= 1.0


def test_adapter_result_round_trip_preserves_manifest_and_tuple_semantics(tmp_path):
    import numpy as np
    from sagittarius import SimulationResult, SolverConfig, validate_run_manifest
    from batch_verify import generate_random_udg
    from mwis_solver import MWIS_AQC
    adapter = MWIS_AQC(generate_random_udg(3, density=.8, seed=101))
    result = adapter.solve_result(SolverConfig(blockade_radius=1., saveat=7), duration=.1, observables={"pop0": 0})
    validate_run_manifest(result.manifest)
    assert result.manifest["initial_state"]["preparation"]["type"] == "all_ground"
    path = tmp_path / "actual.result.json"
    result.save(str(path))
    reloaded = SimulationResult.load(str(path))
    bits, probabilities, basis = adapter.decode_result(reloaded)
    assert reloaded.manifest == result.manifest
    assert basis == sorted(basis) and len(reloaded.data["t"]) == 7
    expected = result.final_bitstring_distribution()
    np.testing.assert_allclose(probabilities, [expected[format(value, '03b')[::-1]] for value in basis], rtol=0, atol=0)
    best = basis[int(np.argmax(probabilities))]
    assert bits.tolist() == [(best >> i) & 1 for i in range(3)]
