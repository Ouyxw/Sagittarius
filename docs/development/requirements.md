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
| **MWIS Batch Verification** | Medium | Done | `sagittarius_py/projects/mwis_udg/batch_verify.py` compares AQC outputs against exact PuLP/CBC ILP solutions across seeded randomized UDG/MWIS instances and returns a `mwis-batch-verification/v1` in-memory aggregate report. |
| **Ablation Benchmarks** | High | Done | `benchmark_ablation.py` emits `benchmark-artifact/v1` results for full dense, full sparse, reduced matrix-free, reduced sparse, and opt-in reduced sparse CUDA-cached execution paths. |

## ✅ Phase 10: Documentation & Patent Readiness (Done)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Known Limitations** | High | Done | Document current scale limits, backend limitations, numerical assumptions, reproducibility gaps, and unsupported scenarios in `docs/reference/known-limitations.md`. |
| **Verifiable Performance Claims** | High | Done | Added `docs/governance/SPEC-GOV-001-performance-claims.md` with claim requirements, artifact sources, and approved wording; updated README, MWIS notes, and historical GPU/MWIS conclusions to require `benchmark-artifact/v1` or `mwis-batch-verification/v1` evidence before public performance claims. |
| **Benchmark Governance Plan** | High | Done | Added `docs/governance/SPEC-GOV-004-benchmarking-plan.md` to define benchmark layers, suite priorities, required row metadata, correctness gates, running discipline, release cadence, and roadmap alignment. |
| **Architecture, Data Model, and Technical Stack Docs** | High | Done | Added `docs/reference/architecture-overview.md`, `docs/reference/data-model.md`, and `docs/reference/technical-stack.md` to explain Sagittarius system architecture, object/schema/artifact model, dependency stack, backend maturity, and roadmap-linked maintenance triggers. |
| **Minimal Examples with Expected Output** | Medium | Done | Add short examples with expected diagnostics shape, validation errors, indexing behavior, basis size, observable values, and serialization output in `docs/getting-started/minimal-examples.md`. |
| **Dual SDK Documentation** | Medium | Deferred | The earlier paired-example guide was removed during public-source preparation. A new user-facing guide will be written after the Julia backend reaches the required maturity. |
| **Prior-Art-Aware Technical Notes** | Medium | Done | Added `docs/governance/SPEC-GOV-003-prior-art-notes.md` to distinguish known Rydberg/MWIS mappings, hardness methodology, neutral-atom tooling, and generic numerical techniques from Sagittarius-specific schemas, diagnostics, parity tests, and execution-path implementation work. |
| **Disclosure Control** | Medium | Done | Added `docs/governance/SPEC-GOV-002-disclosure-control.md` with a disclosure register, required review fields, status values, approval workflow, trigger examples, and links to performance-claim, prior-art, and known-limitation checks. |

## ✅ Phase 11: Observable Library (Done)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Julia Observable Library** | High | Done | Add a first-class Julia observable library that returns solver-compatible callables with the stable signature `(state, t, integrator) -> Float64`. Keep `RydbergPopulation` as the existing primitive and add common neutral-atom observables for total Rydberg population, pair correlations, connected correlations, blockade-violation counts, bitstring probabilities, MWIS/cost expectations, Pauli-Z, Pauli-ZZ, and parity. |
| **Shared Basis and State Helpers** | High | Done | Centralize full-basis, reduced-basis, `BasisContext`, bitstring mapping, `Vector`, `Matrix`, and CUDA state handling in internal helper functions so every observable interprets amplitudes, density matrices, and reduced-basis indices consistently. |
| **Diagonal Observable First Scope** | High | Done | Prioritize diagonal occupation/bitstring observables in the first implementation because they are stable across full and reduced bases and directly support Rydberg blockade, AQC, and MWIS workflows. Off-diagonal observables such as Pauli-X, Pauli-Y, coherence, energy with non-diagonal Hamiltonians, and entanglement measures remain future work unless they can be implemented with explicit basis-mapping tests. |
| **Solver-Path Compatibility** | High | Done | Diagonal observable callables work consistently across Schrödinger, Lindblad, MCWF, and existing solver plumbing. Reduced-basis observables share the same `BasisContext` as Hamiltonians and jump operators. Existing GPU observable parity remains opt-in and backend-maturity bounded. |
| **Python Observable Declarations** | High | Done | Extend the Python SDK beyond the current `dict[str, int]` Rydberg-population shorthand with a validated declaration format for named observables, while preserving `observables={"pop0": 0}` as backward-compatible shorthand. Python indices remain zero-based and are converted at the Julia boundary. |
| **Observable Metadata** | Medium | Done | Record observable type, parameters, atom indices, edge lists where applicable, basis mode, and declaration order in run manifests and serialized result artifacts. `shared-result/v1` preserves observable names and series order while typed metadata lives in the linked manifest. |
| **Observable Validation** | High | Done | Validate observable names, type identifiers, atom indices, bitstring bounds, edge endpoints, weight lengths, penalty parameters, and unsupported state/backend combinations before solver execution where possible. Errors must include actionable remediation. |
| **Verification and Documentation** | High | Done | Added Julia constructor tests, Python wrapper tests, shorthand compatibility tests, reduced-basis metadata tests, Lindblad/open-system regression coverage, and MCWF-adjacent regression coverage for the diagonal observable library. Documented Python declaration examples, indexing conventions, and reduced-basis requirements. |

### Phase 11 Acceptance Criteria

1. Julia exports documented constructors for the first-scope observable library while preserving `RydbergPopulation` compatibility.
2. Each first-scope observable returns a solver-compatible callable and produces the same value on equivalent full-basis and reduced-basis states.
3. Observables correctly handle wavefunction vectors and Lindblad density matrices; GPU support is implemented for supported observables or explicitly rejected with a documented diagnostic.
4. `BasisContext` sharing is required and tested for reduced-basis Hamiltonians, observables, jump operators, and MCWF trajectories.
5. Python supports a validated observable declaration format and preserves the existing `observables={"name": atom_index}` shorthand.
6. Result data and `shared-result/v1` preserve observable names and order; run manifests and serialized artifacts preserve observable types and parameters.
7. Automated tests cover indexing, bitstring mapping, full/reduced parity, solver-path behavior, serialization metadata, invalid declarations, and representative Rydberg/MWIS use cases.

## 🧮 Phase 12: Numerical Solver Configuration (Done)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Solver Method Dispatch** | High | Done | Connected `SolverConfig.method` to the Julia backend so the configured method determines the OrdinaryDiffEq algorithm actually used. Supports the explicit whitelist `Tsit5`, `Vern9`, and `RK4`; do not evaluate arbitrary Julia expressions or silently fall back to another method. |
| **All Solver-Path Coverage** | High | Done | Applied method dispatch consistently to Schrödinger, Lindblad, Monte Carlo trajectory, and supported GPU solver paths. No applicable execution path silently ignores a supported method. |
| **Adaptive and Fixed-Step Options** | High | Done | Extended `SolverConfig` with `adaptive: bool = True` and `dt: Optional[float] = None`. `Tsit5` and `Vern9` support adaptive tolerance-driven integration. Fixed-step `RK4` requires `adaptive=False` and a finite positive `dt`; invalid combinations fail validation before solver execution. |
| **Backend Algorithm Resolver** | High | Done | Implemented a Julia-side whitelist resolver that maps stable public names to OrdinaryDiffEq algorithm instances. Unsupported names raise an actionable validation error that lists the supported methods. |
| **Effective Configuration Metadata** | High | Done | Recorded the algorithm and stepping options actually used by the backend in simulation diagnostics, run manifests, serialized result artifacts, and relevant solver start events. Requested and effective configuration agree; metadata must never claim `RK4` or `Vern9` when the backend used `Tsit5`. |
| **Backward Compatibility** | Medium | Done | Preserved current behavior by keeping `method="Tsit5"` and adaptive stepping as defaults. Existing callers that do not specify `method`, `adaptive`, or `dt` continue to use tolerance-controlled `Tsit5`. |
| **Method Dispatch Verification** | High | Done | Added Python/Julia integration tests proving that each supported method reaches the Julia resolver and is used by applicable solver paths, including unsupported names, invalid `dt`, incompatible RK4 stepping options, default behavior, metadata accuracy, and representative numerical agreement across methods. |
| **Documentation** | Medium | Done | Documented the accuracy/cost tradeoffs of `Tsit5`, `Vern9`, and `RK4`, including that `reltol`/`abstol` primarily control adaptive methods while fixed-step RK4 accuracy is governed by `dt`. |

### Phase 12 Acceptance Criteria

1. Changing `SolverConfig.method` changes the Julia OrdinaryDiffEq algorithm used during execution.
2. `SolverConfig(method="Tsit5")` and `SolverConfig(method="Vern9")` run with adaptive stepping by default and honor `reltol` and `abstol`.
3. `SolverConfig(method="RK4", adaptive=False, dt=<positive finite value>)` runs with fixed-step RK4.
4. Unsupported methods and invalid option combinations fail explicitly; no execution path silently substitutes `Tsit5`.
5. Diagnostics and manifests contain the effective method, `adaptive` value, and `dt` where applicable.
6. Schrödinger, Lindblad, MCWF, CPU, and supported GPU paths either honor the selected method or reject it with a documented error.
7. Automated tests verify dispatch, validation, metadata, backward compatibility, and numerical sanity.

## 📦 Phase 13: Packaging & Installation (Mixed)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Source Installation Baseline** | High | Done | Defines the developer installation model as a complete repository checkout followed by `uv sync` and `python -m juliapkg resolve`. Documents `pip install -e .` as development-only; consumer package installation is governed by the authoritative Python package-installation guide for the published 1.0.11 release. |
| **Relocatable Wheel** | High | Done | The published 1.0.11 wheel contains the embedded Julia backend and passed repository-external package-resource, clean-venv, and uninstall/reinstall smoke coverage. |
| **Package Resource Lookup** | High | Done | Replaces direct repository-relative backend discovery with a centralized lookup that prefers the explicit `SAGITTARIUS_JULIA_BACKEND_PATH` environment override, then an editable/source checkout backend, then installed-package resources; diagnostics report `env_override`, `source_checkout`, or `package_resource`. |
| **Julia Package Data** | High | Done | Includes `Sagittarius.jl/Project.toml`, `Manifest.toml`, Julia source files, and runtime metadata as Python package data under `sagittarius/julia/Sagittarius.jl/`, with artifact tests verifying wheel and source distributions contain the embedded backend. |
| **CPU-First Dependency Profile** | High | Done | Default `juliapkg.json` and the embedded Julia backend project now resolve CPU-required Julia packages without CUDA.jl, an NVIDIA driver, or GPU hardware. CUDA is split into the packaged opt-in `juliapkg-cuda.json` profile for future backend setup workflows. |
| **Optional GPU Backend Profiles** | High | Mixed | The CUDA profile is complete: `juliapkg-cuda.json` carries `backend-profile/v1` metadata, is excluded from default CPU resolution, appears in `sagittarius backend profiles`, supports `sagittarius backend install cuda --dry-run`, and is installable through `sagittarius backend install cuda`. Later AMDGPU/Metal profiles remain planned. |
| **Backend Setup Command** | Medium | Done | Adds the `sagittarius` console script with `sagittarius backend resolve`, `sagittarius backend install cuda`, and `sagittarius doctor`. Commands emit JSON setup/diagnostic reports and normalize setup failures to actionable diagnostic messages. |
| **CUDA Wheel Smoke and Parity** | High | Mixed | Added a hardware-gated clean-venv CUDA wheel smoke and manual self-hosted CUDA workflow. The smoke installs the wheel, runs `sagittarius backend install cuda`, runs initialized CUDA doctor diagnostics, executes a small CPU/CUDA parity simulation, and verifies CUDA.jl, driver, runtime, device, backend source, result artifact, manifest, and diagnostics metadata. The 1.0.11 release retained execution evidence from the real NVIDIA GPU hardware gate; CUDA remains experimental. |
| **Clean-Environment Artifact Tests** | High | Done | Artifact tests verify wheel/sdist contents. Clean-venv release smokes install the canonical wheel and retained sdist, run `sagittarius backend resolve`, execute a one-atom CPU simulation, validate result artifact, manifest, doctor, version metadata, source-tree import isolation, and verify wheel uninstall/reinstall behavior in a repo-external environment. The smokes are wired into release CI. |
| **Cross-Platform Installation Matrix** | High | Done | `docs/getting-started/python/compatibility-matrix.md` and manual `.github/workflows/phase13-cross-platform.yml` cover Linux Python 3.10/3.11/3.12 with Julia 1.10.3/1.11 plus macOS and Windows CPU wheel smokes on Python 3.11/Julia 1.11. All five declared rows passed in GitHub Actions run `28577379030`, with retained evidence artifacts under `CI_artifacts/phase13-cross-platform-*`. |
| **CI Clean Artifact Isolation** | High | Done | Clean wheel and uninstall/reinstall smokes run in GitHub Actions as release gates. Day-to-day PRs use a separate fast CI workflow. Detailed trigger policy and evidence retention rules live in `docs/reference/ci-workflows.md`. |
| **Uninstall/Reinstall Smoke Coverage** | Medium | Done | Added a release-artifact smoke test that installs the wheel, runs backend resolution and a minimal CPU simulation, uninstalls the wheel, verifies `sagittarius` is no longer importable, reinstalls the same wheel outside the source checkout, and verifies package-resource backend metadata, JuliaPkg resolution behavior, and a minimal CPU simulation after reinstall. |
| **Package Metadata Review** | Medium | Done | PyPI-facing metadata now includes README rendering, Apache-2.0 license expression and license/NOTICE inclusion, production/stable and supported Python classifiers, scientific classifiers and Julia-backend metadata, author field, keywords, project URLs, console script metadata, and artifact content checks. Packaging tests inspect wheel/sdist metadata and run `twine check` over built artifacts. |
| **TestPyPI and Publication Policy** | Mixed | Done | The manual `.github/workflows/phase13-testpypi.yml` workflow is protected by the `testpypi` environment, publishes only canonical files through OIDC, verifies a clean installed-package CPU simulation and result artifact, reconciles index hashes, and retains versioned evidence. The current canonical candidate passed this gate; it does not authorize production publication. |
| **PyPI Release Readiness** | High | Done | Sagittarius 1.0.11 passed candidate-artifact, regression, clean-artifact, cross-platform, TestPyPI, CUDA-wheel, and protected exact-file production-promotion gates. Production hashes were reconciled and a clean production-index smoke was retained. CUDA remains experimental. |
| **Installation Documentation** | Medium | Done | Documentation distinguishes source/editable setup, local wheel/sdist artifact status, backend source selection, release artifact smoke testing, uninstall/reinstall verification, released-wheel upgrade/uninstall guidance, cross-platform matrix workflow, and PyPI publication gates. |

### Phase 13 CI and Release Automation

| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Fast PR CI** | High | Done | `.github/workflows/pr-fast-ci.yml` runs lightweight docs, benchmark-artifact, and packaging metadata/content checks automatically for pull requests to development and release branches, plus direct pushes to `develop/**` as a fallback. |
| **Clean Artifact Release Smoke** | High | Done | `.github/workflows/phase13-clean-artifact.yml` runs clean wheel install and uninstall/reinstall smokes automatically on relevant pushes to `main` and manually on demand. |
| **Cross-Platform Matrix Evidence** | High | Done | `.github/workflows/phase13-cross-platform.yml` remains manual and uploads per-row OS/Python/Julia evidence artifacts. GitHub Actions run `28577379030` passed all five declared rows, and retained artifacts are stored under `CI_artifacts/phase13-cross-platform-*`. |
| **TestPyPI Publication Evidence** | Medium | Done | `.github/workflows/phase13-testpypi.yml` verified the current canonical candidate through the protected OIDC path, including an installed-package one-atom CPU simulation, result artifact, and retained `phase13-testpypi-<version>` evidence. |
| **CUDA Hardware Evidence** | High | Done | `.github/workflows/phase13-cuda-wheel.yml` passed for the current canonical candidate on a self-hosted CUDA runner and retained GPU name/driver/memory, smoke log, and run metadata. CUDA remains experimental despite this evidence. |
| **CI Documentation** | Medium | Done | `docs/reference/ci-workflows.md` defines automatic workflows, manual release gates, evidence retention, and maintenance rules. |
| **Release Candidate Governance** | High | Done | `SPEC-GOV-006` defines `main`-based lineage, immutable identity, package boundaries, build-once promotion, and CUDA evidence timing. Sagittarius 1.0.11 completed the canonical candidate, artifact reuse, regression, hardware/service evidence, and protected production-promotion process. |
| **Canonical Candidate Artifact** | High | Done | `.github/workflows/phase13-candidate-artifact.yml` validates the frozen identity, builds wheel and sdist once, records filenames, sizes, and SHA-256 digests in `phase13-candidate-artifact/v1`, and supplies those files to the manual clean-install, cross-platform, TestPyPI, and CUDA gates. Production promotion remains a separate protected gate for every release. |
| **Release Identity Enforcement** | High | Done | The candidate build rejects a checkout/tag/commit mismatch, a commit not contained in `origin/main`, a dirty build tree, tag/version disagreement, Python/canonical-Julia/embedded-Julia version drift, and downstream filename, size, version, or digest mismatch. |
| **Release Regression Coverage** | High | Done | The canonical-candidate release-regression workflow runs backend-free and Julia-backed Python suites plus native Julia `Pkg.test()`. Sagittarius 1.0.11 retained final-candidate execution evidence; every future candidate must do the same. |
| **Sdist and Forbidden-Content Coverage** | High | Done | Wheel and sdist denylist tests reject internal development material, debug files, scratch/evidence paths, environment files, and private-key suffixes. Release CI installs the retained canonical sdist in a repository-external clean environment and runs backend-resolution, package-resource, schema, and one-atom CPU checks. |
| **Production Promotion and Failure Evidence** | High | Done | The candidate, clean-install, matrix, TestPyPI, CUDA, and production workflows upload status, logs, identities, manifests, and available partial diagnostics with `if: always()`. The protected 1.0.11 production run promoted exact files, reconciled production digests, and retained a pinned production-index post-install smoke. |

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
10. Production publication promotes the exact wheel and sdist whose commit, version, tag, and SHA-256 digests passed every applicable release gate.
11. Every release gate consumes or verifies the canonical candidate distribution digests rather than rebuilding an untracked equivalent.
12. The frozen candidate passes the complete Python release regression and all required Julia-backed parity tests.
13. A clean repository-external installation from the retained sdist passes version, backend-source, schema, and one-atom CPU checks.
14. Failed release gates retain their logs, commands, candidate identity, and available diagnostics.
15. Production publication uses the validated files and is followed by a pinned clean-install smoke from production PyPI.

### Phase 13 PyPI Readiness Completion Record

Sagittarius 1.0.11 completed the public PyPI release gates below. Candidate identity, branch integration, artifact promotion, CUDA timing, and branch cleanup follow `docs/governance/SPEC-GOV-006-release-candidate-governance.md`; future releases must repeat the applicable gates.

1. CPU-first dependency profile: Done. Default JuliaPkg and backend project metadata resolve CPU-required packages without CUDA.jl; CUDA is available only through the packaged opt-in profile.

2. Backend setup commands: Done. `sagittarius backend resolve`, `sagittarius backend install cuda`, and `sagittarius doctor` provide the documented command path; CUDA setup remains explicit and opt-in.

3. CI and release automation: Done for fast PR CI, canonical build-once distributions, ref/version/`main` identity enforcement, digest-verified reuse, wheel/sdist forbidden-content checks, clean retained-sdist installation, failure evidence, final-candidate regression, TestPyPI, cross-platform, real-hardware CUDA execution, protected production promotion, and post-publication smoke. See `docs/reference/ci-workflows.md`.

4. Uninstall/reinstall smoke coverage: Done. The release-artifact smoke installs the wheel, resolves the backend, runs a minimal CPU simulation, uninstalls the package, verifies it is no longer importable, reinstalls the same wheel outside the source checkout, and verifies backend source detection, JuliaPkg resolution, artifact metadata, and minimal CPU simulation after reinstall.

5. Package metadata review: Done. Wheel/sdist metadata tests inspect README, license, classifiers, URLs, package data, and `twine check` output.

6. TestPyPI and publication policy:
   - Manual TestPyPI workflow and publication policy are in place.
   - The protected OIDC workflow published and clean-installed the TestPyPI 1.0.11 candidate, including an installed-package CPU simulation and result artifact, and retained its evidence artifact. The version-pinned dual-index command remains a release-candidate installation path only.
   - Repository visibility, issue tracker/docs readiness, Apache-2.0 license publication, and accidental-upload controls were approved for 1.0.11 and must be reviewed again when applicable.
   - Acceptance: Done for 1.0.11; CUDA hardware evidence and open-source/publication approval were retained before production upload.

7. GPU optional backend path:
   - CUDA profile setup, clean wheel smoke, CPU/CUDA parity checks, and metadata validation are implemented behind `SAGITTARIUS_RUN_CUDA_WHEEL_SMOKE=1` and `SAGITTARIUS_ENABLE_GPU_TESTS=1`.
   - `.github/workflows/phase13-cuda-wheel.yml` provides a manual self-hosted CUDA runner workflow for hardware-backed validation.
   - Acceptance: CUDA wheel support is marked release-validated only after explicit setup, doctor, parity, artifact metadata, and GPU runner evidence pass; otherwise it remains experimental/local only. AMDGPU/Metal remain future optional profiles.

8. Cross-platform support matrix:
   - Compatibility matrix documentation and manual GitHub Actions workflow are in place.
   - The workflow uploads per-row `phase13-cross-platform-<os>-py<python>-julia<julia>` evidence artifacts with run URL, commit, ref, and validation command metadata.
   - GitHub Actions run `28577379030` passed all five declared rows: Ubuntu Python 3.10/Julia 1.10.3, Ubuntu Python 3.11/Julia 1.11, Ubuntu Python 3.12/Julia 1.11, macOS Python 3.11/Julia 1.11, and Windows Python 3.11/Julia 1.11.
   - Retained evidence artifacts are stored under `CI_artifacts/phase13-cross-platform-*`.
   - Acceptance: Done for the declared OS/Python/Julia matrix; unsupported or experimental combinations remain clearly classified.

## 🌫️ Phase 14: Theoretical Noise Model Extensions (Planned)

Phase 14 implementation should start after the Phase 13 critical packaging path is stable enough for repeatable validation: CPU-first dependency profile, backend setup commands, and CI clean artifact isolation. This avoids expanding solver and metadata surface area on top of unstable install behavior.

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

Phase 15 executable recipes may begin after the Phase 13 CPU-first, backend setup, and clean artifact isolation work is in place, so examples can target stable source and wheel installation paths. Wheel-installed recipes are part of the release-readiness bridge between Phase 13 and user-facing experiment workflows.

| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Measurement / Sampling API** | High | Done | Added final-state bitstring distribution extraction, `SimulationResult.sample(shots, seed=...)`, reduced-basis forbidden-bitstring exclusion metadata, readout metadata in manifests/diagnostics/result artifacts, and `shared-result/v1` compatibility through `series.final_bitstring_probabilities` for readout-capable results. |
| **Random Seed Control** | High | Done | Added user-facing `SolverConfig.seed` control for current MCWF trajectories and record requested/effective RNG metadata in run manifests and result artifacts. Future final-state sampling, randomized project scripts, and benchmark/demo workflows should adopt the same seed metadata contract when they land. |
| **Output Time Grid / Saveat Contract** | High | Done | Added `SolverConfig.saveat` as either a fixed output sample count or explicit output time array. Sagittarius records requested `saveat` and normalized `effective_saveat` in diagnostics, run manifests, and serialized artifacts, and forwards the grid to Schrödinger, Lindblad, MCWF, CPU, and supported GPU solver paths. |
| **MCWF Trajectory Artifact Contract** | High | Done | `SolverConfig.store_trajectories` persists optional individual MCWF samples as validated `trajectory-data/v1`: finite `(trajectory, time)` arrays with exact result-time and observable-order alignment. The `run-manifest/v1` solver section records requested/effective storage configuration and dimensions; `shared-result/v1` remains aggregate-only. |
| **Executable Experiment Recipes** | High | Done | Added user-facing runnable recipes with expected output shapes and `result-artifact/v1` generation for single-atom Rabi, two-atom blockade, Landau-Zener sweep, local Markovian open-system decay/dephasing, and a small UDG/MWIS workflow. Benchmark-grade promotion of these recipes belongs to Phase 16. |
| **Wheel-Installed Experiment Recipes** | Medium | Done | Added a self-contained small UDG/MWIS template that imports only public `sagittarius` APIs, NumPy, and the standard library. Its opt-in Ubuntu WSL `/tmp` clean-wheel smoke copies the template into an external project, installs a built wheel, runs `sagittarius backend resolve`, executes the recipe, and validates `package_resource`, result-artifact, run-manifest, and seeded measurement-samples outputs. |
| **State Preparation Helpers** | Medium | Done | Added `all_ground_state()`, `bitstring_state()`, and `single_excitation_state()` helpers. They validate reduced-basis forbidden bitstrings and preserve `state-preparation/v1` metadata in diagnostics, run manifests, and result artifacts. Uniform superposition remains future work. |
| **Experiment Config Schema** | Medium | Done | Added validated JSON-only `experiment-config/v1` with register geometry, pulse schedule, solver options, typed observables, readout seed/shot controls, output paths, load/run/save helpers, and SHA-256 source-config links in generated run manifests. |
| **Parameter Sweep API and Artifacts** | Medium | Done | Added `sweep-artifact/v1` for scientific exploration: explicit parameter axes, per-item values/status/attempts, failure records, result and run-manifest paths, and retryable resume IDs. It is explicitly separate from governed `benchmark-artifact/v1` evidence. |
| **Documentation Governance Requirements** | Medium | Done | Added offline validation for stable SPEC metadata headers, `docs/development/status.md` registration and local Markdown links. The check runs in PR fast CI and is required for release-oriented documentation changes. |

### Phase 15 Acceptance Criteria

1. Users can sample final-state bitstrings with a declared shot count and seed, and the result is reproducible across equivalent runs.
2. MCWF, sampling, randomized project scripts, and benchmark/demo workflows record requested/effective seed metadata.
3. Users can request an explicit output time grid or stable output count, and every applicable solver path either honors it or rejects it with a documented diagnostic.
4. P0/P1 experiment recipes run from the repository with expected output shapes, diagnostics, manifests, and serialization artifacts.
5. At least one wheel-installed external experiment recipe, preferably small UDG/MWIS, runs outside the source checkout using only public package APIs and emits reproducible artifacts.
6. Common initial-state helpers work consistently in full and reduced bases and fail clearly for forbidden reduced-basis bitstrings.
7. `experiment-config/v1` can reproduce a run and link generated artifacts to the source configuration.
8. Sweep artifacts preserve parameter values, result locations, run manifests, and resumability metadata.
9. Documentation checks verify SPEC metadata and Markdown links before release-oriented documentation changes are accepted.

## 🧪 Phase 16: Benchmarking & Application Validation Suite (Initial Suite Done; Full Plan Partial)

Phase 16 turns the earlier cold-atom project backlog into a systematic benchmark and application-validation suite. Its purpose is to produce reproducible scientific and performance evidence for Sagittarius without mixing exploratory local studies with public claims. Public performance or hardware-facing conclusions from this phase must follow `docs/governance/SPEC-GOV-001-performance-claims.md`, `docs/governance/SPEC-GOV-002-disclosure-control.md`, and `docs/governance/SPEC-GOV-004-benchmarking-plan.md`.

The initial suite is closed with [retained local evidence](../benchmarks/evidence/phase16-e171c584e8e67215f1e5fb00f6f908d2e434b10c/README.md). That closure covers the initial acceptance criteria below, not the complete ongoing [SPEC-GOV-004 benchmarking plan](../governance/SPEC-GOV-004-benchmarking-plan.md). The alignment matrices below track remaining plan scope without reopening completed initial verification or implying release-grade evidence. Implemented runners, retained executions, and completed performance characterization are distinct milestones.

### Phase 16 Initial Suite (Done)

| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Benchmark Taxonomy and Protocol Docs** | High | Done | Added `docs/benchmarks/` with a suite taxonomy, running instructions, artifact conventions, evidence-retention guidance, and interpretation rules that distinguish exploratory local results from release-grade benchmark evidence. |
| **Benchmark Artifact Contracts** | High | Done | `benchmark-artifact/v1` retains compatible structured single-scenario rows, while `benchmark-suite-artifact/v1` now provides validated family/tier aggregation with retained passed, failed, skipped, and incomplete rows plus deterministic summary fields and JSON/CSV/Markdown writers. |
| **Physics Baseline Benchmarks** | High | Done | Runnable CPU smoke and correctness cases cover single-atom Rabi, ideal two-atom blockade, Landau-Zener sweep, and a small-chain projected dense-vs-reduced reference. Correctness rows retain stable tolerances, reference errors, and result/manifest or reference-report links. |
| **Cold-Atom Dynamics Benchmarks** | Medium | Done | Correctness runner covers 3-atom global-chain excitation, 3-atom local addressing, 4-atom Z2 chain, and 2x2 2D array cases against projected dense matrix-exponential references (atol `1e-8`); larger trajectory, correlation, and performance studies are explicitly deferred beyond this initial suite. |
| **Open-System Benchmarks** | Medium | Done | Seeded one-atom decay plus dephasing rows validate analytic population decay, Lindblad trace/positivity, MCWF-vs-Lindblad agreement, and 100/500-trajectory sensitivity (500 no worse); multi-atom decoherence-impact and scaling studies are explicitly deferred beyond this initial suite. |
| **Optimization Benchmark Suite** | High | Done | CPU `smoke`, `correctness`, and bounded `scaling` tiers now run deterministic weighted UDG/MWIS AQC cases with graph/weight/schedule metadata, exact PuLP/CBC baselines, feasibility, objective gap, approximation ratio, optimal-success probability, reference reports, suite artifacts, and retained failure rows. Broader schedules, structured/planted families, and governed performance conclusions are future extensions. |
| **MWIS/UDG GPU Benchmark Protocol** | High | Done | Opt-in `benchmark_cuda_mwis_protocol.py` requires `SAGITTARIUS_ENABLE_GPU_TESTS=1` and successful initialized CUDA doctor diagnostics before executing CPU/CUDA chain and seeded MWIS parity. It retains device/driver/CUDA/Julia metadata, cold/warm timing, GPU-memory snapshots where available, errors, exact MWIS feasibility/objective checks, and doctor/solver failure boundaries; unavailable snapshots remain explicit (`missing` in the initial archive). Hardware-specific scale limits and governed performance conclusions are future extensions. |
| **Solver and Backend Performance Benchmarks** | High | Done | Existing scaling, GPU, cluster, and ablation runners emit structured rows while preserving legacy metrics. `benchmark_solver_performance.py` now repeats dense/sparse/reduced path measurements with declared numerical gates and validates Tsit5/Vern9/RK4 trajectories against a high-accuracy Tsit5 reference; the CUDA protocol records CPU/CUDA error, cold/warm execution, GPU memory, and doctor-gated failure boundaries. Broader scenario standardization is a future extension. |
| **Parameter Sweep and Cluster Benchmarking** | Medium | Done | `benchmark_sweep_cluster.py` records local `ParallelSimulation` parameter-map throughput, checkpointed `sweep-artifact/v1` state, per-item result/manifest links, failure rows, resume-only pending execution, and aggregate suite evidence. Multi-node deployment and physics-workload sweep coverage belong to Phase 18. |
| **Benchmark Failure Reporting** | High | Done | `make_benchmark_failure_row()` records first-class timeout, memory, CUDA initialization, reference mismatch, ILP, and unexpected-execution failure rows with exception type, stage, diagnostics, timeout, process/GPU memory, backend probe, and remediation. Runner-wide timeout and scale-limit policies are future extensions. |
| **Benchmark Documentation and Examples** | Medium | Done | Documents concise examples for running smoke, correctness, parity, scaling, and stress tiers locally. Include guidance for CUDA-only local evidence, release-grade evidence, and how benchmark outputs should be cited in README, papers, demos, or release notes. |

### Phase 16 Alignment with SPEC-GOV-004 Benchmark Suites

Each row maps one-to-one to [SPEC-GOV-004: Benchmark Suites](../governance/SPEC-GOV-004-benchmarking-plan.md#benchmark-suites), in the same order and with the same priority. `Partial` means implementation or local evidence exists but the full declared scope remains open; `Planned` means dedicated benchmark coverage remains to be implemented. Completion requires retained artifacts and the applicable cross-cutting criteria below. P0/P1/P2 are the plan's priorities, separate from the initial suite's High/Medium implementation priorities.

The [P0–P1 implementation plan v2](../benchmarks/plans/v2.md) defines concrete matrices, runner changes, numerical/statistical gates, delivery batches and campaign acceptance for the first seven rows. Agreed scaling, MWIS/UDG and open-system targets extend through 20 atoms with separate basis/representation resource limits. Scaling, ablation, GPU, MWIS, solver and observable runner implementation is complete; execution and acceptance are tracked below. Other expanded matrices remain planned measurements until their evidence is retained. P2 noise/cluster work retains its Phase 14/18 dependencies and is outside that plan.

| GOV-004 suite | Priority | Status | Implemented / retained scope | Remaining work and acceptance evidence |
| :--- | :---: | :--- | :--- | :--- |
| `scaling` | P0 | Done (bounded local v2 matrix) | [Retained v2 campaign](../benchmarks/evidence/p0-scaling-v2-2026-11-26/README.md): 42/42 scenarios through N=20, 210 eligible measurements, 24 independent projected-dense checks and 18 tighter-tolerance checks. JSON/CSV/Markdown, per-repeat results/manifests, process memory, exact config/source/runtime provenance, golden-test logs and audited checksums are retained. | Runner implemented; declared local campaign executed; automated acceptance audit passed. Recurring RC reruns (including ablation), independent governance review and public performance/release approval remain open. Large-system evidence is same-method sensitivity, not physical full-space equivalence. |
| `ablation` | P0 | Done (bounded local CPU/CUDA v2 cases) | [Retained v2 campaign](../benchmarks/evidence/p0-ablation-v2-2026-11-27/README.md): 16/16 targeted CPU paths, 80 eligible batches at N=4,8,12 plus both reduced paths at N=16,20 (N=20 D=17711). Fixed-input Python matvecs, independent references/gates, construction, per-path memory, saved-output audit, companions and golden-test logs retained. All 25 declared rows accounted for, including four full-dimension exclusions and five optional CUDA skips. | CPU acceptance audit passed; [optional CUDA follow-up](../benchmarks/evidence/p0-ablation-cuda-v2-2026-11-27/README.md) passed all five chain sizes through N=20 with 25 measured matched-CPU ODE pairs, saved results/manifests and hardware/golden evidence. Original skip rows remain historical. No matvec/solve or solve ratio. Full P1 GPU coverage, recurring RC, physical approximation validation and public performance/release approval remain separate. |
| `gpu` | P1 | Done (bounded local v2 matrix) | [Retained eight-case campaign](../benchmarks/evidence/p1-gpu-v2-2026-11-27/README.md): chains N=2,4,8,12,16,20 (N=20 D=17711), 2x2 lattice and seeded two-node MWIS. All 40 measured CPU/CUDA pairs and all 64 first/warm/measured pairs passed full-grid/configuration gates. Separate CPU/CUDA workers retain attributable memory, initialized diagnostics, 128 saved result/manifest sets, qualified median ratios and audited companions/source/runtime hashes. The legacy small protocol shares these helpers and preserves its stems/ILP reference. | Runner implemented; declared local campaign executed; automated acceptance audit passed. CUDA remains experimental; GPU peak unavailable. Shared-workstation timing, same-method parity, physical approximation validation, recurring RC and independent public performance/release approval remain separate. |
| `mwis_udg` | P1 | Done (bounded local v2 matrix) | [Retained 40-instance campaign](../benchmarks/evidence/p1-mwis-v2-2026-11-27/README.md): N=2,4,6,8,10,12,16,20 with seeds 101–105 per size. All 200 measured AQC and 200 measured ILP calls passed; 320 AQC results/manifests and 320 exact CBC references retain first/warm/measured evidence. All five N=20 instances executed (D=9240–53760). Independent DOP853/refinement/raw-norm and exhaustive graph/ILP/quality checks, separate path memory/phases, hashes and complete companions are audited. Initial fixture IDs/three-tier outputs and raw tuple semantics are preserved. | Runner implemented; declared local campaign executed; original/relocated automated acceptance passed. Poor feasible AQC objectives remain data; no optimum-hit threshold. Five seeded graphs are bounded workloads, not a distribution-wide quality statement. CBC subprocess peak unavailable; methods have different guarantees and no timing speedup is derived. Broader schedules/families, scientific validation, recurring RC and public approval remain separate. |
| `solver` | P1 | Done (bounded local sensitivity matrix) | [Retained 39-configuration campaign](../benchmarks/evidence/p1-solver-v2-2026-11-27/README.md): analytic Rabi, addressed chain and linear ramp; paired Tsit5/Vern9 tolerances, RK4 steps, explicit grids and combined controls. All 312 results/manifests audited; 38 configurations/190 measured calls meet 1e-6. Stable independent references, raw norm/effective settings, per-process memory and recomputable error/runtime companions retained. | Runner implemented; all 39 executed; local characterization acceptance passed. Coarse ramp RK4 T/100 retains five ineligible measured calls and failed accuracy status; full-matrix all-accuracy-pass is false. Physical/model validation, broader stiffness/scenarios, recurring RC and public approval remain separate. |
| `observables` | P1 | Done (bounded local v2 matrix) | [Retained 52-cost/12-fixture campaign](../benchmarks/evidence/p1-observables-v2-2026-11-27/README.md): N=4,8,12,16,20 reduced chain, all ten types, counts 1/4/16/64, grids 21/101/501 and original/reverse/permuted order. All 260 measured calls and 476 saved results/manifests pass; small full/reduced static/evolving/Lindblad/five-seed MCWF references, raw samples, two empty-history controls, cross-order equality, worker memory, source/runtime and companions audited. | Runner implemented; full matrix executed; original/relocated acceptance passed. Duplicates are labeled collection workloads; timings include construction/collection/manifest. No incremental-overhead estimator, off-diagonal/CUDA support, physical/model validation, expanded open-system convergence, recurring RC or public approval follows. |
| `open_system` | P1 | Partial | `benchmark_phase16_validation.py` retains one-atom analytic decay, Lindblad trace/positivity, and fixed-seed 100/500-trajectory MCWF agreement. | Execute the [v2 local-noise matrix](../benchmarks/plans/v2.md#p1-open-system) through N=20 with independent Lindblad/MCWF resource budgets, repeated runtime/memory, seed/output-grid metadata, multi-seed convergence, trace/positivity and dephasing references, and linked manifests/results. Retain exclusions, failures and large-case reference limitations; multi-atom decoherence-impact conclusions remain separate from cost characterization. |
| `noise` | P2 | Planned; depends on Phase 14 | Current baseline is local Markovian decay/dephasing; custom/structured channels and stochastic Hamiltonian ensembles remain planned. | After relevant Phase 14 models and Phase 15 reproducibility contracts are available, benchmark custom Lindblad, correlated noise, collective decay, and stochastic-ensemble overhead. Retain noise parameters, requested/effective seeds and realization counts, runtime/memory, numerical references, and unsupported-combination failures. |
| `cluster_sweep` | P2 | Partial; advanced deployment depends on Phase 18 | `benchmark_sweep_cluster.py` retains local deterministic parameter-map throughput, checkpoint/resume behavior, per-item artifacts, and suite aggregation. | Preserve the completed local baseline. Extend to physics-solver workloads and, in Phase 18, declared multi-node deployments; retain config hashes, worker/backend diagnostics, correctness, failures, restart behavior, and repeated throughput statistics. Local mapping results do not establish physics-solver or multi-node scalability. |

### Phase 16 Alignment with SPEC-GOV-004 Cross-Cutting Requirements

These requirements apply to every relevant suite. Release-cadence actions recur for each triggering event rather than becoming permanently complete after one run. GOV-004 remains authoritative for policy and wording; this table records implementation/evidence status and closure conditions.

The [v2 shared measurement implementation](../benchmarks/plans/v2.md#shared-measurement-implementation) and [completion checklist](../benchmarks/plans/v2.md#completion-recurring-runs-and-maintenance) operationalize the P0–P1 work below. Defaults of two warmups and at least five independent repeats, frozen statistical seed sets, explicit timer/memory scope and retained resource failures are planned campaign acceptance requirements; the retained scaling, ablation, GPU, MWIS, solver and observable campaigns implement and audit these controls. Other P1/P2 runners still require the listed implementation and evidence audits. Track runner implementation, campaign execution and evidence acceptance separately.

All first seven suites must deliver the [v2 runtime outputs](../benchmarks/plans/v2.md#runtime-reporting-requirements-for-all-seven-suites):
per-configuration raw wall times, declared timer/cache/output scope, eligible
counts/member IDs and median/min/max/p25/p75 with matching companion tables.
Suite-specific acceptance adds matched CPU/CUDA distributions and qualified
ratio, per-instance AQC/ILP phase statistics/termination, solver error-versus-time,
observable collection/storage context, and separate Lindblad/MCWF time plus
MCWF throughput and convergence. Correctness-only/rejection tests are exempt
from a dedicated timing campaign. The [P0 timing report](../benchmarks/reports/p0-runtime-statistics-2026-11-27.md)
recomputes existing 210 scaling calls, 80 CPU batches and 25 CPU/CUDA pairs;
it changes no suite milestone or original archive and requires no simulation
rerun. Shared-workstation timings remain local diagnostics, not a current-code
or controlled performance baseline; recurring RC and affected-scope reruns remain.

| GOV-004 section | Current status | Remaining work / acceptance condition |
| :--- | :--- | :--- |
| [Goals](../governance/SPEC-GOV-004-benchmarking-plan.md#goals) and [Benchmark Layers](../governance/SPEC-GOV-004-benchmarking-plan.md#benchmark-layers) | Initial correctness/application evidence retained; performance characterization partial. | Track software/numerical verification separately from scientific validation. Complete declared suite measurements before claiming runtime, memory, observable-cost, or scaling coverage. Initial closure establishes no general quantum speedup, production CUDA, or hardware-control capability. |
| [Required Row Metadata](../governance/SPEC-GOV-004-benchmarking-plan.md#required-row-metadata) | Contracts and writers implemented; all-runner/scenario completeness remains to be audited. | Audit applicable scenario/geometry/basis/pruning, pulse, requested/effective solver and output grid, backend/device/doctor, observable declarations/count/samples, noise/trajectory/seed, timing/memory/repeat/warmup/statistics, versions/commit/dirty state, and result/manifest/report links. Preserve unavailable values explicitly; incomplete measurement evidence remains diagnostic. |
| [Running Discipline](../governance/SPEC-GOV-004-benchmarking-plan.md#running-discipline) | V2 scaling, ablation, GPU, MWIS, solver and observables retain two warmups/five independent measurements with audited per-configuration statistics. Other suites remain partial; historical initial solver/CUDA rows retain their earlier repeat policy and are not pooled with V2 campaigns. | Apply recommended 1–3 warmups and at least 5 measured repeats for runtime claims; retain median/min/max/p25/p75, distinct cold/warm timings where material, and fixed seeds. Operations within one timed matvec batch are not independent run repeats. Name both environments for cross-machine comparisons. |
| [Correctness Gates](../governance/SPEC-GOV-004-benchmarking-plan.md#correctness-gates) | Small analytic/projected-dense, CPU/CUDA, open-system, and exact-MWIS references retained; cross-language golden tests exist. | Before promoting each measured scenario, retain applicable numerical/parity gates and matching Python/Julia golden-test evidence. A projected dense reference verifies reduced implementation, not general physical equivalence to finite-interaction full-space evolution; approximation claims need their own error budget. Solver-sensitive cases require tighter-tolerance or smaller-step references. |
| [Visualization and Report Outputs](../governance/SPEC-GOV-004-benchmarking-plan.md#visualization-and-report-outputs) | Governed benchmark plot/export validation and diagnostic-only helpers implemented. | For each report, retain source artifact links/IDs and validate complete evidence. Charts, fitted curves, sidecars, and caller-selected classifications do not replace benchmark or disclosure review. |
| [Reporting Rules](../governance/SPEC-GOV-004-benchmarking-plan.md#reporting-rules) | Initial archive is reviewable local evidence only; `DISC-0002` is an internal Draft. | Before public use, attach exact artifacts, commit/versions, hardware/backend/container, scenario/solver configuration, metric names, bounded wording, and performance/disclosure/prior-art review. Roadmap alignment does not imply public performance approval. |
| [Release Cadence](../governance/SPEC-GOV-004-benchmarking-plan.md#release-cadence) | Recurring; initial closure is not a complete P0 RC campaign. | For affected PRs run appropriate smoke/sanity checks; for each RC run/archive both P0 suites (`scaling`, `ablation`) and verify companions; for public reports attach reviewed provenance. Hardware/backend or solver/observable/seed/noise/schema changes trigger the corresponding diagnostics and suite reruns. |
| [Roadmap Alignment](../governance/SPEC-GOV-004-benchmarking-plan.md#roadmap-alignment) | Initial suite closed; broader plan partial with Phase 14/18 dependencies. | Track noise prerequisites in Phase 14, reproducibility contracts in Phase 15, and advanced deployment/physics-sweep coverage in Phase 18. API availability in Phase 11/12/15 does not itself close the related performance suite. |
| [Maintenance Triggers](../governance/SPEC-GOV-004-benchmarking-plan.md#maintenance-triggers) | Ongoing. | Update these matrices, the P0–P1 implementation plan, GOV-004, benchmark protocol/family/tier/artifact documents, the benchmark index, and documentation status triggers together when applicable scope/status, runners, artifacts, execution or release/disclosure requirements change. Record retained evidence before advancing completion status. |

### Phase 16 Benchmark Families

This taxonomy describes broader target scenarios. Implemented and retained coverage, including deferred extensions, is tracked in the alignment matrices above and in [Benchmark Families](../benchmarks/families.md).

| Family | Initial scenarios | Primary evidence |
| :--- | :--- | :--- |
| **Physics baselines** | Single-atom Rabi, two-atom blockade, Landau-Zener sweep, dense-vs-reduced small chains. | Analytic/dense-reference errors, basis sizes, pruning ratios, solver metadata, artifact output. |
| **Cold-atom dynamics** | Rydberg chain excitation profiles, local addressing, Z2 ordering, 2D pattern formation. | Observable trajectories, correlations, blockade violations, solver/backend metadata. |
| **Open-system dynamics** | Lindblad decay/dephasing, MCWF-vs-Lindblad, decoherence impact on blockade/ordering. | Trace/positivity checks, trajectory variance, runtime/memory scaling, seed metadata. |
| **Optimization/AQC** | UDG/MWIS, weighted MWIS, schedule sensitivity, planted or structured graph families. | Feasibility, exact optimum where available, objective value, approximation ratio, success probability when sampling lands. |
| **Backend performance** | Dense/sparse/reduced ablation, CPU/CUDA parity, solver method sensitivity, CUDA cached path. | Runtime, memory, GPU memory where available, max trajectory error, speedup with bounded wording. |
| **Sweep/cluster execution** | Parameter sweeps, phase-diagram scans, cluster throughput. | Jobs/sec, resumability, per-run manifest links, aggregate artifacts, failure rows. |

### Phase 16 Benchmark Tiers

1. **Smoke tier**: small systems, one or two seeds, CPU-first, fast enough for local or optional PR validation.
2. **Correctness tier**: small and medium systems with analytic, dense, or exact ILP baselines.
3. **Parity tier**: CPU/CUDA or solver-method comparisons with fixed seeds, shared schedules, and bounded tolerances.
4. **Scaling tier**: increasing size, density, basis size, or trajectory count until timeout, memory pressure, or numerical failure.
5. **Stress tier**: local hardware-specific exploration such as RTX 5070 Ti CUDA scale limits; these results are not public claims unless promoted through governance review.

### Phase 16 Initial Suite Acceptance Criteria (Closed)

These eight criteria describe the retained initial closure. Full-plan completion additionally requires the applicable suite and cross-cutting acceptance evidence above.

1. Benchmark documentation explains suite taxonomy, benchmark tiers, required metadata, artifact layout, and the difference between exploratory local results and release-grade evidence.
2. Each benchmark family emits machine-readable aggregate artifacts plus linked run manifests or result artifacts where simulations are produced.
3. Physics baseline benchmarks include analytic, dense, or reduced-reference correctness checks with stable tolerances.
4. MWIS/UDG benchmarks include seeded instance generation, graph metadata, exact ILP baselines where tractable, feasibility checks, objective metrics, and failure rows.
5. CUDA benchmark protocols record initialized CUDA doctor metadata, CPU/CUDA parity evidence where tractable, GPU device/driver/runtime metadata, and local hardware caveats.
6. Benchmark failures are preserved in aggregate outputs with diagnostic codes and enough context to audit scale-limit conclusions.
7. Public benchmark or performance statements cite artifact IDs, commit SHA, hardware/runtime metadata, and applicable disclosure/performance-claim reviews.
8. Benchmark scripts remain optional for ordinary PR CI unless explicitly designated as smoke-tier checks.

## 🧩 Phase 17: Experimental Interop & Readout Models (Future)
| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Readout Noise and Detection Error Models** | Medium | Future | Add optional shot-level readout error models for false positives, false negatives, atom loss, and confusion-matrix style post-processing. Readout errors must be explicitly opt-in and recorded in manifests and result artifacts. |
| **External Neutral-Atom Tool Interop** | Low | Future | Explore bounded import/export workflows for neutral-atom schedules, geometries, or pulse descriptions used by tools such as Pulser, Bloqade-style workflows, or hardware-provider formats. Any interop claims must follow prior-art and disclosure controls and must not imply Sagittarius is a calibrated hardware control stack. |
| **Hardware-Oriented Schedule Export** | Low | Future | Provide an optional export format for reviewed, simulation-derived schedules with unit metadata, pulse definitions, and backend diagnostics. Exported schedules are for review and translation, not direct hardware execution without a vendor calibration layer. |

### Phase 17 Acceptance Criteria

1. Readout error models are opt-in, parameterized, validated, and recorded in reproducibility metadata.
2. Interop import/export paths preserve units, atom ordering, pulse timing, and unsupported-feature diagnostics.
3. Documentation distinguishes simulation artifacts from hardware-control artifacts and passes governance review before public interop claims.

## 🔬 Phase 18: HPC & Advanced Deployment (Future)
- **Slurm Integration**: Native support for `ClusterManagers.jl` to manage multi-node jobs.
- **MPI Backend**: Distributed-memory Hamiltonian evolution for $N > 40$ atoms.
- **Cluster and Sweep Benchmarks**: Extend Phase 16 benchmark workflows for cluster execution, parameter-sweep throughput, resumability, artifact aggregation, and hardware/backend-specific diagnostics. Public claims must follow `docs/governance/SPEC-GOV-004-benchmarking-plan.md` and `docs/governance/SPEC-GOV-001-performance-claims.md`.
- **C++ FFI**: Direct bindings for C++ applications to leverage the Julia engine.
- **Web Dashboard**: Interactive results explorer for large-scale sweeps.

---

## 📊 Phase 19: Visualization & Reporting API (Done)

Phase 19 adds a user-facing visualization and lightweight reporting layer on top of existing Sagittarius data, metadata, manifests, and artifacts. The goal is to make common experiment and analysis views easy to produce without weakening the separation between simulation data, reproducibility metadata, and public benchmark claims. Visualization helpers should prefer backend-free data extraction and plotting from Python objects or saved artifacts; they must not imply hardware calibration or performance evidence unless linked to governed artifacts.

| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Visualization API Contract** | High | Done | The canonical `SPEC-API-006` reference documents public helpers, extractor/plotter separation, return types, acceptance evidence, persisted sweep-artifact resolution, benchmark-evidence boundaries, and backend-free behavior. |
| **Register Layout Visualization** | High | Done | Add backend-free helpers such as `plot_register(register, blockade_radius=None, edges=True, labels=True, ax=None)` for 2D atom layouts, topology metadata, atom labels, UDG/blockade edges, and selected-bitstring overlays where applicable. 3D register visualization may be optional or explicitly limited. |
| **Pulse Waveform Sampling and Plots** | High | Done | Add deterministic pulse sampling helpers for `PulseSequence` omega/delta waveforms over an explicit time grid, including global, local vector, dict, callable, and Pulse AST inputs where supported. Plot helpers should support selected atoms, fields, axes injection, and return sampled data plus matplotlib axes without unexpectedly initializing Julia unless required by a documented Pulse AST path. |
| **Observable Trajectory Plot Improvements** | Medium | Done | Extend `SimulationResult.plot()` or add `plot_observables(result, names=None, ax=None, show=False)` so users can select series, pass axes, receive matplotlib objects, and preserve backward compatibility with existing observable trajectory plots. |
| **Population Heatmap Visualization** | Medium | Done | Add helpers for atom-by-time population heatmaps using Rydberg-population observable metadata or conventional population series names, with explicit atom ordering and missing-series diagnostics. |
| **Bitstring Distribution Visualization** | High | Done | Final-state probability plots support readout-capable results and reduced-basis metadata. A `save()` → `load_result()` → plot regression validates the persisted artifact path. |
| **Shot Count Histogram Visualization** | High | Done | Add helpers to plot `measurement-samples/v1` outputs from `SimulationResult.sample(shots, seed=...)`, including counts/frequencies, shot count, seed metadata, and consistent bitstring ordering. |
| **MWIS/UDG Result Visualization** | Medium | Done | Add optional helpers for UDG/MWIS workflows that overlay selected bitstrings, weights, graph edges, and constraint violations on register layouts. These helpers should support experiment recipes and Phase 16 benchmarks without making optimization-performance claims by themselves. |
| **Basis and Reduced-Basis Visualization** | Medium | Done | Add small-system helpers to inspect represented basis bitstrings, forbidden bitstrings, full-vs-reduced basis sizes, pruning ratio, and the relationship between blockade edges and reduced-basis validity. These views should be clearly marked as diagnostic and should preserve Sagittarius bitstring ordering. |
| **Interaction and Blockade Graph Visualization** | High | Done | Add backend-free plots or data helpers for atom pair distances, van der Waals interaction matrices, blockade adjacency, and UDG graph overlays. These diagnostics should help users validate geometry, units, and blockade-radius choices before expensive solver runs. |
| **Correlation Matrix Visualization** | Medium | Done | Add helpers for pair-correlation, connected-correlation, Pauli-ZZ, and blockade-violation matrix or edge heatmap views when the result contains compatible observable series or metadata. Missing observables should produce actionable diagnostics rather than silent empty plots. |
| **Time-Resolved Spatial Population Views** | Medium | Done | Add spatial snapshots and optional small-multiple or animation-ready data helpers that color atoms by population or selected observable value at one or more output times. Animation may remain optional, but the extracted frame data should be stable and artifact-compatible. |
| **Solver and Open-System Diagnostic Plots** | Medium | Done | Add diagnostic views for output grids, saveat samples, Lindblad trace/positivity checks, MCWF-vs-Lindblad comparisons, and trajectory mean/variance or confidence bands where the underlying data are available. These should support Phase 14 and Phase 16 validation workflows without replacing numerical verification. |
| **Parameter Sweep Visualization** | Medium | Done | `sweep-artifact/v1` extractors resolve persisted result paths into two-axis metric grids while preserving parameter axes, per-item statuses, failed-run masks, failure records, result paths, manifest links, and resumability metadata. The exploratory contract remains separate from governed benchmark evidence. |
| **Benchmark Plotting Helpers** | Medium | Done | Public performance plotting and MWIS benchmark export accept only validated `benchmark-artifact/v1` envelopes or JSON paths. Explicit `plot_diagnostic_*` and `save_diagnostic_mwis_figure` helpers accept caller mappings and remain non-claim diagnostic tools. |
| **State Vector and Density-Matrix Diagnostics** | Low | Done | Add small-system debug views for state probability vectors, density-matrix diagonals, density-matrix magnitude heatmaps, and phase heatmaps. These helpers should be explicitly limited to small Hilbert spaces and should fail clearly when data are unavailable or too large. |
| **Figure Export and Report Bundles** | Low | Done | Add convenience helpers for saving PNG/SVG/PDF figures and optional metadata sidecar JSON. Exported figures should retain enough metadata to identify source result artifacts, schema versions, seeds, backend, basis mode, and plot parameters. |
| **Artifact-Aware Reporting** | Medium | Done | Add lightweight report helpers that summarize result artifacts with plots, schema versions, backend/runtime metadata, basis mode, seed/output-grid metadata, and linked manifests. Reports must distinguish exploratory visualization from benchmark or public-claim evidence. |
| **Documentation and Examples** | High | Done | The canonical API contract, task-oriented saved-result and pre-solver visualization examples, governance boundaries, artifact round-trip coverage, and backend-free regression are documented and tested. |

### Phase 19 Visualization Tiers

1. **P0 basic views**: register layout, interaction/blockade graph, pulse waveform, observable trajectory, final bitstring distribution, sample-count histogram, and final bitstring overlay on register.
2. **P1 scientific diagnostics**: population heatmaps, basis-pruning views, pair/connected-correlation matrices, open-system sanity plots, time-resolved spatial population frames, and parameter-sweep heatmaps.
3. **P2 reporting and advanced views**: benchmark artifact plots, artifact-aware report bundles, animation-ready helpers, state-vector/density-matrix diagnostics, and figure export sidecars.

### Phase 19 Acceptance Criteria

1. Users can plot a 2D register layout with atom labels and optional UDG/blockade edges without initializing Julia.
2. Users can sample and plot omega/delta waveforms over an explicit time grid for supported pulse declaration forms, with local addressing shown in register order.
3. Observable trajectory plotting supports selecting series, passing matplotlib axes, returning axes or figure objects, and preserving existing `SimulationResult.plot()` behavior.
4. Users can plot atom-by-time Rydberg population heatmaps when the result contains compatible population series or observable metadata.
5. Users can plot final bitstring probability histograms from readout-capable results loaded directly or through `load_result()`.
6. Users can plot seeded shot-count or frequency histograms from `measurement-samples/v1` sample outputs.
7. Reduced-basis visualizations clearly identify represented bitstrings and forbidden-bitstring exclusion metadata.
8. MWIS/UDG visualizations can overlay selected nodes, weighted nodes, graph edges, and violation edges for small examples.
9. Visualization helpers separate data extraction from plotting wrappers and return reusable Python objects suitable for notebooks, scripts, and saved figures.
10. Visualization documentation explains that plots are analysis/reporting aids; benchmark or performance claims still require governed benchmark artifacts and disclosure controls.
11. Users can inspect basis pruning, represented bitstrings, forbidden bitstrings, interaction matrices, and blockade adjacency for small systems before running a solver.
12. Users can visualize pair/connected correlations, Pauli-ZZ correlations, or blockade-violation structure when compatible observable data exist.
13. Users can create time-resolved spatial population snapshots or frame data with atom positions, values, and time metadata preserved.
14. Users can visualize open-system diagnostics such as trace error, positivity metrics, Lindblad-vs-MCWF comparisons, or trajectory uncertainty bands when those reports provide the required data.
15. Parameter-sweep visualizations preserve parameter axes, failed-run masks, result artifact paths, and run-manifest links.
16. Benchmark plotting helpers consume governed benchmark artifacts or retained evidence and do not turn local ad hoc timings into project performance claims.
17. Small-system state-vector and density-matrix diagnostic plots fail clearly for missing data or unsafe Hilbert-space sizes.
18. Figure export helpers can save plots with optional metadata sidecars that identify source artifacts, schema versions, seeds, backend, basis mode, and plot parameters.
19. Automated tests use a non-interactive matplotlib backend and cover smoke rendering, input validation, artifact round trips, reduced-basis bitstring handling, and no-unexpected-backend-initialization paths where applicable.

---

## 🛠️ Maintenance & Verification
All features are verified via the `tests/` and `sagittarius_py/tests/` suites.
Run the full verification: `cd sagittarius_py && uv run python -m pytest tests/`
For Phase 5 lightweight runtime checks: `cd sagittarius_py && uv run python -m pytest tests/test_runtime_hardening.py tests/test_serialization.py`
