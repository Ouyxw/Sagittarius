# Branch workflow: P1 MWIS/UDG benchmark

Status: Branch-local working document
Merge policy: Retain as a development record; formal contracts and acceptance live in benchmark documentation.

## Baseline and authorized scope

- Date: 2026-11-27; branch `feature/benchmarking`; baseline `58dfd10`; initial tree clean.
- Authorization: user requested continuation and completion of v2 MWIS/UDG after the completed P1 GPU work.
- Context: project SOP and development SOP, agent workflow/prompt templates, requirements Phase 16, status routing, limitations, GOV-004, benchmark plan v2 and artifact contracts, solver/parity contracts, existing MWIS adapter/ILP/tier tests.
- Scope: N=2,4,6,8,10,12,16,20, five instances per size (seeds 101–105), density parameter .8, Rb=1, weights [1,1.5], existing sin-squared/ramped-detuning schedule at duration .15. Preserve initial IDs/tier outputs. No physics/API/schema version or release/public-claim expansion.

## Slices and acceptance

1. Compatible real-result/manifest outlet from the project AQC adapter; split setup, SDK execution and decoding without changing legacy tuple outputs. Exact ILP status must require both PuLP problem and solution optimality; preserve incumbents/timeouts and logs.
2. Freeze all 40 graphs/configs and source identity. Run independently initialized supervised AQC and ILP processes per instance, first execution, two warmups and five measured executions each. Separate generation/setup/model construction/post-processing/serialization/reference timings. Retain path memory and explicit CBC-subprocess memory limitations.
3. Verify graph/basis/atom/bitstring mapping, probability normalization and feasibility/objective metrics; small brute-force controls verify ILP and optimal-state mass. Freeze a 1e-6 probability/trajectory numerical gate after tighter-solver pilot checks. A poor feasible AQC objective is a valid result. Missing exact optimality leaves gap/ratio/optimal mass null with reasons while retaining AQC output.
4. Backend-free saved-evidence audit of real results/manifests, numerical references, ILP status/logs, stats/membership, all report companions, hashes and links. Execute/archive all 40 instances through N=20 and verify extraction/checksums.

Public change surface: project adapter methods and benchmark CLI/artifacts (compatible optional fields); SDK solver/physics and existing schema names unchanged. Runtime reports compare different solution guarantees and derive no AQC/ILP speedup. Scientific validation, schedule optimization, distribution-wide quality, CUDA and release gates remain outside scope.

## Requirement status

| Item | Status | Validation |
| --- | --- | --- |
| Adapter provenance and exact-reference termination | Verified | Legacy raw-probability tuples preserved; actual SDK result/manifest outlet; PuLP problem+solution optimality checked. |
| Frozen repeated performance runner | Verified | Independent process per instance/path, reset state/fresh CBC model, separate phases and statistics. |
| Numerical/graph/probability/failure contracts | Verified | Independent sparse-Hamiltonian SciPy DOP853 and refinement, raw norm from Z0+2n0, exhaustive ILP/quality controls; 17 MWIS tests and 49 regressions passed. |
| Full campaign and retained audit | Verified | 40/40 passed, 200 measured AQC and 200 measured ILP calls; all 320 AQC result/manifest sets and 320 CBC references audited, including all five N=20 instances. Original/relocated audits and checksums passed. |
| Formal docs reconciliation | Verified | Plan, requirements/cross-cutting matrices, benchmark index/V2 protocol/tiers/families/artifacts, GOV-004, status and limitations reconciled; V1 chapters unchanged. |

## Validation and handoff

Start with adapter/batch/optimal-probability and new contract tests; then real small-backend integration, serialization/solver/golden tests and documentation governance. Long campaigns stay outside ordinary CI. Retain all failed/short pilots, exact commands, frozen source/runtime projects, original result/manifest pairs and checksums. Before handoff inspect diffs, preserve earlier archives and V1 chapters, record actual coverage and residual limits here and in formal docs. No commit is authorized.


## Validation log — 2026-11-27

[Evidence, exact commands and logs](../../benchmarks/evidence/p1-mwis-v2-2026-11-27/README.md) retain every gate.

| Command / scope | Result |
| --- | --- |
| MWIS adapter, legacy tiers/batch/optimal probability, new performance contract/integration pytest modules | 17 passed, no skips; earlier 2-failure compatibility regression and its fix retained. |
| Cross-language golden, solver configuration, serialization, observable/invariant and benchmark artifact/row/suite/failure pytest modules | 49 passed, no skips. |
| Documentation governance and benchmark consistency pytest modules | 5 passed. |
| `benchmark_mwis_aqc.py --tier performance --sizes 2 4 6 8 10 12 16 20 --seeds 101 102 103 104 105 --warmups 2 --repeat-count 5 --timeout-seconds 600 --memory-limit-mb 4096 --ilp-time-limit 30 --numerical-atol 1e-6` | 40 passed; no skipped/failed/incomplete rows. Frozen SHA256 `9e1995d01461933a75d97086d9f981a3e3bfd643af02cd3c84d3e69951009472`. |
| `scripts/audit_mwis_campaign.py` on original/extracted campaign plus retained report-field checker | Passed: 320 saved AQC results/manifests, 320 proven ILP references; exact stats/quality/numerics/source/runtime/links and every companion value verified. Extracted review imported no Julia and executed no CBC. |
| Extracted campaign `sha256sum -c SHA256SUMS` | All 1851 retained files passed. |
| `python3 scripts/validate_documentation.py`, frozen source comparison and V1 comparison | Passed; all 25 frozen source/configuration files match handoff; all four historical V1 chapters preserved exactly. |

## Completion and residual scope

The bounded local P1 MWIS/UDG slice is complete. All five N=20 graphs executed (D=9240–53760). Maximum numerical trajectory/probability error is 8.41542979745924e-9, maximum raw-state norm error 8.676439344768028e-9 (gate 1e-6). Refinement is separately checked at 1e-9. All 320 CBC calls prove optimality and agree with independent exhaustive objectives. Repeated measured counts are 200 per method; first/warmup data remains separate. Runtime Project/Manifest and CBC binary identities remain constant across all 40 instances.

The .15-duration schedule's highest-probability candidate is the empty set on all 40 instances, giving objective ratio zero. These poor but feasible results are retained as required; no optimization improvement or AQC/ILP timing speedup is claimed. Very small optimal-state probabilities have an absolute gate, not relative-precision assurance. AQC SDK timing includes construction/collection/manifest; ILP timing includes native subprocess startup/IPC and parsing. Worker memory includes initialization/reference/writes; CBC subprocess peak is unavailable. Shared-host archival/documentation activity can overlap and no affinity/exclusive-load control is claimed.

Changed code surfaces: source-project adapter's compatible prepare/result/decode methods, optional performance tier/flags, new benchmark/reference/status/statistics module and backend-free audit. Legacy `solve_full` raw probabilities and initial three-tier defaults/IDs/stems remain compatible. No SDK physics/solver implementation, Julia source, required artifact schema or package/release behavior changed. Formal docs and durable archive carry the final contracts and acceptance. Full Python-suite execution, CUDA, clean-wheel/container validation, broader schedules/families, scientific/blockade validation, recurring RC and independent public disclosure approval remain outside this slice. No commit or merge was created. Retain this branch record alongside formal documentation.
