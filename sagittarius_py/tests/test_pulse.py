import numpy as np
from sagittarius import Atom, Register, solve, PulseSequence, SolverConfig, Constant, Ramp, Piecewise

def test_pulses():
    print("Testing AST-based Time-Dependent Pulses")
    
    # 1. Setup a single atom
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    
    # 2. Define a time-dependent pulse sequence for Omega
    # Ramp from 0 to 2*pi over 1.0s, then stay constant at 2*pi for 1.0s
    omega_pulse = Piecewise([
        Ramp(0.0, 2.0 * np.pi, duration=1.0),
        Constant(2.0 * np.pi, duration=1.0)
    ])
    
    # Detuning is constant zero
    delta = 0.0
    
    # 3. Initial state: |g> (ground state)
    psi0 = np.array([1.0, 0.0], dtype=complex)
    
    # 4. Observables: Track Rydberg population
    obs = {"population": 0}
    
    import time
    start = time.time()
    
    # Total time is 2.0s
    seq = PulseSequence(omega=omega_pulse, delta=delta)
    results = solve(reg, seq, psi0=psi0, t_start=0.0, t_end=2.0, observables=obs)
    
    end = time.time()
    print(f"Simulation completed in {end - start:.4f} seconds.")
    
    # Analyze results
    t = results['t']
    pop = results['population']
    print(f"Final Population: {pop[-1]:.4f}")
    
    # During the ramp, population should slowly increase.
    # During the constant phase, it should oscillate rapidly.
    max_pop = max(pop)
    print(f"Max Population during pulse: {max_pop:.4f}")

if __name__ == "__main__":
    test_pulses()
