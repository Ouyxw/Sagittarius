# Agent Workflow Template

Status: `Template`
Roadmap: Cross-phase development workflow
Version: `agent-workflow-template/v1`
Last reviewed: 2026-07-03


This template defines a reusable workflow for AI-assisted Sagittarius development. Copy or reference it for feature branches, development branches, release branches, benchmark work, documentation work, or experiment-project work. Branch owners may specialize the checklist, but they should not remove scientific correctness, reproducibility, artifact-contract, or documentation-maintenance gates without recording why.

For standard session prompts, see [`prompt-context.md`](prompt-context.md). Prompt text may be written in English or Chinese; the workflow requirements are the same.

## How To Use This Template

At the start of a branch or feature, create a branch-local workflow note in the pull request description, issue, or a branch document. For long-running feature branches, use a file such as:

```text
docs/development/branches/phase14-noise-models.md
```

Branch-local workflow documents are working records. Before merging, decide whether to delete them, keep them as retained development records, or extract the durable content into formal specs, docs, or the PR description.

Use `AGENTS.md` as the standing agent behavior policy. Use this file as the per-task operating workflow.

## Context Recovery

Every restarted AI session should rebuild context before editing.

Minimum context:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
sed -n '1,220p' AGENTS.md
sed -n '1,320p' docs/development/requirements.md
sed -n '1,180p' docs/development/status.md
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

## Branch Customization Block

Copy this block into the PR, issue, or branch-local planning doc. Fill it before implementation begins.

```markdown
# Branch Workflow: <branch-or-feature-name>

Status: Branch-local working document
Merge policy: <remove before merge | retain as development record | extract into formal docs/PR description>

## Agent Workflow Customization

### Branch Baseline
- Base branch:
- Base commit:
- Current branch:
- Created at:
- Initial working tree status:

### Scope
- Roadmap phase:
- Feature or bug:
- In scope:
- Out of scope:

### Requirement Items

| ID | Requirement | Priority | Source | Specs | Status | Tests | Docs | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| <P14-R1> | <requirement text> | <High/Medium/Low> | `docs/development/requirements.md` Phase <N> | <docs paths> | Planned | TBD | TBD | <notes> |

Status values: `Planned`, `In progress`, `Implemented`, `Verified`, `Deferred`, `Blocked`.

### Cross-Phase Dependencies

| Dependency | Direction | Reason | Status | Impact |
| :--- | :--- | :--- | :--- | :--- |
| <Phase/feature> | <blocks/depends on/enables> | <why it matters> | <status> | <implementation impact> |

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

### Current Slice
- Slice ID:
- Requirement items covered:
- In scope:
- Out of scope:
- Acceptance checks:
- Required tests:
- Required docs:
- Known risks:

### Required Validation
- Unit tests:
- Integration/parity tests:
- Numerical verification:
- Serialization/schema tests:
- Docs or link checks:
- CI/release gates:

### Validation Log

| Date | Command | Result | Notes |
| :--- | :--- | :--- | :--- |
| <YYYY-MM-DD> | `<command>` | <passed/failed/skipped> | <notes> |

### Progress Log

| Date | Slice | Status | Summary | Commit |
| :--- | :--- | :--- | :--- | :--- |
| <YYYY-MM-DD> | <slice id> | <status> | <summary> | <commit or pending> |

### Handoff Requirements
- Summary:
- Tests run:
- Docs updated:
- Known limitations or residual risks:
- Follow-up issues:

### Conclusion
- Completed requirement items:
- Deferred or blocked items:
- Final validation:
- Formal docs updated:
- Branch-local document disposition:
```

## Standard Development Loop

1. Recover context.
2. Create or update the Branch Customization Block.
3. Classify the change surface.
4. Identify acceptance criteria, non-goals, and cross-phase dependencies.
5. Ask for the smallest P0 slice. Do not implement until the developer approves the slice.
6. Inspect existing implementation and tests before designing new abstractions.
7. Implement the approved slice.
8. Add or update tests that prove behavior and prevent regression.
9. Update formal docs listed in `docs/development/status.md` for the touched surface.
10. Update the branch-local workflow document with progress and validation results.
11. Run targeted tests, then broaden based on risk.
12. Inspect `git diff` for unrelated edits and schema/documentation drift.
13. Handoff with commands run, results, residual risks, and next-slice recommendation.

## Rolling Development Prompt Pattern

For ongoing feature branches, each new session should ask the agent to read the branch-local workflow document and report current progress before selecting the next task.

Required status report:

- base commit and current working tree status;
- requirement items by status;
- completed and verified items;
- implemented but unverified or undocumented items;
- blocked/deferred items;
- suggested next requirement priority;
- smallest slice for the highest-priority item;
- acceptance checks, tests, docs, and risks for that slice.

The agent should not edit code during this status report unless explicitly authorized.

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
| Artifact or schema | serializers, validators, result objects | serialization and artifact tests | `docs/reference/*`, `docs/development/status.md` |
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
- Update `docs/reference/data-model.md`, the relevant schema doc, and `docs/development/status.md` if triggers change.
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

Use `docs/development/status.md` as the routing table.

At minimum, update docs when:

- Public API names, arguments, defaults, or validation behavior change.
- Solver, backend, observable, pulse, noise, sampling, or bitstring semantics change.
- Artifact, manifest, benchmark, or diagnostic schemas change.
- Installation or release support changes.
- A planned feature becomes implemented or a limitation is removed.
- A benchmark or public claim is added, modified, or promoted.

Branch-local workflow documents do not replace formal docs. They record progress; formal docs describe the project state after the change.

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

## Branch Workflow Update
- Requirement items updated:
- Current slice status:
- Validation log updated:
- Next recommended slice:

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

- context recovery from `AGENTS.md`, `docs/development/requirements.md`, and relevant specs;
- branch baseline and requirement-item status tracking for long-running branches;
- tests for behavior changes;
- docs updates for public behavior or schema changes;
- artifact-backed evidence for performance or release claims;
- explicit handling of Python/Julia parity when semantics cross the language boundary;
- preservation of reproducibility metadata for executable workflows.
