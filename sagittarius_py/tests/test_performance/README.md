# Sagittarius Performance Benchmarking 🚀

This directory contains scripts for profiling and benchmarking the Sagittarius numerical engine.

## 📊 Benchmarks

### 1. `benchmark_scaling.py`
- **Goal**: Measure simulation time as a function of atom number ($N$).
- **Metric**: CPU time per simulation step.
- **Pruning Effect**: Visualizes the exponential advantage of Hilbert space pruning in the Rydberg blockade regime.

### 2. `benchmark_gpu.py`
- **Goal**: Compare CPU vs GPU integration speed.
- **Metric**: Speedup factor ($T_{CPU} / T_{GPU}$).
- **Optimal Range**: Identifies the "break-even" point where GPU overhead is overcome by parallel throughput (typically $N > 12$).

### 3. `benchmark_cluster.py`
- **Goal**: Measure parallel scaling efficiency for parameter sweeps.
- **Metric**: Execution time vs number of workers.
- **Sweep Logic**: Rabi frequency ($\Omega$) sweep over multiple processes.

## 🛠️ Execution
```bash
cd sagittarius_py/tests/test_performance
uv run python benchmark_scaling.py
uv run python benchmark_gpu.py
uv run python benchmark_cluster.py
```

## 📈 Output
Each script generates a `.csv` file with the results, suitable for analysis in Pandas or visualization in Matplotlib.
