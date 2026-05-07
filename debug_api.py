import numpy as np
from sagittarius import Atom, Register, Simulation, PulseSequence, Pulse

def debug_local():
    reg = Register([Atom(0, 0, 0), Atom(10.0, 0, 0)], C6=0.0)
    omega = {0: Pulse.constant(2.0 * np.pi * 1.0, duration=1.0)}
    seq = PulseSequence(omega=omega, delta=0.0)
    sim = Simulation(reg, seq)
    psi0 = np.array([1, 0, 0, 0], dtype=complex)
    results = sim.run(psi0, 0.0, 0.5, observables={"a1": 0, "a2": 1})
    
    print(f"Times: {results.t}")
    print(f"Pop 1: {results.data['a1']}")
    print(f"Pop 2: {results.data['a2']}")

if __name__ == "__main__":
    debug_local()
