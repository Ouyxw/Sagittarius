import time
import numpy as np
from sagittarius import Atom, Register, solve, get_basis

def benchmark_scaling():
    print("="*40)
    print("      Sagittarius Performance Report      ")
    print("="*40)
    print(f"{'Atoms':<8} | {'Full Basis':<12} | {'Reduced':<8} | {'Time (s)':<10}")
    print("-"*40)
    
    # We test scaling from 2 to 14 atoms in a blockade chain
    for n in range(2, 15, 2):
        # 1. Setup chain
        atoms = [Atom(float(i), 0, 0) for i in range(n)]
        reg = Register(atoms, C6=100.0)
        
        # 2. Get basis
        radius = 1.1 # Blockade nearest neighbors
        reduced_basis = get_basis(reg, radius)
        basis_size = len(reduced_basis)
        
        # 3. Time the simulation
        psi0 = np.zeros(basis_size, dtype=complex)
        psi0[0] = 1.0 # |g> state
        
        start = time.time()
        # Integrate for 1.0s (adaptive steps handled by Julia)
        solve(reg, psi0, 0.0, 1.0, omega=2.0*np.pi*1.0, delta=0.0, blockade_radius=radius)
        dt = time.time() - start
        
        print(f"{n:<8} | {2**n:<12} | {basis_size:<8} | {dt:.4f}")

    print("="*40)

if __name__ == "__main__":
    benchmark_scaling()
