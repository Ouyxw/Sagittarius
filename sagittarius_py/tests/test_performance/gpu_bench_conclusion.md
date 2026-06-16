# GPU Benchmark Conclusion: RTX 5070 Ti (Full Path)

This historical note records a local performance evaluation of the Sagittarius CUDA path on an **NVIDIA GeForce RTX 5070 Ti** (16GB VRAM, CUDA 13.1) environment, conducted on April 30, 2026. Treat these values as historical context unless they are regenerated as `benchmark-artifact/v1` output with current `version-info/v1` metadata. See [../../../docs/PERFORMANCE_CLAIMS.md](../../../docs/PERFORMANCE_CLAIMS.md).

## 1. Environment Status
- **Hardware**: NVIDIA GeForce RTX 5070 Ti
- **Software Stack**: CUDA 13.1, Julia 1.11.9, Python 3.10.12
- **Optimizations**: Hamiltonian caching, Matrix-reuse, and Fixed GPU Observables (1-based index fix).

## 2. Benchmark Results (Integration + Observables)
The table below came from a 1D chain simulation (1.0 microsecond duration) with one observable tracked. Use the current `benchmark_gpu.py` artifact output for new claims.

| Atoms (\$N\$) | Basis Dimension | CPU Time (s) | GPU Time (s) | Speedup |
| :--- | :--- | :--- | :--- | :--- |
| 10 | 144 | 0.029 | 0.222 | 0.13x |
| 12 | 377 | 0.072 | 0.212 | 0.34x |
| 14 | 987 | 0.272 | 0.257 | **1.06x** |
| 16 | 2,584 | 0.666 | 0.262 | **2.54x** |
| 18 | 6,765 | 1.730 | 0.249 | **6.96x** |
| 20 | 17,711 | 5.203 | 0.370 | **14.07x** |

## 3. Key Findings

### 3.1 Observables Overhead
In this historical run, observable evaluation added GPU kernel-launch overhead and the measured CPU/CUDA crossover occurred at N=14. That crossover is not a general claim; cite a current artifact for the target hardware and configuration.

### 3.2 Result Parity & Stability
For this historical run, CPU and CUDA observable outputs matched within the recorded tolerance (mean difference below 1e-6), and the N=20 row completed without observed memory or signal-handling failures.

### 3.3 Optimized Scaling
For the N=20 row in this historical table, the recorded CUDA time was 0.370 seconds and the recorded CPU time was 5.203 seconds. Re-run `benchmark_gpu.py` and cite its JSON artifact before using this comparison externally.

## 4. Conclusion
The current public maturity contract marks CUDA as experimental. This note should be read as a historical local benchmark, not as a production-readiness or scaling guarantee.

---
*Updated by Gemini CLI - 2026-04-30*
