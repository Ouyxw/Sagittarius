# Benchmarking Plan

Spec ID: `SPEC-GOV-004`
Status: `Policy`
Roadmap: Phase 9, Phase 10, Phase 11, Phase 12, Phase 14, Phase 15, Phase 16, Phase 18
Version: `benchmarking-plan/v1`
Last reviewed: 2026-06-30


This document defines the Sagittarius benchmarking plan. It complements [`SPEC-GOV-001-performance-claims.md`](SPEC-GOV-001-performance-claims.md): this page defines what to run and how to organize evidence, while `SPEC-GOV-001` defines how measured performance may be stated publicly.

Benchmarking in Sagittarius is evidence production, not marketing. Every public number should be traceable to reproducible artifacts, bounded hardware and solver settings, and known limitations.

## Goals

The benchmark program has three goals:

- verify that optimized execution paths preserve scientific behavior on representative small systems;
- characterize runtime, memory, basis size, and observable overhead under explicit configurations;
- produce artifact-backed evidence that can be safely cited in releases, reports, papers, and demos.

Benchmarks must not be used to imply general quantum speedup, production-ready GPU support, or broad hardware-control capability.

## Benchmark Layers

| Layer | Purpose | Output |
| :--- | :--- | :--- |
| Correctness-first benchmarks | Confirm dense/reduced, CPU/CUDA, Lindblad/MCWF, and Python/Julia semantics on small fixtures before performance numbers are interpreted. | Test results, run manifests, parity artifacts where available. |
| Performance-characterization benchmarks | Measure runtime, memory, basis size, observable cost, backend behavior, and solver sensitivity for bounded configurations. | `benchmark-artifact/v1` JSON with CSV and Markdown companions. |
| Application benchmarks | Exercise end-to-end cold-atom and quantum-computing workflows such as Rabi, blockade, Landau-Zener, open-system decay/dephasing, and UDG/MWIS studies. | Result artifacts, benchmark artifacts, verification reports, and disclosure-ready summaries. |

## Benchmark Suites

| Suite | Priority | Scope | Evidence |
| :--- | :--- | :--- | :--- |
| `scaling` | P0 | Reduced-basis CPU scaling across atom count, geometry, basis size, and blockade radius. | `benchmark-artifact/v1` from `benchmark_scaling.py`. |
| `ablation` | P0 | Full dense, full sparse, reduced matrix-free, reduced sparse, and optional CUDA cached sparse paths. | `benchmark-artifact/v1` from `benchmark_ablation.py`. |
| `gpu` | P1 | CPU/CUDA timing and observable parity on machines where CUDA diagnostics pass. | `benchmark-artifact/v1` from `benchmark_gpu.py` plus backend diagnostics. |
| `mwis_udg` | P1 | Seeded UDG/MWIS AQC-vs-ILP verification, feasibility, objective value, and runtime. | `mwis-batch-verification/v1` and linked result artifacts. |
| `solver` | P1 | Solver method, tolerance, adaptive/fixed-step, `dt`, and output-grid sensitivity. | `benchmark-artifact/v1`; depends on Phase 12 and Phase 15 contracts. |
| `observables` | P1 | Observable type, count, declaration order, and output-grid cost. | `benchmark-artifact/v1` plus observable metadata; depends on Phase 11. |
| `open_system` | P1 | Lindblad vs MCWF runtime, memory, trajectory count, and convergence behavior. | Benchmark artifacts, run manifests, and convergence notes. |
| `noise` | P2 | Custom Lindblad, correlated noise, collective decay, and stochastic Hamiltonian ensemble overhead. | Benchmark artifacts with noise metadata; depends on Phase 14 and Phase 15. |
| `cluster_sweep` | P2 | Parallel parameter sweep throughput, resumability, and artifact aggregation. | `benchmark-artifact/v1` or sweep artifacts; tied to Phase 17. |

## Required Row Metadata

Every benchmark row should record enough context to reproduce or audit the measurement:

- benchmark name, suite, scenario, and artifact schema version;
- problem type, atom count, register geometry, blockade radius, and basis mode;
- full or reduced basis size and pruning ratio where applicable;
- pulse schedule identifier and relevant pulse parameters;
- solver method, tolerances, `adaptive`, `dt`, and output-grid settings where applicable;
- backend, accelerator device, container status, and `doctor()` diagnostics;
- observable declarations, observable count, and output sample count;
- open-system path, noise model, rates, trajectory count, and seed metadata where applicable;
- runtime metric names, memory metric names, repeat index, warmup status, and aggregate statistics;
- `version-info/v1`, git commit, dirty state, Python version, Julia version, and package versions;
- linked `run-manifest/v1`, result artifact paths, and generated report stems.

## Running Discipline

Benchmark scripts should separate warmup runs from measured runs.

Recommended defaults:

- 1 to 3 warmup runs per scenario;
- at least 5 measured repeats for runtime claims;
- median, min, max, p25, and p75 for reported runtime summaries;
- separate first-run and warmed timing for GPU paths when initialization cost is material;
- fixed seeds for stochastic workflows once Phase 15 seed contracts are available;
- no public comparison across machines unless both artifact sets name hardware, backend diagnostics, container status, and version metadata.

If a benchmark fails validation or emits incomplete metadata, its runtime numbers should be treated as diagnostic output only.

## Correctness Gates

Performance results are publishable only after the relevant correctness gates pass:

- dense/full-basis and blockade-reduced observables agree on small systems within declared tolerances;
- Python and Julia golden tests preserve atom ordering, bitstring ordering, Hamiltonian semantics, pulse addressing, solver settings, and result metadata;
- CPU and CUDA smoke parity passes for the measured GPU scenario when CUDA is discussed;
- Lindblad trace preservation and density-matrix positivity checks pass for open-system scenarios;
- MCWF results converge toward Lindblad observables on small systems as trajectory count increases;
- MWIS examples are checked against exact ILP or another declared exact baseline;
- solver-sensitive scenarios include a tighter-tolerance or smaller-step sanity comparison.

## Reporting Rules

Benchmark reports should use bounded wording from [`SPEC-GOV-001-performance-claims.md`](SPEC-GOV-001-performance-claims.md).

Allowed pattern:

```text
In artifact <path>, benchmark <name> measured <metric> on <hardware>
for <problem/config>.
```

Avoid unqualified claims such as:

- "Sagittarius scales linearly";
- "CUDA is faster";
- "Sagittarius efficiently solves MWIS";
- "the GPU backend is production-ready";
- "Sagittarius demonstrates quantum speedup".

For public reports, create or update a disclosure row in [`SPEC-GOV-002-disclosure-control.md`](SPEC-GOV-002-disclosure-control.md) and review prior-art-sensitive wording against [`SPEC-GOV-003-prior-art-notes.md`](SPEC-GOV-003-prior-art-notes.md).

## Release Cadence

| Event | Required benchmark action |
| :--- | :--- |
| Pull request | Run correctness smoke tests and small benchmark sanity checks where the change touches solver, backend, observable, artifact, or performance code. Do not publish PR-local timing as a project claim. |
| Release candidate | Run P0 benchmark suites, archive generated artifacts, and verify companion CSV/Markdown reports. |
| Public release or benchmark report | Attach artifact paths, version metadata, run manifests, disclosure row, and bounded wording review. |
| Hardware/backend change | Regenerate backend diagnostics and rerun affected CPU/GPU parity and ablation benchmarks. |
| Solver, observable, seed, noise, or artifact-schema change | Rerun the corresponding P1/P2 suite and update this plan if required metadata changes. |

## Roadmap Alignment

- Phase 9 provides scientific verification and baseline benchmark scripts.
- Phase 10 provides performance-claim governance, disclosure control, prior-art notes, and known limitations.
- Phase 11 should add observable metadata to benchmark rows and manifests.
- Phase 12 should add effective solver configuration and solver-sensitivity benchmarks.
- Phase 14 should add theory-noise benchmark scenarios and noise metadata.
- Phase 15 should add seed and output-grid reproducibility for MCWF, sampling, stochastic noise, and benchmark scripts.
- Phase 16 defines application benchmark protocols and artifact expectations.
- Phase 18 should add cluster and advanced deployment benchmarks without weakening artifact or disclosure requirements.

## Maintenance Triggers

Update this document when:

- a benchmark script is added, removed, renamed, or changes artifact shape;
- `benchmark-artifact/v1`, `run-manifest/v1`, or `version-info/v1` changes;
- public performance wording policy changes;
- GPU, solver, observable, open-system, noise, or sweep behavior changes;
- new release or disclosure workflows require different benchmark evidence.
