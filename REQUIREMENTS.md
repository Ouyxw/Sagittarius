# Sagittarius Development Roadmap & Requirements

This document outlines the development lifecycle of Sagittarius, from a functional prototype to a reproducible scientific SDK.

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
| **Structured Python/Julia Logging** | High | Partial | Python logs enrich cataloged events with stable event IDs, schema version, default severity, and optional JSON output; Julia now emits taxonomy-aligned structured physics events for basis generation and Hamiltonian construction. Remaining work: full Julia solver/runtime emitter parity. |
| **Event Taxonomy** | High | Done | Stable catalog implemented in `sagittarius.events`, exposed through `event_taxonomy()` / `get_event_spec()`, documented in `docs/EVENT_TAXONOMY.md`, and covered by tests for IDs, payload fields, severity conventions, and compatibility rules. |
| **Run Manifest Schema** | High | Done | Python `SimulationResult` outputs now include a validated `run-manifest/v1` manifest with register geometry, pulse configuration, solver options, backend diagnostics, package versions, random/trajectory metadata, and cataloged log event IDs. Benchmark scripts now link generated run manifests through benchmark artifacts where simulation results are produced. |
| **Result Artifact Envelope** | Medium | Done | Python `SimulationResult.save()` now writes a stable `result-artifact/v1` envelope with schema version, artifact type, data, metadata, diagnostics, and manifest fields; `load_result()` preserves compatibility with legacy result JSON. Julia workflow parity remains tracked by the broader shared result schema work. |
| **Benchmark Artifact Metadata** | High | Done | Benchmark scripts emit `benchmark-artifact/v1` JSON plus CSV and generated Markdown tables with parameters, timings, memory usage, runtime/backend diagnostics, Python/Julia/CUDA metadata from `version_info()`, and linked run manifests where simulations produce them. |
| **Version and Build Metadata** | Medium | Done | `version_info()` now emits `version-info/v1` with Python package versions, Julia project/runtime versions, git source/build metadata, container metadata, and CUDA/AMDGPU/Metal toolchain probes. `doctor()`, simulation run manifests, and benchmark artifacts carry this metadata. |
| **Failure Diagnostics Normalization** | High | Done | Backend, solver, validation, and serialization failures normalize to actionable diagnostic issue codes, remediation messages, and `failure_diagnostic` log events while preserving compatible Python exception types. |

## 🚀 Phase 7: Core Performance Improvements (Planned)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Reduced Basis Cache** | High | Done | Cache blockade-reduced bases by an adjacency hash, blockade radius, and atom count to avoid repeated basis generation across validation, Hamiltonian construction, observables, and jump operators. |
| **Fast Basis Mapping** | High | Done | Reduced-basis hot paths use dense bitstring-to-index lookup tables when the state range is bounded, with `Dict{Int, Int}` retained as a fallback for larger state spaces. |
| **Sparse Pattern Reuse** | High | Done | Full and reduced-basis Hamiltonians cache their CSC sparse row/column structure and update only stored values when time-dependent $\Omega$ or $\Delta$ changes; CUDA sparse buffers are retained across value-only pulse updates. |
| **GPU Buffer Reuse** | High | Done | CUDA reduced-basis execution reuses the cached `CuSparseMatrixCSC` and copies updated Hamiltonian values into the existing device value buffer instead of rebuilding GPU sparse structure on value-only pulse changes. |
| **Observable/Jumps Basis Sharing** | Medium | Done | Added a shared Julia `BasisContext` so reduced Hamiltonians, observables, Lindblad jump operators, MCWF trajectories, and Python simulations reuse the same basis and mapping. |
| **Specialized Register Constructors** | Medium | Done | Python `Register.chain()`, `Register.square_lattice()`, `Register.udg()`, and `Register.from_udg_graph()` construct common geometries with topology metadata; simulation diagnostics include register geometry and reduced-basis pruning-ratio data. |

## 🧩 Phase 8: API & Data Model Refinement (In Progress)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Explicit Pulse Types** | High | Done | Added validated `GlobalPulse`, `LocalPulseVector`, and `CallablePulse` wrappers plus `Pulse.global_()`, `Pulse.local()`, and `Pulse.callable()` factories while preserving legacy scalar/list/dict/callable shorthand compatibility. |
| **Local Addressing Validation** | High | Done | Validate local pulse vector length, dictionary keys, atom index ranges, pulse value types, observable indices, and callable return dimensions before backend initialization. |
| **Indexing Semantics** | High | Done | Python atom indices are zero-based in `Register.atoms` order; Julia boundary calls convert to one-based indices, and local pulse vectors are not reversed. Documented in `docs/PULSE_CONTRACT.md` and covered by tests. |
| **Pulse Compilation Contract** | Medium | Done | Define scalar, list, dict, callable, and Pulse AST behavior, including callable vector dimensions and local addressing defaults. Documented in `docs/PULSE_CONTRACT.md` and covered by validation tests. |
| **Julia Native Developer API** | High | Done | Julia now exports first-class constructors, register helpers, basis/Hamiltonian facades, pulse nodes, solver functions, jump operators, GPU solver entry points, and structured logging APIs; documented in `docs/JULIA_NATIVE_API.md`. |
| **Python SDK Parity Contract** | High | Done | Documented Python/Julia parity semantics for atom ordering, bitstrings, pulse addressing, Hamiltonians, solver settings, result manifests, and validation boundaries in `docs/PYTHON_JULIA_PARITY.md`. |
| **Cross-Language Golden Tests** | High | Done | Added Python-vs-Julia golden tests for full and reduced Hamiltonians, reduced basis ordering, local addressing, observable solver trajectories, and manifest parity fields. |
| **Shared Result Schema** | Medium | Done | Defined `shared-result/v1` as a language-neutral result payload, embedded it in Python result artifacts, added validation helpers, and documented required fields in `docs/SHARED_RESULT_SCHEMA.md`. |

## 🧪 Phase 9: Scientific Verification & Benchmarks (In Progress)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Dense-vs-Reduced Validation** | High | Done | Backend-free `dense_vs_reduced_validation()` compares small-system full dense Hamiltonians projected onto the blockade basis with reduced-basis Hamiltonian evolution, reporting basis sizes, pruning ratio, and max errors. |
| **Open-System Sanity Checks** | High | Done | `open_system_sanity_checks()` reports Lindblad trace preservation, density-matrix positivity, and MCWF-vs-Lindblad observable agreement for small open systems. |
| **CPU/GPU Parity Suite** | High | Done | Opt-in CUDA parity suite compares deterministic CPU/GPU observable trajectories across global drive, local addressing, and blockade-reduced seeded-state cases with fixed tolerances. |
| **MWIS Batch Verification** | Medium | Done | `projects/mwis_udg/batch_verify.py` compares AQC outputs against exact PuLP/CBC ILP solutions across seeded randomized UDG/MWIS instances and emits `mwis-batch-verification/v1` aggregate reports. |
| **Ablation Benchmarks** | High | Done | `benchmark_ablation.py` emits `benchmark-artifact/v1` results for full dense, full sparse, reduced matrix-free, reduced sparse, and opt-in reduced sparse CUDA-cached execution paths. |

## 📚 Phase 10: Documentation & Patent Readiness (In Progress)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Known Limitations** | High | Done | Document current scale limits, backend limitations, numerical assumptions, reproducibility gaps, and unsupported scenarios in `docs/KNOWN_LIMITATIONS.md`. |
| **Verifiable Performance Claims** | High | Done | Added `docs/PERFORMANCE_CLAIMS.md` with claim requirements, artifact sources, and approved wording; updated README, MWIS notes, and historical GPU/MWIS conclusions to require `benchmark-artifact/v1` or `mwis-batch-verification/v1` evidence before public performance claims. |
| **Minimal Examples with Expected Output** | Medium | Done | Add short examples with expected diagnostics shape, validation errors, indexing behavior, basis size, observable values, and serialization output in `docs/MINIMAL_EXAMPLES.md`. |
| **Dual SDK Documentation** | Medium | Done | Added `docs/DUAL_SDK_EXAMPLES.md` with paired Python and Julia workflows for algorithm prototyping, experiment-style pulse simulation, baseline validation, and hardware-demo preparation, linked from README, Julia API, and parity docs. |
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
