import numpy as np
import pytest

from sagittarius import (
    Atom, PulseSequence, Register, Simulation, SolverConfig,
    all_ground_state, bitstring_state, single_excitation_state, validate_run_manifest,
)
from sagittarius.api import _simulation_result_with_manifest
from sagittarius.runtime import SagittariusValidationError


def test_full_basis_helpers_follow_register_bitstring_order():
    simulation = Simulation(Register([Atom(0, 0), Atom(1, 0)]), PulseSequence())

    ground = all_ground_state(simulation)
    assert np.allclose(ground.amplitudes, [1.0, 0.0, 0.0, 0.0])
    assert ground.metadata["type"] == "all_ground"
    assert ground.metadata["bitstring"] == "00"
    assert ground.metadata["basis_mode"] == "full"

    bitstring = bitstring_state(simulation, "01")
    single = single_excitation_state(simulation, 1)
    assert np.allclose(bitstring.amplitudes, [0.0, 0.0, 1.0, 0.0])
    assert np.allclose(single.amplitudes, bitstring.amplitudes)
    assert single.metadata["atom_index"] == 1


def test_reduced_basis_helper_rejects_forbidden_bitstring(monkeypatch):
    simulation = Simulation(
        Register([Atom(0, 0), Atom(0.5, 0)]),
        PulseSequence(),
        SolverConfig(blockade_radius=0.6),
    )

    def fake_validate():
        simulation._basis = [0, 1, 2]
        return 3

    monkeypatch.setattr(simulation, "validate", fake_validate)
    with pytest.raises(SagittariusValidationError) as excinfo:
        bitstring_state(simulation, "11")
    assert excinfo.value.issue.code == "VALIDATION_STATE_PREPARATION_FORBIDDEN"


def test_preparation_metadata_persists_in_result_artifact_sections():
    simulation = Simulation(Register([Atom(0, 0)]), PulseSequence())
    prepared = single_excitation_state(simulation, 0)
    result = _simulation_result_with_manifest(
        {"t": [0.0], "pop": [1.0]}, metadata={}, diagnostics={},
        register=simulation.register, sequence=simulation.sequence, config=simulation.config,
        t_start=0.0, t_end=1.0, observables={"pop": 0}, observable_metadata=[],
        psi0=prepared.amplitudes, result_type="observables",
        state_preparation=prepared.metadata,
    )
    validate_run_manifest(result.manifest)
    assert result.metadata["state_preparation"] == prepared.metadata
    assert result.diagnostics["state_preparation"] == prepared.metadata
    assert result.manifest["initial_state"]["preparation"] == prepared.metadata


def test_prepared_state_runs_and_retains_metadata():
    simulation = Simulation(Register([Atom(0, 0)]), PulseSequence(omega=0.0))
    prepared = single_excitation_state(simulation, 0)
    result = simulation.run(prepared, 0.0, 0.1, observables={"pop": 0})
    assert result.manifest["initial_state"]["preparation"] == prepared.metadata
    assert result.metadata["state_preparation"] == prepared.metadata
    assert result.diagnostics["state_preparation"] == prepared.metadata
