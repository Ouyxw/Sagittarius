import time
import numpy as np
import pandas as pd
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

def benchmark_scaling(n_max=16, blockade_radius=5.0):
    print(f"Benchmarking scaling up to N={n_max} atoms...")
    results = []
    
    for n in range(2, n_max + 1):
        # 1. Setup
        reg = Register([Atom(i*4.0, 0) for i in range(n)], C6=100.0)
        seq = PulseSequence(omega=2*np.pi, delta=0.0)
        config = SolverConfig(blockade_radius=blockade_radius)
        
        sim = Simulation(reg, seq, config)
        basis_size = sim.validate()
        
        psi0 = np.zeros(basis_size, dtype=complex)
        psi0[0] = 1.0
        
        # 2. Measure
        start = time.time()
        res = sim.run(psi0, 0.0, 0.5) # Short integration
        end = time.time()
        
        elapsed = end - start
        print(f"N={n:2d} | Basis={basis_size:6d} | Time={elapsed:6.4f}s")
        
        results.append({
            "N": n,
            "basis_size": basis_size,
            "time": elapsed,
            "full_dim": 2**n
        })
        
    df = pd.DataFrame(results)
    df.to_csv("scaling_results.csv", index=False)
    print("\nScaling benchmark complete. Results saved to scaling_results.csv")

if __name__ == "__main__":
    benchmark_scaling()
