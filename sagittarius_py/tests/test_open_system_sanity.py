import numpy as np
import pytest

from sagittarius import (
    Atom,
    PulseSequence,
    Register,
    SolverConfig,
    open_system_sanity_checks,
)
from sagittarius.runtime import SagittariusValidationError


def test_open_system_sanity_checks_decay_channel():
    reg = Register([Atom(0, 0)], C6=0.0)
    seq = PulseSequence(omega=0.0, delta=0.0)
    psi0 = np.array([0.0, 1.0], dtype=complex)

    report = open_system_sanity_checks(
        reg,
        seq,
        config=SolverConfig(gamma=0.5, reltol=1e-7, abstol=1e-9),
        psi0=psi0,
        t_end=2.0,
        observables={"pop": 0},
        n_trajectories=300,
        mc_mean_abs_atol=0.08,
    )

    assert report["schema_version"] == "open-system-sanity-checks/v1"
    assert report["ok"] is True
    assert report["lindblad_trace"]["ok"] is True
    assert report["lindblad_trace"]["max_error"] < 1e-6
    assert report["lindblad_positivity"]["ok"] is True
    assert report["lindblad_positivity"]["min_eigenvalue"] >= -1e-7
    assert report["mcwf_vs_lindblad"]["ok"] is True
    assert report["mcwf_vs_lindblad"]["observables"]["pop"]["mean_abs_error"] < 0.08


def test_open_system_sanity_checks_requires_noise():
    reg = Register([Atom(0, 0)], C6=0.0)
    with pytest.raises(SagittariusValidationError, match="VALIDATION_OPEN_SYSTEM_NO_NOISE"):
        open_system_sanity_checks(reg, PulseSequence(), config=SolverConfig())
