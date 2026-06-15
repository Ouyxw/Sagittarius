import argparse

import numpy as np

from sagittarius import (
    PulseSequence,
    Register,
    doctor,
    write_benchmark_artifacts,
)
from sagittarius.ablation import benchmark_ablation_modes


def benchmark_ablation(
    atom_count=10,
    spacing=2.0,
    blockade_radius=3.0,
    repeats=25,
    include_gpu=False,
    output_dir=".",
):
    print("Benchmarking Hamiltonian execution path ablations...")
    register = Register.chain(atom_count, spacing=spacing, C6=100.0)
    sequence = PulseSequence(omega=2 * np.pi, delta=0.0)

    rows, run_manifests = benchmark_ablation_modes(
        register,
        sequence,
        blockade_radius=blockade_radius,
        repeats=repeats,
        include_gpu=include_gpu,
    )

    for row in rows:
        if row["status"] == "ok":
            print(
                f"{row['mode']:<28} | {row['backend']:<4} | {row['basis_size']:>7} | "
                f"{row['time_per_operation_s']:.6g}s/{row['workload']}"
            )
        else:
            print(f"{row['mode']:<28} | skipped | {row['reason']}")

    diagnostics = doctor(backend="CUDA" if include_gpu else "CPU", initialize_backend=False)
    paths = write_benchmark_artifacts(
        output_dir=output_dir,
        stem="ablation_bench_results",
        name="Hamiltonian execution path ablation benchmark",
        description="Compares full dense, full sparse, reduced matrix-free, reduced sparse, and reduced sparse CUDA-cached execution paths.",
        parameters={
            "atom_count": atom_count,
            "spacing": spacing,
            "C6": 100.0,
            "blockade_radius": blockade_radius,
            "repeats": repeats,
            "include_gpu": include_gpu,
            "omega": float(2 * np.pi),
            "delta": 0.0,
        },
        rows=rows,
        backend="CUDA" if include_gpu else "CPU",
        diagnostics=diagnostics,
        run_manifests=run_manifests,
        columns=[
            "mode",
            "status",
            "backend",
            "workload",
            "representation",
            "atom_count",
            "full_dim",
            "basis_size",
            "repeats",
            "duration_s",
            "total_time_s",
            "time_per_operation_s",
            "reference_error",
            "max_rss",
            "max_rss_unit",
            "reason",
        ],
    )
    print(f"Ablation benchmark complete. Results saved to {paths['json']}")
    return paths


def _parse_args():
    parser = argparse.ArgumentParser(description="Run Sagittarius ablation benchmarks.")
    parser.add_argument("--atom-count", type=int, default=10)
    parser.add_argument("--spacing", type=float, default=2.0)
    parser.add_argument("--blockade-radius", type=float, default=3.0)
    parser.add_argument("--repeats", type=int, default=25)
    parser.add_argument("--include-gpu", action="store_true", help="Run the CUDA cached sparse path when a backend is available.")
    parser.add_argument("--output-dir", default=".")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    benchmark_ablation(
        atom_count=args.atom_count,
        spacing=args.spacing,
        blockade_radius=args.blockade_radius,
        repeats=args.repeats,
        include_gpu=args.include_gpu,
        output_dir=args.output_dir,
    )
