import pytest
import numpy as np
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig, Pulse

def test_local_addressing_rabi():
    """Two atoms, but only one is driven. Verify only that one oscillates."""
    reg = Register([Atom(0, 0, 0), Atom(10.0, 0, 0)], C6=0.0)
    
    # Driven atom 0 with Rabi frequency 1Hz
    # Atom 1 is NOT driven (omega=0.0)
    omega = {0: Pulse.constant(2.0 * np.pi * 1.0, duration=1.0)}
    seq = PulseSequence(omega=omega, delta=0.0)
    
    sim = Simulation(reg, seq)
    psi0 = np.array([1, 0, 0, 0], dtype=complex) # |gg>
    
    # Run for 0.5s -> Atom 0 should flip to |r>, Atom 1 stays |g>
    # Basis: |gg>, |rg>, |gr>, |rr>
    results = sim.run(psi0, 0.0, 0.5, observables={"a1": 0, "a2": 1})
    
    p1 = results.data["a1"][-1]
    p2 = results.data["a2"][-1]
    print(f"DEBUG: p1={p1}, p2={p2}")
    
    assert np.isclose(p1, 1.0, atol=1e-2)
    assert np.isclose(p2, 0.0, atol=1e-2)

def test_gaussian_pulse():
    """Drive a single atom with a Gaussian pulse and check for excitation."""
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    
    # Pulse area should be large enough to cause some excitation
    # Integral of A*exp(-t^2/2s^2) is A*s*sqrt(2pi)
    # Let's set A=2pi, s=0.2, duration=1.0, mu=0.5
    omega = Pulse.gaussian(amplitude=2.0 * np.pi * 5.0, sigma=0.1, duration=1.0, mu=0.5)
    seq = PulseSequence(omega=omega)
    
    sim = Simulation(reg, seq)
    psi0 = np.array([1, 0], dtype=complex)
    
    results = sim.run(psi0, 0.0, 1.0, observables={"pop": 0})
    
    # Just check that it actually executed and we have some population
    assert len(results.t) > 1
    assert np.max(results.data["pop"]) > 0.1

def test_blackman_pulse():
    """Verify Blackman pulse doesn't crash."""
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    omega = Pulse.blackman(amplitude=2.0 * np.pi, duration=1.0)
    sim = Simulation(reg, PulseSequence(omega=omega))
    psi0 = np.array([1, 0], dtype=complex)
    results = sim.run(psi0, 0.0, 1.0, observables={"pop": 0})
    assert len(results.t) > 1

def test_local_detuning_landscape():
    """Shift atom 0 out of resonance using local detuning."""
    reg = Register([Atom(0, 0, 0), Atom(10.0, 0, 0)], C6=0.0)
    
    # Global drive at 1Hz
    omega = 2.0 * np.pi * 1.0
    # Local detuning on atom 0 (huge shift), atom 1 is resonant
    delta = {0: 100.0, 1: 0.0}
    
    seq = PulseSequence(omega=omega, delta=delta)
    sim = Simulation(reg, seq)
    psi0 = np.array([1, 0, 0, 0], dtype=complex)
    
    results = sim.run(psi0, 0.0, 0.5, observables={"a1": 0, "a2": 1})
    
    p1 = results.data["a1"][-1]
    p2 = results.data["a2"][-1]
    
    # Atom 1 should have oscillated, Atom 0 should be suppressed
    assert p1 < 0.01
    assert p2 > 0.95
