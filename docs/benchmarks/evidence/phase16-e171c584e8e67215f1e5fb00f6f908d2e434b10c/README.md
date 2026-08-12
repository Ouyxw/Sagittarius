# Phase 16 Closure Evidence

- Source commit: `e171c584e8e67215f1e5fb00f6f908d2e434b10c` (`e171c58`); the artifacts preserve the recorded dirty-state flag.
- Executed: 2026-08-12 UTC in the documented WSL2 devcontainer.
- Runtime: Python 3.10.12, Julia 1.11.9, Sagittarius Python/Julia 1.0.8.
- CUDA host: NVIDIA GeForce RTX 5070 Ti, driver 591.86, CUDA runtime 12.8, CUDA.jl 6.2.0; CUDA remains experimental.
- Disclosure: `DISC-0002` is internal-only and all rows are `local_only`. This archive does not authorize a public performance or hardware claim.
- [Markdown summary report](report.md)

## Retained executions

All commands ran from `sagittarius_py` with `--output-dir` set to this directory.

| Coverage | Command | Primary artifacts |
| :--- | :--- | :--- |
| CPU smoke | `uv run python tests/test_performance/benchmark_physics_smoke.py` | `physics_smoke.json`, `physics_smoke_suite.json`, result/manifest pairs. |
| Physics correctness | `uv run python tests/test_performance/benchmark_physics_correctness.py` | `physics_correctness.json`, `physics_correctness_suite.json`, analytic/dense-reference reports. |
| Dynamics and open system | `uv run python tests/test_performance/benchmark_phase16_validation.py` | `cold_atom_dynamics*.json`, `open_system_dynamics*.json`. |
| MWIS/UDG | `uv run python tests/test_performance/benchmark_mwis_aqc.py` | `mwis_aqc_{smoke,correctness,scaling}*.json`, exact-reference reports. |
| Solver/path | `uv run python tests/test_performance/benchmark_solver_performance.py` | `solver_performance*.json`, result/manifest pairs. |
| Local sweep | `uv run python tests/test_performance/benchmark_sweep_cluster.py` | `sweep_cluster*.json`, `parallel-sweep-workers-*.sweep.json`, result/manifest pairs. |
| CUDA parity | `SAGITTARIUS_ENABLE_GPU_TESTS=1 uv run python tests/test_performance/benchmark_cuda_mwis_protocol.py` | `cuda_parity*.json`, `mwis_gpu_parity*.json`, CPU/CUDA reference reports. |
| Stress ablation | `uv run python tests/test_performance/benchmark_ablation.py --atom-count 12 --repeats 50 --include-gpu` | `ablation_bench_results.json` plus CSV/Markdown. |

## Acceptance evidence

1. Taxonomy, tiers, artifact requirements, and evidence levels are documented in the parent benchmark protocol set.
2. Every Phase 16 family has a `benchmark-artifact/v1` and, where implemented, a `benchmark-suite-artifact/v1` aggregate linked to manifests/results.
3. `physics_correctness.json` and its suite retain analytic Rabi/blockade/Landau-Zener and projected dense-reference checks.
4. `mwis_aqc_*.json` retain seeded graph metadata, PuLP/CBC exact baselines, feasibility/objective metrics, and per-row failures.
5. `cuda_parity.json` and `mwis_gpu_parity.json` retain initialized doctor metadata, device/runtime fields, cold/warm timing, memory snapshots, and passing CPU/CUDA parity.
6. Every runner retains failed, skipped, or incomplete rows instead of filtering them; the artifact contracts define their diagnostic payload.
7. No public claim is made from this archive. Any future public statement must cite these artifact paths and create/update `DISC-0002` with the required governance review.
8. Benchmark commands remain opt-in for ordinary PR CI; the CUDA runner additionally requires `SAGITTARIUS_ENABLE_GPU_TESTS=1`.

## Verification boundary

This archive closes the documented initial Phase 16 suite. It is reviewable project evidence, not release-grade performance evidence. Hardware-specific scaling limits, multi-node deployment, and broader scientific validation remain future scoped work.
