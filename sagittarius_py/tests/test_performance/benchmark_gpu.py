import time
import numpy as np
import pandas as pd
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

def benchmark_gpu(n_range=[10, 12, 14, 15]):
    print("Benchmarking GPU vs CPU speedup...")
    results = []
    
    for n in n_range:
        # High density to ensure blockade basis is still large enough to stress GPU
        reg = Register([Atom(i*2.0, 0) for i in range(n)], C6=100.0)
        seq = PulseSequence(omega=2*np.pi, delta=0.0)
        
        # 1. CPU
        config_cpu = SolverConfig(blockade_radius=3.0)
        sim_cpu = Simulation(reg, seq, config_cpu)
        basis_size = sim_cpu.validate()
        psi0 = np.zeros(basis_size, dtype=complex)
        psi0[0] = 1.0
        
        start = time.time()
        sim_cpu.run(psi0, 0.0, 1.0)
        t_cpu = time.time() - start
        
        # 2. GPU
        config_gpu = SolverConfig(blockade_radius=3.0, use_gpu=True)
        sim_gpu = Simulation(reg, seq, config_gpu)
        
        # Warmup
        sim_gpu.run(psi0, 0.0, 0.1)
        
        start = time.time()
        sim_gpu.run(psi0, 0.0, 1.0)
        t_gpu = time.time() - start
        
        speedup = t_cpu / t_gpu
        print(f"N={n:2d} | Basis={basis_size:6d} | CPU={t_cpu:6.3f}s | GPU={t_gpu:6.3f}s | Speedup={speedup:5.2f}x")
        
        results.append({
            "N": n,
            "basis_size": basis_size,
            "t_cpu": t_cpu,
            "t_gpu": t_gpu,
            "speedup": speedup
        })
        
    df = pd.DataFrame(results)
    df.to_csv("gpu_bench_results.csv", index=False)

if __name__ == "__main__":
    benchmark_gpu()
