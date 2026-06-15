import numpy as np
import pytest

from sagittarius import (
    PulseSequence,
    Register,
    SagittariusValidationError,
    dense_vs_reduced_validation,
)


def test_dense_vs_reduced_validation_matches_projected_evolution_for_chain():
    reg = Register.chain(3, spacing=0.5, C6=10.0)

    report = dense_vs_reduced_validation(
        reg,
        PulseSequence(omega=[0.2, 0.3, 0.4], delta=[-0.1, 0.0, 0.2]),
        blockade_radius=0.6,
        duration=0.7,
    )

    assert report["schema_version"] == "dense-vs-reduced-validation/v1"
    assert report["ok"] is True
    assert report["basis"] == [0, 1, 2, 4, 5]
    assert report["full_basis_size"] == 8
    assert report["reduced_basis_size"] == 5
    assert np.isclose(report["reduced_basis_pruning_ratio"], 3 / 8)
    assert report["max_hamiltonian_error"] <= report["atol"]
    assert report["max_state_error"] <= report["atol"]


def test_dense_vs_reduced_validation_accepts_dict_local_pulses():
    reg = Register.chain(2, spacing=0.5)

    report = dense_vs_reduced_validation(
        reg,
        PulseSequence(omega={0: 0.5}, delta={1: -0.25}),
        blockade_radius=1.0,
        duration=0.2,
    )

    assert report["ok"] is True
    assert report["basis"] == [0, 1, 2]


def test_dense_vs_reduced_validation_rejects_large_dense_systems():
    reg = Register.chain(11, spacing=1.0)

    with pytest.raises(SagittariusValidationError) as excinfo:
        dense_vs_reduced_validation(reg, PulseSequence(), blockade_radius=1.1)

    assert excinfo.value.issue.code == "VALIDATION_DENSE_REDUCED_SYSTEM_TOO_LARGE"
    assert "2**N" in excinfo.value.issue.remediation


def test_dense_vs_reduced_validation_rejects_time_dependent_pulses():
    reg = Register.chain(2, spacing=1.0)

    with pytest.raises(SagittariusValidationError) as excinfo:
        dense_vs_reduced_validation(reg, PulseSequence(omega=lambda t: [1.0, 1.0]), blockade_radius=1.1)

    assert excinfo.value.issue.code == "VALIDATION_DENSE_REDUCED_PULSE_UNSUPPORTED"
