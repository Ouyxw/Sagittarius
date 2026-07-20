# Repository and Versioning Governance

Spec ID: `SPEC-GOV-005`
Status: `Policy`
Roadmap: Phase 13, Phase 17
Version: `repository-versioning-policy/v1`
Last reviewed: 2026-06-30


This document defines how Sagittarius manages a mixed Python and Julia scientific-computing codebase. It explains why the current repository should remain a hybrid monorepo, how package boundaries should be made explicit, and what conditions would justify splitting into multiple repositories later.

## Decision Summary

Sagittarius should remain a monorepo while the Python SDK and Julia backend still share fast-moving physics semantics, solver behavior, artifact schemas, and cross-language tests.

The target is not an undifferentiated mixed-language project. The target is a hybrid monorepo with clear package, documentation, test, and release boundaries:

```text
Sagittarius/
|-- Sagittarius.jl/      # Julia-native package and solver/physics backend
|-- sagittarius_py/      # Python SDK package and Python-facing tests
|-- docs/                # Shared specs plus language-specific user guides
|-- examples/            # Short repository examples
`-- scripts/             # Repository maintenance and diagnostics
```

Python and Julia users should see separate installation and user-guide paths. Shared semantics should remain in shared API/reference specifications.

## Why Monorepo Is Current Policy

The monorepo remains the default because Sagittarius currently has strong cross-language coupling:

- Python `Simulation` delegates physics and solver execution to the Julia backend.
- Python and Julia must preserve one physical semantics contract for atom order, bitstrings, bases, pulse addressing, solver settings, observables, events, and result metadata.
- Cross-language golden tests need to change in the same review as API, backend, manifest, and documentation changes.
- Phase 8, Phase 11, Phase 12, Phase 13, Phase 14, and Phase 15 all depend on consistent Python/Julia behavior.
- The public API is still evolving; splitting repositories now would turn many single changes into coordinated multi-repository releases.

The main current problem is boundary clarity, not repository count.

## Accepted Repository Model

Sagittarius uses a hybrid monorepo model.

| Layer | Owner | Boundary |
| :--- | :--- | :--- |
| Julia backend | `Sagittarius.jl/` | Physics objects, basis construction, Hamiltonians, solver algorithms, Julia-native API. |
| Python SDK | `sagittarius_py/` | User ergonomics, validation, Julia bridge, diagnostics, manifests, artifacts, Python packaging. |
| Shared contracts | `docs/api`, `docs/reference`, tests | Cross-language semantics, result schemas, event taxonomy, manifest fields, parity expectations. |
| User guides | `docs/getting-started/python`, `docs/getting-started/julia` | Language-specific installation, project layout, backend setup, and minimal examples. |
| Governance | `docs/governance` | Release policy, benchmark policy, disclosure policy, repository/versioning decisions. |

A pull request that changes shared semantics should update all affected layers together: Julia implementation, Python SDK behavior, parity tests, schemas/manifests, and docs.

## Package Boundary Rules

### Julia Package

`Sagittarius.jl/` is the canonical Julia-native source. Julia users should be able to depend on it directly:

```julia
using Pkg
Pkg.develop(path="Sagittarius.jl")
using Sagittarius
```

Future Julia package registration may allow:

```julia
using Pkg
Pkg.add("Sagittarius")
using Sagittarius
```

Python wheel packaging must not redefine the Julia-native user path. If a Python wheel embeds a copy of the Julia backend, that copy exists to serve Python runtime relocatability, not to replace `Sagittarius.jl/` as the Julia package source.

### Python Package

`sagittarius_py/` is the Python package source. Python users should see a Python-first interface:

```python
from sagittarius import Register, Simulation, PulseSequence, SolverConfig
```

The Python runtime may load Julia backend code through one of these sources, in priority order once Phase 13 lookup work lands:

1. explicit environment override, such as `SAGITTARIUS_JULIA_PROJECT`;
2. repository checkout source, such as `../Sagittarius.jl`;
3. packaged resource embedded in the Python wheel.

The selected backend source should be recorded in runtime metadata once implemented.

## Versioning Policy

Sagittarius should track three related versions:

| Version | Source | Meaning |
| :--- | :--- | :--- |
| Python package version | `sagittarius_py/pyproject.toml` | Python SDK release version. |
| Julia package version | `Sagittarius.jl/Project.toml` | Julia backend/native API release version. |
| Contract schema versions | docs and code constants | Stability of result artifacts, manifests, events, diagnostics, and shared results. |

These versions do not have to be identical forever, but compatibility must be explicit.

During the current monorepo phase, Python and Julia package versions should normally advance together for shared semantic changes. A Python-only documentation, packaging, or ergonomics fix may bump only the Python package once independent release automation exists. A Julia-only native API fix may bump only the Julia package once Julia registration and compatibility tests exist.

Contract schema versions are independent of package versions. A package release may include multiple unchanged schemas, and a schema change must be documented even when the package version bump is small.

## Compatibility Matrix

Release notes should eventually record a matrix like:

| Python package | Julia backend | Contract schemas | Notes |
| :--- | :--- | :--- | :--- |
| `sagittarius-py 1.0.0` | `Sagittarius.jl 1.0.0` | `run-manifest/v1`, `shared-result/v1`, `event-taxonomy/v1` | Initial stable compatible monorepo release. |

Until independent releases exist, the git commit is the primary compatibility identifier. Result artifacts should keep recording git/build metadata so runs remain auditable.

## Documentation Boundary

Documentation should follow this split:

| Document type | Location | Rule |
| :--- | :--- | :--- |
| Python user guides | `docs/getting-started/python/` | Python installation, `uv`, JuliaPkg, Python `Simulation`, artifacts, Python backend diagnostics. |
| Julia user guides | `docs/getting-started/julia/` and `docs/api/SPEC-API-003-*` | `Pkg.develop`, Julia project activation, native constructors, native solvers. |
| Shared API contracts | `docs/api/` | Cross-language semantics and stable API contracts. Do not duplicate full user guides here. |
| Physics guides | `docs/physics/` | Physical meaning and modeling assumptions. Include language snippets only when useful. |
| Reference docs | `docs/reference/` | Architecture, data model, technical stack, schemas, known limitations. |
| Governance docs | `docs/governance/` | Release, benchmark, disclosure, repository, and versioning policy. |

A document should be split by language when the commands, installation path, package manager, or user-facing API are different. A document should remain shared when the subject is physical semantics, schema, event taxonomy, benchmark policy, or parity rules.

## When to Consider Splitting Repositories

Splitting repositories is allowed only after the following conditions are substantially true:

1. `Sagittarius.jl` can be installed, tested, and released as an independent Julia package.
2. The Python wheel no longer depends on the source checkout layout.
3. The Python SDK depends on a documented Julia backend version range or packaged backend artifact.
4. Cross-language compatibility tests can run against released artifacts, not only a shared checkout.
5. Shared contracts have stable schema versions and clear backward-compatibility rules.
6. Release automation can coordinate Python package, Julia package, docs, and compatibility matrix updates.
7. The contributor or user communities are clearly separated enough that repository separation reduces friction rather than increasing coordination cost.

Before these conditions hold, splitting repositories is likely to increase maintenance risk.

## If Repositories Are Split Later

A future split should use explicit ownership and compatibility paths, for example:

```text
sagittarius-jl/       # Julia package and native docs
sagittarius-py/       # Python SDK and Python packaging
sagittarius-docs/     # Optional shared docs site, or docs retained in one primary repo
```

The split must include:

- a compatibility matrix for Python and Julia versions;
- cross-repository CI that runs golden tests against released or pinned artifacts;
- release notes that identify contract schema changes;
- migration docs for source checkout users;
- an explicit policy for where shared docs and governance policies live.

## Review Checklist

Use this checklist when a change affects repository or release boundaries:

- Does the change affect Python users, Julia users, or both?
- Does it alter shared physics semantics, schemas, events, manifests, or solver behavior?
- Are Python and Julia tests updated in the same change when shared semantics change?
- Are language-specific docs updated without duplicating shared contracts?
- Does `version_info()` or future release metadata record enough information to audit compatibility?
- Does the change introduce a reason to update the compatibility matrix?
- Would this change be harder to review or release if the project were already split across repositories?

## Current Policy

For the current Sagittarius roadmap, keep the hybrid monorepo. Invest in clearer boundaries first:

- language-specific getting-started docs;
- explicit Python and Julia package ownership;
- shared contract documents for semantics and artifacts;
- parity tests and golden fixtures;
- version metadata and release compatibility records.

Repository splitting should be treated as a later governance decision, not as a near-term cleanup task.
