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
| **Source Installation Baseline** | High | Done | Defines the currently supported installation model as a complete repository checkout followed by `uv sync` and `python -m juliapkg resolve`. Documents `pip install -e .` as a development-only editable install that still depends on the repository layout, and explicitly states that an independent PyPI installation is not yet supported. |
| **Relocatable Wheel** | High | Mixed | Local wheel artifacts contain the embedded Julia backend and pass repo-external package-resource, clean-venv, and uninstall/reinstall smoke coverage. Full production release status remains gated on CUDA hardware evidence and release approval. |
| **Package Resource Lookup** | High | Done | Replaces direct repository-relative backend discovery with a centralized lookup that prefers the explicit `SAGITTARIUS_JULIA_BACKEND_PATH` environment override, then an editable/source checkout backend, then installed-package resources; diagnostics report `env_override`, `source_checkout`, or `package_resource`. |
| **Julia Package Data** | High | Done | Includes `Sagittarius.jl/Project.toml`, `Manifest.toml`, Julia source files, and runtime metadata as Python package data under `sagittarius/julia/Sagittarius.jl/`, with artifact tests verifying wheel and source distributions contain the embedded backend. |
| **CPU-First Dependency Profile** | High | Done | Default `juliapkg.json` and the embedded Julia backend project now resolve CPU-required Julia packages without CUDA.jl, an NVIDIA driver, or GPU hardware. CUDA is split into the packaged opt-in `juliapkg-cuda.json` profile for future backend setup workflows. |
| **Optional GPU Backend Profiles** | High | Mixed | The CUDA profile is complete: `juliapkg-cuda.json` carries `backend-profile/v1` metadata, is excluded from default CPU resolution, appears in `sagittarius backend profiles`, supports `sagittarius backend install cuda --dry-run`, and is installable through `sagittarius backend install cuda`. Later AMDGPU/Metal profiles remain planned. |
| **Backend Setup Command** | Medium | Done | Adds the `sagittarius` console script with `sagittarius backend resolve`, `sagittarius backend install cuda`, and `sagittarius doctor`. Commands emit JSON setup/diagnostic reports and normalize setup failures to actionable diagnostic messages. |
| **CUDA Wheel Smoke and Parity** | High | Mixed | Added a hardware-gated clean-venv CUDA wheel smoke and manual self-hosted CUDA workflow. The smoke installs the wheel, runs `sagittarius backend install cuda`, runs initialized CUDA doctor diagnostics, executes a small CPU/CUDA parity simulation, and verifies CUDA.jl, driver, runtime, device, backend source, result artifact, manifest, and diagnostics metadata. Release validation still requires execution evidence on real NVIDIA GPU hardware. |
| **Clean-Environment Artifact Tests** | High | Done | Artifact tests verify wheel/sdist contents, and `SAGITTARIUS_RUN_RELEASE_ARTIFACT_SMOKE=1` clean-venv release smokes install the wheel, run `sagittarius backend resolve`, execute a one-atom CPU simulation, validate result artifact, manifest, doctor, version metadata, source-tree import isolation, and verify uninstall/reinstall behavior in a repo-external environment. The smokes are wired into Ubuntu CI. |
| **Cross-Platform Installation Matrix** | High | Mixed | `docs/getting-started/python/compatibility-matrix.md` and manual `.github/workflows/phase13-cross-platform.yml` cover Linux Python 3.10/3.11/3.12 with Julia 1.10.3/1.11 plus macOS and Windows CPU wheel smokes on Python 3.11/Julia 1.11. All five declared rows passed in GitHub Actions run `28577379030`, with retained evidence artifacts under `CI_artifacts/phase13-cross-platform-*`. |
| **CI Clean Artifact Isolation** | High | Done | Clean wheel and uninstall/reinstall smokes run in GitHub Actions as release gates. Day-to-day PRs use a separate fast CI workflow. Detailed trigger policy and evidence retention rules live in `docs/reference/ci-workflows.md`. |
| **Uninstall/Reinstall Smoke Coverage** | Medium | Done | Added a release-artifact smoke test that installs the wheel, runs backend resolution and a minimal CPU simulation, uninstalls the wheel, verifies `sagittarius` is no longer importable, reinstalls the same wheel outside the source checkout, and verifies package-resource backend metadata, JuliaPkg resolution behavior, and a minimal CPU simulation after reinstall. |
| **Package Metadata Review** | Medium | Done | PyPI-facing metadata now includes README rendering, MIT license expression and license file inclusion, production/stable and supported Python classifiers, scientific classifiers and Julia-backend metadata, author field, keywords, project URLs, console script metadata, and artifact content checks. Packaging tests inspect wheel/sdist metadata and run `twine check` over built artifacts. |
| **TestPyPI and Publication Policy** | Medium | Mixed | Added a TestPyPI publication policy document and manual `.github/workflows/phase13-testpypi.yml` workflow protected by the `testpypi` environment. It verifies built versions, publishes through OIDC trusted publishing without `skip-existing`, verifies a clean TestPyPI install plus a one-atom CPU simulation and result artifact, and retains versioned evidence artifacts. The TestPyPI `1.0.0` candidate has clean-install evidence but predates the CPU-smoke gate; production PyPI remains blocked until CUDA hardware evidence and repository visibility/publication policy are approved. |
| **PyPI Release Readiness** | High | Mixed | PyPI publication remains blocked. Fast PR CI, local artifact readiness checks, CPU-first dependency behavior, backend setup commands, Ubuntu clean artifact and reinstall CI coverage, gated CUDA wheel smoke, package metadata checks, TestPyPI workflow/policy, and retained cross-platform matrix pass evidence now exist, but publication approval and GPU runner evidence are still required. |
| **Installation Documentation** | Medium | Done | Documentation distinguishes source/editable setup, local wheel/sdist artifact status, backend source selection, release artifact smoke testing, uninstall/reinstall verification, released-wheel upgrade/uninstall guidance, cross-platform matrix workflow, and PyPI publication gates. |

### Phase 13 CI and Release Automation

| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Fast PR CI** | High | Done | `.github/workflows/pr-fast-ci.yml` runs lightweight docs, benchmark-artifact, and packaging metadata/content checks automatically for pull requests to development and release branches, plus direct pushes to `develop/**` as a fallback. |
| **Clean Artifact Release Smoke** | High | Done | `.github/workflows/phase13-clean-artifact.yml` runs clean wheel install and uninstall/reinstall smokes automatically on relevant pushes to `main` and manually on demand. |
| **Cross-Platform Matrix Evidence** | High | Done | `.github/workflows/phase13-cross-platform.yml` remains manual and uploads per-row OS/Python/Julia evidence artifacts. GitHub Actions run `28577379030` passed all five declared rows, and retained artifacts are stored under `CI_artifacts/phase13-cross-platform-*`. |
| **TestPyPI Publication Evidence** | Medium | Mixed | `.github/workflows/phase13-testpypi.yml` successfully published and clean-installed the `1.0.0` candidate through the protected OIDC path. The strengthened workflow now also requires an installed-package one-atom CPU simulation and result artifact, so the next frozen candidate must retain new `phase13-testpypi-<version>` evidence before production publication. |
| **CUDA Hardware Evidence** | High | Mixed | `.github/workflows/phase13-cuda-wheel.yml` remains manual on a self-hosted CUDA runner and retains GPU name/driver/memory, smoke log, and run metadata in a `phase13-cuda-wheel-<run-id>` artifact; CUDA wheel support is release-validated only after this hardware-backed evidence passes. |
| **CI Documentation** | Medium | Done | `docs/reference/ci-workflows.md` defines automatic workflows, manual release gates, evidence retention, and maintenance rules. |

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

### Phase 13 PyPI Readiness Completion Plan

Before any public PyPI upload, complete these remaining blockers:

1. CPU-first dependency profile: Done. Default JuliaPkg and backend project metadata resolve CPU-required packages without CUDA.jl; CUDA is available only through the packaged opt-in profile.

2. Backend setup commands: Done. `sagittarius backend resolve`, `sagittarius backend install cuda`, and `sagittarius doctor` provide the documented command path; CUDA setup remains explicit and opt-in.

3. CI and release automation: Done for fast PR CI, clean artifact smoke, CI documentation, and retained cross-platform matrix evidence. The TestPyPI `1.0.0` clean-install gate has passed, while the strengthened CPU-smoke gate must pass on the next frozen candidate; the CUDA workflow remains a manual release gate until retained real-hardware evidence passes. See `docs/reference/ci-workflows.md`.

4. Uninstall/reinstall smoke coverage: Done. The release-artifact smoke installs the wheel, resolves the backend, runs a minimal CPU simulation, uninstalls the package, verifies it is no longer importable, reinstalls the same wheel outside the source checkout, and verifies backend source detection, JuliaPkg resolution, artifact metadata, and minimal CPU simulation after reinstall.

5. Package metadata review: Done. Wheel/sdist metadata tests inspect README, license, classifiers, URLs, package data, and `twine check` output.

6. TestPyPI and publication policy:
   - Manual TestPyPI workflow and publication policy are in place.
   - The protected OIDC workflow published and clean-installed the TestPyPI `1.0.0` candidate. The strengthened workflow now also requires an installed-package CPU simulation and result artifact; run it on the next frozen candidate and retain its evidence artifact. The version-pinned dual-index command remains a release-candidate installation path only.
   - Approve repository visibility, issue tracker/docs readiness, MIT license publication, and accidental-upload controls before production release.
   - Acceptance: production PyPI upload remains blocked until CUDA hardware evidence and the open-source/publication policy are approved.

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
| **Executable Experiment Recipes** | High | Planned | Provide user-facing runnable examples with expected outputs and artifact generation, including single-atom Rabi, two-atom blockade, Landau-Zener sweep, open-system decay/dephasing, and small UDG/MWIS workflows. Benchmark-grade promotion of these recipes belongs to Phase 16. |
| **Wheel-Installed Experiment Recipes** | Medium | Planned | Add external-user recipes that run from an installed wheel outside the source checkout, starting with a small UDG/MWIS workflow using only public `sagittarius` APIs and ordinary Python dependencies. Repo-local `projects/` scripts may remain source-checkout examples, but wheel recipes must not depend on project files being packaged. |
| **State Preparation Helpers** | Medium | Planned | Add helpers for common initial states, including all-ground state, named bitstring states, single-excitation states, and optional uniform superpositions. Helpers must validate full/reduced basis compatibility and preserve state-preparation metadata. |
| **Experiment Config Schema** | Medium | Planned | Define an `experiment-config/v1` schema that can describe register geometry, pulse schedule, solver options, observables/readout, seed controls, and output artifact paths. Provide load/run/save workflow and link generated run manifests back to the source config. |
| **Parameter Sweep API and Artifacts** | Medium | Planned | Add a user-facing parameter sweep workflow for `omega`, `delta`, `blockade_radius`, geometry, noise, solver settings, and observable declarations. Emit resumable sweep artifacts with per-run manifest links, distinct from benchmark artifacts when the purpose is scientific exploration rather than performance measurement. |
| **Documentation Governance Requirements** | Medium | Planned | Treat stable SPEC IDs, metadata headers, `docs/status.md`, and Markdown link validation as required documentation maintenance checks for future roadmap phases and public release preparation. |

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

## 🧪 Phase 16: Benchmarking & Application Validation Suite (Planned)

Phase 16 turns the earlier cold-atom project backlog into a systematic benchmark and application-validation suite. Its purpose is to produce reproducible scientific and performance evidence for Sagittarius without mixing exploratory local studies with public claims. Public performance or hardware-facing conclusions from this phase must follow `docs/governance/SPEC-GOV-001-performance-claims.md`, `docs/governance/SPEC-GOV-002-disclosure-control.md`, and `docs/governance/SPEC-GOV-004-benchmarking-plan.md`.

| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Benchmark Taxonomy and Protocol Docs** | High | Done | Added `docs/benchmarks/` with a suite taxonomy, running instructions, artifact conventions, evidence-retention guidance, and interpretation rules that distinguish exploratory local results from release-grade benchmark evidence. |
| **Benchmark Artifact Contracts** | High | Planned | Define benchmark-family aggregate artifacts for application benchmarks, including case IDs, seeds, parameters, backend/runtime metadata, result artifact links, run manifest links, correctness metrics, performance metrics, failure diagnostics, and disclosure status. Reuse `benchmark-artifact/v1` where sufficient and version any new family-specific envelopes explicitly. |
| **Physics Baseline Benchmarks** | High | Planned | Promote single-atom Rabi oscillation, two-atom Rydberg blockade, Landau-Zener/adiabatic sweep, and small-chain full-vs-reduced validation into runnable benchmark tiers with expected output shapes, analytic or dense-reference checks, run manifests, and artifact output. |
| **Cold-Atom Dynamics Benchmarks** | Medium | Planned | Add Rydberg chain excitation profiles, local-addressing stress cases, Z2/antiferromagnetic ordering dynamics, and 2D array pattern-formation benchmarks that exercise pulse compilation, register geometry, observables, reduced bases, and solver-method metadata. |
| **Open-System Benchmarks** | Medium | Planned | Add Lindblad decay/dephasing scaling, MCWF-vs-Lindblad agreement, and decoherence-impact studies with trace/positivity checks, trajectory-count sensitivity, runtime/memory metrics, and reproducibility metadata. |
| **Optimization Benchmark Suite** | High | Planned | Promote UDG/MWIS and weighted MWIS workflows into benchmark tiers with exact ILP baselines for small instances, feasibility checks, objective/approximation metrics, schedule metadata, seed-controlled graph generation, and artifact-backed conclusions. |
| **MWIS/UDG GPU Benchmark Protocol** | High | Planned | Define and implement a local-first CUDA benchmark protocol for MIS/UDG scale limits, precision, speed, CPU/CUDA parity, GPU memory behavior, timeout/failure boundaries, and result interpretation on hardware such as the local RTX 5070 Ti. |
| **Solver and Backend Performance Benchmarks** | High | Planned | Standardize dense-vs-sparse-vs-reduced ablation, CPU/CUDA parity and speed, solver method sensitivity (`Tsit5`, `Vern9`, fixed-step `RK4`), GPU setup overhead, and CUDA cached sparse-buffer behavior. |
| **Parameter Sweep and Cluster Benchmarking** | Medium | Planned | Extend benchmark workflows for parameter-sweep throughput, resumability, artifact aggregation, and cluster execution using `ParallelSimulation`, while keeping benchmark artifacts distinct from user-facing experiment sweep artifacts. |
| **Benchmark Failure Reporting** | High | Planned | Record failed cases as first-class benchmark rows with failure stage, exception type, diagnostic issue code, backend probe, timeout, memory-at-failure where available, and remediation hints. Scale-limit conclusions must include failures, not only successful rows. |
| **Benchmark Documentation and Examples** | Medium | Planned | Provide concise examples for running smoke, correctness, parity, scaling, and stress tiers locally. Include guidance for CUDA-only local evidence, release-grade evidence, and how benchmark outputs should be cited in README, papers, demos, or release notes. |

### Phase 16 Benchmark Families

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

### Phase 16 Acceptance Criteria

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

## 📊 Phase 19: Visualization & Reporting API (Planned)

Phase 19 adds a user-facing visualization and lightweight reporting layer on top of existing Sagittarius data, metadata, manifests, and artifacts. The goal is to make common experiment and analysis views easy to produce without weakening the separation between simulation data, reproducibility metadata, and public benchmark claims. Visualization helpers should prefer backend-free data extraction and plotting from Python objects or saved artifacts; they must not imply hardware calibration or performance evidence unless linked to governed artifacts.

| Requirement | Priority | Status | Description |
| :--- | :---: | :---: | :--- |
| **Visualization API Contract** | High | Mixed | The canonical `SPEC-API-006` reference documents public helpers, extractor/plotter separation, return types, acceptance evidence, and explicit incomplete sweep, benchmark-evidence, and backend-initialization boundaries. |
| **Register Layout Visualization** | High | Done | Add backend-free helpers such as `plot_register(register, blockade_radius=None, edges=True, labels=True, ax=None)` for 2D atom layouts, topology metadata, atom labels, UDG/blockade edges, and selected-bitstring overlays where applicable. 3D register visualization may be optional or explicitly limited. |
| **Pulse Waveform Sampling and Plots** | High | Done | Add deterministic pulse sampling helpers for `PulseSequence` omega/delta waveforms over an explicit time grid, including global, local vector, dict, callable, and Pulse AST inputs where supported. Plot helpers should support selected atoms, fields, axes injection, and return sampled data plus matplotlib axes without unexpectedly initializing Julia unless required by a documented Pulse AST path. |
| **Observable Trajectory Plot Improvements** | Medium | Done | Extend `SimulationResult.plot()` or add `plot_observables(result, names=None, ax=None, show=False)` so users can select series, pass axes, receive matplotlib objects, and preserve backward compatibility with existing observable trajectory plots. |
| **Population Heatmap Visualization** | Medium | Done | Add helpers for atom-by-time population heatmaps using Rydberg-population observable metadata or conventional population series names, with explicit atom ordering and missing-series diagnostics. |
| **Bitstring Distribution Visualization** | High | Mixed | Final-state probability plots support readout-capable results and reduced-basis metadata. Dedicated plotting coverage through a `load_result()` artifact round trip remains required before phase closure. |
| **Shot Count Histogram Visualization** | High | Done | Add helpers to plot `measurement-samples/v1` outputs from `SimulationResult.sample(shots, seed=...)`, including counts/frequencies, shot count, seed metadata, and consistent bitstring ordering. |
| **MWIS/UDG Result Visualization** | Medium | Done | Add optional helpers for UDG/MWIS workflows that overlay selected bitstrings, weights, graph edges, and constraint violations on register layouts. These helpers should support experiment recipes and Phase 16 benchmarks without making optimization-performance claims by themselves. |
| **Basis and Reduced-Basis Visualization** | Medium | Done | Add small-system helpers to inspect represented basis bitstrings, forbidden bitstrings, full-vs-reduced basis sizes, pruning ratio, and the relationship between blockade edges and reduced-basis validity. These views should be clearly marked as diagnostic and should preserve Sagittarius bitstring ordering. |
| **Interaction and Blockade Graph Visualization** | High | Done | Add backend-free plots or data helpers for atom pair distances, van der Waals interaction matrices, blockade adjacency, and UDG graph overlays. These diagnostics should help users validate geometry, units, and blockade-radius choices before expensive solver runs. |
| **Correlation Matrix Visualization** | Medium | Done | Add helpers for pair-correlation, connected-correlation, Pauli-ZZ, and blockade-violation matrix or edge heatmap views when the result contains compatible observable series or metadata. Missing observables should produce actionable diagnostics rather than silent empty plots. |
| **Time-Resolved Spatial Population Views** | Medium | Done | Add spatial snapshots and optional small-multiple or animation-ready data helpers that color atoms by population or selected observable value at one or more output times. Animation may remain optional, but the extracted frame data should be stable and artifact-compatible. |
| **Solver and Open-System Diagnostic Plots** | Medium | Done | Add diagnostic views for output grids, saveat samples, Lindblad trace/positivity checks, MCWF-vs-Lindblad comparisons, and trajectory mean/variance or confidence bands where the underlying data are available. These should support Phase 14 and Phase 16 validation workflows without replacing numerical verification. |
| **Parameter Sweep Visualization** | Medium | Mixed | In-memory helpers render parameter axes, failed-run masks, and caller-supplied manifest links. A versioned user-facing sweep artifact, retained failure-row contract, and artifact-path resolver remain planned. |
| **Benchmark Plotting Helpers** | Medium | Done | Public performance plotting and MWIS benchmark export accept only validated `benchmark-artifact/v1` envelopes or JSON paths. Explicit `plot_diagnostic_*` and `save_diagnostic_mwis_figure` helpers accept caller mappings and remain non-claim diagnostic tools. |
| **State Vector and Density-Matrix Diagnostics** | Low | Done | Add small-system debug views for state probability vectors, density-matrix diagonals, density-matrix magnitude heatmaps, and phase heatmaps. These helpers should be explicitly limited to small Hilbert spaces and should fail clearly when data are unavailable or too large. |
| **Figure Export and Report Bundles** | Low | Done | Add convenience helpers for saving PNG/SVG/PDF figures and optional metadata sidecar JSON. Exported figures should retain enough metadata to identify source result artifacts, schema versions, seeds, backend, basis mode, and plot parameters. |
| **Artifact-Aware Reporting** | Medium | Done | Add lightweight report helpers that summarize result artifacts with plots, schema versions, backend/runtime metadata, basis mode, seed/output-grid metadata, and linked manifests. Reports must distinguish exploratory visualization from benchmark or public-claim evidence. |
| **Documentation and Examples** | High | Mixed | The canonical API contract records current coverage, examples, governance boundaries, and acceptance evidence. Additional task-focused user examples and a dedicated backend-initialization regression remain required for phase closure. |

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
