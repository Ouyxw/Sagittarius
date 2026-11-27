# P0 scaling workflow

Status: Branch-local working document
Merge policy: Retain as development record; formal behavior belongs in benchmark docs.

## Baseline and authorization

- Branch: `feature/benchmarking`; baseline: `efef375`; initial tree clean.
- Date: 2026-11-26.
- User authorized completion of plan v2 P0 scaling. No commit/publication requested.
- Scope: Phase 16 scaling and the shared measurement helpers it needs. Other suites are deferred.

## Current slice and acceptance

Implement the frozen chain/rectangle × radius × size matrix through N=20,
preserving the legacy function and `scaling_results` stem. Require projected
independent dense Hamiltonian/trajectory checks at N<=8 (Hamiltonian 1e-12,
observable 1e-8), tighter tolerance sensitivity at larger N, two warmups and
five independent reset-state measurements. Retain configuration values/hash,
initialized CPU doctor, requested/effective settings, explicit 101-point grid,
per-repeat result/manifest/reference links and statistics. Supervise each
scenario in its own process with timeout and RSS budget; retain exclusions,
partial progress and failed rows. All 42 declared scenarios must be accounted
for, and N=20 coverage requires successful measurements.

No solver/API/physics semantics or required artifact schema fields change.
Optional benchmark fields use the existing v1 contracts. Legacy flat `time_s`
continues to describe one SDK call (the first measured repeat); repeated
statistics have separately named fields.

## Validation and risks

- Tests: focused statistics, matrix, numerical-reference, timer/eligibility,
  failure/supervisor and compatibility checks; real Julia smoke and golden tests.
- Campaign: pilot then freeze thresholds, limits, commands and full inputs;
  archive original artifacts/logs and checksums, including dirty-source snapshot.
- Docs: plan, requirements, V2 protocol/families/tiers/artifact contracts,
  index, governance and known limitations/status as evidence warrants.
- Risks: Julia process startup and caches affect setup; RSS is process-lifetime
  peak including reference work, not isolated solve allocation. Projected
  references do not validate physical blockade approximation. Local evidence
  does not close release/public disclosure gates.

## Progress

- Implementation complete: matrix, CLI/legacy compatibility, numerical gates,
  measurement/statistics helpers, supervised RSS/timeout/crash retention and audit.
- Full local campaign: 42/42 passed, 210 eligible repeats; all six N=20 rows passed.
- Final focused validation: 71 passed, including real reduced/full backend smoke,
  Python/Julia golden, solver, serialization, benchmark and documentation tests.
- `python3 scripts/validate_documentation.py`: passed; V1 chapters preserved byte-for-byte.
- Evidence: [local archive](../../benchmarks/evidence/p0-scaling-v2-2026-11-26/README.md),
  original compressed artifacts, frozen source/runtime/config, pilots, test logs,
  recomputed numerical audit and internal/archive SHA256 inventories.
- Formal benchmark/requirements/governance/status/limitations docs reconciled.
- No commit, release, publication, CUDA or other-suite completion performed.
- Retain this workflow as a development record. Recurring RC P0 runs and
  independent governance/public-use review remain separate; larger references
  are sensitivity evidence rather than independent physical validation.

## Validation log — 2026-11-26

| Check | Result |
| --- | --- |
| Focused pytest modules recorded in archive `validation/commands.json` | 71 passed; no skips |
| Full matrix and saved-trajectory audit | 42 passed; 210 result/manifest pairs; no missing scenarios |
| Extracted original-file SHA256 inventory | 847 passed |
| Audit after archive extraction/relocation | Passed with the same numerical errors and coverage |
| Documentation governance and links | Passed; V1 chapters unchanged |
| `git diff --check` and scope inspection | Passed; no solver, Julia, schema-version or unrelated changes |
