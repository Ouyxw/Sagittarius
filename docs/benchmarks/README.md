# Benchmark Protocols

Status: `Mixed`
Roadmap: Phase 16
Version: `benchmark-protocols/v1`
Last reviewed: 2026-11-27

This directory defines the Phase 16 benchmark protocols for Sagittarius. It translates the roadmap benchmark suite into runnable tiers, benchmark families, artifact requirements, and evidence-retention rules.

The initial suite was closed with [retained Phase 16 evidence](evidence/phase16-e171c584e8e67215f1e5fb00f6f908d2e434b10c/README.md); it is reviewable local evidence, not a public performance claim.

The initial protocol suite is done. `Mixed` reflects the implemented initial suite and planned full-plan extensions; see the [Phase 16 suite alignment matrix](../development/requirements.md#phase-16-alignment-with-spec-gov-004-benchmark-suites) and [cross-cutting requirements](../development/requirements.md#phase-16-alignment-with-spec-gov-004-cross-cutting-requirements) for per-suite status, remaining acceptance evidence, and Phase 14/18 dependencies.

The [P0–P1 implementation plan v2](plans/v2.md) defines the seven-suite matrices, references, delivery batches and evidence gates. Scaling, MWIS/UDG and open-system campaigns target 20 atoms with separate basis/resource limits. Scaling and the bounded GPU matrix have retained N=20 measurements; The 40-instance MWIS/UDG campaign also retains N=20 measurements; open-system now implements a resource-guarded local-noise matrix and offline audit. CUDA remains experimental. P2 noise/cluster work remains outside that plan.

The protocol, tier, family and artifact documents each contain parallel `Benchmarking V1` and `Benchmarking V2` parts. V1 preserves the full original content and its commands/evidence wording; V2 uses the same chapter organization for plan v2 acceptance work. The V1 metadata and future-scope statements belong to that initial baseline; V2 and the implementation plan track current scaling/ablation/GPU/MWIS support and remaining suite targets.

These documents complement the governance pages:

- [`SPEC-GOV-004-benchmarking-plan.md`](../governance/SPEC-GOV-004-benchmarking-plan.md) defines benchmark governance, release cadence, and required correctness gates.
- [`SPEC-GOV-001-performance-claims.md`](../governance/SPEC-GOV-001-performance-claims.md) defines how measured performance may be stated publicly.
- [`SPEC-GOV-002-disclosure-control.md`](../governance/SPEC-GOV-002-disclosure-control.md) defines disclosure review for public benchmark reports.
- [`SPEC-GOV-003-prior-art-notes.md`](../governance/SPEC-GOV-003-prior-art-notes.md) defines wording boundaries for Rydberg, MWIS, and neutral-atom claims.


Scaling has [retained local v2 acceptance evidence](evidence/p0-scaling-v2-2026-11-26/README.md): 42 scenarios and 210 eligible repeats, including all six N=20 geometry/radius configurations. This is bounded local numerical/software evidence; other suite targets and release/public-use gates remain separate.

Ablation has [local ablation evidence](evidence/p0-ablation-v2-2026-11-27/README.md): all 16 targeted CPU paths and 80 independent measured batches passed, including both reduced paths at N=20 (D=17711). Four full-dimension exclusions and five optional CUDA skips are retained. CUDA, recurring RC and public-use approval remain separate.

CUDA follow-up has [retained local hardware evidence](evidence/p0-ablation-cuda-v2-2026-11-27/README.md): all five ablation chain cases through N=20 passed, with 25 measured CPU/CUDA ODE pairs and 80 saved first/warm/measured result/manifest pairs. First-call initialization and diagonal-observable transfer fixes are included. The original CPU archive and its historical CUDA skips remain unchanged. CUDA stays experimental; this ablation-only archive is separate from the P1 GPU matrix below, recurring RC and public-use gates.

The [P1 GPU local campaign](evidence/p1-gpu-v2-2026-11-27/README.md) completes the declared eight-case matrix: chains N=2,4,8,12,16,20, a 2x2 lattice and seeded two-node MWIS. All 40 measured CPU/CUDA pairs passed at 101 shared times after symmetric warmups; N=20 has D=17711. Separate backend memory, saved results/manifests, qualified median ratios and all companion values passed the backend-free audit. CUDA remains experimental; this is shared-workstation software/numerical evidence, not independent physical validation, recurring RC or public-use approval.

The [P1 MWIS/UDG local campaign](evidence/p1-mwis-v2-2026-11-27/README.md) completes all 40 frozen instances through N=20 (five seeds per size), with 200 eligible AQC and 200 eligible ILP measurements. Independent DOP853/refinement, raw-norm checks, exhaustive graph objectives and CBC problem/solution optimality gate the results. Actual AQC result/manifests, native solver logs, per-path memory and all companion statistics pass the saved-evidence audit. Short-schedule suboptimal candidates remain valid data; different solution guarantees prevent an AQC/ILP speedup interpretation. This is bounded local numerical/software evidence, separate from scientific validation, general algorithm quality and release/public-use approval.

The [P1 solver local campaign](evidence/p1-solver-v2-2026-11-27/README.md) completes all 39 declared sensitivity configurations across Rabi, the addressed chain and a linear ramp. All 312 first/warm/measured results and manifests are retained and audited; 38 configurations and 190/195 measured calls meet the frozen 1e-6 accuracy target. The coarse ramp RK4 T/100 case remains a failed accuracy row with all raw times/errors, as required by the plan. Independent stable references, raw norm checks, effective settings, per-configuration memory and error-versus-runtime companions support bounded local numerical characterization. Full-matrix all-accuracy-pass remains false; accepted characterization does not promote under-resolved times into performance comparisons or close scientific validation, recurring RC or public-use gates.

The [P1 observable local campaign](evidence/p1-observables-v2-2026-11-27/README.md) completes 52 cost configurations through reduced N=20 (D=17711) and 12 small full/reduced state-path fixtures. All 260 measured SDK calls and 476 saved results/manifests pass value/order, round-trip and independent-reference gates; five-seed MCWF samples use explicit simultaneous uncertainty bounds. Two empty-observable history controls, cross-order equality, attributable worker memory, frozen source/runtime and matching companions are audited after relocation. Counts/grids/orders are separate workloads; duplicate physical declarations are labeled. Timings include SDK construction/collection/manifest and provide no incremental-overhead subtraction. This closes bounded local numerical/software characterization, separate from physical validation, expanded open-system costs/convergence, recurring RC and public-use approval.

The [P1 open-system local campaign](evidence/p1-open-system-v2-2026-11-27/README.md) accounts for all 99 frozen rows: 85 pass and 14 resource exclusions remain explicit. All 375 eligible measured SDK calls, 916 first/warm/measured/statistical/correctness results and 63 separate tighter results are retained. Reduced N=20 (Rb=12.4 um, D=907) executes MCWF at 100/500/1000 trajectories with five separate seeds and target-size analytic decay controls. Independent small dense/analytic references, 67 raw-density histories, trace/positivity/coherence, seed uncertainty, runtime/throughput statistics, manifests and all companions pass original/relocated backend-free audits. Full N=20 Lindblad/full-space coverage and independent large interacting references remain open. This is bounded shared-workstation local evidence, separate from scientific validation, recurring RC and public-use approval.

## Documents

| Document | Purpose |
| :--- | :--- |
| [`protocol.md`](protocol.md) | Parallel [V1](protocol.md#benchmarking-v1)/[V2](protocol.md#benchmarking-v2) execution stages, pre-run records, measurement rules, correctness and evidence levels. |
| [`tiers.md`](tiers.md) | Parallel [V1](tiers.md#benchmarking-v1)/[V2](tiers.md#benchmarking-v2) tier summaries, command/output boundaries, and smoke/correctness/parity/scaling/stress requirements. |
| [`families.md`](families.md) | Parallel [V1](families.md#benchmarking-v1)/[V2](families.md#benchmarking-v2) family summaries and physics/dynamics/open-system/optimization/backend/sweep protocols. |
| [`artifact-contracts.md`](artifact-contracts.md) | Parallel [V1](artifact-contracts.md#benchmarking-v1)/[V2](artifact-contracts.md#benchmarking-v2) artifact types, aggregate/row contracts, failures, metrics, retention and compatibility. |
| [`plans/v2.md`](plans/v2.md) | P0–P1 plan, implemented scaling/ablation/GPU/MWIS/solver/observable matrices and controls, remaining targets, numerical/statistical gates, resource policy and delivery/acceptance evidence. |
| [`reports/p0-runtime-statistics-2026-11-27.md`](reports/p0-runtime-statistics-2026-11-27.md) | Complete derived timing distributions for 42 scaling scenarios, 16 CPU ablation paths and five matched CPU/CUDA ODE cases; raw-source links, exclusions and local-only interpretation. |

All seven P0–P1 suites have explicit [runtime reporting requirements](plans/v2.md#runtime-reporting-requirements-for-all-seven-suites)
and suite-specific timer/output definitions. Default performance evidence uses
two warmups and at least five independent measurements, with median/min/max/
p25/p75, counts and raw membership. Scaling and ablation already retain these
statistics; the linked report recomputes and presents them without modifying
original archives or rerunning simulations. GPU distributions are retained in its own campaign. MWIS also retains separate per-graph AQC/ILP distributions. Solver now retains its per-configuration sensitivity distributions. Observable and open-system suites now implement their per-configuration distributions, reference controls and sampling reports; correctness-only tests need no separate performance campaign.

## Implemented CPU smoke

Run the initial Phase 16 physics smoke command from `sagittarius_py`:

```bash
uv run python tests/test_performance/benchmark_physics_smoke.py --output-dir benchmark-output
```

It runs deterministic Rabi and blockade cases on CPU, writes a compatible `physics_smoke.json` plus CSV/Markdown and a validated `physics_smoke_suite.json` aggregate with matching CSV/Markdown companions; it stores one `result-artifact/v1` and one `run-manifest/v1` per successful case. Its runtime values are local diagnostics only.

Run the correctness-tier physics baselines separately:

```bash
uv run python tests/test_performance/benchmark_physics_correctness.py --output-dir benchmark-output
```

It checks analytic Rabi and ideal-blockade trajectories, a wide finite-sweep Landau-Zener result against its asymptotic analytic transition probability, and a small static chain against an exact projected dense matrix-exponential reference. It writes a compatible `physics_correctness.json` plus CSV/Markdown and a validated `physics_correctness_suite.json` aggregate with matching CSV/Markdown companions; SDK simulation rows retain result/manifest links and the dense-vs-reduced row retains its reference report. Runtime values remain local diagnostics only.

Run the Phase 16 cold-atom and open-system correctness families:

```bash
uv run python tests/test_performance/benchmark_phase16_validation.py --output-dir benchmark-output
```

It writes `cold_atom_dynamics` and `open_system_dynamics` single-scenario artifacts and matching suite aggregates. Cold-atom rows retain projected-dense reference reports for global-chain, local-addressing, Z2, and 2D cases. Open-system rows retain analytic decay error, Lindblad trace/positivity, seeded MCWF-vs-Lindblad errors, and 100/500-trajectory sensitivity. The evidence is CPU small-system correctness only; it is not a performance, scaling, or hardware claim.

Run the deterministic weighted MWIS/UDG AQC family:

```bash
uv run python tests/test_performance/benchmark_mwis_aqc.py --output-dir benchmark-output
```

It emits `smoke`, `correctness`, and bounded `scaling` artifacts with matching suite aggregates. Each scenario retains its seed, graph/weight metadata, schedule, exact PuLP/CBC baseline, feasibility, objective gap, approximation ratio, and final-state optimal-success probability; failed ILP or AQC cases are retained as failure rows. The reported CPU runtime and approximation values validate a bounded implementation, not general optimization performance.

Run the CUDA parity and MWIS GPU protocol only on an approved CUDA host:

```bash
SAGITTARIUS_ENABLE_GPU_TESTS=1 uv run python tests/test_performance/benchmark_cuda_mwis_protocol.py --output-dir benchmark-output
```

The runner first requires `doctor(backend="CUDA", initialize_backend=True)` to pass. Without opt-in it writes skipped rows; an initialized-doctor failure becomes retained failure rows. On success it writes separate CPU/CUDA chain-parity and weighted-MWIS parity artifacts plus suite aggregates, including hardware/runtime versions, cold/warm timing, GPU memory snapshots, parity errors, and MWIS exact-baseline feasibility. These are local diagnostic artifacts, not general GPU or optimization performance claims.

Run repeated CPU solver/path correctness measurements:

```bash
uv run python tests/test_performance/benchmark_solver_performance.py --output-dir benchmark-output
```

It emits repeated dense/sparse/reduced path rows, a cached-GPU skip unless independently validated through the CUDA protocol, and Tsit5/Vern9/RK4 trajectory rows against a high-accuracy Tsit5 reference. Each SDK solver row retains result and manifest links; timing remains local diagnostic evidence.

For the implemented 39-configuration solver sensitivity matrix, use
`benchmark_solver_performance.py --tier sensitivity` in a new output directory.
It retains independent stable references, first execution/two warmups/five measured
SDK calls, per-configuration memory, actual results/manifests and error-versus-runtime
JSON/CSV/Markdown. See [commands and audit](tiers.md#v2-runnable-commands-and-outputs)
and [measurement boundaries](plans/v2.md#implemented-solver-matrix-and-measurement-boundaries).
Under-resolved runs remain failed accuracy rows with raw diagnostics; they do not
qualify for comparisons at the frozen 1e-6 target.


Run the local resumable ParallelSimulation sweep benchmark:

```bash
uv run python tests/test_performance/benchmark_sweep_cluster.py --output-dir benchmark-output
```

It records per-worker throughput rows, a `sweep-artifact/v1` checkpoint and final aggregate, per-item result/manifest links, and a benchmark suite aggregate. Use `--resume-from path/to/sweep.json --workers 1` to retry only pending/failed items. This covers local Julia Distributed execution, not multi-node performance.

## Runnable Tier Guide

Run every command in this section from `sagittarius_py`. Unless stated otherwise, each runner writes JSON, CSV, and Markdown companions under `benchmark-output`; suite-capable runners additionally write a `*_suite.json` aggregate that retains passed, failed, skipped, and incomplete rows.

The [V2 scaling and ablation CLIs](tiers.md#v2-runnable-commands-and-outputs) provide frozen CPU matrices, references, independent repeats, resource supervision and suite companions. Ablation retains fixed-input batch semantics, saved numerical outputs and an acceptance audit; CUDA ODE remains separate diagnostic scope. This guide lists existing commands only. The seven implemented runners, measurement controls and evidence milestones are tracked in [plan v2](plans/v2.md) and the [V2 command guide](tiers.md#v2-runnable-commands-and-outputs).

| Tier | Runnable command | Expected output and boundary |
| :--- | :--- | :--- |
| Smoke | `uv run python tests/test_performance/benchmark_physics_smoke.py --output-dir benchmark-output` | `physics_smoke` artifacts and `physics_smoke_suite`; deterministic CPU wiring evidence only. |
| Correctness | `uv run python tests/test_performance/benchmark_physics_correctness.py --output-dir benchmark-output` | `physics_correctness` artifacts and suite; analytic/dense-reference errors and tolerances. |
| Parity | `SAGITTARIUS_ENABLE_GPU_TESTS=1 uv run python tests/test_performance/benchmark_cuda_mwis_protocol.py --output-dir benchmark-output` | `cuda_parity` and `mwis_gpu_parity` artifacts and suites; records opt-in skips or doctor failures when CUDA is unavailable. |
| Scaling | `uv run python tests/test_performance/benchmark_sweep_cluster.py --output-dir benchmark-output` | `sweep_cluster` artifacts and suite, plus resumable `sweep-artifact/v1` checkpoint/final aggregate; local Distributed evidence only. |
| Stress | `uv run python tests/test_performance/benchmark_ablation.py --atom-count 12 --repeats 50 --output-dir benchmark-output/ablation-n12` | `ablation_bench_results` and `ablation_bench_results_suite` JSON/CSV/Markdown plus per-repeat/config/reference outputs. |

For additional correctness coverage, run the cold-atom/open-system and MWIS commands below; their outputs are `cold_atom_dynamics`/`open_system_dynamics` and `mwis_aqc_smoke`, `mwis_aqc_correctness`, or `mwis_aqc_scaling`, each with matching suite aggregates.

## Evidence Levels

| Level | Purpose | Public use |
| :--- | :--- | :--- |
| Exploratory local evidence | Developer investigation, local GPU scale-limit probing, and protocol tuning. | Not public claim material. |
| Reviewable project evidence | Structured artifacts from documented commands on a named commit. | Internal comparison and release candidate review. |
| Release-grade evidence | Artifacts plus governance review, disclosure row, and bounded wording. | May support public release notes, README claims, reports, or papers. |

Benchmark scripts are optional for ordinary PR CI unless a change touches solver behavior, backend execution, observables, artifact schemas, or benchmark code.
