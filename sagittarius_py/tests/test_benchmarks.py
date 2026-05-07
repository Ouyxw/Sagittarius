import numpy as np
import pytest
from sagittarius import Atom, Register, Simulation, PulseSequence, Pulse

def test_landau_zener():
    """Verify LZ transition probability: P_r = 1 - exp(-pi * Omega^2 / (2 * |v|))"""
    # System: 1 atom
    reg = Register([Atom(0,0)], C6=0.0)
    
    # Parameters
    Omega = 2.0 * np.pi * 1.0 # 1 MHz
    v = 2.0 * np.pi * 0.5    # 0.5 MHz/us sweep rate
    
    # Theoretical P_r
    P_theory = 1.0 - np.exp(-np.pi * Omega**2 / (2 * np.abs(v)))
    
    # Pulse: constant Omega, ramping Delta from -10 to +10
    duration = 20.0 / (v / (2*np.pi)) # time to cover 20 MHz
    t_mid = duration / 2.0
    
    # Delta(t) = v * (t - t_mid)
    # Piecewise or Ramp? Pulse.ramp(start, end, duration)
    seq = PulseSequence(
        omega=Omega,
        delta=Pulse.ramp(start=-10.0*2*np.pi, end=10.0*2*np.pi, duration=duration)
    )
    
    sim = Simulation(reg, seq)
    psi0 = np.array([1, 0], dtype=complex) # |g>
    
    res = sim.run(psi0, 0.0, duration, observables={"pop": 0})
    
    P_numeric = res.data["pop"][-1]
    
    print(f"LZ Benchmark: Theory={P_theory:.4f}, Numeric={P_numeric:.4f}")
    assert pytest.approx(P_numeric, abs=0.01) == P_theory

def test_rabi_oscillations():
    """Verify simple Rabi oscillations."""
    reg = Register([Atom(0,0)], C6=0.0)
    Omega = 2.0 * np.pi * 1.0
    seq = PulseSequence(omega=Omega, delta=0.0)
    
    sim = Simulation(reg, seq)
    psi0 = np.array([1, 0], dtype=complex)
    
    # Run for 1.0 us (1 full cycle if Omega = 2pi * 1.0)
    # P_r(t) = sin^2(Omega * t / 2)
    t_end = 0.5 # half cycle, should be at max
    res = sim.run(psi0, 0.0, t_end, observables={"pop": 0})
    
    P_max = res.data["pop"][-1]
    assert pytest.approx(P_max, abs=1e-3) == 1.0
    
    t_end = 1.0 # full cycle, should be back at 0
    res = sim.run(psi0, 0.0, t_end, observables={"pop": 0})
    P_end = res.data["pop"][-1]
    assert pytest.approx(P_end, abs=1e-3) == 0.0

if __name__ == "__main__":
    test_rabi_oscillations()
    print("Rabi oscillation benchmark passed!")
    test_landau_zener()
    print("Landau-Zener benchmark passed!")
