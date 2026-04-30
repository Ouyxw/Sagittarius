# Sagittarius 🏹

**Sagittarius** is a high-performance classical emulator for **Neutral Atom Analog Quantum Simulation**. It provides a beginner-friendly Python SDK backed by a lightning-fast Julia numerical engine.

By leveraging **Bit-Manipulation**, **Graph-based Hilbert Space Pruning**, and **Abstract Syntax Tree (AST) Pulse Compilation**, Sagittarius allows researchers to simulate Rydberg atom dynamics with unprecedented efficiency on standard classical hardware.

---

## ✨ Key Features

*   **🚀 High-Performance Julia Backend**: Core physics and solvers written in Julia for C-level performance.
*   **🧠 Intelligent Basis Pruning**: Automatically detects "Rydberg Blockade" regions using graph theory to truncate the Hilbert space, enabling simulation of 20+ atoms.
*   **⚡ Matrix-Free Evolution**: Employs bitwise operations to apply Hamiltonian terms on-the-fly, avoiding the memory overhead of $2^N \times 2^N$ matrices.
*   **🔥 GPU Acceleration**: Support for **CUDA**, **AMDGPU**, and **Metal** backends to offload heavy numerical integration.
*   **📡 Clustered Solvers**: Distributed simulation for high-throughput parameter sweeps using Julia's cluster management.
*   **🎭 Pulse Library & AST**: Define complex pulse sequences (**Gaussian, Blackman, Sinc, Ramps**) via a unified `Pulse` factory.
*   **📍 Local Addressing**: Support per-atom Rabi frequencies ($\Omega_i$) and detunings ($\Delta_i$) for simulating quantum gates.
*   **🫧 Open Quantum Systems**: High-performance **Lindblad** and **Monte Carlo Trajectory (MCWF)** solvers for decoherence.
*   **🧪 Object-Oriented SDK**: Reusable Python components for simulations, sequences, and configurations.
*   **💾 Easy Serialization**: Save and load results via JSON for long-running experiments.
*   **⚖️ Scientific Integrity**: Rigorous verification against physical invariants and analytic benchmarks.
*   **🐍 Seamless Python SDK**: Fully managed environment via `uv` and `juliapkg`.

---

## 📏 Physical Units

| Quantity | Unit | Description |
| :--- | :---: | :--- |
| **Distance** | $\mu m$ | Micrometers (spatial coordinates) |
| **Time** | $\mu s$ | Microseconds (duration, simulation time) |
| **Frequency** | $rad/\mu s$ | Angular frequency ($2\pi \times MHz$) |
| **Interaction ($C_6$)** | $rad/\mu s \cdot \mu m^6$ | Van der Waals coefficient |
| **Decay Rate ($\gamma$)** | $\mu s^{-1}$ | Transition rates ($T_1, T_2$) |

---

## 🛠️ Installation

```bash
git clone https://github.com/yourusername/Sagittarius.git
cd Sagittarius/sagittarius_py
uv pip install -e .
uv run python -m juliapkg resolve
```

---

## 📦 Containerized Development

Sagittarius supports **VS Code Dev Containers** for a seamless, GPU-optimized development experience. This ensures all Julia and Python dependencies are correctly configured with CUDA support out of the box.

For setup instructions, see the [Containerization Guide](docs/CONTAINERIZATION.md).

---

## 🚀 Performance & Scale

### 🔥 GPU Acceleration
Sagittarius can offload simulations to your GPU. Supported backends include `CUDA` (NVIDIA), `AMDGPU` (AMD), and `Metal` (Apple).

```python
from sagittarius import Simulation, SolverConfig

# Enable CUDA acceleration
config = SolverConfig(use_gpu=True, gpu_backend="CUDA")
sim = Simulation(reg, seq, config)
results = sim.run(psi0, 0.0, 1.0)
```

### 📡 Clustered Solvers
For large-scale parameter sweeps, use the `ParallelSimulation` object to distribute work across multiple CPU cores or cluster nodes.

```python
from sagittarius import ParallelSimulation

# Spin up 4 workers
psim = ParallelSimulation(n_workers=4)

# Define a Julia function on all workers and map it over parameters
results = psim.map("my_simulation_func", [0.1, 0.2, 0.3, 0.4])
```

---

## 🏗️ Architecture
Sagittarius follows a **Three-Layer Design**:
1.  **Frontend (Python)**: Declarative SDK for describing experiments.
2.  **Middle-end (AST/IR)**: Symbolic representation of pulses and blockade graphs.
3.  **Backend (Julia)**: High-performance numerical integration using `OrdinaryDiffEq.jl` and `Distributed.jl`.

---

## 🧪 Scientific Verification
Run the verification suite:
```bash
cd sagittarius_py
uv run python -m pytest tests/
```

---

## 📈 Performance Scaling

| Atoms ($N$) | Hilbert Space ($2^N$) | Pruned Space (Blockade) | Simulation Time |
| :--- | :--- | :--- | :--- |
| 2 | 4 | 3 | < 0.1s |
| 10 | 1024 | 144 | ~0.8s |
| 15 | 32,768 | ~1,500 | ~5s |
| 20 | 1,048,576 | ~15,000 | ~60s |

---

## 📄 License
MIT License. See `LICENSE` for details.
