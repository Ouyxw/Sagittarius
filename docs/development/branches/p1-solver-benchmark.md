# Branch workflow: P1 solver sensitivity

Status: Branch-local working document
Merge policy: Retain as a development record; durable behavior and acceptance belong in formal benchmark docs.

## Branch baseline and scope

- Date: 2026-11-27; branch `feature/benchmarking`; baseline `781a09e`; initial tree clean.
- Authorization: user requested completion of plan v2 P1 solver. This covers implementation, tests, docs and a bounded local campaign, without a commit.
- Context: project SOP, development SOP, requirements Phase 16, status routing, limitations, workflow/prompt templates, GOV-004, plan v2, benchmark contracts, SPEC-API-005 and existing solver/path tests.
- In scope: preserve correctness fixtures/stems; correct timing boundary; add deterministic solver sensitivity matrix, references, repeated measurements, supervised resources, saved-output audit and retained evidence.
- Out of scope: SDK/Julia solver semantics, new physics, CUDA, observables/open-system suites, release/public performance approval.

## Requirement items and current slice

| Item | Acceptance | Status |
| --- | --- | --- |
| Matrix | Three scenarios; paired adaptive tolerances, RK4 steps, output grids and declared combined cases; legal configs only | Verified |
| Measurement | First execution, two warmups, five reset-state repeats; isolated SDK timer, process memory, requested/effective metadata | Verified |
| References | Analytic Rabi, independently projected constant H, independent time-dependent integration with second-method stability; 1e-6 observable/norm gate | Verified |
| Retention/audit | Invalid/short/resource/interrupted rows retained; recompute saved-output gates, statistics, companions, links and hashes without Julia | Verified |
| Campaign/docs | Pilot then freeze full matrix; archive local evidence; reconcile formal status without scientific/release claims | Verified |

## Cross-phase dependencies and change surface

Phase 12 supplies legal solver configuration and effective metadata; Phase 15 supplies grids, manifests and readout. Reuse benchmark-artifact/v1 and benchmark-suite-artifact/v1 with optional metrics; no required schema fields or solver semantics change. New Python benchmark module, existing script adapter, tests, audit script and benchmark/requirements/governance docs are affected. The reference verifies the reduced model, not the physical blockade approximation. Output-grid density is not integration-step refinement.

## Required validation

- Backend-free matrix/reference/status/statistics/audit corruption checks.
- Small real-backend integration; existing solver/path regression, solver configuration, serialization and Python/Julia golden tests.
- Full local matrix with two warmups/five measured repeats per configuration and audited relocated artifacts.
- Benchmark documentation consistency and `python3 scripts/validate_documentation.py`.
- Inspect final diff for unrelated changes and schema drift; no GPU or release gate is claimed.

## Validation log

| Scope | Result |
| --- | --- |
| Backend-free matrix/reference/status/statistics/options | 17 passed; real-backend integration separately executed. |
| Real ramp saved-output/tampering integration, legacy solver/path, solver configuration, serialization and Python/Julia golden tests | 28 passed, no skips. |
| Artifact/row/suite/failure and documentation tests | 21 passed. |
| Short pilots | Initial declaration/full-space basis errors retained; second pilot passes numerical gates but remains incomplete at 0 warmups/1 repeat. |
| Full 39-configuration campaign | All 39 executed; 38 accuracy-pass/1 under-resolved coarse ramp RK4 row retained. 190/195 eligible measured calls; 312 saved result/manifest pairs audited. |

Exact commands and logs are retained under `docs/benchmarks/evidence/p1-solver-v2-2026-11-27/validation`.

## Progress log

2026-11-27: Recovered clean baseline and explicit implementation authorization; defined bounded acceptance above. Implemented the 39-case matrix, references and timers, kept legacy outputs, and passed targeted verification. Full campaign is frozen and complete. Independent RK4 precheck indicates ramp T/100 is under-resolved at the fixed target; preserve it as a failed numerical row rather than relax the gate. The explicit local characterization policy records how complete under-resolved outcomes count as data while backend/reference/resource/write failures remain gaps.

## Handoff requirements and conclusion

Report changed surfaces, exact validation/results, formal docs, campaign coverage, retained failures and residual limits. Preserve earlier archives and historical V1 chapters. Retain this branch record; full-suite, recurring RC, physical validation and public approval remain separate.


## Final validation and conclusion — 2026-11-27

- Completed the bounded P1 solver slice. [Durable archive](../../benchmarks/evidence/p1-solver-v2-2026-11-27/README.md) retains campaign/source identity, failed/short pilots, original raw results/manifests, references, reports, exact commands, tests and checksums.
- 17 backend-free tests, 28 backend/golden regressions, 21 artifact/documentation tests and one deterministic timer-boundary test passed (67 targeted tests, no skips; the backend-free command deselects the separately run real integration test). Final documentation/link checks are recorded in the archive validation directory.
- All 39 configurations completed with first + two warmups + five measurements. 38 configurations and 190/195 measured calls meet 1e-6. Ramp RK4 T/100 error 1.6501632661980459e-6 correctly fails; raw norm error is 3.742790406491281e-7. All numerical-failure times/results remain present and ineligible. No target changed.
- Original/relocated saved-output audits and explicit characterization reviews agree, including all 312 saved calls and nine tight/fine controls. All 931 internal checksums passed. `full_v2_matrix_passed=false` remains truthful; full numerical characterization acceptance is a separate field/policy.
- All 22 frozen source/config files match handoff; runtime Project/Manifest identity is constant across workers; effective Julia/BLAS/provider thread counts are one. Historical V1 chapters remain exactly unchanged.
- Formal docs reconciled: plan v2, benchmark index/protocol/tiers/families/artifacts, Phase 16 suite/cross-cutting requirements, GOV-004, status routing and known limitations. Existing schemas and SDK/Julia solver behavior remain unchanged. Changes are the solver benchmark module, legacy CLI/timer, audit, two test modules and evidence/docs.
- Deferred: broader/stiff scenarios, physical/blockade scientific validation, full Python-suite execution, CUDA, clean-wheel/container, recurring RC and independent public-use approval. SDK times include construction/collection/manifest; host is shared and memory includes initialization/reference/writes. No method superiority is inferred.
- Keep this branch record. No commit, merge or publication was requested or created. The remaining planned P1 suites are observables and expanded open-system work, outside this authorization.
