# Project Agent Instructions

## Project Context

Sagittarius is a research SDK for classical simulation of Rydberg neutral-atom analog dynamics. It combines a Julia backend with a Python SDK. Treat it as scientific computing software: correctness, reproducibility, diagnostics, and artifact contracts are first-class requirements.

Follow these references before changing behavior:

- `docs/development/SOP.md` for lifecycle and quality principles.
- `docs/development/requirements.md` for roadmap phase scope and acceptance criteria.
- `docs/development/status.md` for documentation maintenance triggers.
- `docs/reference/known-limitations.md` for current unsupported scenarios.
- `docs/reference/development-sop.md` for logging, diagnostics, manifest, artifact, and benchmark contracts.
- `docs/development/agent-workflow-template.md` for per-task workflow and branch handoff requirements.
- `docs/development/prompt-context.md` for bilingual session and authorization templates.

## Collaboration Workflow

- Before editing, recover context with `git status --short`, `git branch --show-current`, and `git rev-parse --short HEAD`; identify existing uncommitted changes and preserve unrelated work.
- Read the relevant roadmap requirements, specs, tests, and any branch-local workflow document before choosing an implementation approach.
- During planning or status-only requests, report findings without editing implementation code unless explicitly authorized.
- For planned feature work, define the smallest P0 slice with scope, acceptance criteria, tests, docs, schema impact, and risks; implement after the developer authorizes the slice. Existing explicit authorization applies within its stated scope.
- For long-running branches, maintain a branch-local workflow document with the baseline, requirement status, current slice, progress, and validation results. Before merge, decide whether to remove it, retain it, or extract durable content into formal docs.
- Before handoff, inspect `git diff` for unrelated edits and contract drift. Report changed surfaces, validation commands and results, docs updated, residual risks, and deferred work.

## Engineering Rules

- Keep changes scoped to the requested roadmap phase or bug.
- Prefer existing Python and Julia API patterns over new abstractions.
- Preserve Python/Julia semantic parity for atom ordering, bitstrings, pulse addressing, solver options, manifests, and result artifacts.
- Do not weaken validation, diagnostics, schema versioning, or reproducibility metadata.
- Any change to public behavior must update tests and the relevant docs listed in `docs/development/status.md`.

## Scientific Software Rules

- Distinguish testing, software verification, numerical verification, and scientific validation.
- New physics, solver, observable, noise, sampling, or benchmark behavior must include explicit acceptance criteria.
- Use analytic, dense, exact, or parity references where practical.
- Record requested and effective configuration in diagnostics/manifests when behavior is executed by a backend.
- Do not make performance or scalability claims without artifact-backed evidence and governance docs.

## Artifact and Schema Rules

- Preserve current schema names unless intentionally versioning a breaking change:
  - `run-manifest/v1`
  - `result-artifact/v1`
  - `shared-result/v1`
  - `benchmark-artifact/v1`
  - `version-info/v1`
  - `doctor/v2.1`
  - `event-taxonomy/v1`
- If a required field or field meaning changes, update validators, tests, docs, and compatibility behavior together.
- Keep `data`, `metadata`, `diagnostics`, `manifest`, and `shared_result` responsibilities separate.

## Testing Expectations

Run the narrowest meaningful test set first, then broaden based on risk.

Common commands:

- `cd sagittarius_py && uv run pytest tests/test_serialization.py`
- `cd sagittarius_py && uv run pytest tests/test_api_v2.py`
- `cd sagittarius_py && uv run pytest tests/test_solver_configuration.py`
- `cd sagittarius_py && uv run pytest tests/`

GPU tests are opt-in and must not be treated as ordinary CPU CI:

- require `SAGITTARIUS_ENABLE_GPU_TESTS=1`
- require backend diagnostics to pass
- claims require retained artifact evidence

Skipped GPU tests do not establish CUDA validation.

## Documentation Expectations

When code changes affect public APIs, schema fields, solver behavior, backend behavior, artifacts, benchmarks, or limitations, update:

- `docs/development/requirements.md`
- relevant `docs/api/`, `docs/physics/`, `docs/reference/`, or `docs/governance/` pages
- `docs/development/status.md` if document status or maintenance triggers change
- `README.md` only for user-visible capability or installation changes

Branch-local progress notes do not replace formal documentation. Before accepting release-oriented documentation changes, run `python3 scripts/validate_documentation.py` from the repository root to check stable-SPEC metadata, status registration, and local Markdown links.

## Release and Packaging Rules

- Follow `docs/getting-started/python/package-installation.md` for current source, wheel/sdist, and production PyPI installation support; do not infer release support from a local build alone.
- Source/editable installs remain the development baseline. Validate released artifacts outside the source checkout using the packaged Julia backend.
- Follow `docs/governance/SPEC-GOV-005-repository-versioning.md`, `docs/governance/SPEC-GOV-006-release-candidate-governance.md`, `docs/governance/SPEC-GOV-007-public-release-authorization.md`, and `docs/development/pypi-publication.md` for versioning, candidate identity, publication authorization, and release gates.
- Every new release must pass its applicable gates for the same immutable candidate identity. Production promotion uses the validated wheel and sdist without rebuilding and retains hash reconciliation and production-install smoke evidence.
- Wheel, TestPyPI, cross-platform, CUDA, and clean-environment claims require their documented smoke evidence.

## Benchmark and Claim Rules

- Treat local timing as diagnostic unless emitted as governed artifacts.
- Public performance wording must follow:
  - `docs/governance/SPEC-GOV-001-performance-claims.md`
  - `docs/governance/SPEC-GOV-002-disclosure-control.md`
  - `docs/governance/SPEC-GOV-004-benchmarking-plan.md`
- Benchmark failures must be preserved as evidence, not filtered out.

## Commit Messages

- Planning and handoff requests do not authorize creating a commit; commit only when explicitly requested.
- Keep commit messages concise and focused on the main change.
- Prefer clear bullet points for supporting details.
- Avoid long, exhaustive explanations in commit messages.
