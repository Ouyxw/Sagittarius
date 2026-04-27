# MWIS on Unit-Disk Graphs via Rydberg Adiabatic Simulation 🏹

This project demonstrates the application of the Sagittarius SDK to solve the **Maximum Weighted Independent Set (MWIS)** problem on **Unit-Disk Graphs (UDG)** using Neutral Atom Analog Quantum Simulation.

## 📖 Background

An **Independent Set** is a set of vertices in a graph where no two vertices are adjacent. In a **Weighted** graph, the MWIS is the independent set with the largest total weight. Solving MWIS on general graphs is NP-hard, and it remains NP-hard even for Unit-Disk Graphs.

### Physics Mapping
1.  **Vertices $\to$ Atoms**: Each vertex $v_i$ with coordinates $(x_i, y_i)$ is mapped to an atom in the Sagittarius `Register`.
2.  **Edges $\to$ Blockade**: Edges in a UDG exist between vertices within distance $R$. By setting the Rydberg `blockade_radius` $\ge R$, the physical interaction prevents adjacent atoms from both being in the Rydberg state $|r\rangle$, enforcing the independent set constraint.
3.  **Weights $\to$ Detunings**: Node weights $w_i$ are mapped to local detunings $\Delta_i$. The Hamiltonian ground state minimizes $E = - \sum \Delta_i n_i$, which is equivalent to maximizing the total weight.

## 📊 Performance & Hardness Metrics

The benchmarking suite follows the methodology described in:
*"Hardness of the maximum-independent-set problem on unit-disk graphs and prospects for quantum speedups"* (Andrist et al., PRR 5, 043277, 2023).

We evaluate Sagittarius and classical baselines against several key metrics:

### 1. Hardness Metrics
These characterize the optimization difficulty of the instance:
- **Hardness Parameter ($\mathbb{H}$)**: The ratio $N_{|MIS|-1}/N_{|MIS|}$ (ratio of independent sets of size one-less-than-maximum to the number of maximum independent sets).
- **Graph Density (Average Degree)**: Higher density increases the number of constraints and the complexity of the blockade interaction.
- **Graph Degeneracy**: A measure of the graph's structural density; high degeneracy often correlates with more difficult optimization landscapes.

### 2. Performance Metrics
- **Time-to-Solution ($TTS_{99}$)**: Expected time required to find the exact MIS with 99% probability.
- **Success Probability ($P_{MIS}$)**: Total probability of all maximum independent set states in the final wavefunction.
- **Approximation Ratio**: Ratio of the weight of the found independent set to the true maximum weight ($W_{AQC} / W_{Exact}$).

### 3. Classical Baselines
- **Greedy**: A constructive heuristic picking nodes with maximum weight-to-degree ratio.
- **Simulated Annealing (SA)**: A Markov Chain Monte Carlo heuristic with an optimized annealing schedule.
- **CPLEX/ILP**: Integer Linear Programming formulation solved exactly using IBM CPLEX or CBC.
- **Exact Solver**: A branch-and-bound algorithm used to provide ground truth for all instances.

Results are saved to `mwis_improved_benchmark.csv` and visualized in `mwis_tts_comparison.png`.

**References**: 
- Andrist, R. S., et al. (2023). "Hardness of the maximum-independent-set problem on unit-disk graphs and prospects for quantum speedups." *Physical Review Research*, 5(4), 043277. [Link](https://doi.org/10.1103/PhysRevResearch.5.043277)
- Clark, B. N., Colbourn, C. J., & Johnson, D. S. (1990). "Unit disk graphs." *Discrete Mathematics*, 86(1-3), 165-177. [Link](https://doi.org/10.1016/0012-365X(90)90358-O)

## 📁 Project Structure

- `mwis_solver.py`: Core logic for translating UDGs to Sagittarius simulations.
- `example_mwis.py`: An illustrative workflow demonstration on a 7-node UDG.
- `solution_verify.py`: Classical MWIS solver for correctness verification and hardness calculation.
- `baselines.py`: Collection of classical heuristic and ILP solvers.
- `benchmark_mwis.py`: Comprehensive performance evaluation and scaling analysis.

## 🚀 Getting Started

```bash
cd sagittarius_py/projects/mwis_udg
# Run the example
uv run python example_mwis.py
# Run the benchmarks
uv run python benchmark_mwis.py
```
