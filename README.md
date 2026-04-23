# Sagittarius 🏹

**Sagittarius** is a high-performance classical emulator for **Neutral Atom Analog Quantum Simulation**. It provides a beginner-friendly Python SDK backed by a lightning-fast Julia numerical engine.

By leveraging **Bit-Manipulation**, **Graph-based Hilbert Space Pruning**, and **Abstract Syntax Tree (AST) Pulse Compilation**, Sagittarius allows researchers to simulate Rydberg atom dynamics with unprecedented efficiency on standard classical hardware.

---

## ✨ Key Features

*   **🚀 High-Performance Julia Backend**: Core physics and solvers written in Julia for C-level performance with mathematical elegance.
*   **🧠 Intelligent Basis Pruning**: Automatically detects "Rydberg Blockade" regions using graph theory to truncate the Hilbert space, enabling simulation of 20+ atoms.
*   **⚡ Matrix-Free Evolution**: Employs bitwise operations to apply Hamiltonian terms on-the-fly, avoiding the memory overhead of $2^N \times 2^N$ matrices.
*   **🎭 Pulse AST DSL**: Define complex, time-dependent pulse sequences (Ramps, Piecewise, Constants) in Python that compile directly to optimized machine code.
*   **📊 Real-time Observables**: Track Rydberg populations and other physical quantities during simulation with zero-copy overhead.
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

## 🚀 Quick Start: Rydberg Blockade

The following example simulates two atoms in the **blockade regime**, where the strong interaction prevents both atoms from being excited simultaneously.

```python
import numpy as np
from sagittarius import Atom, Register, solve, Constant, Ramp, Piecewise

# 1. Define the Atomic Register
# Atoms at distance 1.0 with a strong C6 coefficient
reg = Register([
    Atom(0.0, 0.0), 
    Atom(1.0, 0.0)
], C6=100.0)

# 2. Design a Pulse Sequence (AST)
# Ramp Omega from 0 to 2π, then hold constant
omega_pulse = Piecewise([
    Ramp(0.0, 2*np.pi, duration=1.0),
    Constant(2*np.pi, duration=1.0)
])

# 3. Initial State: Both atoms in Ground State |gg>
# For 2 atoms, the basis is [|gg>, |rg>, |gr>, |rr>]
psi0 = np.array([1, 0, 0, 0], dtype=complex)

# 4. Run the Simulation
results = solve(
    reg, 
    psi0, 
    t_start=0.0, 
    t_end=2.0, 
    omega=omega_pulse, 
    delta=0.0,
    observables={"atom1": 0, "atom2": 1}
)

# 5. Analyze Results
print(f"Max Total Rydberg Population: {max(np.array(results['atom1']) + np.array(results['atom2'])):.4f}")
# Expected: Value near 1.0 due to Rydberg Blockade
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
