# P0 ablation workflow

Status: Branch-local working document
Merge policy: Retain as development record; formal behavior belongs in benchmark docs.

## Branch baseline and authorization

- Branch `feature/benchmarking`, baseline `d4f4cea`, initially clean.
- Date: 2026-11-27. User explicitly requested completion of plan v2 P0 ablation.
- No commit or publication authorized or required.

## Scope and requirement items

Phase 16 `ablation`: fixed normalized seeded H*psi, four Python CPU paths,
independent repeats, independent references, construction timing, attributable
memory and supervised resource/failure retention. Initial chain N=4,8,12;
reduced extensions N=16,20. Optional CUDA ODE evidence stays separate.
P1 suites, solver/physics semantics, release and performance claims are excluded.

## Cross-phase dependencies and required context

Read AGENTS, development SOP/requirements/status/workflow/prompt context,
reference SOP/limitations, GOV-004, plan v2, existing scaling measurement,
benchmark artifact/failure/suite contracts and ablation/solver tests.
Python/Julia golden tests verify shared Hamiltonian conventions; CPU ablation
timings characterize Python/NumPy/SciPy, not Julia solver internals.

## Change surface and current slice

Implement the requested P0 as one bounded slice: ablation helper, supervised
campaign/CLI, audit, tests and formal benchmark docs. Preserve legacy `repeats`
as operations per batch and existing `ablation_bench_results` companions.
Add optional fields and suite/repeat companions within existing schemas.

## Acceptance and required validation

- Independent dense/full and projected-dense checks at N<=8; independent
  transition-action reference for larger fixtures, with its limitations retained.
- Full max relative error <=1e-12; reduced max absolute error <=1e-10;
  normalized seeded complex128 inputs and finite checks outside measured batches.
- Two warmups, five independent batches of 50 fixed-input matvecs by default;
  setup/first/warm boundaries and linear type-7 statistics retained.
- Fresh child per path; preflight dense intermediates, full-dimension guard,
  sampled RSS/timeout limits; preserve exclusions, failures and partial repeats.
- Required small CPU rows pass, extended rows accounted for; exclusions do not
  count as successful N=20 execution. CUDA opt-in and initialized doctor required.
- Focused ablation/measurement/artifact/solver tests, Python/Julia golden tests,
  pilot and frozen local campaign, saved-output numerical audit, documentation
  validator, diff scope/whitespace review.

## Risks

Dense intermediates grow as D squared, including current CSR construction.
RSS is process lifetime including doctor/references; sampled enforcement is
not a hard address-space cap. Full/reduced bases describe different workloads.
Projected correctness does not validate the physical blockade approximation.
Workload v2 cannot be pooled with historical H^k*psi timings. Local evidence
does not authorize CUDA, release or public performance claims.

## Validation log

| Check | Result |
| --- | --- |
| Focused ablation/artifact/suite/solver/golden/documentation tests | 33 passed, no skips |
| Serialization/solver config/row/failure/public suite/shared supervision tests | 53 passed, no skips |
| Numerical pilot N=4,8 | Eight CPU gates passed; short runs correctly incomplete |
| Frozen full campaign | 25 rows retained; 16 CPU paths passed, 80 eligible batches, 9 documented skips |
| Saved-output/config/source/statistics/companion audit | Passed; max absolute error 4.577566798522237e-16 |
| Extracted original-file checksums and relocated audit | Passed; all 80 outputs rechecked |
| Documentation governance/local links and V1 preservation | Passed |
| Diff whitespace and scope inspection | Passed; no API/Julia/required-schema changes |

Exact commands and original logs are retained in the [evidence archive](../../benchmarks/evidence/p0-ablation-v2-2026-11-27/README.md).

## Progress log

- Implementation and local CPU acceptance complete on 2026-11-27.
- Preserved `repeats` operation-count semantics; introduced `repeat_count`, fixed
  normalized input workload, independent dense/analytic references and gates.
- Added per-path resource preflight/supervision, checkpoints, saved numerical
  outputs, suite/repeat companions and replay audit. Existing schema names retained.
- Initial sandbox doctor failures retained; writable depot/CondaPkg Null
  remediation and successful pilot preceded the full campaign freeze.
- Both N=20 reduced paths passed at D=17711 under frozen 9216 MiB budget.
- Updated benchmark plan/protocol/tiers/families/artifact/index, requirements,
  status, governance, limitations and performance-runner README. Historical V1
  chapters preserved. Solver runner adaptation only labels the new workload
  and preserves its existing outer-repeat boundary; no P1 expansion.
- Exact runtime/source/configuration and validation retained with checksums.
  No commit, publication, CUDA or release completion performed.

## Handoff requirements

Report code/tests/docs/artifacts, commands/results, retained evidence, residual
limits and deferred P1/RC/public-use work. Inspect diff and preserve unrelated work.

## Conclusion

All requested P0 CPU requirement items are implemented, verified and archived.
86 tests passed with no skips; full CPU campaign and relocated numerical audit
passed. No deferred CPU path remains within the declared matrix. Full N=16,20
paths remain dimension exclusions; CUDA rows remain optional skips and do not
close GPU-suite parity. Larger references use analytic transition action;
physical approximation validation, P1 suites, recurring RC and independent
public/governance review remain separate. Shared-workstation validation overlapped
early sizes; no host-isolated performance claim is made. Retain this document
as development record; formal behavior/evidence is in the benchmark docs.

CUDA follow-up on baseline `11f22d2` is tracked separately in the
[CUDA validation workflow](p0-ablation-cuda.md); the original CPU archive
and its historical skip rows remain immutable.
