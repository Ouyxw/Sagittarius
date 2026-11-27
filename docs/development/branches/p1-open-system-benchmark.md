# Branch workflow: P1 open-system

Status: Branch-local working document
Merge policy: Retain development record; extract durable contracts/evidence into formal docs.

## Baseline and authorization

2026-11-27, `feature/benchmarking@3efa732`, clean working tree. User requested
completion of plan-v2 P1 open-system; this authorizes implementation and local
measurements within that existing plan. No commit, publication or release.
Read project SOP/workflow, Phase 16 requirements/status/limitations, benchmark
plan and GOV-004, local-noise spec, existing observable measurement/audit and
open-system implementation/tests.

## Current slice, acceptance and risks

Implement CPU local decay/dephasing/combined Lindblad and seeded MCWF only.
Freeze a one-axis full/reduced size matrix (1,2,4,6,8,10,12,16,20), 100/500/1000
trajectories, scalar and small per-site rates, 101 times, supported linear
site/total/pair observables. Preserve the original one-atom runner/archive.
Use separate resource estimates for D-squared Lindblad histories/temporaries
and MCWF state/workspace/output; retain exclusions and failures.

Small references: independent dense master equation, analytic excited decay
and coherence dephasing; save raw density histories outside timed workloads,
check trace <=1e-6, eigenvalues >=-1e-7, deterministic error <=1e-6.
Five fixed seeds separately from fixed-seed 2-warmup/5-repeat timing; freeze
simultaneous Hoeffding absolute bounds (alpha1e-6) before measurement, retain
count/seed error reports without monotonic-error requirements. Larger interacting
cases use tighter-solver and multi-seed consistency plus target-size analytic
controls; explicitly retain the independent interacting-reference gap.
Optional raw trajectory retention is a separate measured small workload.

Reuse shared measurement, row, artifact, suite and failure helpers. Require
requested/effective solver/noise/seed/count/grid/basis, serial execution mode,
throughput distributions, source/runtime hashes, real result/manifest links,
raw membership, matching companions, original/relocated backend-free audits.
No required schema changes, SDK/Julia physics extensions or performance claims.

## Validation and documentation

Focused independent-reference/matrix/resource/statistics/failure/corruption tests,
bounded real-backend pilots, open-system/MCWF/serialization/artifact/golden
regressions, complete guarded local campaign, original/relocated audit and
checksums. Update v2 plan, benchmark index/protocol/tiers/families/artifacts,
requirements matrices, GOV-004, status and limitations. Run documentation checker.
Scientific validation, GPU, clean packaging, recurring RC and public approval
remain separate. Large-case exclusions are boundaries, not successful coverage.

## Progress

- Context and acceptance recovered; implementing frozen matrix and references.

Pilot decision: Rb=8.4 (D2745 at N20) costs about16s/100 trajectories. Before
formal freeze choose Rb=12.4 (D907 at N20), MCWF D<=1024 and Lindblad D<=256
validation/time budgets, retaining every excluded full/reduced row. Rate/count,
accuracy and statistical acceptance targets unchanged. Preserve short pilots,
initial read-only Julia-cache failures and source-freeze rejections during test
development; none count as accepted campaign evidence.

## Validation progress

- Backend-free matrix/analytic/dense/reference/resource/statistics/options checks:
  27 passed. Includes independent scalar/per-site decay/dephasing/combined
  references, reference instability rejection, pooled-bound failure and seed gaps.
- Full targeted backend selection (new integration, open-system sanity, Python/
  Julia golden, MCWF and solver configuration): 48 passed, no skips (82.78s).
- Artifact/row/suite/failure/serialization and documentation regressions: 33
  passed; documentation governance/link script passed.
- Small raw-storage integration audits actual result/manifest/sample means and
  detects companion, seed/manifest, convergence and raw-coherence corruption;
  monkeypatched Julia initialization proves its audit is backend-free.
- N12 reduced Lindblad pilot passes all raw density/invariant and primary
  observable gates; short warmup/repeat settings correctly remain incomplete.
- N20 K1000 sensitivity completes; first SDK call ~52s, tighter call ~106s.
  Formal 1800s row budget accommodates declared repeats; no speed claim follows.
- MCWF currently writes nominal full-bitstring unsupported-readout metadata even
  for reduced execution. Retain this SDK behavior, account for its allocation,
  distinguish actual solver basis from unavailable final sampling, and document
  it. No SDK physics or readout API extension is part of this benchmark task.

## Frozen campaign

Final source/reporting gates are frozen. All 82 distinct targeted tests pass
across the retained full regression and final 28-test runner rerun; no skip is
counted as backend evidence. One initial corruption-test regex failure correctly
reported the new earlier initial-state check; fixed expectation and rerun pass.
Raw eigenvalue audit comparisons allow 1e-12 floating replay differences while
recomputing the original trace/Hermiticity/positivity acceptance thresholds.

The full 99-row campaign is running with two warmups/five measurements and
1800s/4096MiB limits, densityD256/stateD1024 caps. Expected boundary accounting:
75 cost and ten correctness rows executable, 14 explicit resource exclusions;
375 measured calls, 315 statistical calls, 150 warmups, 75 first calls and one
coherence call, plus 63 separate tighter sensitivity results and 67 raw-density
controls. These are expected counts, not completion evidence until audited.
The frozen-source inventory includes the nominal full-space MCWF readout
allocation, even for reduced simulation. SDK/schema/physics code is unchanged.

Documentation correction: PHYS-004 had pre-Phase15 seed/grid bullets despite
existing API-005 and implemented seed/saveat support. Updated this current
baseline and serial/raw-storage explanation; advanced Phase14 models remain
planned. No physics, solver, seed or required schema behavior changed.

## Direct Lindblad/MCWF review

The frozen worker supplies independent small references and larger tighter-MCWF
controls. Required direct MCWF/Lindblad consistency also uses separately retained
Lindblad outputs wherever the campaign permits that density path (including
D69/250/256). Added a separate backend-free acceptance review, preserving all
measurement sources/configuration/raw files and their original hashes. Its own
source/test identities are retained independently. It uses the already frozen
32-slot Hoeffding union rule plus two deterministic 1e-6 floors, without changing
any measurement or acceptance tolerance. A raw-storage flag changes cost identity
but not the linear physical mean being compared. Missing matching density paths
remain explicit; analytic controls keep their independent special-case gates.

Five review tests pass. An early saved-output review of completed configurations
checks 30 matched configurations/420 individual or tighter outputs, all passing.
Final acceptance must pass both the original measurement audit and this direct
cross-path review through `scripts/accept_open_system_campaign.py`.

## Final acceptance and handoff — 2026-11-27

| Requirement | Status | Retained evidence |
| --- | --- | --- |
| Frozen local-noise matrix / source / resources | Verified | 99 rows; 85 pass, 14 preflight exclusions; all measurement code hashes match handoff. |
| Runtime / throughput / raw storage | Verified | 75 cost configurations, 375 eligible measurements, two warmups each, fixed-seed timing and separate export workload; exact type-7 statistics/member IDs and companions. |
| Analytic / dense / density gates | Verified | Ten correctness controls; 67 raw density histories; coherence, trace, Hermiticity and positivity; independent small master equations/refinement. |
| Multi-seed and direct cross-path review | Verified | 315 statistical calls; 45 cross-count checks; 54 directly matched configurations, 708 individual/tighter and 54 pooled Lindblad/MCWF checks. Nine unavailable matching density references retained. |
| Result / manifest / runtime identity | Verified | 916 regular plus 63 tighter saved pairs; 23 frozen measurement source files, two separate review source/test files; 979 manifests match source/Python packages and one Julia1.13.4 Project/Manifest identity. |
| Tests | Verified | 88 distinct targeted tests covered by passing retained regressions: 82 initial/new-runner tests, five cross-review units and one real per-atom reduced-noise/cross-review integration; no skips counted as evidence. |
| Durable archive / relocation | Verified | Three archive parts and separate original pilots; all 2779 internal checksums pass; original tree hidden during relocated backend-free acceptance; complete reports identical. |

[Durable evidence](../../benchmarks/evidence/p1-open-system-v2-2026-11-27/README.md)
retains commands, original failures/short pilots, complete raw data, source/runtime
and review identities, companions, checksums and acceptance reports. Original
one-atom/V1 archives and V1 document bodies remain unchanged. Formal docs reconcile
plan/index/protocol/tiers/families/artifacts, requirements/status, GOV-001/004,
noise-model seed/grid baseline and known limitations. Final documentation/link,
V1 preservation, outer checksum and diff checks are retained with the evidence.

Residual/deferred: reduced N20 coverage is D907 at Rb12.4, not full space or a
physical blockade validation. Full/density resource exclusions remain open;
independent large interacting references are unavailable. Same-method sensitivity,
matched Lindblad/MCWF checks and conservative absolute bounds are software/
numerical evidence. Timings are end-to-end SDK on a shared workstation; memory
is worker-lifetime including reference/writes. MCWF completion count is inferred
from successful return/manifests and nominal full-space unsupported-readout
metadata still allocates. No GPU, clean package/container, full Python-suite,
recurring RC, scientific calibration or public-use approval is established.

Retain this workflow as a development record. No commit, merge or publication
was requested or created. The bounded P1 open-system task is complete.
