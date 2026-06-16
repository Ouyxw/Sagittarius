# MWIS on Unit-Disk Graphs via Rydberg Adiabatic Simulation 🏹

This project demonstrates the application of the Sagittarius SDK to solve the **Maximum Weighted Independent Set (MWIS)** problem on **Unit-Disk Graphs (UDG)** using Neutral Atom Analog Quantum Simulation.

## 📖 Background

An **Independent Set** is a set of vertices in a graph where no two vertices are adjacent. In a **Weighted** graph, the MWIS is the independent set with the largest total weight. Solving MWIS on general graphs is NP-hard, and it remains NP-hard even for Unit-Disk Graphs.

### Physics Mapping
1.  **Vertices $\to$ Atoms**: Each vertex $v_i$ with coordinates $(x_i, y_i)$ is mapped to an atom in the Sagittarius `Register`.
2.  **Edges $\to$ Blockade**: Edges in a UDG exist between vertices within distance $R$. By setting the Rydberg `blockade_radius` $\ge R$, the physical interaction prevents adjacent atoms from both being in the Rydberg state $|r\rangle$, enforcing the independent set constraint.
3.  **Weights $\to$ Detunings**: Node weights $w_i$ are mapped to local detunings $\Delta_i$. The Hamiltonian ground state minimizes $E = - \sum \Delta_i n_i$, which is equivalent to maximizing the total weight.

## 🚀 Performance Optimizations

This project leverages the high-performance Sagittarius backend features:
- **Native Pulse Compilation**: Uses `Pulse.sin_squared` and `Pulse.ramp` to eliminate Python-Julia bridge overhead.
- **GPU Acceleration**: Offloads sparse matrix-vector multiplications to CUDA for large graphs ($N \ge 14$).
- **Hamiltonian Caching**: Reuses operator structures to minimize Host-to-Device synchronization.

For a detailed performance analysis on the RTX 5070 Ti, see the [Conclusion Report](CONCLUSION.md).

## 📊 Performance & Hardness Metrics

The benchmarking suite follows the methodology described in:
*"Hardness of the maximum-independent-set problem on unit-disk graphs and prospects for quantum speedups"* (Andrist et al., PRR 5, 043277, 2023).

We evaluate Sagittarius and classical baselines against several key metrics:

### 1. Hardness Metrics
These characterize the optimization difficulty of the instance:
- **Hardness Parameter ($\mathbb{H}$)**: The ratio $N_{|MIS|-1}/N_{|MIS|}$ (ratio of independent sets of size one-less-than-maximum to the number of maximum independent sets).
- **Graph Density (Average Degree)**: Higher density increases the number of constraints and the complexity of the blockade interaction.

### 2. Performance Metrics
- **Time-to-Solution ($TTS_{99}$)**: Expected time required to find the exact MIS with 99% probability.
- **Success Probability ($P_{MIS}$)**: Total probability of all maximum independent set states in the final wavefunction.
- **Approximation Ratio**: Ratio of the weight of the found independent set to the true maximum weight ($W_{AQC} / W_{Exact}$).

### 3. Classical Baselines
- **Greedy**: A constructive heuristic picking nodes with maximum weight-to-degree ratio.
- **Simulated Annealing (SA)**: A Markov Chain Monte Carlo heuristic with an optimized annealing schedule.
- **ILP (PULP/CBC)**: Integer Linear Programming formulation solved exactly.

## 📁 Project Structure

- `mwis_solver.py`: Core logic for translating UDGs to Sagittarius simulations.
- `example_mwis.py`: An illustrative workflow demonstration on a 7-node UDG.
- `solution_verify.py`: Classical MWIS solver for correctness verification and hardness calculation.
- `baselines.py`: Collection of classical heuristic and ILP solvers.
- `benchmark_mwis.py`: Comprehensive performance evaluation and scaling analysis.
- `batch_verify.py`: Seeded randomized MWIS batch verifier comparing AQC outputs against exact PuLP/CBC ILP solutions.
- `test_gpu_mwis.py`: Specialized parity test for hardware acceleration.
- `CONCLUSION.md`: Summary of technical gains and benchmark results.

## 🚀 Getting Started

```bash
cd sagittarius_py/projects/mwis_udg
# Run the example
uv run python example_mwis.py
# Run the benchmarks
PYTHON_JULIACALL_HANDLE_SIGNALS=yes uv run python benchmark_mwis.py
```

## Batch Verification

`batch_verify.py` provides a reproducible Phase 9 verification harness. It generates seeded weighted UDG instances, solves each instance exactly with PuLP/CBC ILP, runs the configured AQC solver, and reports validity, exact-match count, approximation ratios, and optional optimal-state probability when the solver exposes full basis probabilities.

```python
from batch_verify import verify_mwis_batch

report = verify_mwis_batch(n_instances=8, n_nodes=8, seed=2026)
print(report.to_dict())
```
