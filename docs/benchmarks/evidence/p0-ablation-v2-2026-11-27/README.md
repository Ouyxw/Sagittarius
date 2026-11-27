# P0 ablation v2 local evidence — 2026-11-27

Status: Retained local software/numerical verification evidence; automated audit passed.

The [suite](ablation_bench_results_suite.json) accounts for all 25 declared
size/path rows. All 16 targeted CPU paths passed: four Python/NumPy/SciPy
implementations at N=4,8,12 and both reduced implementations at N=16,20.
Each path retained two actual-batch warmups and five eligible independent
measured batches of 50 fixed-input H*psi operations (80 saved measured outputs).
Four full-space rows above the dimension guard and five optional CUDA rows
are skipped with explicit reasons. There are no failed/incomplete CPU rows.
The [audit](audit.json) recomputes saved numerical errors and statistics;
maximum absolute error is 4.577566798522237e-16 and maximum relative error is
2.4263650282272366e-16 (full gate 1e-12, reduced absolute gate 1e-10).

| N | Full dimension | Reduced dimension | Executed CPU paths |
| --- | ---: | ---: | --- |
| 4 | 16 | 8 | All four |
| 8 | 256 | 55 | All four |
| 12 | 4096 | 377 | All four |
| 16 | 65536 | 2584 | Both reduced; full excluded by guard |
| 20 | 1048576 | 17711 | Both reduced; full excluded by guard |

## Source and environment

- Branch `feature/benchmarking`, baseline `d4f4cea0c255d984246f12014d3b906bdc6e722f`, dirty tree; no commit or publication.
- [Frozen campaign](campaign.json) config SHA256: `ac2fc7c2fc4df7d35088c6ee273a435e6979f69b96efbd414b8a6b6fc401a44a`.
- Host: Intel Core i7-14700KF, 16637784064 bytes physical memory, Linux/WSL shared workstation.
- Python 3.11.15, Julia 1.13.4, Sagittarius Python/Julia 1.0.8, NumPy 2.4.6, SciPy 1.17.1. Exact package/build/container/doctor data accompany checkpoints.
- Requested Julia/OpenBLAS/OpenMP/MKL threads: one. Effective Julia/Julia BLAS and loaded Python OpenBLAS counts are retained and checked as one.
- Chain spacing 2.0 um, C6=100 rad*um^6/us, Rb=3.0 um, omega=2*pi rad/us, delta=0, normalized complex128 input from NumPy seed 1234. Bit i denotes atom i (LSB).
- Per-path limits: 600 seconds and 9216 MiB sampled RSS. Construction preflight includes the existing dense intermediates used to build sparse CSR matrices. The direct helper's default budget is 8192 MiB; this campaign explicitly freezes 9216 MiB so reduced sparse N=20 is admitted.

The first [pilot](ablation-v2-pilot-01.tar.gz) retained eight initialized-doctor
failures because the sandbox disallowed Julia writes under the home depot.
A writable `/tmp/ablation-julia-depot` overlay and `JULIA_CONDAPKG_BACKEND=Null`
allowed reuse of installed dependencies without network resolution. The exact
[environment script](validation/environment.sh) is retained; the `/tmp` cache
is disposable and requires regeneration after cleanup. The second
[pilot](ablation-v2-pilot-02.tar.gz) passed all eight N=4,8 CPU numerical gates
and its [partial audit](validation/pilot-audit.json); its one-repeat/one-warmup
rows remain incomplete diagnostic evidence. Thresholds were confirmed before
the full campaign freeze. No pilot or failed row was filtered from its archive.

## Commands and validation

From `sagittarius_py`, after sourcing the retained environment script:

```bash
uv run python tests/test_performance/benchmark_ablation.py \
  --sizes 4 8 12 16 20 --repeats 50 --repeat-count 5 --warmups 2 \
  --memory-limit-mb 9216 --timeout-seconds 600 \
  --output-dir benchmark-output/p0-ablation-v2-2026-11-27
.venv/bin/python ../scripts/audit_ablation_campaign.py \
  benchmark-output/p0-ablation-v2-2026-11-27
```

[Validation commands](validation/commands.json), [first test log](validation/ablation-validation-01.log)
and [second test log](validation/ablation-validation-02.log) retain 86 passed
tests with no skips. These include fixed-input/gate/finite/failure/opt-in checks,
N=9 independent analytic-vs-dense reference checks, saved-output audit tampering,
benchmark rows/artifacts/suites, real CPU campaign smoke, solver performance,
serialization, solver configuration, shared resource-supervisor tests and all
four Python/Julia golden tests. [Documentation checks](validation/documentation.log)
and preservation of all four historical V1 chapters passed.

The automated audit verifies ordered frozen configuration, source hashes,
scenario/repeat contracts, independent seeded inputs/reference arrays,
saved H*psi outputs, numerical errors, operation counts, statistic membership,
initialized diagnostics, effective threads, runtime-project hashes and companion
JSON/CSV/Markdown rows. It also passed after extraction/relocation. These checks
are software/numerical verification; they are not independent governance review.

## Original evidence and replay

Directly review [benchmark JSON](ablation_bench_results.json),
[CSV](ablation_bench_results.csv), [Markdown](ablation_bench_results.md),
[suite JSON](ablation_bench_results_suite.json), [suite CSV](ablation_bench_results_suite.csv),
[suite Markdown](ablation_bench_results_suite.md), [repeats](ablation_repeats.json),
[coverage](coverage.json) and [audit](audit.json).

The [complete campaign](campaign.tar.gz) retains original child commands,
configs/checkpoints, baseline/peak memory, doctor diagnostics, Julia runtime
projects/manifests, inputs/reference NPZs, all 80 measured output NPYs,
source snapshots/hashes, Python lockfile, entry point/tests/audit, replay
environment and an internal SHA256 inventory. Parent aggregate memory belongs
to the supervisor; per-path memory belongs to the corresponding child.
Absolute original paths are retained; the audit remaps the campaign prefix.

```bash
mkdir -p /tmp/sagittarius-ablation-evidence
tar -xzf docs/benchmarks/evidence/p0-ablation-v2-2026-11-27/campaign.tar.gz \
  -C /tmp/sagittarius-ablation-evidence
(cd /tmp/sagittarius-ablation-evidence/campaign && sha256sum -c SHA256SUMS)
sagittarius_py/.venv/bin/python scripts/audit_ablation_campaign.py \
  /tmp/sagittarius-ablation-evidence/campaign
```

[Archive checksums](SHA256SUMS) cover summaries, compressed originals, pilots,
source/audit/test snapshots and validation logs. Computation replay requires
the baseline checkout plus the retained implementation files, lockfile,
Julia projects and environment, using a new empty output directory.

## Interpretation boundaries

CPU timings characterize Python/NumPy/SciPy implementations. Each operation
uses the same read-only normalized input; no H^k*psi iteration is timed.
`fixed-normalized-input-matvec/v2` cannot be pooled with historical workloads.
Construction and independent reference work precede first-operation/warmup
measurement, and may warm numerical libraries. Batch timers exclude reference
checks, serialization, checkpoints and report generation. The first measured
batch's flat fields are separate from independent-repeat statistics; no slow
valid repeat was removed.

N<=8 uses independent full/projected Kronecker dense references; larger N uses
independently enumerated analytic transition action, with N=9 reference tests.
There is no independent large dense or physical blockade-approximation
validation. Full and reduced rows have different Hilbert spaces; their times
require dimension/approximation context. Sparse construction still materializes
dense intermediates; successful matvec execution is not sparse-construction
scalability evidence.

The workstation was shared; automated validation overlapped the early sizes.
Timings have no host-load isolation and establish no general performance or
speedup claim. Child RSS/HWM includes doctor, construction, references and
serialization. Polling every 50 ms is not a hard address-space cap and does
not capture all transient/descendant allocations. GPU peak memory is not
measured. Optional CUDA rows are skips, with no CUDA execution or parity claim;
GPU-suite matched parity remains separate. Recurring RC P0 reruns, public
performance/disclosure review and release approval remain open.
