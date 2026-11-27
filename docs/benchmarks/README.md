# Benchmark Protocols

Status: `Mixed`
Roadmap: Phase 16
Version: `benchmark-protocols/v1`
Last reviewed: 2026-11-27

This directory defines the Phase 16 benchmark protocols for Sagittarius. It translates the roadmap benchmark suite into runnable tiers, benchmark families, artifact requirements, and evidence-retention rules.

The initial suite was closed with [retained Phase 16 evidence](evidence/phase16-e171c584e8e67215f1e5fb00f6f908d2e434b10c/README.md); it is reviewable local evidence, not a public performance claim.

The initial protocol suite is done. `Mixed` reflects the implemented initial suite and planned full-plan extensions; see the [Phase 16 suite alignment matrix](../development/requirements.md#phase-16-alignment-with-spec-gov-004-benchmark-suites) and [cross-cutting requirements](../development/requirements.md#phase-16-alignment-with-spec-gov-004-cross-cutting-requirements) for per-suite status, remaining acceptance evidence, and Phase 14/18 dependencies.

The [P0–P1 implementation plan v2](plans/v2.md) defines the seven-suite matrices, references, delivery batches and evidence gates. Scaling, MWIS/UDG and open-system campaigns target 20 atoms with separate basis/resource limits. These are planned campaign targets; existing retained measurements and CUDA maturity remain unchanged. P2 noise/cluster work remains outside that plan.

The protocol, tier, family and artifact documents each contain parallel `Benchmarking V1` and `Benchmarking V2` parts. V1 preserves the full original content and its commands/evidence wording; V2 uses the same chapter organization for plan v2 acceptance work. The V1 metadata and future-scope statements belong to that initial baseline; V2 and the implementation plan track current scaling/ablation support and remaining suite targets.

These documents complement the governance pages:

- [`SPEC-GOV-004-benchmarking-plan.md`](../governance/SPEC-GOV-004-benchmarking-plan.md) defines benchmark governance, release cadence, and required correctness gates.
- [`SPEC-GOV-001-performance-claims.md`](../governance/SPEC-GOV-001-performance-claims.md) defines how measured performance may be stated publicly.
- [`SPEC-GOV-002-disclosure-control.md`](../governance/SPEC-GOV-002-disclosure-control.md) defines disclosure review for public benchmark reports.
- [`SPEC-GOV-003-prior-art-notes.md`](../governance/SPEC-GOV-003-prior-art-notes.md) defines wording boundaries for Rydberg, MWIS, and neutral-atom claims.


Scaling has [retained local v2 acceptance evidence](evidence/p0-scaling-v2-2026-11-26/README.md): 42 scenarios and 210 eligible repeats, including all six N=20 geometry/radius configurations. This is bounded local numerical/software evidence; other suite targets and release/public-use gates remain separate.

Ablation has [local ablation evidence](evidence/p0-ablation-v2-2026-11-27/README.md): all 16 targeted CPU paths and 80 independent measured batches passed, including both reduced paths at N=20 (D=17711). Four full-dimension exclusions and five optional CUDA skips are retained. CUDA, recurring RC and public-use approval remain separate.

## Documents

| Document | Purpose |
| :--- | :--- |
| [`protocol.md`](protocol.md) | Parallel [V1](protocol.md#benchmarking-v1)/[V2](protocol.md#benchmarking-v2) execution stages, pre-run records, measurement rules, correctness and evidence levels. |
| [`tiers.md`](tiers.md) | Parallel [V1](tiers.md#benchmarking-v1)/[V2](tiers.md#benchmarking-v2) tier summaries, command/output boundaries, and smoke/correctness/parity/scaling/stress requirements. |
| [`families.md`](families.md) | Parallel [V1](families.md#benchmarking-v1)/[V2](families.md#benchmarking-v2) family summaries and physics/dynamics/open-system/optimization/backend/sweep protocols. |
| [`artifact-contracts.md`](artifact-contracts.md) | Parallel [V1](artifact-contracts.md#benchmarking-v1)/[V2](artifact-contracts.md#benchmarking-v2) artifact types, aggregate/row contracts, failures, metrics, retention and compatibility. |
| [`plans/v2.md`](plans/v2.md) | P0–P1 plan, implemented scaling matrix/controls, remaining targets, numerical/statistical gates, resource policy and delivery/acceptance evidence. |

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

Run the local resumable ParallelSimulation sweep benchmark:

```bash
uv run python tests/test_performance/benchmark_sweep_cluster.py --output-dir benchmark-output
```

It records per-worker throughput rows, a `sweep-artifact/v1` checkpoint and final aggregate, per-item result/manifest links, and a benchmark suite aggregate. Use `--resume-from path/to/sweep.json --workers 1` to retry only pending/failed items. This covers local Julia Distributed execution, not multi-node performance.

## Runnable Tier Guide

Run every command in this section from `sagittarius_py`. Unless stated otherwise, each runner writes JSON, CSV, and Markdown companions under `benchmark-output`; suite-capable runners additionally write a `*_suite.json` aggregate that retains passed, failed, skipped, and incomplete rows.

The [V2 scaling and ablation CLIs](tiers.md#v2-runnable-commands-and-outputs) provide frozen CPU matrices, references, independent repeats, resource supervision and suite companions. Ablation retains fixed-input batch semantics, saved numerical outputs and an acceptance audit; CUDA ODE remains separate diagnostic scope. This guide lists existing commands only. Remaining planned measurement flags, the observable/open-system performance runners and new artifact stems are tracked in [plan v2](plans/v2.md); add their runnable examples after implementation and smoke verification.

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
