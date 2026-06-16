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
- **Metric**: Time per repeated matvec for full dense, full sparse, reduced matrix-free, and reduced sparse CPU paths; optional CUDA cached sparse solve timing.
- **GPU Gate**: Pass `--include-gpu` only on a machine where CUDA diagnostics pass.

## Execution
```bash
cd sagittarius_py/tests/test_performance
uv run python benchmark_scaling.py
uv run python benchmark_gpu.py
uv run python benchmark_cluster.py
uv run python benchmark_ablation.py
```

## Output
Each benchmark writes a `benchmark-artifact/v1` JSON envelope plus companion CSV and Markdown files. The JSON captures parameters, timings, process memory usage, `version_info()` metadata, backend diagnostics, and linked run manifests when a benchmark run produces `SimulationResult` objects. Use [../../../docs/governance/performance-claims.md](../../../docs/governance/performance-claims.md) before turning these rows into public performance statements.
