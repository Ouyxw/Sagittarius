# Benchmark Protocols

Status: `Mixed implementation`
Roadmap: Phase 16
Version: `benchmark-protocols/v1`
Last reviewed: 2026-08-11

This directory defines the Phase 16 benchmark protocols for Sagittarius. It translates the roadmap benchmark suite into runnable tiers, benchmark families, artifact requirements, and evidence-retention rules.

These documents complement the governance pages:

- [`SPEC-GOV-004-benchmarking-plan.md`](../governance/SPEC-GOV-004-benchmarking-plan.md) defines benchmark governance, release cadence, and required correctness gates.
- [`SPEC-GOV-001-performance-claims.md`](../governance/SPEC-GOV-001-performance-claims.md) defines how measured performance may be stated publicly.
- [`SPEC-GOV-002-disclosure-control.md`](../governance/SPEC-GOV-002-disclosure-control.md) defines disclosure review for public benchmark reports.
- [`SPEC-GOV-003-prior-art-notes.md`](../governance/SPEC-GOV-003-prior-art-notes.md) defines wording boundaries for Rydberg, MWIS, and neutral-atom claims.

## Documents

| Document | Purpose |
| :--- | :--- |
| [`protocol.md`](protocol.md) | Cross-suite benchmark protocol, execution discipline, and evidence levels. |
| [`tiers.md`](tiers.md) | Smoke, correctness, parity, scaling, and stress tier definitions. |
| [`families.md`](families.md) | Benchmark-family protocols for physics, dynamics, open systems, optimization, backend performance, and sweeps. |
| [`artifact-contracts.md`](artifact-contracts.md) | Required aggregate artifact fields, failure rows, evidence retention, and the implemented `benchmark-suite-artifact/v1` wrapper. |

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

## Evidence Levels

| Level | Purpose | Public use |
| :--- | :--- | :--- |
| Exploratory local evidence | Developer investigation, local GPU scale-limit probing, and protocol tuning. | Not public claim material. |
| Reviewable project evidence | Structured artifacts from documented commands on a named commit. | Internal comparison and release candidate review. |
| Release-grade evidence | Artifacts plus governance review, disclosure row, and bounded wording. | May support public release notes, README claims, reports, or papers. |

Benchmark scripts are optional for ordinary PR CI unless a change touches solver behavior, backend execution, observables, artifact schemas, or benchmark code.
