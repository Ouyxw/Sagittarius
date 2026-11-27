# Benchmarking Plan

Spec ID: `SPEC-GOV-004`
Status: `Policy`
Roadmap: Phase 9, Phase 10, Phase 11, Phase 12, Phase 14, Phase 15, Phase 16, Phase 18
Version: `benchmarking-plan/v1`
Last reviewed: 2026-11-27


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
| `gpu` | P1 | CPU/CUDA timing and observable parity on machines where initialized CUDA diagnostics pass. | `benchmark-artifact/v1` and `benchmark-suite-artifact/v1` from `benchmark_gpu.py` or opt-in `benchmark_cuda_mwis_protocol.py`, plus per-backend diagnostics, raw pairs and saved-result audit. |
| `mwis_udg` | P1 | Seeded UDG/MWIS AQC-vs-ILP verification, feasibility, objective value, and runtime. | `benchmark-artifact/v1` and suite aggregates from `benchmark_mwis_aqc.py`; `mwis-batch-verification/v1` remains the project-specific exact-verification helper. |
| `solver` | P1 | Solver method, tolerance, adaptive/fixed-step, `dt`, output-grid sensitivity, and dense/sparse/reduced path gates. | `benchmark-artifact/v1` from `benchmark_solver_performance.py`; depends on Phase 12 and Phase 15 contracts. |
| `observables` | P1 | Observable type, count, declaration order, and output-grid cost. | `benchmark-artifact/v1` plus observable metadata; depends on Phase 11. |
| `open_system` | P1 | Lindblad vs MCWF runtime, memory, trajectory count, and convergence behavior. | Benchmark artifacts, run manifests, and convergence notes. |
| `noise` | P2 | Custom Lindblad, correlated noise, collective decay, and stochastic Hamiltonian ensemble overhead. | Benchmark artifacts with noise metadata; depends on Phase 14 and Phase 15. |
| `cluster_sweep` | P2 | Local ParallelSimulation parameter-map throughput, resumability, and artifact aggregation. | `benchmark-artifact/v1` plus linked `sweep-artifact/v1` from `benchmark_sweep_cluster.py`; multi-node deployment remains tied to Phase 18. |

## Implementation and Evidence Tracking

This plan is ongoing policy, not a completed Phase 16 checklist. The [Phase 16 suite alignment matrix](../development/requirements.md#phase-16-alignment-with-spec-gov-004-benchmark-suites) maps all nine suites above, in the same order and with the same priorities, to implemented runners, retained evidence, remaining scope, dependencies, and acceptance conditions. The [cross-cutting alignment matrix](../development/requirements.md#phase-16-alignment-with-spec-gov-004-cross-cutting-requirements) tracks metadata, measurement discipline, correctness gates, reporting, release cadence, and maintenance. Keep implementation status in those matrices; this document remains the policy authority.

The [initial Phase 16 archive](../benchmarks/evidence/phase16-e171c584e8e67215f1e5fb00f6f908d2e434b10c/README.md) closes bounded small-system and local execution verification. It does not close all nine suites, a release-candidate P0 campaign, or public performance review. Noise benchmarking depends on Phase 14 model extensions; advanced cluster deployment and physics-solver sweep coverage remain tied to Phase 18. Completed API or artifact infrastructure is distinct from completed performance measurements.

The [P0–P1 implementation plan v2](../benchmarks/plans/v2.md) defines the seven-suite implementation batches, frozen measurement discipline and numerical/statistical acceptance targets. Its scaling, MWIS/UDG and open-system campaigns target 20 atoms with separate representation/basis resource limits. The scaling, ablation, GPU and MWIS runners implement their matrices and measurement controls; retained campaign acceptance is tracked in the requirements matrix. Other expanded targets remain planned measurements. Runner support alone does not establish retained coverage or a backend capability claim. Keep runner implementation, campaign execution and evidence review as separate milestones; resource exclusions and missing references remain visible. This policy's existing suite priorities, artifact schema meanings and recurring release gates continue to apply. P2 noise/cluster scope remains outside that implementation plan.

The [2026-11-26 local scaling archive](../benchmarks/evidence/p0-scaling-v2-2026-11-26/README.md) retains all 42 v2 scaling scenarios and an automated acceptance audit. Its same-method large-case references, shared-workstation timing and local-only evidence classification remain explicit. This closes the bounded local scaling campaign, not recurring RC, other-suite acceptance, independent disclosure review or public performance approval.

The [2026-11-27 local ablation archive](../benchmarks/evidence/p0-ablation-v2-2026-11-27/README.md)
retains all 16 targeted CPU paths, 80 independently measured batches and an
accepted saved-output/configuration/statistics audit. Four full-dimension
exclusions and five optional CUDA skips are retained. Python matvecs and CUDA
ODE solves remain different workloads; this CPU completion establishes no
CUDA parity, physical approximation validation, recurring RC or public-use approval.

The [2026-11-27 optional ablation CUDA follow-up](../benchmarks/evidence/p0-ablation-cuda-v2-2026-11-27/README.md)
retains five chain cases through N=20 with 25 independently measured CPU/CUDA
ODE pairs and audited full-grid numerical gates. It preserves initial failures
and interrupted progress separately from final accepted measurements. CUDA
remains experimental; same-method parity and unavailable peak memory do not
close the full P1 GPU matrix, physical validation, RC or public-use approval.

The [P1 GPU local campaign](../benchmarks/evidence/p1-gpu-v2-2026-11-27/README.md) completes the declared eight-case matrix: chains N=2,4,8,12,16,20, a 2x2 lattice and seeded two-node MWIS. All 40 measured CPU/CUDA pairs passed at 101 shared times after symmetric warmups; N=20 has D=17711. Separate backend memory, saved results/manifests, qualified median ratios and all companion values passed the backend-free audit. CUDA remains experimental; this is shared-workstation software/numerical evidence, not independent physical validation, recurring RC or public-use approval.

The [P1 MWIS/UDG local campaign](../benchmarks/evidence/p1-mwis-v2-2026-11-27/README.md) completes all 40 frozen instances through N=20 (five seeds per size), with 200 eligible AQC and 200 eligible ILP measurements. Independent DOP853/refinement, raw-norm checks, exhaustive graph objectives and CBC problem/solution optimality gate the results. Actual AQC result/manifests, native solver logs, per-path memory and all companion statistics pass the saved-evidence audit. Short-schedule suboptimal candidates remain valid data; different solution guarantees prevent an AQC/ILP speedup interpretation. This is bounded local numerical/software evidence, separate from scientific validation, general algorithm quality and release/public-use approval.

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

The first seven suites implement these rules through the
[v2 runtime reporting requirements](../benchmarks/plans/v2.md#runtime-reporting-requirements-for-all-seven-suites)
and suite-specific timer/output definitions. Performance acceptance includes
recomputable per-configuration distributions, raw membership/counts, explicit
workload and phase boundaries, and matching JSON/CSV/Markdown summaries.
Report numerical error, optimization quality/termination or stochastic
uncertainty beside time. Single setup measurements and timeout elapsed time
must not masquerade as repeated successful execution statistics. Correctness-only
controls and invalid-configuration tests need no dedicated performance campaign;
no performance gate requires CUDA or another implementation to be faster.

The [P0 timing report](../benchmarks/reports/p0-runtime-statistics-2026-11-27.md)
reorganizes existing scaling/CPU-ablation/CUDA-follow-up measurements without
modifying archives or rerunning simulations. Such presentation changes do not
advance evidence status or satisfy a new current-code, controlled-comparison,
RC or public-use gate. Expanded P1 outputs remain planned until implemented
and accepted; the release cadence below continues to apply.

## Correctness Gates

Performance results are publishable only after the relevant correctness gates pass:

- dense/full-basis and blockade-reduced observables agree on small systems within declared tolerances;
- Python and Julia golden tests preserve atom ordering, bitstring ordering, Hamiltonian semantics, pulse addressing, solver settings, and result metadata;
- CPU and CUDA smoke parity passes for the measured GPU scenario when CUDA is discussed;
- Lindblad trace preservation and density-matrix positivity checks pass for open-system scenarios;
- MCWF results converge toward Lindblad observables on small systems as trajectory count increases;
- MWIS examples are checked against exact ILP or another declared exact baseline;
- solver-sensitive scenarios include a tighter-tolerance or smaller-step sanity comparison.

## Visualization and Report Outputs
Public benchmark plot and MWIS export helpers require a validated `benchmark-artifact/v1` envelope. Explicit `plot_diagnostic_*` and diagnostic MWIS export helpers may render local mappings, but their output is diagnostic only and cannot satisfy this plan's evidence requirements.

Visualization helpers may summarize governed benchmark rows, but chart generation is not a benchmark-validation step. Reports and figure sidecars must retain the source artifact path or identifier when available and must not use fitted curves, local timing dictionaries, or user-selected classifications as performance evidence. Public use still requires the artifact and disclosure checks in this plan and in `SPEC-GOV-001`.

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
- Phase 11 provides supported observable APIs and metadata; dedicated observable-cost measurements remain tracked in the Phase 16 alignment matrix.
- Phase 12 provides effective solver configuration; initial solver-method reference checks exist, while broader sensitivity measurements remain tracked in Phase 16.
- Phase 14 model extensions remain planned and are prerequisites for the corresponding theory-noise benchmark scenarios and metadata.
- Phase 15 provides implemented seed/output-grid reproducibility contracts for supported workflows; benchmark adoption and future stochastic-noise coverage must be tracked separately from API availability.
- Phase 16 defines application benchmark protocols and artifact expectations, with a closed initial local suite and a partially complete full-plan alignment matrix.
- Phase 18 remains future work for cluster and advanced deployment benchmarks, including physics-solver sweep coverage, without weakening artifact or disclosure requirements.

## Maintenance Triggers

Update this document when:

- a benchmark script is added, removed, renamed, or changes artifact shape;
- `benchmark-artifact/v1`, `run-manifest/v1`, or `version-info/v1` changes;
- public performance wording policy changes;
- GPU, solver, observable, open-system, noise, or sweep behavior changes;
- a CUDA/MWIS benchmark protocol changes its opt-in gate, doctor criteria, retained hardware fields, parity checks, or failure boundaries;
- new release or disclosure workflows require different benchmark evidence.
- suite implementation or retained-evidence status changes; update the Phase 16 alignment matrices and the benchmark protocol index at the same time.
- P0–P1 campaign targets or measurement/acceptance scope change; reconcile the implementation plan, alignment matrices, benchmark protocol/family/tier/artifact documents and documentation status index without advancing evidence status before retained runs exist.
