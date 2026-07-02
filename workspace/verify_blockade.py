import numpy as np
import time
from sagittarius.api import Atom, Register, solve

def run_blockade_test():
    print("Initializing 2-atom Rydberg Blockade simulation...")
    
    # 1. Setup Atoms
    # C6 = 100.0, Distance = 1.0 (Strong interaction)
    atom1 = Atom(0, 0, 0)
    atom2 = Atom(1.0, 0, 0)
    reg = Register([atom1, atom2], C6=100.0)
    
    # 2. Initial state: both atoms in ground state |gg>
    # Basis: |gg>, |rg>, |gr>, |rr>
    psi0 = np.zeros(4, dtype=complex)
    psi0[0] = 1.0
    
    # 3. Parameters
    omega = 2.0 * np.pi * 1.0  # Rabi frequency
    t_end = 2.0  # Simulation time
    
    # 4. Observables: Track Rydberg population of both atoms
    obs = {"atom1": 0, "atom2": 1}
    
    print(f"Running simulation with Omega={omega:.2f}...")
    start_time = time.time()
    
    results = solve(reg, psi0, 0.0, t_end, omega=omega, observables=obs)
    
    end_time = time.time()
    print(f"Simulation completed in {end_time - start_time:.4f} seconds.")
    
    # 5. Analysis
    # In a blockade regime, we expect atom1 and atom2 to oscillate, 
    # but the state |rr> should be suppressed.
    t = results['t']
    p1 = results['atom1']
    p2 = results['atom2']
    
    print("\nResults at t=t_end:")
    print(f"Time steps saved: {len(t)}")
    print(f"Final Population Atom 1: {p1[-1]:.4f}")
    print(f"Final Population Atom 2: {p2[-1]:.4f}")
    
    # Check for blockade: sum of populations should not exceed 1.0 significantly
    # if the blockade is perfect.
    max_total_pop = max([p1[i] + p2[i] for i in range(len(t))])
    print(f"Max Total Rydberg Population: {max_total_pop:.4f} (Expected < 1.0 for strong blockade)")

if __name__ == "__main__":
    run_blockade_test()
