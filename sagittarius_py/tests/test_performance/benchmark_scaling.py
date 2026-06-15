import time

import numpy as np

from sagittarius import (
    Atom,
    PulseSequence,
    Register,
    Simulation,
    SolverConfig,
    current_memory_usage,
    write_benchmark_artifacts,
)


def benchmark_scaling(n_max=16, blockade_radius=5.0, output_dir="."):
    print(f"Benchmarking scaling up to N={n_max} atoms...")
    results = []
    run_manifests = []

    for n in range(2, n_max + 1):
        reg = Register([Atom(i * 4.0, 0) for i in range(n)], C6=100.0)
        seq = PulseSequence(omega=2 * np.pi, delta=0.0)
        config = SolverConfig(blockade_radius=blockade_radius)

        sim = Simulation(reg, seq, config)
        basis_size = sim.validate()

        psi0 = np.zeros(basis_size, dtype=complex)
        psi0[0] = 1.0

        start = time.perf_counter()
        res = sim.run(psi0, 0.0, 0.5, observables={"pop0": 0})
        elapsed = time.perf_counter() - start
        memory = current_memory_usage()

        print(f"N={n:2d} | Basis={basis_size:6d} | Time={elapsed:6.4f}s")

        results.append({
            "N": n,
            "basis_size": basis_size,
            "full_dim": 2 ** n,
            "time_s": elapsed,
            "max_rss": memory["max_rss"],
            "max_rss_unit": memory["max_rss_unit"],
        })
        run_manifests.append({
            "label": f"N={n}",
            "manifest": res.manifest,
        })

    paths = write_benchmark_artifacts(
        output_dir=output_dir,
        stem="scaling_results",
        name="Reduced-basis scaling benchmark",
        description="CPU timing as atom count and blockade-reduced basis size grow.",
        parameters={
            "n_min": 2,
            "n_max": n_max,
            "blockade_radius": blockade_radius,
            "duration": 0.5,
            "observable": "pop0",
        },
        rows=results,
        backend="CPU",
        run_manifests=run_manifests,
        columns=["N", "basis_size", "full_dim", "time_s", "max_rss", "max_rss_unit"],
    )
    print(f"\nScaling benchmark complete. Results saved to {paths['json']}")
    return paths


if __name__ == "__main__":
    benchmark_scaling()
