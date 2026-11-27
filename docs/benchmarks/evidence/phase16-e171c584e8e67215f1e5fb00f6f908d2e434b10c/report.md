# Phase 16 Benchmark Summary Report

- Source commit: `e171c584e8e67215f1e5fb00f6f908d2e434b10c` (`e171c58`), with the artifact-recorded dirty-state flag.
- Evidence archive: [`phase16-e171c584e8e67215f1e5fb00f6f908d2e434b10c`](README.md).
- Evidence class: reviewable local evidence.
- Disclosure: `DISC-0002` is internal-only; all benchmark rows are `local_only`.

## Scope and interpretation

This report summarizes retained benchmark artifacts. It is not release-grade performance evidence and makes no cross-machine, general GPU-speedup, scalability, hardware-control, or optimization-quality claim.

## Environment

- Execution date: 2026-08-12 UTC in the WSL2 devcontainer.
- Runtime: Python 3.10.12, Julia 1.11.9, Sagittarius Python/Julia 1.0.8.
- Accelerator: NVIDIA GeForce RTX 5070 Ti, driver 591.86, CUDA runtime 12.8, CUDA.jl 6.2.0.
- CUDA status: experimental; device memory snapshots were unavailable from this runtime and are recorded as `missing` in the CUDA rows.

## Correctness and application results

### Physics baselines and dynamics

- CPU smoke passed for one-atom Rabi (`5.52e-11` maximum error) and two-atom reduced-basis blockade (zero forbidden-double-excitation error).
- CPU correctness passed analytic Rabi (`7.97e-11`), ideal blockade (`5.10e-11`), Landau-Zener final-state error (`1.08e-3` against a `1.5e-2` tolerance), and projected dense-vs-reduced three-atom chain (zero Hamiltonian and state error).
- Four cold-atom dynamics cases—global chain, local addressing, Z2 chain, and 2x2 array—passed their projected dense references at `1e-8` tolerance.

### Open-system dynamics

- Seeded local decay/dephasing passed analytic decay with `4.24e-11` error, Lindblad trace error `1.11e-16`, and minimum density eigenvalue `0`.
- MCWF/Lindblad mean absolute error improved from `2.49e-2` at 100 trajectories to `1.44e-2` at 500 trajectories for seed `20260811`.

### MWIS/UDG AQC

- Deterministic smoke, correctness, and bounded-scaling instances from two to six nodes all retained feasible candidates and optimal PuLP/CBC status.
- The selected AQC candidates in this archive have objective value zero and therefore do not match the exact optimum; their objective gaps and final optimal-success probabilities are retained in `mwis_aqc_*.json`.
- These rows validate mapping, reference, feasibility, and artifact behavior—not general MWIS solution quality or optimization performance.

### Solver and execution paths

- Dense, sparse, reduced matrix-free, and reduced sparse CPU paths passed both repeats; cached GPU-path rows are explicitly skipped in this CPU protocol.
- Full-path absolute roundoff errors were retained together with scale-normalized errors (`3.01e-17` and `3.30e-16`), both below the declared `1e-12` relative gate; reduced-path absolute errors were zero.
- Tsit5, Vern9, and fixed-step RK4 trajectories all passed against the high-accuracy Tsit5 reference with a `1e-6` tolerance.

### CUDA parity and stress

- Initialized CUDA doctor diagnostics passed before execution.
- The three-atom CPU/CUDA chain row passed with zero observable error at `1e-6` tolerance; cold-start and warm timings are retained but are local diagnostics only.
- The seeded two-node MWIS CPU/CUDA row passed probability parity with zero error and retained a feasible CUDA candidate; it does not demonstrate optimality.
- The 12-atom, 50-repeat ablation stress artifact retained dense, sparse, reduced, and cached-GPU rows. It is a local hardware-specific characterization, not a scale limit or speedup claim.

### Sweep execution

- Local `ParallelSimulation` sweeps with one and two workers completed four deterministic items each with zero reference error and persisted checkpoint, final sweep, result, and manifest artifacts.

## Artifact map

- Physics: `physics_smoke*.json`, `physics_correctness*.json`, `cold_atom_dynamics*.json`, and `open_system_dynamics*.json`.
- Optimization: `mwis_aqc_{smoke,correctness,scaling}*.json` and their exact-reference reports.
- Backend and execution: `solver_performance*.json`, `cuda_parity*.json`, `mwis_gpu_parity*.json`, and `ablation_bench_results.*`.
- Sweep and provenance: `sweep_cluster*.json`, `parallel-sweep-workers-*.sweep.json`, `*.result.json`, and `*.manifest.json`.

## Reproduction and disclosure

Use the commands and paths in the [closure record](README.md). Any public statement must cite its exact artifact, commit, hardware/runtime metadata, and complete the `DISC-0002` governance and disclosure review.
