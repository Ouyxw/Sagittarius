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
