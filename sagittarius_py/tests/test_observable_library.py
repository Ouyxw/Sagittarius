import numpy as np
import pytest

from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig
from sagittarius.runtime import SagittariusValidationError


def test_typed_diagonal_observables_for_static_bitstring_state():
    reg = Register([Atom(0, 0), Atom(1, 0), Atom(2, 0)], C6=0.0)
    seq = PulseSequence(omega=0.0, delta=0.0)
    cfg = SolverConfig(saveat=[0.0, 0.1])
    psi0 = np.zeros(8, dtype=complex)
    psi0[0b101] = 1.0
    observables = {
        "n0": {"type": "rydberg_population", "atom": 0},
        "total": {"type": "total_rydberg_population"},
        "pair02": {"type": "pair_correlation", "atoms": [0, 2]},
        "connected02": {"type": "connected_pair_correlation", "atoms": [0, 2]},
        "violations": {"type": "blockade_violation", "edges": [[0, 2], [1, 2]]},
        "target": {"type": "bitstring_probability", "bitstring": "101"},
        "cost": {"type": "mwis_cost", "weights": [1.0, 2.0, 4.0], "edges": [[0, 2]], "penalty": 10.0},
        "z1": {"type": "pauli_z", "atom": 1},
        "zz02": {"type": "pauli_zz", "atoms": [0, 2]},
        "parity": {"type": "parity", "atoms": [0, 1, 2]},
    }

    result = Simulation(reg, seq, cfg).run(psi0, 0.0, 0.1, observables=observables)

    assert result.data["n0"] == [1.0, 1.0]
    assert result.data["total"] == [2.0, 2.0]
    assert result.data["pair02"] == [1.0, 1.0]
    assert result.data["connected02"] == [0.0, 0.0]
    assert result.data["violations"] == [1.0, 1.0]
    assert result.data["target"] == [1.0, 1.0]
    assert result.data["cost"] == [-5.0, -5.0]
    assert result.data["z1"] == [1.0, 1.0]
    assert result.data["zz02"] == [1.0, 1.0]
    assert result.data["parity"] == [1.0, 1.0]
    assert list(result.data.keys())[:-1] == list(observables.keys())

    metadata = result.manifest["solver"]["observable_metadata"]
    assert [item["name"] for item in metadata] == list(observables.keys())
    assert metadata[0]["type"] == "rydberg_population"
    assert metadata[0]["parameters"] == {"atom": 0}
    assert metadata[0]["basis_mode"] == "full"
    assert metadata[-1]["declaration_index"] == len(observables) - 1


def test_observable_shorthand_metadata_compatibility():
    reg = Register([Atom(0, 0)], C6=0.0)
    psi0 = np.array([0.0, 1.0], dtype=complex)
    result = Simulation(reg, PulseSequence(omega=0.0), SolverConfig(saveat=2)).run(
        psi0, 0.0, 0.1, observables={"pop": 0}
    )

    assert result.data["pop"] == [1.0, 1.0]
    assert result.manifest["solver"]["observables"] == {"pop": 0}
    assert result.manifest["solver"]["observable_metadata"] == [
        {
            "name": "pop",
            "type": "rydberg_population",
            "parameters": {"atom": 0},
            "basis_mode": "full",
            "declaration_index": 0,
        }
    ]


def test_invalid_typed_observable_rejected_before_solver():
    reg = Register([Atom(0, 0)], C6=0.0)
    sim = Simulation(reg, PulseSequence(), SolverConfig())
    psi0 = np.array([1.0, 0.0], dtype=complex)

    with pytest.raises(SagittariusValidationError) as excinfo:
        sim.run(psi0, 0.0, 0.1, observables={"bad": {"type": "pair_correlation", "atoms": [0, 1]}})

    assert excinfo.value.issue.code == "VALIDATION_ATOM_INDEX_OUT_OF_RANGE"


def test_reduced_basis_observable_metadata_marks_basis_mode():
    reg = Register([Atom(0, 0), Atom(0.5, 0)], C6=10.0)
    psi0 = np.array([1.0, 0.0, 0.0], dtype=complex)
    result = Simulation(reg, PulseSequence(omega=0.0), SolverConfig(blockade_radius=1.0, saveat=2)).run(
        psi0,
        0.0,
        0.1,
        observables={"total": {"type": "total_rydberg_population"}},
    )

    assert result.data["total"] == [0.0, 0.0]
    assert result.manifest["solver"]["observable_metadata"][0]["basis_mode"] == "reduced"
