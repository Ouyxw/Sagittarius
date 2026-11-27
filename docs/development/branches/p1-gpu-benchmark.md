# Branch workflow: P1 GPU benchmark

Status: Branch-local working document
Merge policy: Retain as a development record; durable contracts and evidence go in formal benchmark docs.

## Baseline and authorization

- Branch: `feature/benchmarking`; baseline `3891b14`; initial tree clean.
- Date: 2026-11-27.
- Authorization: user requested completion of the P1 GPU scope in `docs/benchmarks/plans/v2.md`.
- Required context: project SOP, requirements Phase 16, status maintenance table, limitations, development SOP, workflow and prompt templates, GOV-004, v2 benchmark plan and existing CUDA/ablation contracts.

## Current slice

Implement the existing eight-case matrix (chains N=2,4,8,12,16,20, 2x2 lattice, seeded weighted MWIS), retaining the legacy small protocol fixtures and output stems. Share matched timing/grid/parity helpers. Use separately initialized persistent CPU/CUDA child processes per scenario so each backend has attributable process memory. Alternate measured execution order, reset initial states, synchronize CUDA around SDK timers, retain first solves/two warmups/five measured repeats, saved results/manifests and full-grid gates. Compute a median ratio only with sufficient matched eligible evidence.

Acceptance: opt-in never initializes CUDA when disabled; initialized doctor failures and resource/solver/serialization failures retain partial timings; all declared rows accounted for; full saved-trajectory/configuration gates at 1e-6; recomputable statistics and matching JSON/CSV/Markdown; actual hardware campaign and backend-free evidence audit. No physics/solver API or required schema changes. No release/public performance approval.

Tests: focused GPU contract/failure/audit tests, existing CUDA/ablation/artifact/row/suite tests, real CUDA and Python/Julia golden checks, documentation validator and consistency tests. Risk: shared workstation timing and device snapshots cannot establish isolated performance or peak GPU memory; same-method parity is software/numerical verification only.

## Requirement status

| Item | Status | Evidence |
| --- | --- | --- |
| Shared protocol and scan measurement | Verified | Shared scenarios, timers and full-grid/configuration/application gates; 24 hardware/GPU/golden tests passed without skips. |
| Per-backend memory and retained failures | Verified | Separate CPU/CUDA workers; budget/deadline/crash/interruption/write-failure tests; attributable baseline/HWM and device snapshots retained. |
| Campaign through N=20 plus geometry/application | Verified | All 8 scenarios, 40 measured pairs and 64 total first/warm/measured pairs passed; N=20 D=17711. |
| Automated saved-evidence audit | Verified | Original and relocated archive audit passed, 128 result/manifest sets; maximum full-observable error 2.9629076969683865e-15. Julia/CUDA never imported by relocated audit. |
| Formal docs reconciliation | Verified | Requirements, plan, benchmark index and V2 protocol/tiers/families/artifacts, GOV-004, status and limitations updated; four V1 chapters unchanged. |

## Validation and handoff

Host GPU probe passed outside the sandbox: RTX 5070 Ti, NVIDIA driver 610.57.01. Sandbox GPU access is blocked. Hardware steps require host GPU access; CPU skips alone never close CUDA acceptance. Validation results and final changed surfaces will be recorded here before handoff. No commit is authorized.


## Validation log — 2026-11-27

Full commands, environment and original logs: [retained evidence](../../benchmarks/evidence/p1-gpu-v2-2026-11-27/README.md).

| Command / gate | Result | Scope |
| --- | --- | --- |
| GPU benchmark, CUDA protocol, GPU acceleration and cross-language golden pytest modules | 24 passed, no skips | Actual initialized host CUDA; global/local/seeded/multiple-observable parity, new integration/memory/audit and original small fixtures. |
| Ablation, benchmark artifact/row/suite/failure pytest modules | 36 passed | Includes original short-campaign saved-output audit after selecting the documented Julia environment. |
| Serialization, solver configuration, observable library and invariants pytest modules | 29 passed | Public solver/result/observable regression. |
| Final GPU contracts/supervision and legacy protocol CPU tests | 17 passed, 2 CUDA tests deselected | Disabled opt-in, budgets, timeout/crash/interruption, timer reset/sync, numerical gates, warmup exclusion, slow repeats, missing ratio and source/companion tampering. |
| Documentation governance and benchmark documentation consistency | 5 passed | Formal documentation routing and source/stem consistency. |
| `benchmark_gpu.py --sizes 2 4 8 12 16 20 --warmups 2 --repeat-count 5 --memory-limit-mb 9216 --timeout-seconds 1200` | 8 passed, no skipped/failed/incomplete rows | Frozen config SHA256 `8d01bcb716f6e01d89ffb9f367ec9a35f52ce976cc1bcd8034996fc49ce91683`; actual source files match handoff. |
| `scripts/audit_gpu_campaign.py` on original and relocated archive | Passed | 64 pairs, 40 measured; all saved trajectories, configs, source/runtime hashes, order, statistics/ratio and companion cells checked. |
| `sha256sum -c SHA256SUMS` on extracted campaign | Passed | Entire internal inventory checked. |
| `python3 scripts/validate_documentation.py` and V1 source comparison | Passed | Four historical V1 chapters preserved byte-for-byte. |

## Progress and handoff

Implementation, frozen hardware campaign and automated acceptance are complete for this bounded P1 GPU slice. The [archive](../../benchmarks/evidence/p1-gpu-v2-2026-11-27/README.md) retains original failed/short pilots, legacy protocol hardware subcampaigns, visible JSON/CSV/Markdown companions, raw pairs, 128 result/manifest sets, source/runtime files, tests and checksums. Final source snapshots match all 23 frozen source/configuration files. No Julia solver/backend or simulation artifact schema changed; `cuda_parity.solve_pair_gate` now supports every declared observable while preserving its default single-observable behavior. No commit or merge was created.

The final N=20 local medians were CPU 3.52281 s and CUDA 3.81894 s, ratio 0.922459. No speed threshold was an acceptance requirement. These end-to-end SDK distributions include transfers, host observable summation, construction and manifest creation, on a shared workstation. GPU peak memory is unavailable; RSS includes worker initialization/construction/writes. Same-method numerical parity is not independent scientific or blockade-approximation validation. CUDA remains experimental. Full Python-suite execution, clean-wheel/container smoke, recurring RC, independent disclosure/public performance approval and other P1 suites were not claimed by this slice. The branch-local record is retained; durable behavior and acceptance status are in formal docs.
