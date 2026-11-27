# Seven-suite benchmark runtime requirements workflow

Status: Branch-local working document
Merge policy: Retain as development record; durable requirements and tables are in benchmark docs.

## Baseline and authorization

- Branch `feature/benchmarking`, baseline `9294a8b`, initially clean, 2026-11-27.
- User authorized runtime-statistics requirements for seven P0/P1 benchmarks and
  organization of existing scaling/ablation timing evidence.
- Documentation-only slice: plan and linked protocol/family/tier/artifact,
  requirements/status and GOV-004; derived report from existing measurements.

## Requirement items and current slice

| Item | Acceptance | Status |
| --- | --- | --- |
| Common timing requirements | Two warmups/five repeats by default, wall-time scope, counts/membership, five statistics, failure/accuracy boundaries | Verified |
| Seven suite definitions | Primary workload, phases, grouping axes, statistical outputs and qualification rules per suite | Verified |
| P0 evidence organization | Full 42 scaling/16 CPU ablation/five paired ODE distributions; source links, exclusions, recomputation and immutable archives | Verified |
| Documentation reconciliation | V1 unchanged; no status promotion, required schema/API or runner changes | Verified |

## Context, dependencies and risks

Read AGENTS, development SOP/requirements/status/workflow/prompt context,
reference SOP/limitations, GOV-001/GOV-004, plan v2 and V2 reference chapters,
prior P0 branch workflows, documentation tests and retained campaign records.
Reuse existing v1 artifact semantics. P1 implementation and hardware campaigns
remain future work. SDK timing includes actual construction/collection overhead;
CPU matvec and CUDA ODE scopes stay separate. Shared-host measurements do not
establish isolated comparisons, current-code baselines or public claims.

## Validation and progress

- Recomputed all five runtime statistics from 210 scaling records, 80 CPU
  batches and 25 matched CPU/CUDA pairs; checked saved counts/member IDs and
  separate CPU summaries. Linear type-7 quantiles; full precision before display.
- Original archived numerical audits are referenced, not claimed as rerun.
- Required checks: documentation validator, existing documentation-governance
  and benchmark-consistency tests, V1 byte equality, report/source consistency,
  archive checksums and final diff scope/whitespace review.
- No simulation reruns, benchmark implementation changes, commits or publication.

## Validation results — 2026-11-27

| Command/check | Result |
| --- | --- |
| `python3 scripts/validate_documentation.py` | Passed metadata/status/local links |
| `cd sagittarius_py` then `UV_CACHE_DIR=/tmp/sagittarius-uv-cache uv run --offline pytest tests/test_benchmark_documentation_consistency.py tests/test_documentation_governance.py` | Five passed |
| Independent raw-record recomputation | 210 scaling, 80 CPU batch and 25 paired CPU/CUDA records match saved distributions/counts/member IDs |
| Independent rendered-table check using standard-library inclusive quantiles | All 68 displayed distributions and CPU median-us/op values match raw measurements at stated rounding; all six source fingerprints match |
| `sha256sum --check SHA256SUMS --quiet` in each of the three P0 archives | All passed; original evidence unchanged |
| Four reference-document V1 prefixes against baseline | Byte-for-byte preserved |
| `git diff --check` and scope review | Passed; only authorized docs/report/workflow changed |

All authorized documentation items are complete. P1 statistical runner work,
new hardware/controlled measurements, recurring RC runs and public approval
remain separate. The branch note is retained as a development record.

## Handoff

Report changed docs, evidence/counts, validation commands/results and retained
local-only/RC/P1 limits. Keep this workflow as development record.
