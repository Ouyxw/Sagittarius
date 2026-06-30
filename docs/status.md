# Documentation Status

This table maps each documentation page to its purpose, roadmap phase, current status, and maintenance trigger. Use it when updating `REQUIREMENTS.md`, changing public APIs, changing artifact schemas, or preparing public disclosures.

Status values:

- `Current`: describes implemented behavior and should be kept in sync with code and tests.
- `Planned contract`: documents an accepted roadmap target that is not fully implemented yet.
- `Policy`: governance material that constrains public wording and release process.
- `Future`: intentionally describes unsupported or future work.

## Getting Started

| Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- |
| [`getting-started/installation.md`](getting-started/installation.md) | Installation map and current support boundary. | Phase 13 | Planned contract | Source/wheel/PyPI support changes. |
| [`getting-started/source-installation.md`](getting-started/source-installation.md) | Current source checkout installation and verification. | Phase 13 source baseline | Current | Repository layout, uv workflow, JuliaPkg setup, or test command changes. |
| [`getting-started/python-experiment-projects.md`](getting-started/python-experiment-projects.md) | Independent Python experiment layout using editable source dependency. | Phase 13 editable/dev install | Current | Editable dependency behavior, JuliaPkg project selection, or CPU/GPU dependency profile changes. |
| [`getting-started/julia-projects.md`](getting-started/julia-projects.md) | Independent Julia project layout using `Pkg.develop`. | Phase 8 Julia native API, Phase 13 install docs | Current | Julia package registration, project activation, or native API import flow changes. |
| [`getting-started/backend-setup.md`](getting-started/backend-setup.md) | Julia executable discovery, JuliaPkg resolution, CPU/CUDA setup, planned backend commands. | Phase 5 diagnostics, Phase 13 backend setup | Mixed: current plus planned command notes | Backend setup CLI, CPU-first dependency profile, CUDA policy, or Julia discovery changes. |
| [`getting-started/package-installation.md`](getting-started/package-installation.md) | Wheel/sdist/PyPI status, upgrade, uninstall, release artifact criteria. | Phase 13 | Planned contract | Any artifact build, wheel, sdist, package data, or PyPI readiness change. |
| [`getting-started/minimal-examples.md`](getting-started/minimal-examples.md) | Minimal backend-free and Julia-backed examples with expected output. | Phase 10 | Current | Output shapes, validation messages, diagnostics schema, or examples change. |
| [`getting-started/dual-sdk-examples.md`](getting-started/dual-sdk-examples.md) | Paired Python and Julia workflows. | Phase 8, Phase 10 | Current | Python/Julia parity semantics, API names, or example workflows change. |
| [`getting-started/containerization.md`](getting-started/containerization.md) | CUDA-focused devcontainer setup and troubleshooting. | Phase 5 backend diagnostics, Phase 10 install docs | Current | Devcontainer image, CUDA.jl pin, driver requirements, or GPU test policy changes. |

## API Guides

| Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- |
| [`api/julia-native-api.md`](api/julia-native-api.md) | Julia-native constructors, basis/Hamiltonian helpers, solvers, logging. | Phase 8 | Current | Julia exports or native solver signatures change. |
| [`api/python-julia-parity.md`](api/python-julia-parity.md) | Cross-language semantic contract and golden test scope. | Phase 8 | Current | Atom ordering, bitstrings, pulse addressing, solver defaults, manifests, or parity tests change. |
| [`api/pulse-and-indexing-contract.md`](api/pulse-and-indexing-contract.md) | Python pulse forms and zero-based indexing rules. | Phase 8 | Current | Pulse wrappers, shorthand compatibility, callable validation, or index conversion changes. |
| [`api/observable-library.md`](api/observable-library.md) | Planned Phase 11 observable declaration, Julia constructors, metadata, validation, tests. | Phase 11 | Planned contract | Observable library implementation lands or type IDs/metadata shape change. |
| [`api/solver-configuration.md`](api/solver-configuration.md) | Planned Phase 12 method dispatch, adaptive/fixed-step options, metadata, validation. | Phase 12 | Planned contract | Solver method dispatch, `adaptive`, `dt`, metadata, or solver-path support changes. |

## Physics Guides

| Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- |
| [`physics/units.md`](physics/units.md) | Unit conventions, Hamiltonian sign convention, parameter selection, blockade radius guidance. | Phase 2, Phase 9 | Current | Hamiltonian convention, rate definitions, blockade semantics, or numerical controls change. |
| [`physics/observables.md`](physics/observables.md) | Physical meaning of current and planned neutral-atom observables. | Phase 11 | Mixed: current primitive plus planned observable set | Observable library scope, sign conventions, or MWIS/cost definitions change. |

## Reference

| Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- |
| [`reference/backends.md`](reference/backends.md) | Backend maturity matrix, diagnostics shape, CUDA policy. | Phase 5, Phase 10 | Current | Backend maturity, doctor schema, CUDA/AMDGPU/Metal support, or parity evidence changes. |
| [`reference/known-limitations.md`](reference/known-limitations.md) | Current limitations and unsupported scenarios. | Phase 10 | Current | A planned feature ships, backend maturity changes, scale assumptions change, or public limitations need tightening. |
| [`reference/shared-result-schema.md`](reference/shared-result-schema.md) | `shared-result/v1` language-neutral result payload. | Phase 8 | Current | Shared result schema, result artifact envelope, or Julia serialization behavior changes. |
| [`reference/event-taxonomy.md`](reference/event-taxonomy.md) | `event-taxonomy/v1` event IDs, severity, payload compatibility. | Phase 6 | Current | Event IDs, required fields, severity, or compatibility rules change. |

## Governance

| Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- |
| [`governance/performance-claims.md`](governance/performance-claims.md) | Artifact-backed performance claim policy. | Phase 10 | Policy | Benchmark artifact schema, benchmark scripts, or public wording rules change. |
| [`governance/prior-art-notes.md`](governance/prior-art-notes.md) | Prior-art boundaries for Rydberg, MWIS, neutral-atom tooling, and numerical methods. | Phase 10 | Policy | New public disclosure, paper draft, benchmark claim, or reviewed source changes the boundary. |
| [`governance/disclosure-control.md`](governance/disclosure-control.md) | Disclosure register and review workflow. | Phase 10 | Policy | A public release/report/demo/paper is planned or published. |

## Maintenance Checklist

Before marking a roadmap phase complete, check this table for every document tied to that phase. In particular:

- Phase 11 completion should update [`api/observable-library.md`](api/observable-library.md), [`physics/observables.md`](physics/observables.md), [`reference/shared-result-schema.md`](reference/shared-result-schema.md), and [`reference/known-limitations.md`](reference/known-limitations.md).
- Phase 12 completion should update [`api/solver-configuration.md`](api/solver-configuration.md), [`api/python-julia-parity.md`](api/python-julia-parity.md), [`reference/event-taxonomy.md`](reference/event-taxonomy.md), and [`reference/known-limitations.md`](reference/known-limitations.md).
- Phase 13 completion should update all installation pages, [`reference/backends.md`](reference/backends.md), [`reference/known-limitations.md`](reference/known-limitations.md), root [`README.md`](../README.md), and any packaging release notes.
- Any public benchmark or hardware-facing claim should be checked against [`governance/performance-claims.md`](governance/performance-claims.md), [`governance/prior-art-notes.md`](governance/prior-art-notes.md), and [`governance/disclosure-control.md`](governance/disclosure-control.md).
