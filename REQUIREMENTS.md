# Sagittarius Development Roadmap & Requirements

This document outlines the development lifecycle of Sagittarius, from a functional prototype to a high-performance scientific SDK.

## ✅ Phase 1: Core API & Ergonomics (Completed)
| Feature | Status | Description |
| :--- | :---: | :--- |
| **Simulation Object** | Done | OO-API with `Simulation` and `SimulationResult`. |
| **SimulationResult API** | Done | Methods for `.plot()`, `.to_pandas()`, and `.save()`. |
| **Validation Layer** | Done | Hilbert space size checks and Hamiltonian consistency. |

## ✅ Phase 2: Advanced Physics (Completed)
| Feature | Status | Description |
| :--- | :---: | :--- |
| **Local Addressing** | Done | Per-atom control of $\Omega$ and $\Delta$. |
| **Lindblad Master Eq.** | Done | Density matrix evolution with $T_1$ and $T_2$ noise. |
| **Monte Carlo Traj.** | Done | Memory-efficient Quantum Jump (MCWF) solver. |

## ✅ Phase 3: Scientific Integrity & Ops (Completed)
| Feature | Status | Description |
| :--- | :---: | :--- |
| **Physical Invariants** | Done | Automated checks for norm/trace conservation. |
| **Serialization** | Done | JSON support for simulation data persistence. |
| **Analytic Benchmarks** | Done | Verification against Rabi and Landau-Zener limits. |

## ✅ Phase 4: Performance & Scale (Completed)
| Feature | Status | Description |
| :--- | :---: | :--- |
| **GPU Acceleration** | Done | Support for CUDA, AMDGPU, and Metal backends. |
| **Clustered Solvers** | Done | Distributed parameter sweeps via `ParallelSimulation`. |

## 🚧 Phase 5: Production Hardening (Planned)
| Requirement | Priority | Description |
| :--- | :---: | :--- |
| **Lazy Backend Initialization** | High | Importing `sagittarius` must remain lightweight even inside Docker/devcontainer workflows. Julia, GPU runtimes, and optional solver stacks should initialize only when a backend is selected or an explicit setup/doctor command is run. |
| **Backend Capability Detection** | High | Provide a formal `doctor`/backend inspection path that reports actual runtime availability inside or outside Docker, including missing GPU passthrough, driver/runtime mismatches, and optional backend dependencies. |
| **GPU Maturity Matrix** | High | Document each backend as `stable`, `experimental`, or `planned`; CUDA, AMDGPU, and Metal must not be presented as equally mature unless parity tests exist. |
| **Package Versioning** | Medium | Expose Python, Julia, backend, solver, CUDA/AMDGPU/Metal, and container/build metadata through the public API and simulation artifacts for reproducibility. |
| **Repository Cleanup** | Medium | Remove temporary files such as `api.py-FIX`, move debug scripts into `examples/` or `scripts/`, and verify that referenced license files exist. |

## 🚀 Phase 6: Core Performance Improvements (Planned)
| Requirement | Priority | Description |
| :--- | :---: | :--- |
| **Reduced Basis Cache** | High | Cache blockade-reduced bases by an adjacency/register hash, blockade radius, and atom count to avoid repeated basis generation. |
| **Fast Basis Mapping** | High | Evaluate faster lookup structures than `Dict{Int, Int}` for bitstring-to-basis-index mapping on hot Hamiltonian paths. |
| **Sparse Pattern Reuse** | High | Reuse Hamiltonian sparse row/column structure and update only values when time-dependent pulses change $\Omega$ or $\Delta$. |
| **GPU Buffer Reuse** | High | Preallocate and reuse GPU sparse/value buffers to reduce repeated host-to-device transfers and sparse matrix construction. |
| **Observable/Jumps Basis Sharing** | Medium | Ensure observables, Lindblad jump operators, MCWF trajectories, and Hamiltonian evolution share the same reduced-basis mapping consistently. |
| **Specialized Register Constructors** | Medium | Add optimized constructors for common 1D chains, 2D lattices, and UDG instances, including pruning-ratio diagnostics. |

## 🧩 Phase 7: API & Data Model Refinement (Planned)
| Requirement | Priority | Description |
| :--- | :---: | :--- |
| **Explicit Pulse Types** | High | Replace ambiguous scalar/list/dict/callable handling with validated `GlobalPulse`, `LocalPulseVector`, and `CallablePulse` style inputs or equivalent typed wrappers. |
| **Local Addressing Validation** | High | Validate local pulse vector length, dictionary keys, atom index ordering, and callable return dimensions before simulation starts. |
| **Indexing Semantics** | High | Document and test Python-to-Julia atom ordering, including any reversal or 1-based/0-based translation. |
| **Pulse Compilation Contract** | Medium | Define the expected behavior for Python callbacks, AST pulse nodes, piecewise pulses, and native Julia pulse compilation. |
| **Julia Native Developer API** | High | Maintain a first-class Julia API for users who need direct access to Hamiltonians, bases, pulse objects, solvers, backend controls, and performance-critical internals. |
| **Python SDK Parity Contract** | High | Define which simulation semantics, defaults, result fields, and error behaviors must remain equivalent between the Python SDK and Julia SDK. |
| **Cross-Language Golden Tests** | High | Add shared Python/Julia test cases that verify equivalent Hamiltonians, observables, solver outputs, serialization, and benchmark fixtures within documented tolerances. |
| **Shared Result Schema** | Medium | Define a stable language-neutral result format for simulations, benchmark artifacts, and hardware-demo handoff workflows. |

## 🧪 Phase 8: Scientific Verification & Benchmarks (Planned)
| Requirement | Priority | Description |
| :--- | :---: | :--- |
| **Dense-vs-Reduced Validation** | High | For small systems, compare full dense Hamiltonian evolution with reduced-basis projected evolution. |
| **Open-System Sanity Checks** | High | Add Lindblad trace-preservation, positivity sanity checks, and MCWF-vs-Lindblad ensemble comparisons. |
| **CPU/GPU Parity Suite** | High | Run deterministic CPU/GPU parity tests with fixed tolerances and seeded random components where applicable. |
| **MWIS Batch Verification** | Medium | Compare AQC output against exact ILP solutions across randomized UDG/MWIS instances. |
| **Ablation Benchmarks** | High | Benchmark full dense, full sparse, reduced matrix-free, reduced sparse, and reduced sparse GPU-cached execution paths. |
| **Reproducible Benchmark Artifacts** | High | Benchmark scripts should emit JSON/CSV with hardware, Julia/Python/CUDA versions, parameters, timings, memory usage, and generated markdown tables. |

## 📚 Phase 9: Documentation & Patent Readiness (Planned)
| Requirement | Priority | Description |
| :--- | :---: | :--- |
| **Known Limitations** | High | Document current scale limits, backend limitations, numerical assumptions, and unsupported scenarios. |
| **Verifiable Performance Claims** | High | Replace broad marketing claims with benchmark-backed statements that name hardware, versions, problem size, and configuration. |
| **Minimal Examples with Expected Output** | Medium | Add short examples with expected basis size, observable values, or solver output for quick user verification. |
| **Dual SDK Documentation** | Medium | Provide parallel Python and Julia examples for algorithm prototyping, experiment-style pulse simulation, baseline validation, and hardware-demo preparation. |
| **Prior-Art-Aware Technical Notes** | Medium | Maintain internal notes distinguishing Sagittarius-specific execution optimizations from known Rydberg/MWIS mappings and existing neutral-atom simulators. |
| **Disclosure Control** | Medium | Track dates for public releases, benchmark reports, and technical disclosures that may affect patent filing strategy. |

## 🔬 Phase 10: HPC & Advanced Deployment (Future)
- **Slurm Integration**: Native support for `ClusterManagers.jl` to manage multi-node jobs.
- **MPI Backend**: Distributed-memory Hamiltonian evolution for $N > 40$ atoms.
- **C++ FFI**: Direct bindings for C++ applications to leverage the Julia engine.
- **Web Dashboard**: Interactive results explorer for large-scale sweeps.

---

## 🛠️ Maintenance & Verification
All features are verified via the `tests/` and `sagittarius_py/tests/` suites. 
Run the full verification: `cd sagittarius_py && uv run python -m pytest tests/`
