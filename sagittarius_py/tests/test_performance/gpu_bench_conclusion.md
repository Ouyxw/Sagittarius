# GPU Benchmark Conclusion: RTX 5070 Ti (Full Path)

This report summarizes the performance evaluation of the Sagittarius GPU-accelerated solver on an **NVIDIA GeForce RTX 5070 Ti** (16GB VRAM, CUDA 13.1) environment, conducted on April 30, 2026. This test covers the **full vectorized path**, including ODE integration and Rydberg population observables.

## 1. Environment Status
- **Hardware**: NVIDIA GeForce RTX 5070 Ti
- **Software Stack**: CUDA 13.1, Julia 1.11.9, Python 3.10.12
- **Optimizations**: Hamiltonian caching, Matrix-reuse, and Fixed GPU Observables (1-based index fix).

## 2. Benchmark Results (Integration + Observables)
The benchmark compares CPU vs GPU performance for a 1D chain simulation (1.0μs duration) with one observable tracked.

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
Adding observables introduces a slight constant overhead for GPU kernel launches (~50ms) but remains highly efficient. The **crossover point remains at N=14**, where the GPU's throughput justifies the overhead.

### 3.2 Result Parity & Stability
After fixing the 1-based indexing bug in `RydbergPopulation`, the GPU results now perfectly match CPU outputs (Mean Diff < 1e-6). The system survived a high-stress $N=20$ run without any memory or signal-handling issues.

### 3.3 Optimized Scaling
At $N=20$, the total simulation time (including all ODE steps and population mapping) is **under 0.4 seconds** on the RTX 5070 Ti, compared to over 5 seconds on a multi-threaded CPU. This represents a robust **14x speedup** for complete physical workflows.

## 4. Conclusion
The Sagittarius GPU backend is **Production-Ready** for Rydberg simulations on the RTX 5000 series. The combination of Hamiltonian caching and vectorized observable reduction ensures that performance gains scale linearly with problem complexity beyond the crossover threshold.

---
*Updated by Gemini CLI - 2026-04-30*
