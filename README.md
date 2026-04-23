# Sagittarius 🏹

**Sagittarius** is a high-performance classical emulator for **Neutral Atom Analog Quantum Simulation**. It provides a beginner-friendly Python SDK backed by a lightning-fast Julia numerical engine.

By leveraging **Bit-Manipulation**, **Graph-based Hilbert Space Pruning**, and **Abstract Syntax Tree (AST) Pulse Compilation**, Sagittarius allows researchers to simulate Rydberg atom dynamics with unprecedented efficiency on standard classical hardware.

---

## ✨ Key Features

*   **🚀 High-Performance Julia Backend**: Core physics and solvers written in Julia for C-level performance with mathematical elegance.
*   **🧠 Intelligent Basis Pruning**: Automatically detects "Rydberg Blockade" regions using graph theory to truncate the Hilbert space, enabling simulation of 20+ atoms.
*   **⚡ Matrix-Free Evolution**: Employs bitwise operations to apply Hamiltonian terms on-the-fly, avoiding the memory overhead of $2^N \times 2^N$ matrices.
*   **🎭 Pulse Library & AST**: Define complex, time-dependent pulse sequences (**Gaussian, Blackman, Sinc, Ramps**) via a unified `Pulse` factory.
*   **📍 Local Addressing**: Support per-atom Rabi frequencies ($\Omega_i$) and detunings ($\Delta_i$) for simulating quantum gates and spatial landscapes.
*   **📊 Real-time Observables**: Track Rydberg populations and other physical quantities during simulation with zero-copy overhead.
*   **🧪 Object-Oriented SDK**: Encapsulate simulations, sequences, and configurations into reusable Python objects.
*   **📊 Data-Centric Results**: Integrated plotting and Pandas support for seamless scientific workflows.
*   **🐍 Seamless Python SDK**: Fully managed environment via `uv` and `juliapkg`. No Julia knowledge required for end-users.

---

## 🛠️ Installation

Sagittarius uses [uv](https://github.com/astral-sh/uv) to manage its Python environment and dependencies.

```bash
# Clone the repository
git clone https://github.com/yourusername/Sagittarius.git
cd Sagittarius/sagittarius_py

# Install dependencies and resolve Julia environment
uv pip install -e .
uv run python -m juliapkg resolve
```

---

## 🚀 Quick Start: Local Addressing & Pulse Library

The following example demonstrates how to use the **Pulse Library** to drive a specific atom with a **Gaussian pulse** while detuning its neighbor.

```python
import numpy as np
from sagittarius import Atom, Register, Simulation, PulseSequence, Pulse

# 1. Define the Atomic Register
reg = Register([Atom(0,0), Atom(10,0)], C6=100.0)

# 2. Design a Local Pulse Sequence
# Drive Atom 0 with a Gaussian pulse, keep Atom 1 detuned
seq = PulseSequence(
    omega={0: Pulse.gaussian(amplitude=2*np.pi, sigma=0.1, duration=1.0)},
    delta={1: 100.0} 
)

# 3. Initialize and Run the Simulation
sim = Simulation(reg, seq)
psi0 = np.array([1, 0, 0, 0], dtype=complex) # |gg>

results = sim.run(
    psi0, 
    t_start=0.0, 
    t_end=1.0, 
    observables={"atom0": 0, "atom1": 1}
)

# 4. Analyze Results
results.plot()
```

---

## 🏗️ Architecture

Sagittarius follows a **Three-Layer Design** for maximum elegance and speed:

1.  **Frontend (Python)**: A declarative SDK where users describe *what* to simulate (Atoms, Pulses, Measurements).
2.  **Middle-end (AST/IR)**: A symbolic representation of the pulse sequence and blockade graph.
3.  **Backend (Julia)**: Uses `OrdinaryDiffEq.jl` to integrate the Time-Dependent Schrödinger Equation (TDSE) using high-order adaptive solvers (Tsit5/Vern9).

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
