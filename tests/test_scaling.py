import numpy as np
from sagittarius.api import Atom, Register, solve, get_basis, PulseSequence, SolverConfig

def test_scaling():
    print("Scaling Test: 10-atom chain with Rydberg Blockade")
    
    # Setup 10 atoms in a chain, distance 1.0
    atoms = [Atom(float(i), 0, 0) for i in range(10)]
    reg = Register(atoms, C6=100.0)
    
    # 1. Check basis size
    # Without blockade: 2^10 = 1024
    # With blockade radius 1.5 (prevents nearest neighbor excitation)
    radius = 1.5
    reduced_basis = get_basis(reg, radius)
    
    print(f"Full Basis size: {2**10}")
    print(f"Reduced Basis size (radius {radius}): {len(reduced_basis)}")
    
    # 2. Run a quick simulation
    psi0 = np.zeros(len(reduced_basis), dtype=complex)
    psi0[0] = 1.0 # Ground state
    
    import time
    start = time.time()
    seq = PulseSequence(omega=2*np.pi*1.0, delta=0.0)
    config = SolverConfig(blockade_radius=radius)
    results = solve(reg, seq, config=config, psi0=psi0, t_start=0.0, t_end=1.0, observables={"atom1": 0})
    end = time.time()
    
    print(f"Simulation of 10 atoms completed in {end - start:.4f} seconds.")

if __name__ == "__main__":
    test_scaling()
