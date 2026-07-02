# Benchmark Protocols

Status: `Planned contract`
Roadmap: Phase 16
Version: `benchmark-protocols/v1`
Last reviewed: 2026-07-02

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
| [`artifact-contracts.md`](artifact-contracts.md) | Required aggregate artifact fields, failure rows, and evidence-retention rules. |

## Evidence Levels

| Level | Purpose | Public use |
| :--- | :--- | :--- |
| Exploratory local evidence | Developer investigation, local GPU scale-limit probing, and protocol tuning. | Not public claim material. |
| Reviewable project evidence | Structured artifacts from documented commands on a named commit. | Internal comparison and release candidate review. |
| Release-grade evidence | Artifacts plus governance review, disclosure row, and bounded wording. | May support public release notes, README claims, reports, or papers. |

Benchmark scripts are optional for ordinary PR CI unless a change touches solver behavior, backend execution, observables, artifact schemas, or benchmark code.
