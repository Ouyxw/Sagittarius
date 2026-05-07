import pytest
import numpy as np
from sagittarius import Atom, Register, solve, PulseSequence, SolverConfig, Constant, Ramp, Piecewise

def test_single_atom_rabi():
    """Verify single atom oscillates correctly under a constant Omega."""
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    psi0 = np.array([1.0, 0.0], dtype=complex) # |g>
    
    # Omega = 2pi * 1.0 (Rabi freq of 1.0 Hz)
    # At t = 0.5s, we expect full inversion to |r>
    omega = 2.0 * np.pi * 1.0
    seq = PulseSequence(omega=omega, delta=0.0)
    results = solve(reg, seq, psi0=psi0, t_start=0.0, t_end=0.5, observables={"pop": 0})
    
    final_pop_rydberg = results["pop"][-1]
    # At t=0.5, Rydberg population should be 1.0
    assert np.isclose(final_pop_rydberg, 1.0, atol=1e-2)

def test_two_atom_blockade():
    """Verify Rydberg blockade prevents simultaneous excitation."""
    # Atoms very close (dist=0.5) with strong C6=100
    reg = Register([Atom(0, 0, 0), Atom(0.5, 0, 0)], C6=100.0)
    
    # Pruned Basis with radius 1.0: [|gg>, |rg>, |gr>] (3 states)
    # |rr> is removed.
    psi0 = np.array([1, 0, 0], dtype=complex)
    
    omega = 2.0 * np.pi * 1.0
    seq = PulseSequence(omega=omega, delta=0.0)
    config = SolverConfig(blockade_radius=1.0)
    results = solve(reg, seq, config=config, psi0=psi0, t_start=0.0, t_end=1.0, observables={"a1": 0, "a2": 1})
    
    p1 = np.array(results["a1"])
    p2 = np.array(results["a2"])
    total_pop = p1 + p2
    
    # Total population should not exceed 1.0 (since |rr> is gone)
    assert np.max(total_pop) <= 1.0001

def test_piecewise_pulse_transition():
    """Verify AST Piecewise pulse correctly transitions from zero to driving."""
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    psi0 = np.array([1, 0], dtype=complex)
    
    # Pulse sequence: Zero for 1.0s, then Constant for 0.5s
    # Total time 1.5s
    pulse = Piecewise([
        Constant(0.0, duration=1.0),
        Constant(2.0 * np.pi * 1.0, duration=0.5)
    ])
    
    seq = PulseSequence(omega=pulse, delta=0.0)
    results = solve(reg, seq, psi0=psi0, t_start=0.0, t_end=1.5, observables={"pop": 0})
    
    # Check that at t=1.0, Rydberg population is still 0.0 (no excitation during zero pulse)
    t = np.array(results["t"])
    idx_1s = np.argmin(np.abs(t - 1.0))
    assert np.isclose(results["pop"][idx_1s], 0.0, atol=1e-3)
    
    # Check that at t=1.5 (after 0.5s of driving), Rydberg population is high (~1.0)
    assert results["pop"][-1] > 0.95

if __name__ == "__main__":
    test_single_atom_rabi()
    test_two_atom_blockade()
    test_piecewise_pulse_transition()
    print("All physics tests passed!")
