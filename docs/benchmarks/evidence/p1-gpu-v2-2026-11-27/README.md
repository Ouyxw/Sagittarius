# P1 GPU v2 local evidence — 2026-11-27

Status: Runner implemented; declared hardware campaign executed; automated saved-evidence acceptance passed.

All eight declared [P1 GPU scenarios](../../plans/v2.md#p1-gpu) passed on one RTX 5070 Ti:
chains N=2,4,8,12,16,20, a 2x2 lattice and the seeded two-node weighted-MWIS fixture.
All **40 independently measured CPU/CUDA pairs** passed the full 101-point observable
trajectory/configuration gate at 1e-6. Including first solves and two symmetric warmups,
the [audit](audit.json) checks **64 pairs and 128 saved result/standalone-manifest sets**.
No final scenario failed, skipped or remained incomplete. Maximum full-observable-trajectory
error over all saved pairs is 2.9629076969683865e-15. N=20 executed at reduced D=17711 (full dimension 1048576).

| Scenario | N / D | CPU median (s) | CUDA median (s) | CPU/CUDA median ratio | Eligible pairs |
| --- | ---: | ---: | ---: | ---: | ---: |
| chain_n2_cpu_cuda | 2 / 3 | 0.28099583 | 0.435630004 | 0.645033233 | 5 / 5 |
| chain_n4_cpu_cuda | 4 / 8 | 0.224877714 | 0.448431351 | 0.501476343 | 5 / 5 |
| chain_n8_cpu_cuda | 8 / 55 | 0.243870539 | 0.686106682 | 0.355441137 | 5 / 5 |
| chain_n12_cpu_cuda | 12 / 377 | 0.259006004 | 0.69233486 | 0.374105103 | 5 / 5 |
| chain_n16_cpu_cuda | 16 / 2584 | 0.620075427 | 1.03576641 | 0.598663386 | 5 / 5 |
| chain_n20_cpu_cuda | 20 / 17711 | 3.52281356 | 3.81893635 | 0.922459356 | 5 / 5 |
| lattice_2x2_cpu_cuda | 4 / 7 | 0.298631618 | 0.547552151 | 0.545393927 | 5 / 5 |
| weighted_udg_n2_seed3_cpu_cuda | 2 / 3 | 2.31062246 | 2.47169099 | 0.93483468 | 5 / 5 |

Ratios are explicitly `median(CPU runtime) / median(CUDA runtime)` for each frozen
scenario, qualified only after both paths have five eligible measurements, two warmups
and successful trajectory/effective-configuration gates. These are shared-workstation
SDK measurements; no speedup threshold is required and no general GPU advantage follows.
The [full table](gpu_bench_results.md) includes min/max/p25/p75, eligible counts,
initialization, first solves, process peaks and raw-pair links. Exact values/statistic
members live in [JSON](gpu_bench_results.json), [CSV](gpu_bench_results.csv) and
[raw repeats](gpu_repeats.json); the [suite](gpu_bench_results_suite.json) and its
[CSV](gpu_bench_results_suite.csv)/[Markdown](gpu_bench_results_suite.md) match.

## Frozen workload and source

- Branch `feature/benchmarking`, baseline `3891b14`, dirty source tree. No commit, merge, publication or release was performed.
- Config SHA256: `8d01bcb716f6e01d89ffb9f367ec9a35f52ce976cc1bcd8034996fc49ce91683`. [Campaign](campaign.json) retains ordered scenarios, exact values, settings, commands/cwd, source identity and file hashes. Source snapshots and runtime Julia Project/Manifest files are inside [campaign.tar.gz](campaign.tar.gz).
- Source/editable execution on Linux/WSL, Intel Core i7-14700KF, NVIDIA GeForce RTX 5070 Ti, compute capability 12.0. [Host observation](validation/host.json), [raw NVIDIA report](validation/nvidia-smi.txt), per-worker initialized doctors and per-result version metadata retain the actual host/driver/runtime/container values. NVIDIA CLI header and query/driver API versions are retained separately rather than conflated. Julia 1.13.4, CUDA.jl 6.2.0, Python 3.11.15, SDK Python/Julia 1.0.8.
- Chain/lattice: spacing 4 um, Rb=4.4 um, C6=100 rad*um^6/us, omega=2*pi rad/us, delta=0, duration .5 us. `pop0` is checked at every shared time.
- Application: existing seeded N=2, density=1, seed=3 weighted UDG; exact coordinates/edges/weights retained. C6=1, Rb=1, duration .1 us, sin-squared global omega_max=2*pi and per-atom delta ramps from -2*omega_max to weight*2*pi. `pop0` and `pop1`, final basis/probabilities, normalization and feasible candidate are checked. Exhaustive enumeration supplies the exact two-node objective; poor feasible AQC objectives remain valid.
- Complex128 all-ground preparation, reset before every call; atom i is bit i (LSB) and bitstring labels are in atom order. Actual basis, pulse, initial-state preparation and requested/effective settings are checked in saved manifests.
- Adaptive Tsit5, reltol=1e-8, abstol=1e-10, dt=None, 101 identical explicit times. One Julia/BLAS/OpenMP/MKL thread per worker; effective Julia/BLAS counts retained and audited.

## Measurement and memory boundaries

Each scenario starts a separate persistent CPU process and CUDA process. Each passes
its own initialized doctor, retains initialization and construction as single measurements,
then executes a first solve, two warmups and five independent measurements. Measured
CPU/CUDA order alternates; monotonic call intervals verify the actual order without overlap.
Doctor/JIT warm state persists per process; operators reconstruct per SDK call. First
solve after doctor is not process-cold initialization.

The timer surrounds one `Simulation.run` call, including SDK validation, pulse/operator
construction, transfers, observable collection and manifest creation. CUDA synchronizes
before and after the timed call. Reset, external references, saved-output validation,
serialization and reporting are outside the timer. Sparse caches reuse within solves;
diagonal observables transfer to host for summation. Historical size-scan single calls,
P0 Python matvecs and this repeated SDK workload have different timing boundaries.
Legacy `t_cpu_s`/`t_gpu_s` remain first measured calls; the v2 `speedup` column is the
qualified median ratio and is explicitly identified by its workload version.

Separate worker baseline/RSS/HWM records in bytes make process memory attributable
to each backend. Lifetimes include doctor, construction, JIT and serialization; controller
reference validation is excluded. The preflight reserve is 2 GiB per worker plus
basis/atom-dependent sparse maps, workspaces and output storage. Default sampled RSS
budget is 9216 MiB per worker, with a 1200-second wall deadline per scenario. Polling
every 50ms is not a hard allocation cap. Worker process groups are deliberately terminated
after checkpoint retention; normal teardown return codes are not solver failures.
GPU free/total snapshots include caches and other users and **do not measure peak GPU memory**;
peak remains null with a reason. Legacy combined `max_rss` is unavailable with a reason.

## Verification and diagnostic history

- [24 hardware/GPU/golden tests](validation/hardware-tests.log), no skips: new saved-result/memory integration and audit tampering check, original small protocol, global/local drives, seeded reduced state, multiple diagonal observables and Python/Julia golden checks.
- [36 benchmark regressions](validation/benchmark-regression.log), [29 solver/artifact/observable regressions](validation/solver-artifact-regression.log), [17 final contract/failure tests](validation/final-contract-tests.log), and [supervision/documentation checks](validation/supervision-documentation-tests.log). Counts describe their individual commands and include overlap.
- [Five final documentation tests](validation/documentation-tests.log), [documentation validation](validation/documentation.log), exact preservation of all four V1 benchmark chapters, checksum verification and relocated backend-free audit.
- The legacy small chain N=3 and weighted-MWIS protocol keeps its original fixture physics, `cuda_parity`/`mwis_gpu_parity` stems and ILP reference while sharing the scan measurement helpers. Its [hardware-test subcampaigns](small-protocol-hardware-test.tar.gz) are retained separately and are not pooled with this campaign.
- [Original pilots](pilots.tar.gz) and [diagnostic history](validation/diagnostic-history.json) retain the initial stdin/teardown failure, the short N=2 pilot and the three-scenario numerical pilot. Pilot 03 audited nine pairs with maximum error 2.9629076969683865e-15; its one-warmup/one-repeat rows correctly remain incomplete and have no qualified ratio. The first narrow ablation test invocation lacked the working Julia environment; the documented environment rerun passed. Original failed/partial measurements are not filtered or pooled into the final statistics.

This distinguishes software testing and numerical implementation verification from scientific
validation. Matched CPU/CUDA trajectories do not independently validate the physical model,
blockade approximation or hardware calibration. The host has external device users and no
CPU/GPU affinity, governor or exclusive-load isolation. This is not clean-wheel/container,
production CUDA, recurring RC, independent governance or public performance/release approval.
Other P1 suites and release/disclosure gates retain their existing scope.

## Replay and saved-evidence audit

[Commands](validation/commands.json) and the [environment script](validation/environment.sh)
retain the exact execution setup. The sandbox hides GPU devices; hardware-backed steps
ran with approved host GPU access. Use a prepared editable source environment and the
existing isolated `.venv/julia_cuda_env`; the writable `/tmp/ablation-julia-depot` overlay
and installed depot fallback are replay inputs, not portable clean-install evidence.
From `sagittarius_py`, after selecting that environment and making the device visible:

```bash
SAGITTARIUS_ENABLE_GPU_TESTS=1 uv run --no-sync python tests/test_performance/benchmark_gpu.py \
  --sizes 2 4 8 12 16 20 --warmups 2 --repeat-count 5 \
  --memory-limit-mb 9216 --timeout-seconds 1200 \
  --output-dir benchmark-output/p1-gpu-v2-2026-11-27
.venv/bin/python ../scripts/audit_gpu_campaign.py benchmark-output/p1-gpu-v2-2026-11-27
```

The complete [campaign archive](campaign.tar.gz) retains raw path logs/checkpoints,
all result/manifests, full report companions, frozen source snapshots, Python lockfile,
runtime Julia projects and internal checksums. Outer [checksums](SHA256SUMS) cover the
archive, visible summaries, source snapshots and validation logs. Absolute saved links
resolve by campaign prefix after relocation. No Julia/CUDA initialization is needed to
audit retained data from the repository root:

```bash
mkdir -p /tmp/sagittarius-p1-gpu-evidence
tar -xzf docs/benchmarks/evidence/p1-gpu-v2-2026-11-27/campaign.tar.gz \
  -C /tmp/sagittarius-p1-gpu-evidence
(cd /tmp/sagittarius-p1-gpu-evidence/campaign && sha256sum -c SHA256SUMS)
sagittarius_py/.venv/bin/python scripts/audit_gpu_campaign.py \
  /tmp/sagittarius-p1-gpu-evidence/campaign
```
