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
| **Backend Capability Detection** | High | Partial | Public `doctor()` reports runtime metadata, container detection, backend maturity, CUDA driver/device/compute-capability visibility, CUDA 12.8/Blackwell driver compatibility, structured diagnostics, and actionable failure codes. Initialized probes cover backend package loading, CUDA.jl version guidance, device visibility/allocation, and sparse backend checks where available. Remaining work: hardware-backed parity validation and fuller backend-specific ABI reporting. |
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
| **Run Manifest Schema** | High | Done | Python `SimulationResult` outputs now include a validated `run-manifest/v1` manifest with register geometry, pulse configuration, solver options, backend diagnostics, package versions, random/trajectory metadata, and cataloged log event IDs. Benchmark scripts now link generated run manifests through benchmark artifacts where simulation results are produced. |
| **Result Artifact Envelope** | Medium | Done | Python `SimulationResult.save()` now writes a stable `result-artifact/v1` envelope with schema version, artifact type, data, metadata, diagnostics, and manifest fields; `load_result()` preserves compatibility with legacy result JSON. Julia workflow parity remains tracked by the broader shared result schema work. |
| **Benchmark Artifact Metadata** | High | Done | Benchmark scripts emit `benchmark-artifact/v1` JSON plus CSV and generated Markdown tables with parameters, timings, memory usage, runtime/backend diagnostics, Python/Julia/CUDA metadata from `version_info()`, and linked run manifests where simulations produce them. |
| **Version and Build Metadata** | Medium | Done | `version_info()` now emits `version-info/v1` with Python package versions, Julia project/runtime versions, git source/build metadata, container metadata, and CUDA/AMDGPU/Metal toolchain probes. `doctor()`, simulation run manifests, and benchmark artifacts carry this metadata. |
| **Failure Diagnostics Normalization** | High | Done | Backend, solver, validation, and serialization failures normalize to actionable diagnostic issue codes, remediation messages, and `failure_diagnostic` log events while preserving compatible Python exception types. |

## 🚀 Phase 7: Core Performance Improvements (Planned)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Reduced Basis Cache** | High | Planned | Cache blockade-reduced bases by an adjacency/register hash, blockade radius, and atom count to avoid repeated basis generation. |
| **Fast Basis Mapping** | High | Planned | Evaluate faster lookup structures than `Dict{Int, Int}` for bitstring-to-basis-index mapping on hot Hamiltonian paths. |
| **Sparse Pattern Reuse** | High | Planned | Reuse Hamiltonian sparse row/column structure and update only values when time-dependent pulses change $\Omega$ or $\Delta$. |
| **GPU Buffer Reuse** | High | Planned | Preallocate and reuse GPU sparse/value buffers to reduce repeated host-to-device transfers and sparse matrix construction. |
| **Observable/Jumps Basis Sharing** | Medium | Planned | Ensure observables, Lindblad jump operators, MCWF trajectories, and Hamiltonian evolution share the same reduced-basis mapping consistently. |
| **Specialized Register Constructors** | Medium | Done | Python `Register.chain()`, `Register.square_lattice()`, `Register.udg()`, and `Register.from_udg_graph()` construct common geometries with topology metadata; simulation diagnostics include register geometry and reduced-basis pruning-ratio data. |

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

## 🧪 Phase 9: Scientific Verification & Benchmarks (In Progress)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Dense-vs-Reduced Validation** | High | Done | Backend-free `dense_vs_reduced_validation()` compares small-system full dense Hamiltonians projected onto the blockade basis with reduced-basis Hamiltonian evolution, reporting basis sizes, pruning ratio, and max errors. |
| **Open-System Sanity Checks** | High | Planned | Add Lindblad trace-preservation, positivity sanity checks, and MCWF-vs-Lindblad ensemble comparisons. |
| **CPU/GPU Parity Suite** | High | Done | Opt-in CUDA parity suite compares deterministic CPU/GPU observable trajectories across global drive, local addressing, and blockade-reduced seeded-state cases with fixed tolerances. |
| **MWIS Batch Verification** | Medium | Planned | Compare AQC output against exact ILP solutions across randomized UDG/MWIS instances. |
| **Ablation Benchmarks** | High | Planned | Benchmark full dense, full sparse, reduced matrix-free, reduced sparse, and reduced sparse GPU-cached execution paths. |

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
