# Project Agent Instructions

## Project Context

Sagittarius is a research SDK for classical simulation of Rydberg neutral-atom analog dynamics. It combines a Julia backend with a Python SDK. Treat it as scientific computing software: correctness, reproducibility, diagnostics, and artifact contracts are first-class requirements.

Follow these references before changing behavior:

- `docs/SOP.md` for lifecycle and quality principles.
- `docs/development/requirements.md` for roadmap phase scope and acceptance criteria.
- `docs/development/status.md` for documentation maintenance triggers.
- `docs/reference/known-limitations.md` for current unsupported scenarios.
- `docs/reference/development-sop.md` for logging, diagnostics, manifest, artifact, and benchmark contracts.

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

## Documentation Expectations

When code changes affect public APIs, schema fields, solver behavior, backend behavior, artifacts, benchmarks, or limitations, update:

- `docs/development/requirements.md`
- relevant `docs/api/`, `docs/physics/`, `docs/reference/`, or `docs/governance/` pages
- `docs/development/status.md` if document status or maintenance triggers change
- `README.md` only for user-visible capability or installation changes

## Release and Packaging Rules

- Do not advertise PyPI installation until Phase 13 release gates are complete.
- Keep source checkout as the supported baseline unless release docs say otherwise.
- Wheel, TestPyPI, cross-platform, CUDA, and clean-environment claims require their documented smoke evidence.

## Benchmark and Claim Rules

- Treat local timing as diagnostic unless emitted as governed artifacts.
- Public performance wording must follow:
  - `docs/governance/SPEC-GOV-001-performance-claims.md`
  - `docs/governance/SPEC-GOV-002-disclosure-control.md`
  - `docs/governance/SPEC-GOV-004-benchmarking-plan.md`
- Benchmark failures must be preserved as evidence, not filtered out.

## Commit Messages

- Keep commit messages concise and focused on the main change.
- Prefer clear bullet points for supporting details.
- Avoid long, exhaustive explanations in commit messages.
