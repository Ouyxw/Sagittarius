# P0 ablation CUDA validation workflow

Status: Branch-local working document
Merge policy: Retain as development record; durable contracts/evidence belong in benchmark docs.

## Branch baseline and authorization

- Branch `feature/benchmarking`, baseline `11f22d2`, initially clean, 2026-11-27.
- User requested completion of CUDA validation following P0 CPU acceptance.
- No commit, release, publication or driver changes requested.

## Scope and requirement items

Close the five optional ablation CUDA chain paths N=4,8,12,16,20 using actual
hardware, initialized doctor, same-scenario CPU ODE parity at 101 shared times,
first/warm/repeated solve evidence, result/manifests and a saved-output audit.
Keep the existing CPU archive immutable. Retain attempted setup/failure evidence.
Full P1 GPU geometry/application matrix, performance ratios, public claims and
release gates remain separate. Existing GPU parity tests/protocol provide
additional bounded checks; their scopes are identified separately.

## Cross-phase dependencies and required context

AGENTS; development SOP/requirements/status/workflow; reference SOP/limitations;
GOV-004 and performance-claim policy; plan v2 P0 ablation/P1 GPU; existing
ablation helper/campaign/audit, CUDA protocol, GPU tests and backend maturity.
CUDA remains experimental. CPU/Julia semantics and existing v1 schemas remain.

## Current slice and acceptance

- Doctor must initialize real CUDA with actual device/runtime/driver metadata.
- Same register, basis/order, pulse, normalized ground state, complex128,
  Tsit5 adaptive reltol=1e-8/abstol=1e-10, duration .2 and 101 explicit times.
- Compare complete pop0 trajectories at max absolute error <=1e-6; reject
  nonfinite data, grid/configuration/manifest mismatch or CPU fallback.
- Separate first solve, two actual-scenario warmups per backend, five measured
  reset-state pairs with alternating order. Synchronize CUDA timing boundaries.
- Retain all CPU/CUDA results/manifests, pair errors/eligibility, statistics,
  setup/source/environment and per-case memory. Snapshots are not GPU peaks.
- No CPU-matvec/CUDA-solve ratio. This work makes no performance-ratio claim.
- Fresh supervised child per CUDA case; timeout/RSS preflight and checkpoint
  partial data. CPU reference is included in that child's lifetime memory scope.

## Change surface and required validation

Ablation optional CUDA measurement, bounded mode selection in campaign CLI,
saved-solve parity helper/audit, regression tests and benchmark formal docs.
CPU measurement semantics and previous artifacts remain unchanged. Backend-free
failure/gate tests, real GPU parity tests, existing small protocol, numerical
pilot, frozen five-case campaign, golden/artifact/serialization checks,
relocation/checksum audit, documentation validator and diff scope review.

## Validation log

- Sandbox preflight: GPU device unavailable inside sandbox; host read-only
  nvidia-smi passed on RTX 5070 Ti after approved sandbox escalation.
- Initialized CUDA doctor: failed because the existing environment is CPU-only
  (CUDA package absent). Original doctor/log retained under benchmark-output.
- Isolated CUDA 6.2.0 environment installed; missing LLVM dependency required
  online resolution. CPU environment and tracked manifests are preserved.

## Progress log

- Context recovered; authorized CUDA slice defined. Hardware access confirmed.
- Found and fixed a fresh-process Julia world-age failure: lazy CUDA imports
  introduced Solver.CUDA too late for the first ODE RHS. The public GPU wrapper
  now imports CUDA then enters the solve through Base.invokelatest; source and
  packaged Julia copies are synchronized. CPU paths still avoid CUDA imports.
- Removed solver-error skips after successful initialized CUDA diagnostics.
  Initial hardware run retained six passes/one skip; corrected run passed all
  seven real GPU/golden checks without skips.
- Added complete CPU/CUDA trajectory/configuration/manifest/backend gates,
  symmetric first/warm/repeated pairs, alternating order, saved outputs and
  separate runtime summaries; no ratio. Structured Julia device fields are
  preserved when saving diagnostics. GPU memory uses explicit snapshots.
- Added bounded --modes selection, CUDA coverage, Julia source snapshot/hash
  guards and paired saved-result audit, preserving existing CPU archives.
- N=4 successful numerical pilot max error 4.440892098500626e-16; one-repeat
  evidence correctly incomplete. First failed pilot and exception chain retained.
- Existing small chain/MWIS CUDA protocol passed both rows. First full campaign retained four passed cases and an intentionally interrupted
  N=20 case after diagnosing repeated whole-state transfers inside the diagonal
  observable loop. Its 20 measured pairs passed saved-output audit; its statistics
  are not mixed with the corrected campaign.
- Diagonal GPU observables now copy the state once before accumulating in the
  original host order, preserving definitions and avoiding per-component whole-
  vector copies. Source and packaged copies match. Added multi-observable GPU
  parity; final hardware/golden run passed all eight tests without skips.
- Final five-case campaign restarted from a new frozen source/configuration with
  two warmups/five paired measurements per size. Cache scope explicitly records
  repeated SDK validation/pulse/operator construction and within-solve sparse reuse.

## Risks and handoff requirements

Report exact source/environment, hardware, tests/commands, scope/exclusions,
CPU-reference versus GPU timer boundaries, memory limitations and remaining
P1/RC/public-use work. Preserve all failures and existing evidence archives.

## Conclusion

Completed the authorized optional ablation CUDA scope: five sizes through
N=20, 25 eligible measured pairs, 80 first/warm/measured result/manifest pairs,
initialized doctor, numerical/artifact/config/source audit and retained failures.
Eight hardware/golden, 37 regression, 20 final ablation and seven observable/
invariant tests passed without skips; earlier focused tests/logs are retained.
All archived output/checksum and relocated audits pass. Formal benchmark,
requirements, governance, API/backend reference, status and limitations docs
are reconciled; V1 and original CPU evidence remain unchanged. Retain this
workflow as development record. No commit/publication/release or full P1 GPU
completion; no ratio or hardware-independent performance claim. Case RSS
includes CPU reference; GPU peaks remain unavailable snapshots.

## Final acceptance and handoff

- All five final CUDA rows passed; no skipped/failed/incomplete final cases.
- Complete archive and exact commands: [retained evidence](../../benchmarks/evidence/p0-ablation-cuda-v2-2026-11-27/README.md).
- Numerical and artifact audit recomputes all 25 measured pairs plus first/warmups.
- Prior failed first-call pilot, six-pass/one-skip test run, dependency failures,
  metadata serialization diagnostic and interrupted four-pass campaign retained.
- Source/package equality, original CPU evidence immutability, V1 preservation,
  documentation links and diff checks passed. Remaining P1 GPU matrix, physical
  approximation, clean-wheel/container, RC and public-use gates are separate.
