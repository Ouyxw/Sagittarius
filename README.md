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
*   **🫧 Open Quantum Systems**: Support for decoherence ($T_1$ decay and $T_2$ dephasing) via high-performance **Lindblad Master Equation** and **Monte Carlo Trajectory (MCWF)** solvers.
*   **🧪 Object-Oriented SDK**: Encapsulate simulations, sequences, and configurations into reusable Python objects.
*   **💾 Easy Serialization**: Save and load simulation results via JSON for long-running experiments and data persistence.
*   **⚖️ Scientific Integrity**: Rigorous verification against physical invariants (norm/trace conservation) and analytic benchmarks (Landau-Zener, Rabi).
*   **📊 Data-Centric Results**: Integrated plotting and Pandas support for seamless scientific workflows.
*   **🐍 Seamless Python SDK**: Fully managed environment via `uv` and `juliapkg`. No Julia knowledge required for end-users.

---

## 📏 Physical Units

Sagittarius adheres to the standard conventions used in the **Ultra-Cold Atom** and **Rydberg Physics** communities. Unless otherwise specified, all physical quantities use the following base units:

| Quantity | Unit | Description |
| :--- | :---: | :--- |
| **Distance** | $\mu m$ | Micrometers (spatial coordinates of atoms) |
| **Time** | $\mu s$ | Microseconds (pulse duration, simulation time) |
| **Frequency** | $rad/\mu s$ | Angular frequency ($2\pi \times MHz$) for $\Omega$ and $\Delta$ |
| **Interaction ($C_6$)** | $rad/\mu s \cdot \mu m^6$ | Van der Waals coefficient |
| **Decay Rate ($\gamma$)** | $\mu s^{-1}$ | Transition rates for decoherence ($T_1, T_2$) |

> **Note**: To drive a system at 1 MHz, you should set $\Omega = 2\pi \approx 6.283$.

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

# 5. Save Results for later
results.save("experiment_01.json")
```

### 🫧 Simulating Decoherence ($T_1, T_2$ Noise)

Sagittarius makes it easy to move from ideal physics to experimental realism by adding noise parameters to the `SolverConfig`. For large systems, use the **Monte Carlo Trajectory** solver to save memory.

```python
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

reg = Register([Atom(0,0)], C6=0.0)
seq = PulseSequence(omega=2*np.pi * 1.0) # 1 MHz Rabi drive

# Add T1 decay (gamma) and T2 dephasing (gamma_phi)
# Set use_mc=True to use the Monte Carlo Wavefunction method
config = SolverConfig(
    gamma=0.1, 
    gamma_phi=0.05, 
    use_mc=True, 
    n_trajectories=500
) 

sim = Simulation(reg, seq, config)
results = sim.run(np.array([1, 0], dtype=complex), 0.0, 5.0, observables={"pop": 0})
results.plot()
```

---

## 🏗️ Architecture

Sagittarius follows a **Three-Layer Design** for maximum elegance and speed:

1.  **Frontend (Python)**: A declarative SDK where users describe *what* to simulate (Atoms, Pulses, Measurements).
2.  **Middle-end (AST/IR)**: A symbolic representation of the pulse sequence and blockade graph.
3.  **Backend (Julia)**: Uses `OrdinaryDiffEq.jl` to integrate the **Time-Dependent Schrödinger Equation (TDSE)**, the **Lindblad Master Equation**, or **Monte Carlo Trajectories** using high-order adaptive solvers (Tsit5/Vern9).

---

## 🧪 Scientific Verification

We maintain a suite of benchmarks to ensure the numerical engine remains physically accurate.

*   **Physical Invariants**: Automated tests for Norm conservation in Schrödinger/MCWF solvers and Trace preservation in Lindblad solvers.
*   **Landau-Zener Benchmarks**: Verification of transition probabilities in detuning sweeps against the analytic formula $P_{LZ} = 1 - e^{-\frac{\pi \Omega^2}{2|v|}}$.
*   **Rabi Oscillations**: Precise tracking of periodicity and amplitude for driven single-atom systems.

Run the verification suite:
```bash
cd sagittarius_py
uv run python -m pytest tests/test_invariants.py tests/test_serialization.py tests/test_benchmarks.py
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
