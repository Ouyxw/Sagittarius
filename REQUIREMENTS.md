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
| **GPU Acceleration** | Done | GPU execution path exists, with CUDA as the primary tested target and AMDGPU/Metal tracked by the maturity matrix. |
| **Clustered Solvers** | Done | Distributed parameter sweeps via `ParallelSimulation`. |

## 🚧 Phase 5: Production Hardening (In Progress)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Lazy Backend Initialization** | High | Done | `import sagittarius` stays lightweight; Julia, CUDA, and cluster workers initialize only when simulation, pulse compilation, cluster setup, GPU execution, or explicit backend initialization needs them. |
| **Backend Capability Detection** | High | Partial | Public `doctor()` reports runtime metadata, container detection, backend maturity, CUDA driver/device visibility, structured diagnostics, and actionable failure codes. Initialized probes cover backend package loading, device visibility/allocation, and sparse backend checks where available. Remaining work: hardware-backed parity validation, fuller backend-specific ABI reporting, and remediation docs. |
| **GPU Maturity Matrix** | High | Done | Backend maturity is documented in `docs/BACKENDS.md` and exposed through `backend_maturity()`: CPU `stable`, CUDA `experimental`, AMDGPU/Metal `planned`. |
| **Package Versioning** | Medium | Partial | `version_info()` exposes Python package, Python runtime, platform, container status, Sagittarius.jl version, and Julia version once loaded. Full build/container metadata is tracked in Phase 6. |
| **Basic Runtime Logging** | High | Partial | Python-side configurable logging exists for backend initialization, doctor reports, solver start/finish, and cluster setup. Full cross-language observability is tracked in Phase 6. |
| **Basic Runtime Diagnostics** | High | Partial | `doctor()` and observable simulation results capture runtime/backend diagnostics, structured issue details, selected solver settings, tolerances, basis size, and reduced-basis pruning ratio. Full run manifests are tracked in Phase 6. |
| **Repository Cleanup** | Medium | Done | Removed `api.py-FIX`, moved root debug scripts into `scripts/`, added `LICENSE`, and updated backend documentation references. |

## 📈 Phase 6: Observability & Reproducibility (In Progress)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Structured Python/Julia Logging** | High | Partial | Python logs now enrich cataloged events with stable event IDs, schema version, default severity, and optional JSON output. Julia emitters and full cross-language parity remain planned. |
| **Event Taxonomy** | High | Done | Stable catalog implemented in `sagittarius.events`, exposed through `event_taxonomy()` / `get_event_spec()`, documented in `docs/EVENT_TAXONOMY.md`, and covered by tests for IDs, payload fields, severity conventions, and compatibility rules. |
| **Run Manifest Schema** | High | Planned | Persist a machine-readable manifest alongside saved results and benchmarks, including random seeds, register geometry, pulse configuration, solver options, backend diagnostics, package versions, and relevant log event IDs. |
| **Result Artifact Envelope** | Medium | Done | Python `SimulationResult.save()` now writes a stable `result-artifact/v1` envelope with schema version, artifact type, data, metadata, diagnostics, and manifest fields; `load_result()` preserves compatibility with legacy result JSON. Julia workflow parity remains tracked by the broader shared result schema work. |
| **Benchmark Artifact Metadata** | High | Planned | Benchmark scripts should emit JSON/CSV with hardware, Julia/Python/CUDA versions, parameters, timings, memory usage, generated markdown tables, and linked diagnostic manifests. |
| **Version and Build Metadata** | Medium | Planned | Record Python, Julia, solver, backend package, CUDA/AMDGPU/Metal, container image, and build metadata in diagnostics, manifests, and benchmark artifacts. |
| **Failure Diagnostics Normalization** | High | Done | Backend, solver, validation, and serialization failures normalize to actionable diagnostic issue codes, remediation messages, and `failure_diagnostic` log events while preserving compatible Python exception types. |

## 🚀 Phase 7: Core Performance Improvements (Planned)
| Requirement | Priority | Description |
| :--- | :---: | :--- |
| **Reduced Basis Cache** | High | Cache blockade-reduced bases by an adjacency/register hash, blockade radius, and atom count to avoid repeated basis generation. |
| **Fast Basis Mapping** | High | Evaluate faster lookup structures than `Dict{Int, Int}` for bitstring-to-basis-index mapping on hot Hamiltonian paths. |
| **Sparse Pattern Reuse** | High | Reuse Hamiltonian sparse row/column structure and update only values when time-dependent pulses change $\Omega$ or $\Delta$. |
| **GPU Buffer Reuse** | High | Preallocate and reuse GPU sparse/value buffers to reduce repeated host-to-device transfers and sparse matrix construction. |
| **Observable/Jumps Basis Sharing** | Medium | Ensure observables, Lindblad jump operators, MCWF trajectories, and Hamiltonian evolution share the same reduced-basis mapping consistently. |
| **Specialized Register Constructors** | Medium | Add optimized constructors for common 1D chains, 2D lattices, and UDG instances, with pruning-ratio data exposed through the Phase 6 diagnostics schema. |

## 🧩 Phase 8: API & Data Model Refinement (In Progress)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Explicit Pulse Types** | High | Planned | Replace ambiguous scalar/list/dict/callable handling with validated `GlobalPulse`, `LocalPulseVector`, and `CallablePulse` style inputs or equivalent typed wrappers. |
| **Local Addressing Validation** | High | Done | Validate local pulse vector length, dictionary keys, atom index ranges, pulse value types, observable indices, and callable return dimensions before backend initialization. |
| **Indexing Semantics** | High | Done | Python atom indices are zero-based in `Register.atoms` order; Julia boundary calls convert to one-based indices, and local pulse vectors are not reversed. Documented in `docs/PULSE_CONTRACT.md` and covered by tests. |
| **Pulse Compilation Contract** | Medium | Done | Define scalar, list, dict, callable, and Pulse AST behavior, including callable vector dimensions and local addressing defaults. Documented in `docs/PULSE_CONTRACT.md` and covered by validation tests. |
| **Julia Native Developer API** | High | Planned | Maintain a first-class Julia API for users who need direct access to Hamiltonians, bases, pulse objects, solvers, backend controls, and performance-critical internals. |
| **Python SDK Parity Contract** | High | Planned | Define which simulation semantics, defaults, result fields, and error behaviors must remain equivalent between the Python SDK and Julia SDK. |
| **Cross-Language Golden Tests** | High | Planned | Add shared Python/Julia test cases that verify equivalent Hamiltonians, observables, solver outputs, serialization, and benchmark fixtures within documented tolerances. |
| **Shared Result Schema** | Medium | Planned | Define stable language-neutral simulation result fields and semantics; artifact envelopes and manifests are tracked in Phase 6. |

## 🧪 Phase 9: Scientific Verification & Benchmarks (Planned)
| Requirement | Priority | Description |
| :--- | :---: | :--- |
| **Dense-vs-Reduced Validation** | High | For small systems, compare full dense Hamiltonian evolution with reduced-basis projected evolution. |
| **Open-System Sanity Checks** | High | Add Lindblad trace-preservation, positivity sanity checks, and MCWF-vs-Lindblad ensemble comparisons. |
| **CPU/GPU Parity Suite** | High | Run deterministic CPU/GPU parity tests with fixed tolerances and seeded random components where applicable. |
| **MWIS Batch Verification** | Medium | Compare AQC output against exact ILP solutions across randomized UDG/MWIS instances. |
| **Ablation Benchmarks** | High | Benchmark full dense, full sparse, reduced matrix-free, reduced sparse, and reduced sparse GPU-cached execution paths. |

## 📚 Phase 10: Documentation & Patent Readiness (In Progress)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Known Limitations** | High | Done | Document current scale limits, backend limitations, numerical assumptions, reproducibility gaps, and unsupported scenarios in `docs/KNOWN_LIMITATIONS.md`. |
| **Verifiable Performance Claims** | High | Planned | Replace broad marketing claims with benchmark-backed statements that reference Phase 6 benchmark artifacts and name hardware, versions, problem size, and configuration. |
| **Minimal Examples with Expected Output** | Medium | Done | Add short examples with expected diagnostics shape, validation errors, indexing behavior, basis size, observable values, and serialization output in `docs/MINIMAL_EXAMPLES.md`. |
| **Dual SDK Documentation** | Medium | Planned | Provide parallel Python and Julia examples for algorithm prototyping, experiment-style pulse simulation, baseline validation, and hardware-demo preparation. |
| **Prior-Art-Aware Technical Notes** | Medium | Planned | Maintain internal notes distinguishing Sagittarius-specific execution optimizations from known Rydberg/MWIS mappings and existing neutral-atom simulators. |
| **Disclosure Control** | Medium | Planned | Track dates for public releases, benchmark reports, and technical disclosures that may affect patent filing strategy. |

## 🔬 Phase 11: HPC & Advanced Deployment (Future)
- **Slurm Integration**: Native support for `ClusterManagers.jl` to manage multi-node jobs.
- **MPI Backend**: Distributed-memory Hamiltonian evolution for $N > 40$ atoms.
- **C++ FFI**: Direct bindings for C++ applications to leverage the Julia engine.
- **Web Dashboard**: Interactive results explorer for large-scale sweeps.

---

## 🛠️ Maintenance & Verification
All features are verified via the `tests/` and `sagittarius_py/tests/` suites.
Run the full verification: `cd sagittarius_py && uv run python -m pytest tests/`
For Phase 5 lightweight runtime checks: `cd sagittarius_py && uv run python -m pytest tests/test_runtime_hardening.py tests/test_serialization.py`
