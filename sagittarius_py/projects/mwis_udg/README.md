# MWIS on Unit-Disk Graphs via Rydberg Adiabatic Simulation 🏹

This project demonstrates the application of the Sagittarius SDK to solve the **Maximum Weighted Independent Set (MWIS)** problem on **Unit-Disk Graphs (UDG)** using Neutral Atom Analog Quantum Simulation.

## 📖 Background

An **Independent Set** is a set of vertices in a graph where no two vertices are adjacent. In a **Weighted** graph, the MWIS is the independent set with the largest total weight. Solving MWIS on general graphs is NP-hard, and it remains NP-hard even for Unit-Disk Graphs.

### Physics Mapping
1.  **Vertices $\to$ Atoms**: Each vertex $v_i$ with coordinates $(x_i, y_i)$ is mapped to an atom in the Sagittarius `Register`.
2.  **Edges $\to$ Blockade**: Edges in a UDG exist between vertices within distance $R$. By setting the Rydberg `blockade_radius` $\ge R$, the physical interaction prevents adjacent atoms from both being in the Rydberg state $|r\rangle$, enforcing the independent set constraint.
3.  **Weights $\to$ Detunings**: Node weights $w_i$ are mapped to local detunings $\Delta_i$. The Hamiltonian ground state minimizes $E = - \sum \Delta_i n_i$, which is equivalent to maximizing the total weight.

## ⚖️ Problem Hardness

We evaluate Sagittarius against two primary metrics of graph hardness:

1.  **Graph Density (Average Degree)**: Higher density increases the number of constraints and the complexity of the blockade interaction.
2.  **Graph Degeneracy**: A measure of how "spread out" or "clustered" the graph is. High degeneracy often correlates with more difficult optimization landscapes.

**Reference**: 
- Clark, B. N., Colbourn, C. J., & Johnson, D. S. (1990). "Unit disk graphs." *Discrete Mathematics*, 86(1-3), 165-177. [Link](https://doi.org/10.1016/0012-365X(90)90358-O)

## 📁 Project Structure

- `mwis_solver.py`: Core logic for translating UDGs to Sagittarius simulations.
- `example_mwis.py`: An illustrative workflow demonstration on a 7-node UDG.
- `solution_verify.py`: Classical MWIS solver for correctness verification and approximation ratio calculation.
- `benchmark_mwis.py`: Comprehensive performance evaluation and scaling analysis.

## 🚀 Getting Started

```bash
cd sagittarius_py/projects/mwis_udg
# Run the example
uv run python example_mwis.py
# Run the benchmarks
uv run python benchmark_mwis.py
```

## 📊 Performance Metrics

- **Approximation Ratio**: $W_{AQC} / W_{Exact}$.
- **Time-Costing**: Wall-clock time for the simulation as $N$ increases.
