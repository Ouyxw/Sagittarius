import numpy as np
import pytest
import time
from sagittarius import Atom, Register, SagittariusSolverError, Simulation, PulseSequence, SolverConfig

def test_gpu_vs_cpu():
    # Large-ish system to see some benefit, or at least verify correctness
    # Let's use 10 atoms
    N = 10
    reg = Register([Atom(i*5.0, 0) for i in range(N)], C6=100.0)
    
    # Global drive
    seq = PulseSequence(omega=2*np.pi * 1.0, delta=2*np.pi * 0.1)
    
    # Start in |g...g>
    psi0 = np.zeros(2**N, dtype=complex)
    psi0[0] = 1.0
    
    t_end = 1.0
    observables = {"pop0": 0, f"pop{N-1}": N-1}
    
    # 1. CPU Run
    config_cpu = SolverConfig()
    sim_cpu = Simulation(reg, seq, config_cpu)
    
    start_cpu = time.time()
    res_cpu = sim_cpu.run(psi0, 0.0, t_end, observables=observables)
    end_cpu = time.time()
    print(f"CPU time: {end_cpu - start_cpu:.4f}s")
    
    # 2. GPU Run
    config_gpu = SolverConfig(use_gpu=True)
    sim_gpu = Simulation(reg, seq, config_gpu)
    
    start_gpu = time.time()
    try:
        res_gpu = sim_gpu.run(psi0, 0.0, t_end, observables=observables)
    except SagittariusSolverError as exc:
        pytest.skip(f"CUDA solver unavailable in this runtime: {exc.issue.code}")
    end_gpu = time.time()
    print(f"GPU time: {end_gpu - start_gpu:.4f}s")
    
    # 3. Compare
    for key in observables.keys():
        cpu_vals = np.array(res_cpu.data[key])
        gpu_vals = np.array(res_gpu.data[key])
        
        # Interpolate if time steps differ
        gpu_interp = np.interp(res_cpu.t, res_gpu.t, gpu_vals)
        
        mean_diff = np.mean(np.abs(cpu_vals - gpu_interp))
        print(f"Mean diff for {key}: {mean_diff}")
        assert mean_diff < 1e-4

if __name__ == "__main__":
    test_gpu_vs_cpu()
    print("GPU acceleration test passed!")
