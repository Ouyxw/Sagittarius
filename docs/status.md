# Documentation Status

This table maps each documentation page to its purpose, specification ID where applicable, roadmap phase, current status, and maintenance trigger. Use it when updating `REQUIREMENTS.md`, changing public APIs, changing artifact schemas, or preparing public disclosures.

Status values:

- `Current`: describes implemented behavior and should be kept in sync with code and tests.
- `Planned contract`: documents an accepted roadmap target that is not fully implemented yet.
- `Policy`: governance material that constrains public wording and release process.
- `Mixed`: combines implemented behavior with planned or future scope.
- `Future`: intentionally describes unsupported or future work.

## Getting Started

| Spec ID | Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- | :--- |
| - | [`getting-started/installation.md`](getting-started/installation.md) | Installation map and current Python/Julia support boundary. | Phase 13 | Planned contract | Source/wheel/PyPI support, Julia package setup, or language-specific install paths change. |
| - | [`getting-started/source-installation.md`](getting-started/source-installation.md) | Compatibility entry that routes source installs to language-specific guides. | Phase 13 source baseline | Current | Source install guide paths or repository layout assumptions change. |
| - | [`getting-started/python/source-installation.md`](getting-started/python/source-installation.md) | Python SDK source checkout installation and verification. | Phase 13 source baseline | Current | Repository layout, uv workflow, JuliaPkg setup, or Python test command changes. |
| - | [`getting-started/python/experiment-projects.md`](getting-started/python/experiment-projects.md) | Independent Python experiment layout using editable source dependency. | Phase 13 editable/dev install | Current | Editable dependency behavior, JuliaPkg project selection, or CPU/GPU dependency profile changes. |
| - | [`getting-started/python/package-installation.md`](getting-started/python/package-installation.md) | Python wheel/sdist/PyPI status, upgrade, uninstall, release artifact criteria, and Julia-native boundary. | Phase 13 | Planned contract | Any artifact build, wheel, sdist, package data, PyPI readiness, or embedded Julia backend policy changes. |
| - | [`getting-started/python/backend-setup.md`](getting-started/python/backend-setup.md) | Python JuliaCall/JuliaPkg executable discovery, CPU/CUDA setup, planned backend commands. | Phase 5 diagnostics, Phase 13 backend setup | Mixed | Backend setup CLI, CPU-first dependency profile, CUDA policy, Julia discovery, or doctor behavior changes. |
| - | [`getting-started/python/minimal-examples.md`](getting-started/python/minimal-examples.md) | Minimal Python backend-free and Julia-backed examples with expected output. | Phase 10 | Current | Python output shapes, validation messages, diagnostics schema, or examples change. |
| - | [`getting-started/julia/projects.md`](getting-started/julia/projects.md) | Independent Julia project layout using `Pkg.develop`. | Phase 8 Julia native API, Phase 13 install docs | Current | Julia package registration, project activation, or native API import flow changes. |
| - | [`getting-started/julia/backend-setup.md`](getting-started/julia/backend-setup.md) | Julia-native executable, project activation, CPU smoke, and GPU setup boundary. | Phase 8 Julia native API, Phase 13 backend setup | Current | Native Julia runtime setup, project activation, or GPU backend policy changes. |
| - | [`getting-started/julia/minimal-examples.md`](getting-started/julia/minimal-examples.md) | Minimal Julia-native examples with expected output. | Phase 8 Julia native API, Phase 12 solver config | Current | Julia native API names, solver kwargs, output shapes, or examples change. |
| - | [`getting-started/python-experiment-projects.md`](getting-started/python-experiment-projects.md) | Compatibility entry for Python experiment projects. | Phase 13 editable/dev install | Current | Redirect target changes. |
| - | [`getting-started/julia-projects.md`](getting-started/julia-projects.md) | Compatibility entry for Julia user projects. | Phase 8 Julia native API, Phase 13 install docs | Current | Redirect target changes. |
| - | [`getting-started/backend-setup.md`](getting-started/backend-setup.md) | Compatibility entry for language-specific backend setup. | Phase 5 diagnostics, Phase 13 backend setup | Mixed | Redirect target changes or backend setup split changes. |
| - | [`getting-started/package-installation.md`](getting-started/package-installation.md) | Compatibility entry for package installation status. | Phase 13 | Planned contract | Redirect target changes or package status split changes. |
| - | [`getting-started/minimal-examples.md`](getting-started/minimal-examples.md) | Compatibility entry for language-specific minimal examples. | Phase 10 | Current | Redirect target changes or example split changes. |
| - | [`getting-started/dual-sdk-examples.md`](getting-started/dual-sdk-examples.md) | Paired Python and Julia workflows. | Phase 8, Phase 10 | Current | Python/Julia parity semantics, API names, or example workflows change. |
| - | [`getting-started/containerization.md`](getting-started/containerization.md) | CUDA-focused devcontainer setup and troubleshooting. | Phase 5 backend diagnostics, Phase 10 install docs | Current | Devcontainer image, CUDA.jl pin, driver requirements, or GPU test policy changes. |

## API Guides

| Spec ID | Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SPEC-API-001` | [`api/SPEC-API-001-pulse-and-indexing-contract.md`](api/SPEC-API-001-pulse-and-indexing-contract.md) | Python pulse forms and zero-based indexing rules. | Phase 8 | Current | Pulse wrappers, shorthand compatibility, callable validation, or index conversion changes. |
| `SPEC-API-002` | [`api/SPEC-API-002-python-julia-parity.md`](api/SPEC-API-002-python-julia-parity.md) | Cross-language semantic contract and golden test scope. | Phase 8 | Current | Atom ordering, bitstrings, pulse addressing, solver defaults, manifests, or parity tests change. |
| `SPEC-API-003` | [`api/SPEC-API-003-julia-native-api.md`](api/SPEC-API-003-julia-native-api.md) | Julia-native constructors, basis/Hamiltonian helpers, solvers, logging. | Phase 8 | Current | Julia exports or native solver signatures change. |
| `SPEC-API-004` | [`api/SPEC-API-004-observable-library.md`](api/SPEC-API-004-observable-library.md) | Implemented diagonal observable declarations, Julia constructors, metadata, validation, and tests; off-diagonal scope remains future work. | Phase 11 | Mixed | Observable type IDs, constructor semantics, metadata shape, validation rules, or future off-diagonal support change. |
| `SPEC-API-005` | [`api/SPEC-API-005-solver-configuration.md`](api/SPEC-API-005-solver-configuration.md) | Implemented solver method dispatch, adaptive/fixed-step options, effective metadata, and validation. | Phase 12 | Current | Solver method dispatch, `adaptive`, `dt`, metadata, or solver-path support changes. |
| `SPEC-API-006` | [`api/SPEC-API-006-visualization.md`](api/SPEC-API-006-visualization.md) | Python visualization and reporting helpers, including backend-free plots, diagnostics, exports, reports, and the current sweep-artifact boundary. | Phase 19 | Mixed | Public visualization API, return types, artifact/report metadata, backend-initialization boundary, benchmark-claim wording, or sweep-artifact support changes. |

## Physics Guides

| Spec ID | Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SPEC-PHYS-001` | [`physics/SPEC-PHYS-001-units.md`](physics/SPEC-PHYS-001-units.md) | Unit conventions, Hamiltonian sign convention, parameter selection, blockade radius guidance. | Phase 2, Phase 9 | Current | Hamiltonian convention, rate definitions, blockade semantics, or numerical controls change. |
| `SPEC-PHYS-002` | [`physics/SPEC-PHYS-002-pulse-shapes.md`](physics/SPEC-PHYS-002-pulse-shapes.md) | Physical intent, parameters, and usage patterns for built-in pulse waveforms. | Phase 8, Phase 10 | Current | Pulse node set, parameter semantics, compile behavior, or addressing guidance changes. |
| `SPEC-PHYS-003` | [`physics/SPEC-PHYS-003-observables.md`](physics/SPEC-PHYS-003-observables.md) | Physical meaning of current and planned neutral-atom observables. | Phase 11 | Mixed | Observable library scope, sign conventions, or MWIS/cost definitions change. |
| `SPEC-PHYS-004` | [`physics/SPEC-PHYS-004-noise-models.md`](physics/SPEC-PHYS-004-noise-models.md) | Current and planned theoretical noise models for open-system and stochastic simulations. | Phase 14 | Planned contract | Noise channels, jump-operator semantics, stochastic ensemble behavior, or readout-scope boundaries change. |

## Benchmark Protocols

| Spec ID | Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- | :--- |
| - | [`benchmarks/README.md`](benchmarks/README.md) | Phase 16 benchmark protocol index and evidence-level routing. | Phase 16 | Planned contract | Benchmark document set, evidence levels, or governance references change. |
| - | [`benchmarks/protocol.md`](benchmarks/protocol.md) | Cross-suite benchmark execution protocol, correctness-before-performance rules, and evidence classification. | Phase 16 | Planned contract | Benchmark execution stages, pre-run metadata, warmup discipline, or evidence classes change. |
| - | [`benchmarks/tiers.md`](benchmarks/tiers.md) | Smoke, correctness, parity, scaling, and stress tier requirements. | Phase 16 | Planned contract | Tier definitions, CI policy, local GPU protocol, or scale-limit rules change. |
| - | [`benchmarks/families.md`](benchmarks/families.md) | Family-specific benchmark protocols for physics, dynamics, open systems, optimization, backend performance, and sweeps. | Phase 16 | Planned contract | Benchmark families, scenario coverage, correctness gates, or required evidence change. |
| - | [`benchmarks/artifact-contracts.md`](benchmarks/artifact-contracts.md) | Phase 16 aggregate artifact, row, metric, failure, and evidence-retention expectations. | Phase 16 | Planned contract | Benchmark artifact schemas, metric names, failure rows, or retention rules change. |

## Development Workflows

| Spec ID | Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- | :--- |
| - | [`development/README.md`](development/README.md) | Index for reusable contributor and AI-agent development workflow templates. | Cross-phase development workflow | Template | Development workflow templates, agent collaboration process, or branch customization policy changes. |
| - | [`development/agent-workflow-template.md`](development/agent-workflow-template.md) | Reusable AI-agent workflow template for feature, development, release, benchmark, and documentation branches. | Cross-phase development workflow | Template | Agent collaboration process, branch workflow expectations, test matrix, or handoff requirements change. |
| - | [`development/prompt-context.md`](development/prompt-context.md) | Bilingual prompt standards for starting, resuming, implementing, reviewing, and closing AI-assisted branch work. | Cross-phase AI-assisted development workflow | Template | Prompt templates, branch context expectations, or AI handoff requirements change. |

## Reference

| Spec ID | Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- | :--- |
| - | [`reference/architecture-overview.md`](reference/architecture-overview.md) | System architecture, module boundaries, runtime lifecycle, execution paths, and architecture roadmap. | Phase 5, Phase 6, Phase 8, Phase 10 | Current | Python/Julia module boundaries, simulation lifecycle, backend initialization, solver paths, or architecture roadmap changes. |
| - | [`reference/data-model.md`](reference/data-model.md) | User objects, Julia physics objects, result sections, manifests, schemas, artifacts, and planned data-model extensions. | Phase 1, Phase 6, Phase 8, Phase 10 | Current | Public objects, manifests, artifacts, schemas, indexing semantics, or Python/Julia parity behavior changes. |
| - | [`reference/technical-stack.md`](reference/technical-stack.md) | Python, Julia, bridge, backend, testing, packaging, benchmark, and deployment stack overview. | Phase 5, Phase 10, Phase 13, Phase 17 | Mixed | Dependencies, backend maturity, packaging/install behavior, test stack, GPU support, or deployment workflows change. |
| `SPEC-BACKEND-001` | [`reference/SPEC-BACKEND-001-backends.md`](reference/SPEC-BACKEND-001-backends.md) | Backend maturity matrix, diagnostics shape, CUDA policy. | Phase 5, Phase 10 | Current | Backend maturity, doctor schema, CUDA/AMDGPU/Metal support, or parity evidence changes. |
| - | [`reference/known-limitations.md`](reference/known-limitations.md) | Current limitations and unsupported scenarios. | Phase 10 | Current | A planned feature ships, backend maturity changes, scale assumptions change, or public limitations need tightening. |
| `SPEC-DATA-001` | [`reference/SPEC-DATA-001-shared-result-schema.md`](reference/SPEC-DATA-001-shared-result-schema.md) | `shared-result/v1` language-neutral result payload. | Phase 8 | Current | Shared result schema, result artifact envelope, or Julia serialization behavior changes. |
| `SPEC-OBS-001` | [`reference/SPEC-OBS-001-event-taxonomy.md`](reference/SPEC-OBS-001-event-taxonomy.md) | `event-taxonomy/v1` event IDs, severity, payload compatibility. | Phase 6 | Current | Event IDs, required fields, severity, or compatibility rules change. |
| - | [`reference/development-sop.md`](reference/development-sop.md) | Reusable logging, diagnostics, artifact, manifest, benchmark, and public-claim SOP derived from Sagittarius contracts. | Phase 6, Phase 8, Phase 10 | Current | Logging contracts, artifact schemas, benchmark governance, or documentation maintenance process changes. |
| - | [`reference/ci-workflows.md`](reference/ci-workflows.md) | Automatic PR CI, manual release gates, workflow triggers, and release-evidence retention rules. | Phase 13 | Current | GitHub Actions triggers, workflow scope, release gates, or CI evidence requirements change. |

## Governance

| Spec ID | Document | Purpose | Roadmap link | Status | Update when |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SPEC-GOV-001` | [`governance/SPEC-GOV-001-performance-claims.md`](governance/SPEC-GOV-001-performance-claims.md) | Artifact-backed performance claim policy. | Phase 10 | Policy | Benchmark artifact schema, benchmark scripts, or public wording rules change. |
| `SPEC-GOV-002` | [`governance/SPEC-GOV-002-disclosure-control.md`](governance/SPEC-GOV-002-disclosure-control.md) | Disclosure register and review workflow. | Phase 10 | Policy | A public release/report/demo/paper is planned or published. |
| `SPEC-GOV-003` | [`governance/SPEC-GOV-003-prior-art-notes.md`](governance/SPEC-GOV-003-prior-art-notes.md) | Prior-art boundaries for Rydberg, MWIS, neutral-atom tooling, and numerical methods. | Phase 10 | Policy | New public disclosure, paper draft, benchmark claim, or reviewed source changes the boundary. |
| `SPEC-GOV-004` | [`governance/SPEC-GOV-004-benchmarking-plan.md`](governance/SPEC-GOV-004-benchmarking-plan.md) | Benchmark suite structure, required metadata, correctness gates, and release cadence. | Phase 9, Phase 10, Phase 16, Phase 18 | Policy | Benchmark suite scope, benchmark artifact fields, correctness gates, or release benchmarking workflow changes. |
| `SPEC-GOV-005` | [`governance/SPEC-GOV-005-repository-versioning.md`](governance/SPEC-GOV-005-repository-versioning.md) | Hybrid monorepo policy, package boundaries, version compatibility, and repository-split criteria. | Phase 13, Phase 17 | Policy | Repository layout, package release boundaries, compatibility matrix, or split-repository policy changes. |

## Maintenance Checklist

Before marking a roadmap phase complete, check this table for every document tied to that phase. In particular:

- Phase 11 completion should update [`api/SPEC-API-004-observable-library.md`](api/SPEC-API-004-observable-library.md), [`physics/SPEC-PHYS-003-observables.md`](physics/SPEC-PHYS-003-observables.md), [`reference/SPEC-DATA-001-shared-result-schema.md`](reference/SPEC-DATA-001-shared-result-schema.md), and [`reference/known-limitations.md`](reference/known-limitations.md).
- Phase 12 is complete; future solver configuration changes should update [`api/SPEC-API-005-solver-configuration.md`](api/SPEC-API-005-solver-configuration.md), [`api/SPEC-API-002-python-julia-parity.md`](api/SPEC-API-002-python-julia-parity.md), [`reference/SPEC-OBS-001-event-taxonomy.md`](reference/SPEC-OBS-001-event-taxonomy.md), and [`reference/known-limitations.md`](reference/known-limitations.md).
- Phase 13 completion should update all installation pages, [`reference/SPEC-BACKEND-001-backends.md`](reference/SPEC-BACKEND-001-backends.md), [`reference/known-limitations.md`](reference/known-limitations.md), root [`README.md`](../README.md), and any packaging release notes.
- Phase 19 changes should update [`api/SPEC-API-006-visualization.md`](api/SPEC-API-006-visualization.md), [`reference/data-model.md`](reference/data-model.md) when artifact/report fields change, [`reference/known-limitations.md`](reference/known-limitations.md) when visualization support boundaries change, and the applicable benchmark governance documents for public performance wording.
- Phase 14 completion should update [`physics/SPEC-PHYS-004-noise-models.md`](physics/SPEC-PHYS-004-noise-models.md), [`api/SPEC-API-002-python-julia-parity.md`](api/SPEC-API-002-python-julia-parity.md), [`api/SPEC-API-004-observable-library.md`](api/SPEC-API-004-observable-library.md), and [`reference/known-limitations.md`](reference/known-limitations.md).
- Phase 16 completion should update [`benchmarks/README.md`](benchmarks/README.md), [`benchmarks/protocol.md`](benchmarks/protocol.md), [`benchmarks/tiers.md`](benchmarks/tiers.md), [`benchmarks/families.md`](benchmarks/families.md), [`benchmarks/artifact-contracts.md`](benchmarks/artifact-contracts.md), [`governance/SPEC-GOV-004-benchmarking-plan.md`](governance/SPEC-GOV-004-benchmarking-plan.md), [`governance/SPEC-GOV-001-performance-claims.md`](governance/SPEC-GOV-001-performance-claims.md), and [`reference/known-limitations.md`](reference/known-limitations.md).
- Repository layout or package-boundary changes should be checked against [`governance/SPEC-GOV-005-repository-versioning.md`](governance/SPEC-GOV-005-repository-versioning.md). Any public benchmark or hardware-facing claim should be checked against [`governance/SPEC-GOV-004-benchmarking-plan.md`](governance/SPEC-GOV-004-benchmarking-plan.md), [`governance/SPEC-GOV-001-performance-claims.md`](governance/SPEC-GOV-001-performance-claims.md), [`governance/SPEC-GOV-003-prior-art-notes.md`](governance/SPEC-GOV-003-prior-art-notes.md), and [`governance/SPEC-GOV-002-disclosure-control.md`](governance/SPEC-GOV-002-disclosure-control.md).
