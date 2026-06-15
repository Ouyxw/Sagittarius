import time

import numpy as np

from sagittarius import ParallelSimulation, current_memory_usage, write_benchmark_artifacts
from juliacall import Main as jl


def benchmark_cluster(output_dir="."):
    print("Benchmarking Cluster efficiency (Rabi Sweep)...")

    jl.seval("""
    @everywhere function run_single_sim(omega)
        reg = Register([Atom(SVector(0.0))], 0.0)
        seq = PulseSequence(omega, 0.0)
        config = SolverConfig()
        psi0 = ComplexF64[1.0, 0.0]
        sol = solve_schrodinger(psi0, build_hamiltonian_func(reg, t->[omega], t->[0.0]), (0.0, 1.0))
        return sol.t[end]
    end
    """)

    params = list(np.linspace(0.1, 10.0, 20))

    results = []
    for n in [1, 2, 4]:
        psim = ParallelSimulation(n_workers=n)

        start = time.perf_counter()
        res = psim.map("run_single_sim", params)
        elapsed = time.perf_counter() - start
        memory = current_memory_usage()

        print(f"Workers={n:d} | Time={elapsed:6.3f}s")
        results.append({
            "workers": n,
            "parameter_count": len(params),
            "time_s": elapsed,
            "completed_results": len(res),
            "max_rss": memory["max_rss"],
            "max_rss_unit": memory["max_rss_unit"],
        })

    paths = write_benchmark_artifacts(
        output_dir=output_dir,
        stem="cluster_bench_results",
        name="Cluster Rabi sweep benchmark",
        description="Distributed parameter sweep timing across worker counts.",
        parameters={
            "worker_counts": [1, 2, 4],
            "parameter_count": len(params),
            "omega_min": min(params),
            "omega_max": max(params),
        },
        rows=results,
        backend="CPU",
        columns=["workers", "parameter_count", "time_s", "completed_results", "max_rss", "max_rss_unit"],
    )
    print(f"Cluster benchmark complete. Results saved to {paths['json']}")
    return paths


if __name__ == "__main__":
    benchmark_cluster()
