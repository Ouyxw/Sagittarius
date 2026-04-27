import time
import numpy as np
import pandas as pd
from sagittarius import ParallelSimulation, Atom, Register, Simulation, PulseSequence, SolverConfig
from juliacall import Main as jl

def benchmark_cluster():
    print("Benchmarking Cluster efficiency (Rabi Sweep)...")
    
    # Define a simulation function in Julia on all workers
    jl.seval("""
    @everywhere function run_single_sim(omega)
        reg = Register([Atom(SVector(0.0))], 0.0)
        seq = PulseSequence(omega, 0.0)
        config = SolverConfig()
        # Initial state |g>
        psi0 = ComplexF64[1.0, 0.0]
        # Run
        sol = solve_schrodinger(psi0, build_hamiltonian_func(reg, t->[omega], t->[0.0]), (0.0, 1.0))
        return sol.t[end]
    end
    """)
    
    params = list(np.linspace(0.1, 10.0, 20)) # 20 simulations
    
    results = []
    for n in [1, 2, 4]:
        psim = ParallelSimulation(n_workers=n)
        
        start = time.time()
        # Use our map method
        res = psim.map("run_single_sim", params)
        elapsed = time.time() - start
        
        print(f"Workers={n:d} | Time={elapsed:6.3f}s")
        results.append({"workers": n, "time": elapsed})
        
    df = pd.DataFrame(results)
    df.to_csv("cluster_bench_results.csv", index=False)

if __name__ == "__main__":
    benchmark_cluster()
