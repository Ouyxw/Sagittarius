# Phase 16 Benchmark Protocol

Status: `Planned contract`
Roadmap: Phase 16
Version: `benchmark-protocol/v1`
Last reviewed: 2026-07-02

This protocol defines how Sagittarius Phase 16 benchmarks should be selected, run, recorded, and interpreted. It is intentionally separate from installation validation. Installation CI proves that the package can be installed and smoke-tested. Benchmark protocols produce scientific, correctness, and performance evidence under explicit configurations.

## Scope

Phase 16 benchmark work covers:

- physics baseline checks such as Rabi oscillation, Rydberg blockade, Landau-Zener sweeps, and dense-vs-reduced validation;
- cold-atom dynamics such as chain excitation profiles, local addressing, Z2 ordering, and 2D pattern formation;
- open-system dynamics such as Lindblad, MCWF, decay, dephasing, and trajectory convergence;
- UDG/MWIS and weighted MWIS optimization workflows with exact baselines where tractable;
- solver and backend performance, including dense, sparse, reduced, CPU, CUDA, and solver-method sensitivity;
- parameter-sweep and cluster-oriented benchmark aggregation.

Out of scope for Phase 16:

- package installation readiness, which belongs to Phase 13;
- hardware-control or calibrated device claims;
- public quantum-speedup claims;
- unreviewed cross-machine performance comparisons.

## Execution Stages

1. Choose the benchmark family and tier from [`families.md`](families.md) and [`tiers.md`](tiers.md).
2. Freeze the scenario: problem size, geometry, seed, pulse schedule, solver settings, observables, backend, and timeout.
3. Run environment diagnostics before benchmark execution, including `doctor()` where backend behavior matters.
4. Run warmup iterations separately from measured iterations.
5. Validate correctness gates before interpreting timing, memory, GPU, or scaling metrics.
6. Emit aggregate artifacts following [`artifact-contracts.md`](artifact-contracts.md).
7. Preserve failed cases as benchmark rows with diagnostic context.
8. Classify evidence as exploratory, reviewable, or release-grade.
9. For public use, review wording against governance documents and create or update the disclosure row.

## Required Pre-Run Record

Every benchmark run should record:

- git commit and dirty state;
- Python, Julia, Sagittarius Python package, and Sagittarius.jl versions when available;
- operating system, CPU model, total memory, container status, and accelerator device when available;
- benchmark family, tier, scenario ID, and protocol version;
- exact command and working directory;
- environment variables that affect solver, backend, threading, or GPU behavior;
- timeout policy and failure policy;
- artifact output directory.

## Warmup and Measurement Rules

Recommended defaults:

- 1 to 3 warmup runs for each scenario;
- at least 5 measured repeats for release-grade runtime claims;
- separate first-run CUDA setup timing from warmed execution timing when initialization cost is material;
- record median, min, max, p25, and p75 for repeated runtime rows;
- record peak process memory where available;
- record GPU memory before and after CUDA scenarios when the runtime exposes it;
- treat incomplete metadata or failed correctness validation as diagnostic output, not performance evidence.

## Correctness Before Performance

Performance numbers are interpretable only after the relevant correctness checks pass:

- analytic reference for simple Rabi, blockade, and Landau-Zener cases where feasible;
- dense reference for small full-vs-reduced comparisons;
- exact ILP or declared exact solver for small MWIS instances;
- CPU/CUDA parity for GPU timing claims where the same scenario is tractable on both paths;
- Lindblad trace and positivity checks for open-system density-matrix runs;
- MCWF convergence sanity checks against Lindblad results on small systems;
- solver-method sensitivity check for scenarios known to be numerically stiff.

## Evidence Classification

| Evidence class | Minimum requirements | Typical use |
| :--- | :--- | :--- |
| Exploratory local | Scenario command, commit, local hardware notes, and failure/success status. | Developer investigation and local RTX 5070 Ti probing. |
| Reviewable project | Structured aggregate artifact, run manifests or result artifacts, diagnostics, correctness checks, and failure rows. | Internal planning and release candidate review. |
| Release-grade | Reviewable project evidence plus repeated measurements, governance review, disclosure row, and bounded wording. | Public release notes, README updates, reports, or papers. |

## Reporting Boundary

Benchmark reports must use bounded wording. A valid report names artifact path, commit, hardware, backend, scenario, solver settings, and metric name. Avoid general claims such as "CUDA is faster" or "Sagittarius solves MWIS efficiently" unless the claim is explicitly bounded to one artifact and scenario.
