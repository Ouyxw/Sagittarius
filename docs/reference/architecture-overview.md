# Architecture Overview

Status: `Current`
Roadmap: Phase 5, Phase 6, Phase 8, Phase 10, Phase 13, Phase 17
Version: `architecture-overview/v1`
Last reviewed: 2026-06-30


This page describes the current Sagittarius architecture, module boundaries, runtime data flow, and planned architecture pressure points. For object and artifact details, see [`data-model.md`](data-model.md). For dependency and backend maturity details, see [`technical-stack.md`](technical-stack.md) and [`SPEC-BACKEND-001-backends.md`](SPEC-BACKEND-001-backends.md).

## System Purpose

Sagittarius is a research SDK for classical simulation of Rydberg neutral-atom analog dynamics. It is designed as a simulation and reproducibility layer, not as a calibrated hardware control stack.

The architecture optimizes for:

- an ergonomic Python front door for experiment-style workflows;
- a Julia backend for physics operators, basis construction, and numerical solvers;
- stable contracts for Python/Julia parity, results, diagnostics, logs, and benchmark claims;
- CPU-first execution with an experimental CUDA path;
- artifact-backed reproducibility for simulations, benchmarks, and public statements.

## High-Level Architecture

```text
User code / examples / benchmarks
    |
    v
Python SDK: sagittarius_py/sagittarius
    |  - Atom, Register, PulseSequence, Pulse, SolverConfig
    |  - Simulation, SimulationResult, validation, artifacts
    |  - doctor(), version_info(), event taxonomy, benchmarking helpers
    |
    | juliacall / juliapkg
    v
Julia backend: Sagittarius.jl
    |  - pulse compilation
    |  - basis and BasisContext construction
    |  - Hamiltonian and jump operators
    |  - Schrodinger, Lindblad, MCWF, CUDA-oriented solver paths
    |
    v
SciML / OrdinaryDiffEq / SparseArrays / CUDA
    |
    v
Result, diagnostics, manifest, shared result, benchmark artifacts
```

The Python SDK owns user ergonomics, input validation, serialization, diagnostics, and artifact envelopes. The Julia backend owns the core physics data structures and solver execution.

## Repository Layout

| Path | Responsibility |
| :--- | :--- |
| [`sagittarius_py/sagittarius/api.py`](../../sagittarius_py/sagittarius/api.py) | Python public API, validation, Julia bridge, simulation lifecycle, result artifacts, run manifests. |
| [`sagittarius_py/sagittarius/pulse.py`](../../sagittarius_py/sagittarius/pulse.py) | Python pulse nodes and pulse helper constructors. |
| [`sagittarius_py/sagittarius/runtime.py`](../../sagittarius_py/sagittarius/runtime.py) | Lazy backend initialization, diagnostics, `doctor()`, `version_info()`, failure diagnostics. |
| [`sagittarius_py/sagittarius/events.py`](../../sagittarius_py/sagittarius/events.py) | Python event taxonomy catalog and lookup helpers. |
| [`sagittarius_py/sagittarius/benchmarking.py`](../../sagittarius_py/sagittarius/benchmarking.py) | Benchmark artifact helpers. |
| [`Sagittarius.jl/src/Sagittarius.jl`](../../Sagittarius.jl/src/Sagittarius.jl) | Julia module assembly and exports. |
| [`Sagittarius.jl/src/physics.jl`](../../Sagittarius.jl/src/physics.jl) | Julia physics model, registers, bases, Hamiltonians, reduced-basis helpers, jump operators. |
| [`Sagittarius.jl/src/solver.jl`](../../Sagittarius.jl/src/solver.jl) | Julia solver paths for Schrodinger, Lindblad, MCWF, and CUDA-oriented execution. |
| [`Sagittarius.jl/src/logging.jl`](../../Sagittarius.jl/src/logging.jl) | Julia structured logging aligned with `event-taxonomy/v1`. |
| [`Sagittarius.jl/src/cluster.jl`](../../Sagittarius.jl/src/cluster.jl) | Cluster and distributed workflow foundations. |

## Runtime Lifecycle

A normal Python simulation follows this lifecycle:

1. User constructs `Register`, `PulseSequence`, and `SolverConfig`.
2. Python validates atom ordering, pulse shapes, dimensions, solver settings, backend choices, and initial state size.
3. `doctor()` collects lightweight backend diagnostics without forcing Julia initialization unless explicitly requested.
4. Python initializes the Julia backend lazily when compilation or solver execution needs it.
5. Python compiles pulse declarations into Julia-callable pulse functions.
6. Julia builds the full or reduced basis and Hamiltonian, using a shared `BasisContext` when reduced-basis execution is active.
7. Julia runs the selected solver path and emits taxonomy-aligned structured events.
8. Python wraps the output in `SimulationResult` with data, metadata, diagnostics, and a validated `run-manifest/v1`.
9. `SimulationResult.save()` writes a `result-artifact/v1` envelope with an embedded `shared-result/v1` payload.

## Execution Paths

| Path | Current role | Notes |
| :--- | :--- | :--- |
| Full-basis CPU | Baseline execution path. | Scales as `2^N`; useful for correctness and small systems. |
| Reduced-basis CPU | Main scaling path for blockade-constrained studies. | Uses reduced basis and `BasisContext`; must be validated against full-basis runs on small systems. |
| Lindblad CPU | Deterministic open-system reference. | Density matrix scales as `dim x dim`. |
| MCWF CPU | Trajectory-based open-system path. | More memory-efficient than Lindblad for larger state spaces, but has sampling error. |
| CUDA | Experimental acceleration path. | CUDA is the primary GPU target; use backend diagnostics and parity checks before claims. |
| Cluster / sweeps | Early foundation. | Phase 17 tracks broader Slurm/MPI and sweep benchmark work. |

Backend maturity is documented in [`SPEC-BACKEND-001-backends.md`](SPEC-BACKEND-001-backends.md).

## Cross-Language Boundary

Python is the ergonomic SDK boundary. Julia is the physics and solver boundary.

Important contract rules:

- Python atom indices are zero-based and follow `Register.atoms` order.
- Julia internals use one-based indices.
- Python-to-Julia conversion must preserve atom ordering, bitstring semantics, pulse addressing, solver settings, result metadata, and manifest fields.
- Python results and Julia-native workflows should converge on shared schemas where possible.

See [`SPEC-API-002-python-julia-parity.md`](../api/SPEC-API-002-python-julia-parity.md) and [`SPEC-API-003-julia-native-api.md`](../api/SPEC-API-003-julia-native-api.md).

## Observability and Contract Layer

Sagittarius treats observability as part of the architecture rather than as an afterthought.

| Contract | Purpose |
| :--- | :--- |
| [`SPEC-OBS-001-event-taxonomy.md`](SPEC-OBS-001-event-taxonomy.md) | Stable event IDs, severities, and required payload fields. |
| `doctor/v2.1` | Runtime and backend diagnostics. |
| `version-info/v1` | Runtime, package, git, build, container, and backend metadata. |
| `run-manifest/v1` | Reproducibility record for simulation results. |
| `result-artifact/v1` | Persistent result envelope. |
| [`SPEC-DATA-001-shared-result-schema.md`](SPEC-DATA-001-shared-result-schema.md) | Language-neutral result payload. |
| `benchmark-artifact/v1` | Structured benchmark evidence. |

This layer allows results, benchmark claims, and public reports to be audited after the process that produced them has exited.

## Current Architecture Constraints

- Python artifacts now embed the Julia backend under `sagittarius/julia/Sagittarius.jl`; local release smoke covers clean-venv wheel installation, JuliaPkg resolution, CPU simulation, and artifact metadata. Phase 13 still tracks CPU-first dependency work, CI artifact isolation, uninstall/reinstall smoke coverage, cross-platform validation, and PyPI release gates.
- CUDA is experimental and requires explicit runtime diagnostics and parity evidence before performance claims.
- AMDGPU and Metal are planned backend names, not mature execution paths.
- Solver method dispatch is implemented for current solver paths through an auditable `method`/`adaptive`/`dt` contract; unsupported backend paths must reject explicitly rather than silently substituting algorithms.
- Seed and output-grid contracts are implemented for current solver paths; sampling, stochastic-noise ensembles, and benchmark scripts still need to build on that metadata consistently.
- Advanced cluster/HPC execution is future Phase 17 work.

## Planned Architecture Evolution

| Roadmap | Architectural impact |
| :--- | :--- |
| Phase 11 | Adds typed observable declarations and observable metadata across solver paths and artifacts. |
| Phase 12 | Implemented solver method dispatch and effective solver configuration metadata. |
| Phase 13 | Reduces source-checkout coupling through embedded Julia backend resources, editable/source checkout preference, release artifact smoke tests, and package-resource lookup. |
| Phase 14 | Extends open-system and stochastic-noise architecture around shared basis and metadata contracts. |
| Phase 15 | Adds seed, output-grid, sampling, experiment recipe, and sweep reproducibility contracts. |
| Phase 17 | Expands cluster, sweep, and advanced deployment architecture. |

## Maintenance Triggers

Update this page when:

- Python or Julia module boundaries change;
- simulation lifecycle or backend initialization changes;
- a solver path, backend path, or artifact path is added or removed;
- package layout or source-checkout assumptions change;
- roadmap phases alter architecture-level responsibilities.
