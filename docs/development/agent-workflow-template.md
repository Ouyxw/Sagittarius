# Agent Workflow Template

Status: `Template`
Roadmap: Cross-phase development workflow
Version: `agent-workflow-template/v1`
Last reviewed: 2026-07-03


This template defines a reusable workflow for AI-assisted Sagittarius development. Copy or reference it for feature branches, development branches, release branches, benchmark work, documentation work, or experiment-project work. Branch owners may specialize the checklist, but they should not remove scientific correctness, reproducibility, artifact-contract, or documentation-maintenance gates without recording why.

## How To Use This Template

At the start of a branch or feature, create a short branch-local workflow note in the pull request description, issue, or a branch document. Fill in the placeholders below.

```text
Branch or feature: <name>
Roadmap phase: <phase or N/A>
Primary owner: <person/team>
Target surface: <Python SDK | Julia backend | docs | benchmark | packaging | experiment workflow>
Primary specs: <docs paths>
Required tests: <commands>
Required artifacts: <schemas/files>
Out of scope: <explicit non-goals>
Release or public-claim impact: <yes/no and governance docs>
```

Use `AGENTS.md` as the standing agent behavior policy. Use this file as the per-task operating workflow.

## Context Recovery

Every restarted AI session should rebuild context before editing.

Minimum context:

```bash
git status --short
sed -n '1,220p' AGENTS.md
sed -n '1,320p' REQUIREMENTS.md
sed -n '1,180p' docs/status.md
sed -n '1,180p' docs/reference/known-limitations.md
```

Then read only the specs relevant to the current task:

| Task type | Required context |
| :--- | :--- |
| Public Python API | `docs/api/`, `docs/reference/data-model.md`, affected tests |
| Julia backend or parity | `docs/api/SPEC-API-002-python-julia-parity.md`, `docs/api/SPEC-API-003-julia-native-api.md`, affected Julia/Python tests |
| Solver behavior | `docs/api/SPEC-API-005-solver-configuration.md`, solver tests, run-manifest docs |
| Observables | `docs/api/SPEC-API-004-observable-library.md`, `docs/physics/SPEC-PHYS-003-observables.md` |
| Noise models | `docs/physics/SPEC-PHYS-004-noise-models.md`, open-system tests |
| Artifacts or schemas | `docs/reference/data-model.md`, `docs/reference/SPEC-DATA-001-shared-result-schema.md`, serializers and validators |
| Benchmark work | `docs/benchmarks/`, `docs/governance/SPEC-GOV-004-benchmarking-plan.md`, performance-claim policy |
| Packaging or release | `docs/getting-started/python/package-installation.md`, `docs/reference/ci-workflows.md`, packaging tests |
| Public claim, demo, paper, or report | Governance docs `SPEC-GOV-001`, `SPEC-GOV-002`, `SPEC-GOV-003`, `SPEC-GOV-004` |

Suggested session prompt:

```text
Read AGENTS.md, REQUIREMENTS.md, docs/status.md, and the specs relevant to <task>.
Before editing, summarize the affected code, tests, docs, schemas, artifacts, and CI gates.
Then implement the smallest correct change, run targeted tests, update docs, and report residual risks.
```

## Branch Customization Block

Copy this block into the PR, issue, or branch-local planning doc.

```markdown
## Agent Workflow Customization

### Scope
- Roadmap phase:
- Feature or bug:
- In scope:
- Out of scope:

### Required Context
- Specs:
- Source files:
- Tests:
- Existing artifacts or examples:

### Change Surface
- Public API: yes/no
- Python/Julia parity: yes/no
- Solver or numerical behavior: yes/no
- Manifest/artifact/schema: yes/no
- Benchmark or performance claim: yes/no
- Packaging/release behavior: yes/no
- Documentation-only: yes/no

### Required Validation
- Unit tests:
- Integration/parity tests:
- Numerical verification:
- Serialization/schema tests:
- Docs or link checks:
- CI/release gates:

### Handoff Requirements
- Summary:
- Tests run:
- Docs updated:
- Known limitations or residual risks:
- Follow-up issues:
```

## Standard Development Loop

1. Recover context.
2. Classify the change surface.
3. Identify acceptance criteria and non-goals.
4. Inspect existing implementation and tests before designing new abstractions.
5. Implement the smallest coherent change.
6. Add or update tests that prove behavior and prevent regression.
7. Update docs listed in `docs/status.md` for the touched surface.
8. Run targeted tests, then broaden based on risk.
9. Inspect `git diff` for unrelated edits and schema/documentation drift.
10. Handoff with commands run, results, and remaining risks.

## Code, Docs, Tests, and CI Coupling

Use this coupling rule:

```text
Behavior changes -> tests prove behavior -> docs describe behavior -> roadmap/status records reality -> CI gates preserve it
```

Common mappings:

| Change | Code | Tests | Docs |
| :--- | :--- | :--- | :--- |
| Python SDK API | `sagittarius_py/sagittarius/` | `sagittarius_py/tests/` | `docs/api/`, README if user-visible |
| Julia backend API | `Sagittarius.jl/src/` and packaged copy if applicable | Julia-native and cross-language tests | `docs/api/SPEC-API-003*`, parity docs |
| Solver semantics | Python and Julia solver paths | solver config, invariants, parity, numerical sanity | `SPEC-API-005`, data model, limitations |
| Artifact or schema | serializers, validators, result objects | serialization and artifact tests | `docs/reference/*`, `docs/status.md` |
| Benchmark behavior | benchmark scripts and artifact writers | benchmark artifact tests, smoke scenarios | `docs/benchmarks/`, governance docs |
| Packaging | `pyproject.toml`, package data, CLI, workflows | packaging artifact and clean-env tests | installation docs, CI workflows |

## Test Selection Matrix

Start narrow and expand according to risk.

| Area | Typical targeted tests |
| :--- | :--- |
| Serialization, manifests, shared results | `cd sagittarius_py && uv run pytest tests/test_serialization.py` |
| Python object API | `cd sagittarius_py && uv run pytest tests/test_api_v2.py` |
| Solver configuration | `cd sagittarius_py && uv run pytest tests/test_solver_configuration.py` |
| Pulse/indexing | `cd sagittarius_py && uv run pytest tests/test_phase8_pulse_contract.py tests/test_pulse.py` |
| Observables | `cd sagittarius_py && uv run pytest tests/test_observable_library.py` |
| Runtime diagnostics | `cd sagittarius_py && uv run pytest tests/test_runtime_hardening.py tests/test_failure_diagnostics.py` |
| Packaging | `cd sagittarius_py && uv run pytest tests/test_packaging_artifacts.py tests/test_juliapkg_packaging.py` |
| Benchmark artifacts | `cd sagittarius_py && uv run pytest tests/test_benchmark_artifacts.py tests/test_ablation_benchmarks.py` |
| Full Python suite | `cd sagittarius_py && uv run pytest tests/` |

GPU tests are opt-in and require explicit environment and hardware evidence. Do not treat skipped GPU tests as CUDA validation.

## Schema and Artifact Change Checklist

Before changing schemas, manifests, diagnostics, events, or result artifacts:

- Identify whether the change is compatible or requires a new schema version.
- Update writers, readers, validators, fixtures, and round-trip tests together.
- Preserve compatibility with supported older artifacts where documented.
- Keep `data`, `metadata`, `diagnostics`, `manifest`, and `shared_result` responsibilities separate.
- Update `docs/reference/data-model.md`, the relevant schema doc, and `docs/status.md` if triggers change.
- Include requested/effective configuration where backend execution can differ from user input.

## Numerical and Scientific Change Checklist

For physics, solver, observable, noise, sampling, or benchmark changes:

- State the mathematical or physical assumption being implemented.
- Identify basis semantics: full, reduced, bitstring order, atom index order.
- Add analytic, dense, exact, invariant, parity, or convergence checks where practical.
- Record tolerances and explain why they are appropriate.
- Preserve reproducibility metadata: seeds, output grids, versions, backend diagnostics.
- Update known limitations if the feature remains partial or backend-specific.

## Documentation Maintenance Checklist

Use `docs/status.md` as the routing table.

At minimum, update docs when:

- Public API names, arguments, defaults, or validation behavior change.
- Solver, backend, observable, pulse, noise, sampling, or bitstring semantics change.
- Artifact, manifest, benchmark, or diagnostic schemas change.
- Installation or release support changes.
- A planned feature becomes implemented or a limitation is removed.
- A benchmark or public claim is added, modified, or promoted.

Do not update README to advertise a capability before tests and docs support it.

## CI and Release Gate Expectations

Branch developers should identify which gate they expect to satisfy:

| Gate | Purpose |
| :--- | :--- |
| Local targeted tests | Prove the changed behavior quickly. |
| Full local Python suite | Catch broad SDK regressions. |
| PR fast CI | Ordinary pull-request confidence. |
| Clean wheel and uninstall/reinstall smoke | Release artifact confidence. |
| Cross-platform matrix | OS/Python/Julia release evidence. |
| TestPyPI workflow | Publication readiness evidence. |
| CUDA smoke/parity | Hardware-backed GPU evidence. |
| Benchmark suite | Performance or application-validation evidence. |

Never claim release readiness, CUDA validation, PyPI support, or performance improvement unless the corresponding gate produced retained evidence.

## Handoff Template

Use this for final AI summaries, PR comments, or branch notes.

```markdown
## Summary
- 

## Changed Surfaces
- Code:
- Tests:
- Docs:
- Schemas/artifacts:
- CI/release gates:

## Validation
- Command:
- Result:

## Reproducibility Metadata
- Seeds:
- Backend:
- Artifact schemas:

## Residual Risk
- 

## Follow-up
- 
```

## Tailoring Rules

Feature and development branches may tailor this template by adding stricter checks. They should not remove these baseline requirements:

- context recovery from `AGENTS.md`, `REQUIREMENTS.md`, and relevant specs;
- tests for behavior changes;
- docs updates for public behavior or schema changes;
- artifact-backed evidence for performance or release claims;
- explicit handling of Python/Julia parity when semantics cross the language boundary;
- preservation of reproducibility metadata for executable workflows.
