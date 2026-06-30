import numpy as np
import pytest

from sagittarius import Atom, PulseSequence, Register, SagittariusValidationError, Simulation, SolverConfig


def _one_atom_run(config):
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    psi0 = np.array([1.0, 0.0], dtype=complex)
    return Simulation(reg, PulseSequence(omega=0.0), config).run(
        psi0, 0.0, 0.02, observables={"pop": 0}
    )


def test_default_solver_metadata_is_adaptive_tsit5():
    result = _one_atom_run(SolverConfig(saveat=3))

    solver = result.manifest["solver"]
    assert solver["method"] == "Tsit5"
    assert solver["adaptive"] is True
    assert solver["dt"] is None
    assert solver["effective_method"] == "Tsit5"
    assert solver["effective_adaptive"] is True
    assert solver["effective_dt"] is None
    assert result.diagnostics["simulation"]["effective_method"] == "Tsit5"
    assert np.allclose(result.data["t"], [0.0, 0.01, 0.02])


def test_vern9_runs_and_records_effective_method():
    result = _one_atom_run(SolverConfig(method="Vern9", reltol=1e-9, abstol=1e-9, saveat=3))

    assert result.manifest["solver"]["effective_method"] == "Vern9"
    assert result.manifest["solver"]["effective_adaptive"] is True
    assert result.manifest["solver"]["effective_dt"] is None


def test_rk4_runs_fixed_step_and_records_dt():
    result = _one_atom_run(SolverConfig(method="RK4", adaptive=False, dt=1e-3, saveat=3))

    assert result.manifest["solver"]["effective_method"] == "RK4"
    assert result.manifest["solver"]["effective_adaptive"] is False
    assert result.manifest["solver"]["effective_dt"] == 1e-3
    assert result.diagnostics["simulation"]["effective_dt"] == 1e-3


@pytest.mark.parametrize(
    "config,code",
    [
        (SolverConfig(method="Bogus"), "VALIDATION_SOLVER_METHOD"),
        (SolverConfig(method="RK4"), "VALIDATION_SOLVER_ADAPTIVE_COMBINATION"),
        (SolverConfig(method="RK4", adaptive=False), "VALIDATION_SOLVER_DT_REQUIRED"),
        (SolverConfig(method="RK4", adaptive=False, dt=0.0), "VALIDATION_SOLVER_DT_VALUE"),
        (SolverConfig(method="Tsit5", dt=1e-3), "VALIDATION_SOLVER_DT_COMBINATION"),
        (SolverConfig(method="Vern9", adaptive=False), "VALIDATION_SOLVER_ADAPTIVE_COMBINATION"),
        (SolverConfig(method="Tsit5", reltol=0.0), "VALIDATION_SOLVER_RELTOL_VALUE"),
    ],
)
def test_invalid_solver_config_rejected_before_backend(monkeypatch, config, code):
    import sagittarius.api as api

    def fail_get_modules():
        raise AssertionError("backend should not initialize for invalid solver config")

    monkeypatch.setattr(api, "get_modules", fail_get_modules)
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    psi0 = np.array([1.0, 0.0], dtype=complex)

    with pytest.raises(SagittariusValidationError) as excinfo:
        Simulation(reg, PulseSequence(), config).run(psi0, 0.0, 0.01, observables={"pop": 0})

    assert excinfo.value.issue.code == code
