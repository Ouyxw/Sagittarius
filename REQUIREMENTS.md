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

## ✅ Phase 5: Production Hardening (Done)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Lazy Backend Initialization** | High | Done | `import sagittarius` stays lightweight; Julia, CUDA, and cluster workers initialize only when simulation, pulse compilation, cluster setup, GPU execution, or explicit backend initialization needs them. |
| **Backend Capability Detection** | High | Done | Public `doctor()` reports runtime metadata, container detection, backend maturity, backend capability summaries, ABI/toolchain metadata, CUDA driver/device/compute-capability visibility, CUDA 12.8/Blackwell compatibility, parity-test status, structured diagnostics, and actionable failure codes. Initialized probes cover backend package loading, CUDA.jl version guidance, device visibility/allocation, sparse backend checks, and probe ABI fields where available. |
| **GPU Maturity Matrix** | High | Done | Backend maturity is documented in `docs/reference/SPEC-BACKEND-001-backends.md` and exposed through `backend_maturity()`: CPU `stable`, CUDA `experimental`, AMDGPU/Metal `planned`. |
| **Package Versioning** | Medium | Done | `version_info()` emits `version-info/v1` with Python package/runtime versions, Sagittarius.jl project/runtime versions, platform, build/source metadata, container metadata, backend toolchain probes, and host ABI metadata while preserving compatibility fields. |
| **Basic Runtime Logging** | High | Done | Configurable runtime logging emits cataloged backend initialization, doctor report, solver start/finish, cluster setup, and failure-diagnostic events with stable event IDs, schema metadata, severity, text output, and optional JSON output across Python and Julia paths. |
| **Basic Runtime Diagnostics** | High | Done | `doctor()` and simulation results capture `doctor/v2.1` runtime/backend diagnostics, structured issue details, capability summaries, solver settings, tolerances, basis size, reduced-basis pruning ratio, register geometry, runtime metadata, and validated run manifests for observable result artifacts. |
| **Repository Cleanup** | Medium | Done | Removed `api.py-FIX`, moved root debug scripts into `scripts/`, added `LICENSE`, and updated backend documentation references. |

## ✅ Phase 6: Observability & Reproducibility (Done)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Structured Python/Julia Logging** | High | Done | Python logs enrich cataloged events with stable event IDs, schema version, default severity, and optional JSON output; Julia emits taxonomy-aligned structured events for solver start/finish, cluster setup, basis generation, and Hamiltonian construction, with catalog validation shared across Python and Julia emitters. |
| **Event Taxonomy** | High | Done | Stable catalog implemented in `sagittarius.events`, exposed through `event_taxonomy()` / `get_event_spec()`, documented in `docs/reference/SPEC-OBS-001-event-taxonomy.md`, and covered by tests for IDs, payload fields, severity conventions, and compatibility rules. |
| **Run Manifest Schema** | High | Done | Python `SimulationResult` outputs now include a validated `run-manifest/v1` manifest with register geometry, pulse configuration, solver options, backend diagnostics, package versions, random/trajectory metadata, and cataloged log event IDs. Benchmark scripts now link generated run manifests through benchmark artifacts where simulation results are produced. |
| **Result Artifact Envelope** | Medium | Done | Python `SimulationResult.save()` writes a stable `result-artifact/v1` envelope with schema version, artifact type, data, metadata, diagnostics, manifest fields, and an embedded `shared-result/v1` payload; `load_result()` preserves compatibility with legacy result JSON. |
| **Benchmark Artifact Metadata** | High | Done | Benchmark scripts emit `benchmark-artifact/v1` JSON plus CSV and generated Markdown tables with parameters, timings, memory usage, runtime/backend diagnostics, Python/Julia/CUDA metadata from `version_info()`, and linked run manifests where simulations produce them. |
| **Version and Build Metadata** | Medium | Done | `version_info()` now emits `version-info/v1` with Python package versions, Julia project/runtime versions, git source/build metadata, container metadata, and CUDA/AMDGPU/Metal toolchain probes. `doctor()`, simulation run manifests, and benchmark artifacts carry this metadata. |
| **Failure Diagnostics Normalization** | High | Done | Backend, solver, validation, and serialization failures normalize to actionable diagnostic issue codes, remediation messages, and `failure_diagnostic` log events while preserving compatible Python exception types. |

## ✅ Phase 7: Core Performance Improvements (Done)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Reduced Basis Cache** | High | Done | Cache blockade-reduced bases by an adjacency hash, blockade radius, and atom count to avoid repeated basis generation across validation, Hamiltonian construction, observables, and jump operators. |
| **Fast Basis Mapping** | High | Done | Reduced-basis hot paths use dense bitstring-to-index lookup tables when the state range is bounded, with `Dict{Int, Int}` retained as a fallback for larger state spaces. |
| **Sparse Pattern Reuse** | High | Done | Full and reduced-basis Hamiltonians cache their CSC sparse row/column structure and update only stored values when time-dependent $\Omega$ or $\Delta$ changes; CUDA sparse buffers are retained across value-only pulse updates. |
| **GPU Buffer Reuse** | High | Done | CUDA reduced-basis execution reuses the cached `CuSparseMatrixCSC` and copies updated Hamiltonian values into the existing device value buffer instead of rebuilding GPU sparse structure on value-only pulse changes. |
| **Observable/Jumps Basis Sharing** | Medium | Done | Added a shared Julia `BasisContext` so reduced Hamiltonians, observables, Lindblad jump operators, MCWF trajectories, and Python simulations reuse the same basis and mapping. |
| **Specialized Register Constructors** | Medium | Done | Python `Register.chain()`, `Register.square_lattice()`, `Register.udg()`, and `Register.from_udg_graph()` construct common geometries with topology metadata; simulation diagnostics include register geometry and reduced-basis pruning-ratio data. |

## ✅ Phase 8: API & Data Model Refinement (Done)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Explicit Pulse Types** | High | Done | Added validated `GlobalPulse`, `LocalPulseVector`, and `CallablePulse` wrappers plus `Pulse.global_()`, `Pulse.local()`, and `Pulse.callable()` factories while preserving legacy scalar/list/dict/callable shorthand compatibility. |
| **Local Addressing Validation** | High | Done | Validate local pulse vector length, dictionary keys, atom index ranges, pulse value types, observable indices, and callable return dimensions before backend initialization. |
| **Indexing Semantics** | High | Done | Python atom indices are zero-based in `Register.atoms` order; Julia boundary calls convert to one-based indices, and local pulse vectors are not reversed. Documented in `docs/api/SPEC-API-001-pulse-and-indexing-contract.md` and covered by tests. |
| **Pulse Compilation Contract** | Medium | Done | Define scalar, list, dict, callable, and Pulse AST behavior, including callable vector dimensions and local addressing defaults. Documented in `docs/api/SPEC-API-001-pulse-and-indexing-contract.md` and covered by validation tests. |
| **Julia Native Developer API** | High | Done | Julia now exports first-class constructors, register helpers, basis/Hamiltonian facades, pulse nodes, solver functions, jump operators, GPU solver entry points, and structured logging APIs; documented in `docs/api/SPEC-API-003-julia-native-api.md`. |
| **Python SDK Parity Contract** | High | Done | Documented Python/Julia parity semantics for atom ordering, bitstrings, pulse addressing, Hamiltonians, solver settings, result manifests, and validation boundaries in `docs/api/SPEC-API-002-python-julia-parity.md`. |
| **Cross-Language Golden Tests** | High | Done | Added Python-vs-Julia golden tests for full and reduced Hamiltonians, reduced basis ordering, local addressing, observable solver trajectories, and manifest parity fields. |
| **Shared Result Schema** | Medium | Done | Defined `shared-result/v1` as a language-neutral result payload, embedded it in Python result artifacts, added validation helpers, and documented required fields in `docs/reference/SPEC-DATA-001-shared-result-schema.md`. |

## ✅ Phase 9: Scientific Verification & Benchmarks (Done)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Dense-vs-Reduced Validation** | High | Done | Backend-free `dense_vs_reduced_validation()` compares small-system full dense Hamiltonians projected onto the blockade basis with reduced-basis Hamiltonian evolution, reporting basis sizes, pruning ratio, and max errors. |
| **Open-System Sanity Checks** | High | Done | `open_system_sanity_checks()` reports Lindblad trace preservation, density-matrix positivity, and MCWF-vs-Lindblad observable agreement for small open systems. |
| **CPU/GPU Parity Suite** | High | Done | Opt-in CUDA parity suite compares deterministic CPU/GPU observable trajectories across global drive, local addressing, and blockade-reduced seeded-state cases with fixed tolerances. |
| **MWIS Batch Verification** | Medium | Done | `projects/mwis_udg/batch_verify.py` compares AQC outputs against exact PuLP/CBC ILP solutions across seeded randomized UDG/MWIS instances and emits `mwis-batch-verification/v1` aggregate reports. |
| **Ablation Benchmarks** | High | Done | `benchmark_ablation.py` emits `benchmark-artifact/v1` results for full dense, full sparse, reduced matrix-free, reduced sparse, and opt-in reduced sparse CUDA-cached execution paths. |

## ✅ Phase 10: Documentation & Patent Readiness (Done)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Known Limitations** | High | Done | Document current scale limits, backend limitations, numerical assumptions, reproducibility gaps, and unsupported scenarios in `docs/reference/known-limitations.md`. |
| **Verifiable Performance Claims** | High | Done | Added `docs/governance/SPEC-GOV-001-performance-claims.md` with claim requirements, artifact sources, and approved wording; updated README, MWIS notes, and historical GPU/MWIS conclusions to require `benchmark-artifact/v1` or `mwis-batch-verification/v1` evidence before public performance claims. |
| **Benchmark Governance Plan** | High | Done | Added `docs/governance/SPEC-GOV-004-benchmarking-plan.md` to define benchmark layers, suite priorities, required row metadata, correctness gates, running discipline, release cadence, and roadmap alignment. |
| **Architecture, Data Model, and Technical Stack Docs** | High | Done | Added `docs/reference/architecture-overview.md`, `docs/reference/data-model.md`, and `docs/reference/technical-stack.md` to explain Sagittarius system architecture, object/schema/artifact model, dependency stack, backend maturity, and roadmap-linked maintenance triggers. |
| **Minimal Examples with Expected Output** | Medium | Done | Add short examples with expected diagnostics shape, validation errors, indexing behavior, basis size, observable values, and serialization output in `docs/getting-started/minimal-examples.md`. |
| **Dual SDK Documentation** | Medium | Done | Added `docs/getting-started/dual-sdk-examples.md` with paired Python and Julia workflows for algorithm prototyping, experiment-style pulse simulation, baseline validation, and hardware-demo preparation, linked from README, Julia API, and parity docs. |
| **Prior-Art-Aware Technical Notes** | Medium | Done | Added `docs/governance/SPEC-GOV-003-prior-art-notes.md` to distinguish known Rydberg/MWIS mappings, hardness methodology, neutral-atom tooling, and generic numerical techniques from Sagittarius-specific schemas, diagnostics, parity tests, and execution-path implementation work. |
| **Disclosure Control** | Medium | Done | Added `docs/governance/SPEC-GOV-002-disclosure-control.md` with a disclosure register, required review fields, status values, approval workflow, trigger examples, and links to performance-claim, prior-art, and known-limitation checks. |

## 📏 Phase 11: Observable Library (Planned)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Julia Observable Library** | High | Planned | Add a first-class Julia observable library that returns solver-compatible callables with the stable signature `(state, t, integrator) -> Float64`. Keep `RydbergPopulation` as the existing primitive and add common neutral-atom observables for total Rydberg population, pair correlations, connected correlations, blockade-violation counts, bitstring probabilities, MWIS/cost expectations, Pauli-Z, Pauli-ZZ, and parity. |
| **Shared Basis and State Helpers** | High | Planned | Centralize full-basis, reduced-basis, `BasisContext`, bitstring mapping, `Vector`, `Matrix`, and CUDA state handling in internal helper functions so every observable interprets amplitudes, density matrices, and reduced-basis indices consistently. |
| **Diagonal Observable First Scope** | High | Planned | Prioritize diagonal occupation/bitstring observables in the first implementation because they are stable across full and reduced bases and directly support Rydberg blockade, AQC, and MWIS workflows. Off-diagonal observables such as Pauli-X, Pauli-Y, coherence, energy with non-diagonal Hamiltonians, and entanglement measures remain future work unless they can be implemented with explicit basis-mapping tests. |
| **Solver-Path Compatibility** | High | Planned | Observable callables must work consistently across Schrödinger, Lindblad, MCWF, and supported GPU solver paths, or fail with a documented validation error when a path is unsupported. Reduced-basis observables must share the same `BasisContext` as Hamiltonians and jump operators. |
| **Python Observable Declarations** | High | Planned | Extend the Python SDK beyond the current `dict[str, int]` Rydberg-population shorthand with a validated declaration format for named observables, while preserving `observables={"pop0": 0}` as backward-compatible shorthand. Python indices remain zero-based and are converted at the Julia boundary. |
| **Observable Metadata** | Medium | Planned | Record observable type, parameters, atom indices, edge lists where applicable, basis mode, and declaration order in run manifests, shared results, and serialized result artifacts so observable series can be audited and reproduced. |
| **Observable Validation** | High | Planned | Validate observable names, type identifiers, atom indices, bitstring bounds, edge endpoints, weight lengths, penalty parameters, and unsupported state/backend combinations before solver execution where possible. Errors must include actionable remediation. |
| **Verification and Documentation** | High | Planned | Add Julia unit tests, Python wrapper tests, reduced-vs-full parity tests, Lindblad density-matrix tests, MCWF smoke tests, and opt-in CUDA parity tests for the observable library. Document Julia native examples, Python declaration examples, indexing conventions, and reduced-basis requirements. |

### Phase 11 Acceptance Criteria

1. Julia exports documented constructors for the first-scope observable library while preserving `RydbergPopulation` compatibility.
2. Each first-scope observable returns a solver-compatible callable and produces the same value on equivalent full-basis and reduced-basis states.
3. Observables correctly handle wavefunction vectors and Lindblad density matrices; GPU support is implemented for supported observables or explicitly rejected with a documented diagnostic.
4. `BasisContext` sharing is required and tested for reduced-basis Hamiltonians, observables, jump operators, and MCWF trajectories.
5. Python supports a validated observable declaration format and preserves the existing `observables={"name": atom_index}` shorthand.
6. Result data, shared results, and run manifests preserve observable names, order, types, and parameters.
7. Automated tests cover indexing, bitstring mapping, full/reduced parity, solver-path behavior, serialization metadata, invalid declarations, and representative Rydberg/MWIS use cases.

## 🧮 Phase 12: Numerical Solver Configuration (Planned)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Solver Method Dispatch** | High | Planned | Connect `SolverConfig.method` to the Julia backend so the configured method determines the OrdinaryDiffEq algorithm actually used. Initially support the explicit whitelist `Tsit5`, `Vern9`, and `RK4`; do not evaluate arbitrary Julia expressions or silently fall back to another method. |
| **All Solver-Path Coverage** | High | Planned | Apply method dispatch consistently to Schrödinger, Lindblad, Monte Carlo trajectory, and supported GPU solver paths. A method must not be reported as supported if any applicable execution path silently ignores it. |
| **Adaptive and Fixed-Step Options** | High | Planned | Extend `SolverConfig` with `adaptive: bool = True` and `dt: Optional[float] = None`. `Tsit5` and `Vern9` support adaptive tolerance-driven integration. Fixed-step `RK4` requires `adaptive=False` and a finite positive `dt`; invalid combinations must fail validation before solver execution. |
| **Backend Algorithm Resolver** | High | Planned | Implement a Julia-side whitelist resolver that maps stable public names to OrdinaryDiffEq algorithm instances. Unsupported names must raise an actionable validation error that lists the supported methods. |
| **Effective Configuration Metadata** | High | Planned | Record the algorithm and stepping options actually used by the backend in simulation diagnostics, run manifests, serialized result artifacts, and relevant solver start events. Requested and effective configuration must agree; metadata must never claim `RK4` or `Vern9` when the backend used `Tsit5`. |
| **Backward Compatibility** | Medium | Planned | Preserve current behavior by keeping `method="Tsit5"` and adaptive stepping as defaults. Existing callers that do not specify `method`, `adaptive`, or `dt` must continue to use tolerance-controlled `Tsit5`. |
| **Method Dispatch Verification** | High | Planned | Add Python/Julia integration tests proving that each supported method reaches the Julia resolver and is used by every applicable solver path. Add tests for unsupported names, invalid `dt`, incompatible RK4 stepping options, default behavior, metadata accuracy, and representative numerical agreement across methods. |
| **Documentation** | Medium | Planned | Document the accuracy/cost tradeoffs of `Tsit5`, `Vern9`, and `RK4`, including that `reltol`/`abstol` primarily control adaptive methods while fixed-step RK4 accuracy is governed by `dt`. |

### Phase 12 Acceptance Criteria

1. Changing `SolverConfig.method` changes the Julia OrdinaryDiffEq algorithm used during execution.
2. `SolverConfig(method="Tsit5")` and `SolverConfig(method="Vern9")` run with adaptive stepping by default and honor `reltol` and `abstol`.
3. `SolverConfig(method="RK4", adaptive=False, dt=<positive finite value>)` runs with fixed-step RK4.
4. Unsupported methods and invalid option combinations fail explicitly; no execution path silently substitutes `Tsit5`.
5. Diagnostics and manifests contain the effective method, `adaptive` value, and `dt` where applicable.
6. Schrödinger, Lindblad, MCWF, CPU, and supported GPU paths either honor the selected method or reject it with a documented error.
7. Automated tests verify dispatch, validation, metadata, backward compatibility, and numerical sanity.

## 📦 Phase 13: Packaging & Installation (Planned)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Source Installation Baseline** | High | Planned | Define the currently supported installation model as a complete repository checkout followed by `uv sync` and `python -m juliapkg resolve`. Document `pip install -e .` as a development-only editable install that still depends on the repository layout, and explicitly state that an independent PyPI installation is not yet supported. |
| **Relocatable Wheel** | High | Planned | Build a Python wheel that contains the Julia backend sources and required Julia project metadata. An installed wheel must continue to run after the source checkout is moved or deleted. |
| **Package Resource Lookup** | High | Planned | Replace repository-relative backend discovery such as `Path(__file__).resolve().parents[2] / "Sagittarius.jl"` with installed-package resource lookup, while retaining an explicit development override where needed. |
| **Julia Package Data** | High | Planned | Include `Sagittarius.jl/Project.toml`, Julia source files, and any required runtime metadata as declared Python package data in both wheel and source distributions. Verify that no backend file is obtained accidentally from the build checkout. |
| **CPU-First Dependency Profile** | High | Planned | Make the default installation usable for CPU simulations without CUDA, an NVIDIA driver, or CUDA.jl. Move CUDA and future GPU backend setup to explicit optional workflows rather than resolving CUDA for every user. |
| **Backend Setup Command** | Medium | Planned | Provide a user-facing CLI or equivalent explicit workflow for Julia dependency resolution and backend setup, such as `sagittarius backend resolve`, `sagittarius backend install cuda`, and `sagittarius doctor`. Backend installation failures must return actionable diagnostics. |
| **Clean-Environment Artifact Tests** | High | Planned | Build wheel and sdist artifacts in CI, install them into clean virtual environments outside the repository, and run import, backend initialization, one-atom simulation, serialization, and uninstall/reinstall smoke tests. Tests executed from the source tree alone are insufficient. |
| **Cross-Platform Installation Matrix** | High | Planned | Validate supported Python and Julia versions on Linux, macOS, and Windows. Publish an explicit compatibility matrix and classify platform-specific Julia discovery or compilation limitations. |
| **PyPI Release Readiness** | High | Planned | Publish to PyPI only after wheel/sdist isolation tests pass, CPU installation is independent of CUDA, package metadata and licensing are complete, Julia initialization errors are actionable, and the supported version matrix is documented. |
| **Installation Documentation** | Medium | Planned | Keep local source installation, editable development installation, wheel installation, Julia executable overrides, CPU/GPU setup, upgrade, and uninstall instructions distinct. Do not advertise `pip install sagittarius-py` until a released artifact satisfies the acceptance criteria below. |

### Phase 13 Acceptance Criteria

1. `pip install <built-wheel>` succeeds in a clean virtual environment outside the source repository.
2. `import sagittarius` remains lightweight and does not initialize or download Julia packages.
3. A CPU one-atom simulation succeeds after explicit backend resolution with no source checkout present.
4. Moving or deleting the original repository does not break an installed wheel.
5. The wheel and sdist contain all required Julia backend source and project files, verified from their artifact contents.
6. Default CPU installation does not require CUDA.jl, an NVIDIA driver, or GPU hardware.
7. Unsupported or missing Julia installations produce documented, actionable diagnostics.
8. CI tests installation artifacts across the declared Python, Julia, and operating-system support matrix.
9. PyPI publication remains blocked until all release-readiness requirements and artifact smoke tests pass.

## 🧪 Recommended Cold-Atom / Quantum-Simulation Project Backlog

This backlog prioritizes example projects and validation studies for using Sagittarius as a cold-atom and quantum-computing simulation SDK. These are application milestones rather than core API feature commitments. Performance or hardware-facing conclusions from these projects must follow `docs/governance/SPEC-GOV-001-performance-claims.md` and `docs/governance/SPEC-GOV-002-disclosure-control.md`.

### P0: Foundation Experiments

| Project | Status | Purpose | Sagittarius capabilities exercised | Notes |
| :--- | :---: | :--- | :--- | :--- |
| **Single-Atom Rabi Oscillation and Pulse Calibration** | Recommended | Validate `omega`, pulse duration, unit conventions, Rabi period, and single-site `RydbergPopulation`. | `Register`, `PulseSequence`, `Pulse.constant`, `Pulse.sin_squared`, `Simulation.run`, observable shorthand. | First sanity check for all later simulations; verify expected half-period population transfer under known `omega`. |
| **Two-Atom Rydberg Blockade** | Recommended | Demonstrate suppression of double excitation as distance, `C6`, drive strength, and blockade assumptions vary. | Two-atom registers, local/global drive, `C6/r^6` interaction, observable trajectories, optional `blockade_radius`. | Establish the core physical model before larger arrays. |
| **Small-Chain Full-vs-Reduced Basis Validation** | Recommended | Compare full Hilbert-space dynamics with blockade-reduced dynamics on 3-5 atom chains. | `Register.chain()`, `SolverConfig.blockade_radius`, reduced-basis cache, `dense_vs_reduced_validation()`. | Use to choose a defensible blockade radius and approximation error budget. |
| **Landau-Zener / Adiabatic Detuning Sweep** | Recommended | Simulate detuning ramps and adiabatic-transfer behavior. | `Pulse.ramp` on `delta`, smooth `omega` pulses, solver tolerances, observable trajectories. | Natural bridge from basic dynamics to AQC/annealing workflows. |

### P1: Demonstration Workflows

| Project | Status | Purpose | Sagittarius capabilities exercised | Notes |
| :--- | :---: | :--- | :--- | :--- |
| **Rydberg Chain Excitation Profiles** | Recommended | Study spatial excitation patterns under local addressing. | `Pulse.local`, sparse local dictionaries, `Register.atoms` ordering, multi-observable results. | Good demo for local addressing and pulse-shape documentation. |
| **Open-System Decay and Dephasing Studies** | Recommended | Compare closed-system, Lindblad, and MCWF behavior under `gamma` and `gamma_phi`. | `SolverConfig.gamma`, `gamma_phi`, `use_mc`, `n_trajectories`, `open_system_sanity_checks()`. | Keep systems small enough for trace/positivity and MCWF-vs-Lindblad checks. |
| **CPU/CUDA Parity Smoke Studies** | Recommended | Compare CPU and CUDA observable trajectories for representative small systems. | `doctor(backend="CUDA")`, `SolverConfig(use_gpu=True)`, CUDA parity tests, run manifests. | CUDA remains experimental; claims must cite benchmark/parity artifacts. |
| **Small UDG/MWIS Simulation Examples** | Recommended | Map unit-disk graph constraints to Rydberg blockade dynamics and compare against exact baselines. | `Register.udg()`, `Register.from_udg_graph()`, detuning schedules, `batch_verify.py`, result artifacts. | Treat MWIS mapping as prior art; Sagittarius contribution is reproducible simulation and verification workflow. |

### P2: Phase-Dependent Studies

| Project | Status | Dependency | Purpose | Notes |
| :--- | :---: | :--- | :--- | :--- |
| **Pair-Correlation and Blockade-Violation Diagnostics** | Planned | Phase 11 Observable Library | Track `<n_i n_j>`, connected correlations, and constraint-violation counts directly. | Current shorthand supports single-site populations only; implement after typed observables land. |
| **MWIS Cost Expectation and Bitstring Success Tracking** | Planned | Phase 11 Observable Library | Track weighted objective expectation, target bitstring probabilities, feasibility, and success metrics. | Pair with exact ILP baselines and disclosure controls before external claims. |
| **Solver Method Sensitivity Study** | Planned | Phase 12 Solver Configuration | Compare `Tsit5`, `Vern9`, and fixed-step `RK4` for accuracy/cost tradeoffs on representative workflows. | Wait until `SolverConfig.method`, `adaptive`, and `dt` are connected to the Julia backend. |

### P3: Advanced / Future Studies

| Project | Status | Dependency | Purpose | Notes |
| :--- | :---: | :--- | :--- | :--- |
| **Large Parameter Sweeps and Phase-Diagram Scans** | Future | Stable small-system validations; optional cluster support | Sweep `omega`, `delta`, `blockade_radius`, geometry, and noise parameters. | Generate `benchmark-artifact/v1` outputs when reporting scaling or performance. |
| **Hardware-Demo Preparation Workflow** | Future | Mature diagnostics, manifests, and disclosure review | Package diagnostics, run manifests, version metadata, and bounded wording for hardware-facing demos. | Sagittarius is not a calibrated hardware control stack. |
| **2D Array Ordering and MIS-Like Pattern Formation** | Future | Observable library and scale validation | Study square-lattice or UDG excitation patterns and optimization-like final states. | Requires careful reduced-basis validation and richer observables. |

### Recommended Execution Order

1. Single-atom Rabi oscillation.
2. Two-atom Rydberg blockade.
3. Small-chain full-vs-reduced basis validation.
4. Landau-Zener / adiabatic detuning sweep.
5. Small UDG/MWIS example with exact baseline checks.
6. Open-system Lindblad/MCWF comparison.
7. CPU/CUDA parity or benchmark-artifact generation where hardware is available.

## 🌫️ Phase 14: Theoretical Noise Model Extensions (Planned)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Noise Model Specification** | High | Planned | Document the current local Markovian open-system baseline and define the extension path for theoretical noise models in `docs/physics/SPEC-PHYS-004-noise-models.md`, explicitly separating theory-oriented noise from hardware readout/calibration models. |
| **Custom Lindblad Channels** | High | Planned | Add a validated API for user-defined Lindblad jump operators or structured operator declarations that work consistently in full and blockade-reduced bases, share `BasisContext`, and are recorded in run manifests and result artifacts. |
| **Correlated Dephasing Channels** | High | Planned | Support structured correlated dephasing channels such as `L = sqrt(rate) * sum_i c_i n_i`, including global, regional, and weighted spatial profiles. Validate atom weights, basis mapping, solver-path compatibility, and metadata. |
| **Collective Decay Channels** | Medium | Planned | Support structured collective decay channels such as `L = sqrt(rate) * sum_i c_i sigma_i^-` where physically appropriate, with explicit caveats about model assumptions and reduced-basis behavior. |
| **Stochastic Hamiltonian Ensemble Runner** | High | Planned | Add an ensemble workflow for random Hamiltonian parameter fluctuations, including quasi-static detuning offsets, amplitude noise, colored detuning noise, and seeded realization averaging over observables. This depends on Phase 15 seed and output-grid contracts for reproducibility. |
| **Time-Dependent Noise Rates** | Medium | Planned | Extend theory-noise declarations to support time-dependent rates or scheduled noise strengths where they can be validated and serialized. Unsupported combinations must fail explicitly. |
| **Noise Metadata and Validation** | High | Planned | Record noise model type, parameters, random seeds, basis mode, solver path, and effective realization counts in diagnostics, run manifests, shared results where applicable, and serialized artifacts. |

### Phase 14 Acceptance Criteria

1. `SPEC-PHYS-004` clearly defines the current baseline: local Rydberg decay, local pure dephasing, Lindblad, and MCWF.
2. Custom and structured Lindblad channels preserve trace and positivity in small-system tests and share the same `BasisContext` as Hamiltonians, observables, and jump operators.
3. Correlated dephasing and collective decay declarations validate atom weights, rates, basis compatibility, and unsupported solver/backend combinations.
4. Stochastic Hamiltonian runs support seeded realization generation, stable output grids, and manifest-linked averaged observables.
5. Noise metadata is sufficient to reproduce or audit every non-default noise channel used in a run.
6. Documentation distinguishes theoretical open-system/stochastic models from hardware readout or calibration error models.

## 🧾 Phase 15: Experiment Workflow & Readout Reproducibility (Planned)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Measurement / Sampling API** | High | Planned | Add a stable final-state sampling and measurement API for shot-based workflows, including final bitstring distribution extraction, `SimulationResult.sample(shots, seed=...)`, reduced-basis forbidden-bitstring handling, readout metadata in manifests, and compatibility with `shared-result/v1` result series. |
| **Random Seed Control** | High | Planned | Add user-facing seed controls for MCWF trajectories, final-state sampling, randomized UDG/MWIS project generation, and benchmark/example scripts. Record requested and effective RNG metadata in run manifests, benchmark artifacts, and project reports. |
| **Output Time Grid / Saveat Contract** | High | Planned | Extend solver configuration with a stable output sampling contract such as `saveat`, fixed output sample count, or explicit output time arrays. Record requested and effective output grids in diagnostics, run manifests, and serialized artifacts, and align Schrödinger, Lindblad, MCWF, CPU, and supported GPU paths. |
| **Executable Experiment Recipes** | High | Planned | Promote the recommended P0/P1 project backlog into runnable examples with expected outputs and artifact generation, including single-atom Rabi, two-atom blockade, Landau-Zener sweep, open-system decay/dephasing, and small UDG/MWIS workflows. |
| **State Preparation Helpers** | Medium | Planned | Add helpers for common initial states, including all-ground state, named bitstring states, single-excitation states, and optional uniform superpositions. Helpers must validate full/reduced basis compatibility and preserve state-preparation metadata. |
| **Experiment Config Schema** | Medium | Planned | Define an `experiment-config/v1` schema that can describe register geometry, pulse schedule, solver options, observables/readout, seed controls, and output artifact paths. Provide load/run/save workflow and link generated run manifests back to the source config. |
| **Parameter Sweep API and Artifacts** | Medium | Planned | Add a user-facing parameter sweep workflow for `omega`, `delta`, `blockade_radius`, geometry, noise, solver settings, and observable declarations. Emit resumable sweep artifacts with per-run manifest links, distinct from benchmark artifacts when the purpose is scientific exploration rather than performance measurement. |
| **Documentation Governance Requirements** | Medium | Planned | Treat stable SPEC IDs, metadata headers, `docs/status.md`, and Markdown link validation as required documentation maintenance checks for future roadmap phases and public release preparation. |

### Phase 15 Acceptance Criteria

1. Users can sample final-state bitstrings with a declared shot count and seed, and the result is reproducible across equivalent runs.
2. MCWF, sampling, randomized project scripts, and benchmark/demo workflows record requested/effective seed metadata.
3. Users can request an explicit output time grid or stable output count, and every applicable solver path either honors it or rejects it with a documented diagnostic.
4. P0/P1 experiment recipes run from the repository with expected output shapes, diagnostics, manifests, and serialization artifacts.
5. Common initial-state helpers work consistently in full and reduced bases and fail clearly for forbidden reduced-basis bitstrings.
6. `experiment-config/v1` can reproduce a run and link generated artifacts to the source configuration.
7. Sweep artifacts preserve parameter values, result locations, run manifests, and resumability metadata.
8. Documentation checks verify SPEC metadata and Markdown links before release-oriented documentation changes are accepted.

## 🧩 Phase 16: Experimental Interop & Readout Models (Future)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Readout Noise and Detection Error Models** | Medium | Future | Add optional shot-level readout error models for false positives, false negatives, atom loss, and confusion-matrix style post-processing. Readout errors must be explicitly opt-in and recorded in manifests and result artifacts. |
| **External Neutral-Atom Tool Interop** | Low | Future | Explore bounded import/export workflows for neutral-atom schedules, geometries, or pulse descriptions used by tools such as Pulser, Bloqade-style workflows, or hardware-provider formats. Any interop claims must follow prior-art and disclosure controls and must not imply Sagittarius is a calibrated hardware control stack. |
| **Hardware-Oriented Schedule Export** | Low | Future | Provide an optional export format for reviewed, simulation-derived schedules with unit metadata, pulse definitions, and backend diagnostics. Exported schedules are for review and translation, not direct hardware execution without a vendor calibration layer. |

### Phase 16 Acceptance Criteria

1. Readout error models are opt-in, parameterized, validated, and recorded in reproducibility metadata.
2. Interop import/export paths preserve units, atom ordering, pulse timing, and unsupported-feature diagnostics.
3. Documentation distinguishes simulation artifacts from hardware-control artifacts and passes governance review before public interop claims.

## 🔬 Phase 17: HPC & Advanced Deployment (Future)
- **Slurm Integration**: Native support for `ClusterManagers.jl` to manage multi-node jobs.
- **MPI Backend**: Distributed-memory Hamiltonian evolution for $N > 40$ atoms.
- **Cluster and Sweep Benchmarks**: Extend benchmark workflows for cluster execution, parameter-sweep throughput, resumability, artifact aggregation, and hardware/backend-specific diagnostics. Public claims must follow `docs/governance/SPEC-GOV-004-benchmarking-plan.md` and `docs/governance/SPEC-GOV-001-performance-claims.md`.
- **C++ FFI**: Direct bindings for C++ applications to leverage the Julia engine.
- **Web Dashboard**: Interactive results explorer for large-scale sweeps.

---

## 🛠️ Maintenance & Verification
All features are verified via the `tests/` and `sagittarius_py/tests/` suites.
Run the full verification: `cd sagittarius_py && uv run python -m pytest tests/`
For Phase 5 lightweight runtime checks: `cd sagittarius_py && uv run python -m pytest tests/test_runtime_hardening.py tests/test_serialization.py`
