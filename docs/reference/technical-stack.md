# Technical Stack

Status: `Mixed`
Roadmap: Phase 5, Phase 6, Phase 8, Phase 10, Phase 13, Phase 17
Version: `technical-stack/v1`
Last reviewed: 2026-06-30


This page summarizes the current Sagittarius technical stack, dependency boundaries, backend maturity, and planned packaging/deployment changes. For runtime architecture, see [`architecture-overview.md`](architecture-overview.md). For backend support status, see [`SPEC-BACKEND-001-backends.md`](SPEC-BACKEND-001-backends.md).

## Stack Summary

| Layer | Technologies | Current role |
| :--- | :--- | :--- |
| Python SDK | Python `>=3.10`, NumPy, pandas, matplotlib, NetworkX, SciPy, Click | User-facing API, validation, result handling, examples, benchmarks. |
| Python-Julia bridge | `juliacall`, `juliapkg` | Lazy Julia initialization and Julia dependency resolution from Python workflows. |
| Julia backend | Julia `^1.10.3`, Sagittarius.jl | Physics model, pulse compilation, basis generation, Hamiltonians, solvers. |
| Numerical solvers | OrdinaryDiffEq, SciMLBase, DiffEqCallbacks | Time evolution for Schrodinger, Lindblad, and MCWF workflows. |
| Linear algebra | LinearAlgebra, SparseArrays, StaticArrays | Dense, sparse, and static-vector operations. |
| GPU path | CUDA.jl 6.2.x | Experimental CUDA-oriented execution path. |
| Distributed path | Julia Distributed, cluster helpers | Early cluster foundation; broader HPC remains Phase 17. |
| Optimization examples | NetworkX, PuLP, DOcplex | UDG/MWIS example generation, exact baselines, verification workflows. |
| Testing | pytest, Julia package tests where applicable | Python tests, backend tests, parity tests, benchmark artifact tests. |
| Packaging | setuptools, uv workflows, juliapkg metadata | Source-checkout-oriented today; relocatable packaging is Phase 13. |

## Python Package

The Python package is defined in [`sagittarius_py/pyproject.toml`](../../sagittarius_py/pyproject.toml):

- package name: `sagittarius-py`;
- Python requirement: `>=3.10`;
- build backend: `setuptools.build_meta`;
- package directory: `sagittarius_py/sagittarius`;
- package data currently includes `juliapkg.json`.

Primary Python dependencies:

- `juliacall` and `juliapkg` for Python-to-Julia integration;
- `numpy`, `pandas`, `matplotlib`, and `scipy` for numerical data and analysis;
- `networkx`, `pulp`, and `docplex` for MWIS/UDG examples and exact baselines;
- `click` for command-oriented utilities;
- `pytest` for tests.

## Julia Package

The Julia backend is defined in [`Sagittarius.jl/Project.toml`](../../Sagittarius.jl/Project.toml).

Primary Julia dependencies:

- `OrdinaryDiffEq` for ODE solver algorithms;
- `SciMLBase` and `DiffEqCallbacks` for SciML integration;
- `LinearAlgebra`, `SparseArrays`, and `StaticArrays` for core numerical structures;
- `Random` for stochastic trajectories;
- `CUDA` for the experimental GPU path;
- `Distributed` for cluster foundations;
- `Logging` for structured event emission.

The Julia module exports physics constructors, pulse nodes, basis helpers, Hamiltonian builders, solver functions, jump operators, and structured logging APIs.

## Python-Julia Integration

Sagittarius uses `juliacall` as the runtime bridge and `juliapkg` for Julia dependency resolution in Python workflows.

Current behavior:

- importing `sagittarius` is intended to stay lightweight;
- Julia initializes lazily when simulation, pulse compilation, backend initialization, or explicit diagnostics require it;
- source installs expect `Sagittarius.jl/` and `sagittarius_py/` to remain available together;
- `sagittarius_py/sagittarius/juliapkg.json` declares the Julia dependency environment used by Python workflows;
- the CUDA devcontainer generates JuliaCall shell configuration at post-create time with `.devcontainer/setup-juliacall-env.sh`, deriving `PYTHON_JULIACALL_EXE`, `PYTHON_JULIACALL_PROJECT`, and `PYTHON_JULIACALL_BINDIR` from the container runtime instead of hard-coding Juliaup versioned paths.

Phase 13 tracks the transition toward relocatable wheels, package-resource lookup, and cleaner CPU-first installation behavior.

## Backend Maturity

| Backend | Maturity | Notes |
| :--- | :--- | :--- |
| CPU | Stable | Default SciML/OrdinaryDiffEq execution path used by regular API and physics tests. |
| CUDA | Experimental | Main GPU development target; requires compatible NVIDIA driver, CUDA visibility, CUDA.jl, and parity checks. |
| AMDGPU | Planned | API name may exist, but production behavior is not claimed. |
| Metal | Planned | API name may exist, but production behavior is not claimed. |

Users should call `doctor()` and check [`SPEC-BACKEND-001-backends.md`](SPEC-BACKEND-001-backends.md) before selecting non-CPU backends.

## Development and Test Stack

The Python test suite covers:

- API validation;
- pulse contracts;
- Python/Julia golden parity;
- Julia native API coverage;
- runtime hardening;
- event taxonomy;
- failure diagnostics;
- serialization and shared result behavior;
- dense-vs-reduced validation;
- open-system sanity checks;
- benchmark artifact generation;
- optional CUDA tests.

GPU tests are opt-in and require a working CUDA environment. Benchmark results should follow [`SPEC-GOV-004-benchmarking-plan.md`](../governance/SPEC-GOV-004-benchmarking-plan.md) and [`SPEC-GOV-001-performance-claims.md`](../governance/SPEC-GOV-001-performance-claims.md).

## Packaging and Installation Status

Current support is source-checkout oriented:

- clone the complete repository;
- install the Python package from `sagittarius_py/`;
- resolve Julia dependencies with `python -m juliapkg resolve`;
- keep `Sagittarius.jl/` and `sagittarius_py/` together unless using explicit development overrides.

Phase 13 packaging work now includes relocatable wheel artifacts, installed-package resource lookup, a CPU-first dependency profile that does not require CUDA for regular CPU users, and `sagittarius backend` setup commands. Remaining release-readiness work includes:

- cross-platform matrix pass evidence;
- PyPI release readiness criteria.

See [`package-installation.md`](../getting-started/package-installation.md), [`installation.md`](../getting-started/installation.md), and [`backend-setup.md`](../getting-started/backend-setup.md).

## Containers and GPU Development

CUDA-focused container workflows are documented in [`containerization.md`](../development/containerization.md).

Important constraints:

- container images do not guarantee host GPU availability;
- host driver compatibility and device passthrough must be validated at runtime;
- CUDA 12.8 and Blackwell-class GPUs require current driver/CUDA.jl compatibility checks;
- JuliaCall overrides must be complete and internally consistent; setting only `PYTHON_JULIACALL_EXE` or deriving `PYTHON_JULIACALL_BINDIR` from a Juliaup shim can prevent diagnostics from reaching CUDA checks;
- AMDGPU and Metal should use separate backend-specific environments until dependency constraints are mature.

## Benchmark and Governance Stack

Benchmark scripts live under `sagittarius_py/tests/test_performance/` and should emit structured artifacts rather than only local timing notes.

Governance documents constrain public usage of benchmark numbers:

- [`SPEC-GOV-004-benchmarking-plan.md`](../governance/SPEC-GOV-004-benchmarking-plan.md) defines benchmark suite structure and required metadata.
- [`SPEC-GOV-001-performance-claims.md`](../governance/SPEC-GOV-001-performance-claims.md) defines allowed performance wording.
- [`SPEC-GOV-002-disclosure-control.md`](../governance/SPEC-GOV-002-disclosure-control.md) defines public disclosure tracking.
- [`SPEC-GOV-003-prior-art-notes.md`](../governance/SPEC-GOV-003-prior-art-notes.md) defines prior-art-sensitive boundaries.

## Planned Stack Evolution

| Roadmap | Stack impact |
| :--- | :--- |
| Phase 11 | Observable library and observable metadata across Python and Julia. |
| Phase 12 | Julia solver algorithm resolver and effective solver metadata. |
| Phase 13 | Packaging, resource lookup, CPU-first installation, PyPI readiness. |
| Phase 14 | Theory-noise API, custom Lindblad channels, stochastic Hamiltonian ensembles. |
| Phase 15 | Seed, sampling, output-grid, experiment config, and sweep workflows. |
| Phase 17 | Slurm, MPI, cluster/sweep benchmarks, and advanced deployment. |

## Maintenance Triggers

Update this page when:

- Python or Julia dependency versions or package metadata change;
- backend maturity changes;
- installation, packaging, or juliapkg behavior changes;
- CUDA, AMDGPU, Metal, or cluster workflows change;
- benchmark, testing, or public-governance stack changes.
