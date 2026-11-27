# Branch workflow: P1 observables

Status: Branch-local working document
Merge policy: Retain development record; durable behavior/evidence belongs in formal benchmark docs.

## Baseline, authorization and scope

- 2026-11-27; `feature/benchmarking@bb8725f`; initial tree clean. User explicitly requested completion of P1 observables following P1 solver.
- Context: AGENTS, project/development SOPs, workflow/prompt templates, requirements Phase 16, status/limitations, plan v2/GOV-004, SPEC-API-004/005, SPEC-PHYS-003, observable/serialization/golden tests and solver campaign helpers.
- In scope: all ten existing diagonal types; independent occupation references; declaration/type/parameter/order round trips; small full/reduced Schrodinger, Lindblad and seeded MCWF correctness; guarded N=4,8,12,16,20 solve/collection costs with independent repeats, memory, artifacts and offline audit.
- Out of scope: new physics/API, off-diagonal/coherence/entanglement, GPU, open-system cost/convergence campaign, isolated evaluation-only timing, observable-overhead subtraction, release or public-performance claims. No commit authorized.

## Current slice and acceptance

- Freeze one-axis cost scans: per N, mixed count 4/grid 101/original anchor; counts 1/16/64; grids 21/501; reversed/permuted anchor. Ten single-type N=4 controls plus two combined workloads give 52 configurations. Duplicate outputs under unique names are labeled and add no new physical information.
- Correctness: 3-site full/reduced ground/excited bitstrings, a nontrivial distribution, small evolving states, independent local-decay Lindblad and MCWF fixtures. Original/reverse/seeded permutation; MCWF five fixed seeds and retained raw trajectory samples. Connected correlation on MCWF means per-trajectory subtraction then averaging; use appropriate references rather than assume equality to nonlinear ensemble correlation.
- Audit empty-observable retention before interpreting timings. No incremental-overhead estimator without matched retention.
- Deterministic max observable error <=1e-8. Independent constant-H references with refinement/cross-check; MCWF explicit simultaneous Hoeffding bounds and raw-sample/average checks. Preserve every failure/exclusion/short run.
- Performance: initialized CPU doctor, setup/reference outside primary SDK timer; first + 2 warmups + 5 reset-state measurements per configuration, fresh supervised worker, preflight/timeout/RSS budget, requested/effective configuration and runtime dependency identity.
- Save results/manifests/references, raw membership, linear type-7 summaries, matching JSON/CSV/Markdown, frozen commands/source/config and checksums. Recompute values/order/stats/links after relocation without Julia.

## Requirement status

| Item | Status |
| --- | --- |
| Frozen matrix and independent references | Verified |
| Correctness/order/path/empty-output controls | Verified |
| Supervised repeated runtime and artifact contract | Verified |
| Tests and local full campaign acceptance | Verified |
| Formal documentation and retained evidence | Verified |

## Dependencies, surfaces and risks

Reuse benchmark_measurement, benchmarking, benchmark_suite and failure helpers; use existing SDK/Julia APIs. New observable benchmark module/CLI/audit/tests and formal docs; schema names and required fields unchanged. Large runs use the reduced chain (D=17711 at N=20), not dense full-space allocations. A projected reference verifies the reduced model, not physical blockade equivalence. SDK times include construction/collection/manifest; memory includes references and writes. Order-sensitive dictionaries must survive JSON persistence; retain ordered declaration lists rather than rely on sorted mappings.

## Required validation

Backend-free independent-formula, matrix/options/status/statistic and corruption checks; real small/large pilots; existing observables, serialization, solver and Python/Julia golden tests; full frozen campaign and original/relocated audit; documentation governance/links and V1 preservation. Full Python suite, CUDA, clean packaging and recurring RC gates remain separate.

## Validation log and progress

2026-11-27: Context recovered at clean bb8725f and scope/acceptance recorded. Implemented matrix, independent references, typed/order/round-trip gates, supervisor/retention and offline audit. Pilot N20/count64/grid101 and N20/count16/grid501 pass numerical gates but retain incomplete short-run status; all selected correctness paths pass. Full frozen campaign is running.

| Validation | Result |
| --- | --- |
| Backend-free matrix/formula/reference/status/options | 23 passed; two backend tests separately selected. |
| Marked real cost/Lindblad/audit-corruption integration and Python/Julia golden tests | 6 passed, 49 deselected; no skips. |
| Unmarked observable library, serialization and artifact/row/suite/failure regressions | 32 passed. |
| Solver configuration | 10 passed. |
| Documentation governance/benchmark references | 5 passed; final docs will be rechecked. |
| Pilot saved-output audits | 23 and 5 saved results checked, including reduced MCWF and actual empty-state history. |

Exact commands/logs are retained in the observable evidence validation directory. Frozen default accuracy is 1e-8, reference stability 1e-10, MCWF simultaneous alpha=1e-6, timeout900s and memory4096MiB. No target was relaxed. API/physics docs clarify existing per-trajectory connected-correlation semantics; no implementation change.

## Handoff and conclusion

Report actual coverage, changed surfaces, exact tests/evidence/docs, retained failures, schema compatibility and residual limits. Inspect final diff; preserve prior archives and V1 chapters; retain this branch record. No commit or publication.


## Final validation and conclusion — 2026-11-27

- Completed the bounded P1 observables slice. [Durable evidence](../../benchmarks/evidence/p1-observables-v2-2026-11-27/README.md) retains frozen inputs/source/runtime, both original short pilots, all results/manifests, references, empty histories, MCWF samples, companions, commands and checksums.
- Full matrix: 52 cost configurations and 12 small full/reduced correctness fixtures, all passed. 260/260 eligible measured calls; 416 first/warm/measured cost calls plus 60 correctness calls = 476 saved result/manifest pairs. Two additional bounded raw empty-history controls are retained. N=20 D=17711 ran successfully across the declared nine reduced configurations.
- Original/relocated backend-free audits agree exactly: all 476 outputs, 120 named cross-order pairs, MCWF uncertainty/sample means, requested/effective settings, normalized grids, statistics/member IDs, companions and source/runtime hashes pass. Maximum deterministic error 7.385203559806541e-12 (gate1e-8); reference stability4.2460065325116453e-13 (gate1e-10). All 1500 internal checksums passed.
- 23 backend-free tests, 6 selected marked backend/golden tests, 32 observable/serialization/artifact regressions, 10 solver-configuration and 5 documentation tests passed (76 targeted tests, no skips). Deselected unmarked modules were run separately; full Python-suite execution was not claimed. Final documentation/link check and git diff checks are retained.
- All 22 frozen source/config files match handoff and runtime Project/Manifest identity is constant. Historical V1 chapters are unchanged. SDK/Julia implementation and required artifact schemas are unchanged.
- Formal docs reconciled: plan v2, benchmark index/protocol/tiers/families/artifacts, requirements suite/cross-cutting matrices, GOV-004, status and limitations; API/physics docs clarify existing per-trajectory MCWF covariance semantics.
- One initial extraction started before archive compression ended and reported EOF; the history records it. After writer completion, full re-extraction/checksums/independent audit passed; original measurements were untouched.
- Residual limits: shared workstation, end-to-end SDK timings, lifetime memory including references/writes, duplicate collection outputs, conservative stochastic absolute bounds and three-atom decay controls. No incremental-overhead estimate, general nonlinear ensemble-covariance equivalence, physical/blockade validation, CUDA/off-diagonal support, open-system cost/convergence campaign, clean-wheel/container, recurring RC or public-use approval.
- Retain this branch record. No commit, merge or publication was requested or created. Expanded P1 open-system work remains outside this task.
