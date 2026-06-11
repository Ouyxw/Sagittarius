import numpy as np
import pytest

from sagittarius import Atom, Register, Simulation, PulseSequence, Pulse
from sagittarius.api import _coerce_callable_vector, _local_pulse_values_in_register_order


def _sim(sequence):
    return Simulation(Register([Atom(0, 0, 0), Atom(1, 0, 0)], C6=0.0), sequence)


def test_local_pulse_list_length_must_match_atom_count():
    sim = _sim(PulseSequence(omega=[1.0]))

    with pytest.raises(ValueError, match="omega list length 1 does not match 2 atoms"):
        sim.validate_inputs(sample_time=0.0)


def test_local_pulse_dict_keys_must_be_integer_atom_indices():
    sim = _sim(PulseSequence(omega={"0": 1.0}))

    with pytest.raises(ValueError, match="omega atom index must be an integer"):
        sim.validate_inputs(sample_time=0.0)


def test_local_pulse_dict_keys_must_be_in_range():
    sim = _sim(PulseSequence(delta={2: 1.0}))

    with pytest.raises(ValueError, match="delta atom index 2 is out of range"):
        sim.validate_inputs(sample_time=0.0)


def test_local_pulse_values_must_be_numeric_or_pulse_nodes():
    sim = _sim(PulseSequence(omega={0: object()}))

    with pytest.raises(ValueError, match="omega for atom 0 must be a numeric scalar or Pulse node"):
        sim.validate_inputs(sample_time=0.0)


def test_callable_pulse_return_length_is_validated_before_backend_init():
    sim = _sim(PulseSequence(omega=lambda t: [1.0]))

    with pytest.raises(ValueError, match="returned 1 values for 2 atoms"):
        sim.validate_inputs(sample_time=0.0)


def test_callable_pulse_return_values_must_be_numeric():
    sim = _sim(PulseSequence(delta=lambda t: [0.0, "bad"]))

    with pytest.raises(ValueError, match="delta value for atom 1 must be numeric"):
        sim.validate_inputs(sample_time=0.0)


def test_observable_indices_are_zero_based_and_in_range():
    sim = _sim(PulseSequence())

    with pytest.raises(ValueError, match="Observable 'bad' atom index 2 is out of range"):
        sim.validate_inputs(sample_time=0.0, observables={"bad": 2})


def test_local_pulse_values_follow_register_order_without_reversal():
    values = _local_pulse_values_in_register_order({0: "a0", 2: "a2"}, 3)

    assert values == ["a0", 0.0, "a2"]


def test_callable_vector_accepts_numpy_arrays_in_register_order():
    values = _coerce_callable_vector(np.array([1.0, 2.0]), 2, field_name="omega")

    assert values == [1.0, 2.0]


def test_pulse_nodes_are_valid_local_values():
    sim = _sim(PulseSequence(omega=[Pulse.constant(1.0, duration=1.0), 0.0]))

    sim.validate_inputs(sample_time=0.0)
