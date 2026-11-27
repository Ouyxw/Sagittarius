# P0 scaling v2 local evidence — 2026-11-26

Status: Retained local numerical/software verification evidence; automated audit passed.

The [suite](scaling_results_suite.json) accounts for all 42 declared scenarios:
chain and rectangular geometry, Rb/a=1.1,1.5,2.1 and N=2,4,6,8,12,16,20.
All 42 passed, with two warmups and five eligible independent measured repeats
each (210 measured result/manifest pairs). No scenario was excluded or failed.
The 24 small-system scenarios passed independent projected-dense Hamiltonian
and trajectory checks; the 18 larger scenarios passed tighter-tolerance
sensitivity checks. [Audit report](audit.json) records maximum observable error
1.5280641e-09 (gate 1e-8), maximum Hamiltonian error
4.3368087e-19 (gate 1e-12), companion checks and missing coverage.

| N=20 scenario | Actual D | Full dimension |
| --- | ---: | ---: |
| chain-r1.1-n20 | 17711 | 1048576 |
| chain-r1.5-n20 | 17711 | 1048576 |
| chain-r2.1-n20 | 2745 | 1048576 |
| rectangle-r1.1-n20 | 6743 | 1048576 |
| rectangle-r1.5-n20 | 1213 | 1048576 |
| rectangle-r2.1-n20 | 437 | 1048576 |

## Source and environment

- Baseline: `efef3754237b28b61e0829edf164088597ffc13a`, branch `feature/benchmarking`, dirty working tree.
- Exact executed benchmark/helper sources and hashes are retained in [campaign metadata](campaign.json), [source snapshots](source/scaling_benchmark.py) and the complete compressed campaign.
- Config SHA256: `5721ab4216050fec8ee74ae2cdc96577802d6320c9e93da946425be4c6424d80`; frozen at `2026-11-26T10:36:47.969419+00:00`.
- Host: Intel Core i7-14700KF; 16637784064 bytes physical memory; Linux shared workstation.
- Runtime: Python 3.11.15, Julia 1.13.4, Sagittarius Python/Julia 1.0.8; NumPy 2.4.6, SciPy 1.17.1. Exact Python versions are in doctor payloads; actual JuliaCall Project/Manifest files accompany every scenario checkpoint.
- Effective Julia and BLAS threads: one. CPU/BLAS/OpenMP/MKL requested environment is retained.
- Per-scenario limits: 600 seconds and 4096 MiB sampled RSS, with construction/reference preflight. All initial states are deterministic all-ground; no stochastic seed is applicable.

## Commands and acceptance

The full campaign ran from `sagittarius_py`:

```bash
uv run python tests/test_performance/benchmark_scaling.py \
  --output-dir benchmark-output/p0-scaling-v2-2026-11-26 \
  --timeout-seconds 600 --memory-limit-mb 4096
```

[Validation commands](validation/commands.json) and [final test log](validation/scaling-complete-validation.log)
retain the focused benchmark, serialization, solver, real-backend reduced/full
smoke, Python/Julia golden and documentation checks. The final set passed 71 tests.
[Documentation validation](validation/documentation.log) passed.
Two development pilots confirmed the numerical target before campaign freeze:
[small pilot](scaling-pilot-01.tar.gz) and [N=8/N=20 boundary pilot](scaling-pilot-02.tar.gz).
Pilot implementation/metadata were refined during development; their starting
source snapshots and original outputs are retained as diagnostic probes,
not frozen performance evidence. The complete campaign guarded its frozen
implementation hashes in every child.

The automated evidence audit checked the frozen config/source hashes, ordered
matrix, per-row/repeat contracts, eligible statistic membership, companion
rows, 210 saved result/manifest pairs, effective solver/grids/registers,
actual single-thread settings and recomputed saved-trajectory errors.
There is no independent governance review or release/public-use approval.

## Complete original artifacts and replay audit

[scaling_results.json](scaling_results.json), [CSV](scaling_results.csv),
[Markdown](scaling_results.md), [suite JSON](scaling_results_suite.json),
[suite CSV](scaling_results_suite.csv), [suite Markdown](scaling_results_suite.md),
[repeat rows](scaling_repeats.json) and [coverage](coverage.json) are directly reviewable.
[Complete campaign](campaign.tar.gz) retains all original scenario configs,
commands, checkpoints, doctor/runtime payloads, first solves, warmup records,
references, measured results/manifests, source snapshots and an internal
SHA256 inventory. Original absolute output paths are preserved; the audit
resolves their campaign prefix after extraction. From the repository root:

```bash
mkdir -p /tmp/sagittarius-scaling-evidence
 tar -xzf docs/benchmarks/evidence/p0-scaling-v2-2026-11-26/campaign.tar.gz \
  -C /tmp/sagittarius-scaling-evidence
(cd /tmp/sagittarius-scaling-evidence/campaign && sha256sum -c SHA256SUMS)
sagittarius_py/.venv/bin/python scripts/audit_scaling_campaign.py \
  /tmp/sagittarius-scaling-evidence/campaign
```

[Archive checksums](SHA256SUMS) cover the compressed original campaign, pilots,
summaries, source/audit/test snapshots and validation logs. To rerun computation,
use the baseline checkout plus the retained benchmark/helper/entry-point source
snapshots, restore dependencies from the retained manifests and Python lockfile,
and replay the command with a new output directory.

## Interpretation boundaries

Times describe end-to-end `Simulation.run` calls, including validation,
operator construction, observable collection and manifests. Checks and artifact
writes are outside that timer. First solve, warmups, basis construction and
initialized doctor have separate records; first solve after doctor is not
process-cold initialization. No valid slow repeat was removed.

The workstation was shared; validation overlapped the initial chain group.
These timings are local diagnostics without host-load isolation or a speedup
claim. Per-scenario memory is process-lifetime RSS/HWM including initialization,
references and serialization; supervisor RSS enforcement samples every 50 ms
and does not cap dependency-precompile descendants or short transients.
The top-level benchmark envelope memory belongs to the supervisor.

Projected dense gates verify the reduced implementation. N>8 evidence is
same-method tolerance sensitivity, with the independent small-system evidence
retained; it is not an independent large-system solution or a physical
full-space/blockade approximation validation. N=20 success applies only to
these geometries, radii, basis dimensions and solver/observable settings.
The initial Phase 16 archive is unchanged. Ablation, other suites, recurring RC
P0 reruns, CUDA, public disclosure and release gates remain separate.
