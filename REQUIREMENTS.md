# Sagittarius Development Roadmap & Requirements

This document outlines the path from a functional prototype to a mature, modern scientific SDK for Neutral Atom simulation.

## 🟢 Phase 1: Core API & Ergonomics (High Priority)

| Feature | Priority | Description | Impact |
| :--- | :---: | :--- | :--- |
| **Simulation Object** | 5 | Move from `solve()` function to a `Simulation` class. | Encapsulation, validation, and reusable configs. |
| **SimulationResult API** | 5 | Return a structured object instead of a dictionary. | Adds `.plot()`, `.to_pandas()`, and `.save()` methods. |
| **Validation Layer** | 4 | Pre-run checks for Hamiltonian consistency and memory limits. | Prevents cryptic Julia errors; improves user UX. |

## 🟡 Phase 2: Advanced Physics (Medium-High Priority)

| Feature | Priority | Description | Impact |
| :--- | :---: | :--- | :--- |
| **Local Addressing** | 5 | Support per-atom detuning (`delta`) and drive (`omega`). | Required for simulating quantum gates and algorithms. |
| **Lindblad Master Eq.** | 4 | Support for decoherence ($T_1, T_2$ noise) via jump operators. | Moves simulation from "ideal" to "experimental realism." |
| **Monte Carlo Traj.** | 3 | Alternative to Lindblad for large systems with dissipation. | Memory efficiency for open quantum systems. |

## 🔵 Phase 3: Scientific Integrity & Ops (Medium Priority)

| Feature | Priority | Description | Impact |
| :--- | :---: | :--- | :--- |
| **Physical Invariants** | 5 | Tests for Norm conservation and Symmetry preservation. | Ensures scientific correctness of the numerical engine. |
| **Serialization** | 4 | Support for HDF5 or JSON export of results. | Enables long-running experiments and reproducibility. |
| **Analytic Benchmarks** | 3 | Automated comparison against Landau-Zener and Rabi limits. | Continuous Integration (CI) for physics. |

## 🟣 Phase 4: Performance & Scale (Low-Medium Priority)

| Feature | Priority | Description | Impact |
| :--- | :---: | :--- | :--- |
| **GPU Acceleration** | 3 | Offload Julia heavy-lifting to CUDA/ROCm via `CUDA.jl`. | Enables 30+ atom simulations in pruned spaces. |
| **Clustered Solvers** | 2 | Distributed simulation for parameter sweeps. | Scales research throughput on HPC. |

---

## 🛠️ Immediate Action Items (Priority 5)

1.  **Refactor `api.py`**: Introduce `Simulation` and `SimulationResult`.
2.  **Update Julia Bridge**: Ensure the solver can handle arrays of pulses for local addressing.
3.  **Expand Test Suite**: Add `tests/test_invariants.py`.
