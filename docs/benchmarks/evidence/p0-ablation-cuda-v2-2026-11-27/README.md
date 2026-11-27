# P0 ablation CUDA v2 local evidence — 2026-11-27

Status: Retained local hardware-backed CPU/CUDA numerical verification; automated audit passed.

All five [CUDA cases](ablation_bench_results_suite.md) passed at N=4,8,12,16,20,
including N=20 D=17711. Each case retains first solves, two warmup pairs and
five measured CPU/CUDA pairs at 101 explicit shared times. All 25 measured
pairs passed full-trajectory finite/grid/configuration/manifest/backend checks
at maximum absolute error <=1e-6. The [audit](audit.json) recomputes all saved
pair gates; maximum error over first/warm/measured trajectories is
8.8817841970012523e-16. No scenario failed, skipped or remained
incomplete in the final campaign. This supplements the immutable
[CPU archive](../p0-ablation-v2-2026-11-27/README.md); it does not replace it.

| N | Reduced D | Full dimension | Measured pairs |
| --- | ---: | ---: | ---: |
| 4 | 8 | 16 | 5 |
| 8 | 55 | 256 | 5 |
| 12 | 377 | 4096 | 5 |
| 16 | 2584 | 65536 | 5 |
| 20 | 17711 | 1048576 | 5 |

## Source, hardware and frozen configuration

- Branch `feature/benchmarking`, baseline `11f22d2`, dirty source tree. No commit, publication or release was performed.
- Config SHA256: `93d9c8a34504c383b05bb5619e1aa061e335d3aea839098458f0725426c8ccf8`; exact settings and hashes are in [campaign.json](campaign.json).
- Host: Intel Core i7-14700KF, Linux/WSL, NVIDIA GeForce RTX 5070 Ti, compute capability 12.0, 17094475776 bytes device memory.
- Host NVIDIA driver reported 610.57.01; initialized CUDA driver/runtime API version 13.3.0. Julia 1.13.4, CUDA.jl 6.2.0, Python 3.11.15, SDK Python/Julia 1.0.8. Complete CPU/CUDA doctor/version/device metadata are retained per case.
- Isolated CUDA environment: `sagittarius_py/.venv/julia_cuda_env`; installed without changing the existing CPU environment or tracked manifests. Missing LLVM dependencies required online resolution. Replay uses each child's retained Julia Project/Manifest and Python lockfile.
- Chain a=2.0 um, Rb=3.0 um, C6=100 rad*um^6/us, omega=2*pi rad/us, delta=0; ascending bitstring basis, atom i is bit i (LSB), complex128 all-ground state reset before each solve.
- Both backends use Tsit5 adaptive reltol=1e-8/abstol=1e-10, duration .2 us and 101 explicit times. Requested/effective settings and actual results/manifests are retained.
- One Julia/BLAS/OpenMP/MKL thread; effective Julia and loaded Python OpenBLAS counts checked. Fresh supervised child per CUDA case with 600-second wall limit and 9216 MiB sampled RSS budget. Child lifetime memory includes CPU references, doctor, construction, compilation, validation and serialization.

The sandbox hides GPU devices and its nvidia-smi reports blocked access.
Hardware-backed steps ran with approved host GPU access. Initialized CUDA
doctor passed actual device allocation and sparse backend checks before solves.
This source-checkout host execution is not a clean-wheel or container smoke.
The exact [environment script](validation/environment.sh) retains the writable
`/tmp/ablation-julia-depot` overlay, installed depot fallback and
`JULIA_CONDAPKG_BACKEND=Null`. Disposable caches require regeneration if removed.

## Fixes and preserved diagnostic history

The first actual GPU solve exposed a Julia world-age error from importing CUDA
inside the solver. The GPU entry point now completes lazy imports before
entering the solve in the latest Julia world. Source and packaged Julia copies
match. CPU usage still does not require CUDA. GPU tests no longer turn a solver
exception into a skip after initialized CUDA diagnostics succeed. The initial
hardware log retained six passes/one skip; corrected runs passed without skips.

A first full campaign passed N=4,8,12,16, then was intentionally interrupted
at N=20 after inspection found that diagonal observable accumulation copied
the whole device vector for each component. Both solver copies now transfer
once per observable and sum on the host in the original basis order. The
[interrupted campaign](p0-ablation-cuda-v2-2026-11-27.tar.gz) preserves all rows,
20 measured pairs, partial N=20 progress and the original executed sources;
its [partial audit](validation/interrupted-audit.json) passed. It is not pooled
with the final campaign and establishes no successful N=20 coverage.

[Preflight](cuda-preflight-2026-11-27.tar.gz) retains CPU-only-environment doctor
failure, offline dependency-resolution failure, initial Julia device-dictionary
serialization failure, successful initialized doctor and full solver exception
trace. Structured bridge device fields are normalized as mappings when saving
benchmark diagnostics. The [first pilot](ablation-cuda-pilot-01.tar.gz) retains
the failed first solve; the [second pilot](ablation-cuda-pilot-02.tar.gz) retains
numerical confirmation before final acceptance. Short one-repeat/one-warmup
pilot rows correctly remain incomplete. The legacy small chain and weighted-MWIS
[CUDA protocol](cuda-small-protocol-2026-11-27.tar.gz) passed both rows after the
first-call fix; it is supplementary small-case evidence with its own protocol,
not the five-size campaign or a full P1 GPU acceptance.

## Validation and commands

[Commands](validation/commands.json) and original logs retain:

- [Eight hardware/golden tests](validation/cuda-hardware-tests-final.log), no skips: global drive, local addressing, seeded reduced state, multiple diagonal observables and four Python/Julia golden checks.
- [Thirty-seven regression tests](validation/cuda-regression-tests.log), no skips: serialization, solver configuration, native Julia API, benchmark rows/failures and Julia package configuration.
- [Twenty final ablation tests](validation/cuda-ablation-final-tests.log), no skips: fixed-input compatibility, numerical/finite/failure/opt-in gates, mode selection, saved-output audit and bridge metadata.
- [Seven observable/invariant checks](validation/cuda-observable-regression-tests.log), no skips, after the transfer fix.
- [Earlier focused checks](validation/cuda-validation-cpu-tests.log), 35 passed, including artifact/suite/solver/documentation and CPU golden coverage.
- Documentation governance/links, exact preservation of four historical V1 chapters, original CPU-archive audit compatibility, source/package equality, extracted checksums and relocated audit.

From `sagittarius_py`, after sourcing the retained environment script and making
the GPU visible:

```bash
uv run python tests/test_performance/benchmark_ablation.py \
  --sizes 4 8 12 16 20 --modes reduced_sparse_gpu_cached --include-gpu \
  --repeat-count 5 --warmups 2 --cuda-parity-atol 1e-6 \
  --memory-limit-mb 9216 --timeout-seconds 600 \
  --output-dir benchmark-output/p0-ablation-cuda-v2-final-2026-11-27
.venv/bin/python ../scripts/audit_ablation_campaign.py \
  benchmark-output/p0-ablation-cuda-v2-final-2026-11-27
```

## Complete evidence and audit replay

Directly review [benchmark Markdown](ablation_bench_results.md),
[suite Markdown](ablation_bench_results_suite.md), [repeat rows](ablation_repeats.json),
[coverage](coverage.json) and [audit](audit.json). The original benchmark/suite
JSON and CSV companions are preserved byte-for-byte inside the
[complete campaign](campaign.tar.gz), under their original filenames. Repeated
large-basis readout/manifests make these files large; the archive stores their
losslessly compressed originals once rather than duplicating them uncompressed.
It contains 80 result/manifest pairs:
50 measured outputs and 30 first/warmup outputs. It retains ordered configs,
checkpoints, commands, CPU/CUDA results, per-case initialized doctors, memory
baselines/HWM and GPU snapshots, exact Python/Julia implementation snapshots,
Julia runtime projects/manifests, replay environment, Python lockfile and an
internal SHA256 inventory. [Archive checksums](SHA256SUMS) cover the retained
compressed originals, summaries, sources and validation logs.

The audit checks frozen hashes including Julia source, ordered cases, repeated
statistics/membership, all CPU/CUDA results and standalone manifests, effective
solver/grids/registers/basis sizes, thread counts and execution order. It
recomputes saved pair errors rather than trusting reported metrics. CSV parser
limits are bounded by the retained report size, allowing complete provenance
fields above the stdlib 128 KiB default. The audit distinguishes CUDA-only
coverage from unexecuted CPU-matvec coverage and remains compatible with the
original CPU archive. Original absolute paths are resolved by campaign prefix
after extraction; no GPU is needed to audit saved evidence:

```bash
mkdir -p /tmp/sagittarius-ablation-cuda-evidence
tar -xzf docs/benchmarks/evidence/p0-ablation-cuda-v2-2026-11-27/campaign.tar.gz \
  -C /tmp/sagittarius-ablation-cuda-evidence
(cd /tmp/sagittarius-ablation-cuda-evidence/campaign && sha256sum -c SHA256SUMS)
sagittarius_py/.venv/bin/python scripts/audit_ablation_campaign.py \
  /tmp/sagittarius-ablation-cuda-evidence/campaign
```

## Interpretation boundaries

CPU matvec and CUDA ODE remain different workloads. This archive derives no
matvec/solve or CPU/CUDA solve ratio. Timers describe end-to-end SDK calls,
including validation, pulse/operator construction, observable collection,
transfers and manifest creation. Sparse cache reuse occurs within a solve;
SDK construction repeats across calls. CUDA synchronization brackets the timer;
reference checks, serialization and reporting are outside it. First solve after
doctor is not process-cold startup. No slow valid repeat was removed.

This is a shared workstation; CPU validation overlapped early campaign work.
There is no host/GPU-load isolation or general speedup claim. Child RSS includes
both the CUDA path and its matched CPU references; it is not separate per-backend
allocation evidence. RSS polling every 50 ms is not a hard address-space cap.
GPU before/after free/total values are snapshots that include caches and other
users; GPU peak remains unavailable. Diagonal observables sum on the host and
are not claimed as device-native reductions.

These cases establish bounded local CPU/CUDA numerical implementation parity.
They do not establish independent physical-model/blockade-approximation
validation, general CUDA support, full P1 GPU geometry/application coverage,
container/wheel deployment, recurring RC validation or public performance/release
approval. CUDA remains experimental. Earlier failures and measurements remain
visible; only the final frozen campaign supplies its five-case acceptance.
