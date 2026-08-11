# Benchmark Families

Status: `Mixed implementation`
Roadmap: Phase 16
Version: `benchmark-families/v1`
Last reviewed: 2026-08-11

This page defines the benchmark-family protocols for Phase 16. A family is a stable group of scenarios with shared correctness gates, metadata, and interpretation rules.

## Family Summary

| Family | Initial scenarios | Primary evidence |
| :--- | :--- | :--- |
| Physics baselines | Single-atom Rabi, two-atom blockade, Landau-Zener sweep, dense-vs-reduced small chains. | Analytic or dense-reference errors, basis sizes, solver metadata, artifacts. |
| Cold-atom dynamics | Rydberg chains, local addressing, Z2 ordering, 2D pattern formation. | Observable trajectories, correlations, blockade violations, backend metadata. |
| Open-system dynamics | Lindblad decay/dephasing, MCWF-vs-Lindblad, decoherence impact. | Trace and positivity checks, trajectory variance, runtime/memory scaling, seed metadata. |
| Optimization/AQC | UDG/MWIS, weighted MWIS, schedule sensitivity, structured graph families. | Feasibility, exact optimum where available, objective value, approximation ratio. |
| Backend performance | Dense/sparse/reduced ablation, CPU/CUDA parity, solver sensitivity, CUDA cached path. | Runtime, memory, GPU memory, max trajectory error, bounded speedup statements. |
| Sweep/cluster execution | Parameter sweeps, phase-diagram scans, cluster throughput. | Jobs/sec, resumability, per-run manifest links, aggregate artifacts, failure rows. |

## Physics Baselines

Purpose: prove that basic neutral-atom dynamics and reduced-basis behavior are physically and numerically coherent.

Initial protocol items:

- Rabi oscillation validates drive amplitude, duration, unit convention, and population transfer shape.
- Two-atom blockade validates interaction strength, blockade radius expectations, and double-excitation suppression.
- Landau-Zener sweep validates detuning-ramp handling, adiabatic-transfer behavior, and solver sensitivity.
- Small-chain full-vs-reduced validation compares full Hilbert-space results to blockade-reduced results.

Required evidence:

- scenario ID and physical parameter table;
- analytic or dense-reference output where feasible;
- max trajectory deviation and final-state deviation;
- solver method, tolerances, output grid, and basis mode;
- run manifest and result artifact path when a simulation artifact is emitted.

Current correctness runner: `tests/test_performance/benchmark_physics_correctness.py` records analytic Rabi and ideal-blockade errors, finite-sweep Landau-Zener final-state error against the stated asymptotic formula, and a static small-chain exact projected dense matrix-exponential comparison. The small-chain check verifies the reduced Hamiltonian and evolution against the projection of the dense Hamiltonian; it does not claim physical equivalence between finite-interaction full-basis and hard-blockade trajectories.

## Cold-Atom Dynamics

Purpose: exercise realistic neutral-atom array workflows beyond toy baselines.

Initial protocol items:

- chain excitation profiles under global and local addressing;
- local-addressing sparse dictionary stress cases;
- Z2 or antiferromagnetic ordering dynamics;
- 2D array pattern formation with blockade diagnostics.

Current correctness runner: `tests/test_performance/benchmark_phase16_validation.py` emits one row per CPU case: 3-atom global chain, 3-atom vector/dictionary local addressing, 4-atom alternating-detuning Z2 chain, and a 2x2 array. Each uses a small projected dense matrix-exponential reference with absolute tolerance `1e-8`. These rows establish only small-system solver and pulse/geometry correctness, not a physical pattern-formation or scalability claim.

Required evidence:

- atom geometry and atom-ordering metadata;
- pulse schedule and addressing map;
- observable declarations and output sample count;
- pair-correlation or blockade-violation metrics when the observable API supports them;
- solver/backend metadata and failure diagnostics.

## Open-System Dynamics

Purpose: validate and characterize theory-noise and trajectory workflows.

Initial protocol items:

- Lindblad decay and dephasing on small systems;
- MCWF-vs-Lindblad agreement as trajectory count increases;
- decoherence impact on blockade and ordering scenarios;
- future Phase 14 custom noise and stochastic Hamiltonian scenarios.

Current correctness runner: `tests/test_performance/benchmark_phase16_validation.py` emits fixed-seed (`20260811`) one-atom decay-plus-dephasing rows for 100 and 500 MCWF trajectories. They retain analytic decay expectation, Lindblad trace and positivity errors, MCWF-vs-Lindblad error, and require the 500-trajectory error not to exceed the 100-trajectory error. This is a small-system correctness check; multi-atom decoherence studies and trajectory runtime/memory scaling remain future work.

Required evidence:

- noise model, rates, and affected atoms or weights;
- trace-preservation and density-matrix positivity checks;
- trajectory count, seed metadata, and convergence summary;
- runtime and memory scaling for trajectory count;
- explicit unsupported-combination failures.

## Optimization/AQC

Purpose: validate UDG/MWIS mappings and optimization-like schedules without overstating algorithmic capability.

Initial protocol items:

- seeded UDG generation;
- small exact ILP baseline comparison;
- weighted MWIS objective evaluation;
- schedule sensitivity over drive and detuning ramps;
- final bitstring sampling once Phase 15 readout APIs land.

Current correctness runner: `tests/test_performance/benchmark_mwis_aqc.py` runs deterministic weighted UDG cases across `smoke` (2 nodes), `correctness` (3/4 nodes), and bounded `scaling` (2/4/6 nodes) tiers. Each row retains the seeded edge list, node weights, graph hash, AQC schedule, exact PuLP/CBC objective, feasibility, objective gap, approximation ratio, final-state optimal-solution probability, and a reference report. Per-scenario ILP or solver exceptions remain failed rows. These CPU cases validate the mapping and evidence contract only; their runtime and approximation outputs are not general AQC performance claims.

Required evidence:

- graph seed, geometry, radius, weights, and edge list hash;
- exact baseline method and exact objective where tractable;
- feasibility, objective value, objective gap, approximation ratio, and success probability when sampling exists;
- schedule metadata and solver settings;
- failure rows for ILP failure, infeasible output, timeout, or memory failure.

## Backend Performance

Purpose: characterize execution paths and backend behavior under bounded scenarios.

Initial protocol items:

- dense vs sparse vs reduced ablation;
- CPU vs CUDA parity and timing;
- solver method sensitivity;
- CUDA cached sparse-buffer path;
- first-run setup cost vs warmed execution cost.

Current CUDA protocol: `tests/test_performance/benchmark_cuda_mwis_protocol.py` is opt-in (`SAGITTARIUS_ENABLE_GPU_TESTS=1`) and calls `doctor(backend="CUDA", initialize_backend=True)` before importing or executing CUDA paths. It emits a small CPU/CUDA chain parity row and a seeded weighted-MWIS CPU/CUDA row with device, driver, CUDA.jl/runtime, and Julia metadata; cold/warm timing; GPU-memory snapshots; parity error; and structured skipped/doctor/runtime failure rows. It is local diagnostic evidence only.

Current solver/path protocol: `tests/test_performance/benchmark_solver_performance.py` repeats full dense, full sparse, reduced matrix-free, and reduced sparse matvec paths; it records a skipped cached-GPU row until the opt-in CUDA protocol validates that backend. Full-path repeated matvec comparison uses a `1e-7` numerical gate; reduced paths use `1e-10`. Tsit5, Vern9, and fixed-step RK4 trajectories use a high-accuracy Tsit5 trajectory reference with a `1e-6` gate and retain result/manifest links.

Required evidence:

- backend diagnostics before execution;
- CPU and accelerator hardware metadata;
- effective solver method and backend path;
- runtime, process memory, GPU memory where available, and validation metric;
- separate rows for backend initialization failure and numerical mismatch.

## Sweep/Cluster Execution

Purpose: validate batch execution, resumability, and aggregate evidence production.

Initial protocol items:

- parameter sweeps over `omega`, `delta`, blockade radius, geometry, noise, solver settings, and observables;
- phase-diagram scan scaffolding;
- `ParallelSimulation` throughput;
- future cluster execution through Phase 18 deployment work.

Current local protocol: `tests/test_performance/benchmark_sweep_cluster.py` checkpoints a `sweep-artifact/v1`, executes pending omega values through `ParallelSimulation.map()`, persists per-item result and manifest links, then writes a benchmark aggregate and suite row for each requested worker count. Passing `--resume-from` retries only the artifact's pending/running/failed IDs. This exercises local Julia `Distributed` workers and deterministic kernel correctness; it does not establish multi-node deployment or physics-solver throughput.

Required evidence:

- sweep config hash and parameter grid;
- per-run manifest or result artifact links;
- aggregate artifact row for every completed, skipped, and failed run;
- resumability metadata and restart behavior;
- throughput metrics only when correctness and artifact completeness pass.
