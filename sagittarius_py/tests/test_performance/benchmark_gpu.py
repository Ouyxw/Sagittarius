import time

import numpy as np

from sagittarius import (
    Atom,
    PulseSequence,
    Register,
    Simulation,
    SolverConfig,
    current_memory_usage,
    doctor,
    write_benchmark_artifacts,
)
from juliacall import Main as jl


def benchmark_gpu(n_range=None, output_dir="."):
    if n_range is None:
        n_range = [10, 12, 14, 16, 18, 20]
    print("Benchmarking GPU vs CPU speedup (with Observables)...")
    results = []
    run_manifests = []
    diagnostics = doctor(backend="CUDA", initialize_backend=False)

    print("Warming up JIT...")
    reg_w = Register([Atom(i * 2.0, 0) for i in range(8)], C6=100.0)
    seq_w = PulseSequence(omega=2 * np.pi, delta=0.0)
    sim_w_cpu = Simulation(reg_w, seq_w, SolverConfig(blockade_radius=3.0))
    sim_w_gpu = Simulation(reg_w, seq_w, SolverConfig(blockade_radius=3.0, use_gpu=True))
    psi0_w = np.zeros(sim_w_cpu.validate(), dtype=complex)
    psi0_w[0] = 1.0
    sim_w_cpu.run(psi0_w, 0.0, 0.1, observables={"pop0": 0})
    sim_w_gpu.run(psi0_w, 0.0, 0.1, observables={"pop0": 0})
    jl.seval("CUDA.synchronize()")

    for n in n_range:
        reg = Register([Atom(i * 2.0, 0) for i in range(n)], C6=100.0)
        seq = PulseSequence(omega=2 * np.pi, delta=0.0)

        config_cpu = SolverConfig(blockade_radius=3.0)
        sim_cpu = Simulation(reg, seq, config_cpu)
        basis_size = sim_cpu.validate()
        psi0 = np.zeros(basis_size, dtype=complex)
        psi0[0] = 1.0

        start = time.perf_counter()
        cpu_res = sim_cpu.run(psi0, 0.0, 1.0, observables={"pop0": 0})
        t_cpu = time.perf_counter() - start

        config_gpu = SolverConfig(blockade_radius=3.0, use_gpu=True)
        sim_gpu = Simulation(reg, seq, config_gpu)

        sim_gpu.run(psi0, 0.0, 0.1, observables={"pop0": 0})
        jl.seval("CUDA.synchronize()")

        start = time.perf_counter()
        gpu_res = sim_gpu.run(psi0, 0.0, 1.0, observables={"pop0": 0})
        jl.seval("CUDA.synchronize()")
        t_gpu = time.perf_counter() - start
        memory = current_memory_usage()

        speedup = t_cpu / t_gpu
        print(f"N={n:2d} | Basis={basis_size:6d} | CPU={t_cpu:6.3f}s | GPU={t_gpu:6.3f}s | Speedup={speedup:5.2f}x")

        results.append({
            "N": n,
            "basis_size": basis_size,
            "t_cpu_s": t_cpu,
            "t_gpu_s": t_gpu,
            "speedup": speedup,
            "max_rss": memory["max_rss"],
            "max_rss_unit": memory["max_rss_unit"],
        })
        run_manifests.extend([
            {"label": f"N={n} CPU", "manifest": cpu_res.manifest},
            {"label": f"N={n} CUDA", "manifest": gpu_res.manifest},
        ])

    paths = write_benchmark_artifacts(
        output_dir=output_dir,
        stem="gpu_bench_results",
        name="CUDA vs CPU reduced-basis benchmark",
        description="CPU and CUDA timing comparison with observable evaluation.",
        parameters={
            "n_range": list(n_range),
            "blockade_radius": 3.0,
            "duration": 1.0,
            "observable": "pop0",
        },
        rows=results,
        backend="CUDA",
        diagnostics=diagnostics,
        run_manifests=run_manifests,
        columns=["N", "basis_size", "t_cpu_s", "t_gpu_s", "speedup", "max_rss", "max_rss_unit"],
    )
    print(f"GPU benchmark complete. Results saved to {paths['json']}")
    return paths


if __name__ == "__main__":
    benchmark_gpu()
