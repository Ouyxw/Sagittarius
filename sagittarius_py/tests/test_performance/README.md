# Sagittarius Performance Benchmarking

This directory contains scripts for profiling and benchmarking the Sagittarius numerical engine.

## Benchmarks

### 1. `benchmark_scaling.py`
- **Goal**: Measure simulation time as a function of atom number ($N$).
- **Metric**: CPU time per simulation step.
- **Pruning Effect**: Records basis-size reduction for the configured blockade radius; interpret scaling only with the emitted artifact metadata.

### 2. `benchmark_gpu.py`
- **Goal**: Compare CPU vs GPU integration speed.
- **Metric**: Speedup factor ($T_{CPU} / T_{GPU}$).
- **Range**: Records CPU and CUDA timing rows for the selected atom counts. Any crossover point is hardware- and configuration-specific and must be cited from the generated artifact.

### 3. `benchmark_cluster.py`
- **Goal**: Measure parallel scaling efficiency for parameter sweeps.
- **Metric**: Execution time vs number of workers.
- **Sweep Logic**: Rabi frequency ($\Omega$) sweep over multiple processes.

### 4. `benchmark_ablation.py`
- **Goal**: Compare Hamiltonian execution path representations.
- **Metric**: Fixed normalized H*psi batch and per-operation time for four Python CPU paths, with separate construction and independent-repeat statistics. CLI defaults to N=4,8,12,16,20; full paths above dimension 4096 are excluded. `--repeats` remains operations per batch; `--repeat-count` is independent batches. Optional CUDA cached ODE solves are a separate workload with matched CPU ODE trajectory gates, two warmups and independent paired repeats. Select only that path with `--modes reduced_sparse_gpu_cached --include-gpu`.
- **GPU Gate**: Requires `--include-gpu`, `SAGITTARIUS_ENABLE_GPU_TESTS=1` and initialized CUDA diagnostics. Full-grid matched parity and sufficient paired measurements are required; no runtime ratio is produced by this runner.

## Execution
```bash
cd sagittarius_py/tests/test_performance
uv run python benchmark_scaling.py
uv run python benchmark_gpu.py
uv run python benchmark_cluster.py
uv run python benchmark_ablation.py --output-dir benchmark-output/ablation-v2
```

## Output
Each benchmark writes a `benchmark-artifact/v1` JSON envelope plus companion CSV and Markdown files. The JSON captures parameters, timings, process memory usage, `version_info()` metadata, backend diagnostics, and linked run manifests when a benchmark run produces `SimulationResult` objects. Use [../../../docs/governance/performance-claims.md](../../../docs/governance/performance-claims.md) before turning these rows into public performance statements.
