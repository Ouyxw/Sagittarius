# Sagittarius

Sagittarius is a neutral-atom analog quantum simulation project with a Julia numerical core and a Python SDK. It is intended for two related workflows:

- baseline simulation for Rydberg-atom analog devices and experiment-oriented pulse studies;
- exploratory algorithm research, especially workflows that may later be demonstrated on neutral-atom hardware.

The current repository contains a Julia backend for the physics and solver implementation, a Python package for user-facing workflows, tests for scientific invariants and API behavior, and an MWIS-on-unit-disk-graphs application example.

Sagittarius is still an early research SDK. Treat benchmark numbers, backend maturity, and high-level APIs as actively evolving unless they are covered by tests and documented artifacts in this repository.

## Scope

Sagittarius focuses on classical emulation of Rydberg neutral-atom analog dynamics. The main modeling targets are:

- registers of atoms in 2D or 3D space;
- Rydberg blockade and blockade-reduced Hilbert spaces;
- global and local Rabi frequency and detuning controls;
- closed-system Schrodinger evolution;
- open-system Lindblad and Monte Carlo wave-function trajectories;
- observables such as per-atom Rydberg population;
- parameter sweeps and hardware-oriented baseline studies.

The project is not a replacement for a calibrated hardware control stack. It is a simulation and research layer for testing physical assumptions, algorithm mappings, pulse schedules, solver behavior, and expected observables before moving to real devices.

## Design Goals

- Keep the physics core transparent and inspectable for Julia users.
- Provide a practical Python SDK for notebooks, algorithm prototypes, plotting, and integration with the broader scientific Python ecosystem.
- Maintain consistent simulation semantics across Python and Julia interfaces as the dual SDK matures.
- Prefer benchmark-backed performance claims over broad marketing claims.
- Make failures diagnosable: backend availability, GPU passthrough, package versions, and solver configuration should be explicit.

## Features

Implemented or partially implemented capabilities include:

- Julia backend using SciML/OrdinaryDiffEq-based numerical integration.
- Python SDK with `Atom`, `Register`, `Simulation`, `PulseSequence`, `SolverConfig`, and `SimulationResult`.
- Rydberg blockade basis reduction for constrained Hilbert spaces.
- Specialized register constructors for 1D chains, 2D square lattices, and unit-disk graph instances.
- Backend-free dense-vs-reduced validation for small blockade systems.
- Global and local pulse controls for Rabi frequency and detuning.
- Pulse helpers including constant, ramp, piecewise, Gaussian, Blackman, and sinc shapes.
- Schrodinger, Lindblad, and Monte Carlo trajectory workflows.
- JSON serialization for simulation results using the `result-artifact/v1` envelope with data, metadata, diagnostics, and validated `run-manifest/v1` fields.
- Lightweight Python imports with lazy Julia/GPU initialization.
- Runtime diagnostics through `doctor()`, `version_info()`, and `backend_maturity()`, including `version-info/v1` package, build, container, and backend toolchain metadata.
- GPU execution paths for supported backends, with CUDA as the primary containerized development target.
- Distributed parameter sweeps through `ParallelSimulation`.
- MWIS/UDG example workflows with classical baselines.

See [REQUIREMENTS.md](REQUIREMENTS.md) for the current development roadmap and planned hardening work.
For short verification snippets with expected output, see [docs/getting-started/minimal-examples.md](docs/getting-started/minimal-examples.md). For prior-art-aware wording around Rydberg/MWIS mappings and simulator claims, see [docs/governance/prior-art-notes.md](docs/governance/prior-art-notes.md). For public release, benchmark report, and technical disclosure tracking, see [docs/governance/disclosure-control.md](docs/governance/disclosure-control.md).

## Repository Layout

```text
.
|-- Sagittarius.jl/          # Julia physics and solver backend
|   |-- Project.toml
|   `-- src/
|-- sagittarius_py/          # Python SDK package and tests
|   |-- pyproject.toml
|   |-- sagittarius/
|   |-- tests/
|   `-- projects/mwis_udg/
|-- docs/                    # Development, deployment, and backend notes
|-- scripts/                 # Development/debug helper scripts
|-- LICENSE                  # MIT license
|-- REQUIREMENTS.md          # Roadmap and production requirements
`-- README.md
```

Development/debug helper scripts that are not part of the public SDK live under `scripts/`.

## Installation

### Python SDK

From the repository root:

```bash
cd sagittarius_py
uv sync
uv run python -m juliapkg resolve
```

If you do not use `uv`, install the package in editable mode with your preferred Python environment manager:

```bash
cd sagittarius_py
python -m pip install -e .
python -m juliapkg resolve
```

The Python package depends on Julia through `juliacall`, but importing `sagittarius` is designed to stay lightweight. Julia package resolution and precompilation happen when a backend operation, simulation, pulse compilation, cluster setup, or explicit backend initialization needs Julia.

### Containerized Development

A Docker/VS Code devcontainer workflow is documented in [docs/getting-started/containerization.md](docs/getting-started/containerization.md). The container is the recommended path for CUDA-oriented development because it pins the main system dependencies and configures GPU access for supported hosts.

After entering the container, validate the environment with:

```bash
cd sagittarius_py
uv run python check_env.py
```

A container image does not guarantee that a GPU backend is available at runtime. GPU passthrough, host drivers, and backend-specific Julia packages still need to be checked on the running machine. Use `doctor(backend="CUDA")` for a lightweight check and `doctor(backend="CUDA", initialize_backend=True)` when you also want to validate Julia startup.

## Quick Start

The following example runs a one-atom Rabi oscillation and records the Rydberg population.

```python
import numpy as np
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

reg = Register([Atom(0.0, 0.0, 0.0)], C6=0.0)
seq = PulseSequence(omega=2.0 * np.pi, delta=0.0)
cfg = SolverConfig(reltol=1e-7, abstol=1e-7)

sim = Simulation(reg, seq, cfg)
psi0 = np.array([1.0, 0.0], dtype=complex)

result = sim.run(psi0, 0.0, 0.5, observables={"pop_atom_0": 0})
print(result.to_pandas().tail())
```

For a blockade-reduced simulation, set `blockade_radius` in `SolverConfig` and size the initial state according to the reduced basis:

```python
import numpy as np
from sagittarius import Register, Simulation, PulseSequence, SolverConfig

reg = Register.chain(3, spacing=0.5, C6=100.0)

sim = Simulation(
    reg,
    PulseSequence(omega=1.0, delta=0.0),
    SolverConfig(blockade_radius=0.6),
)

basis_size = sim.validate()
psi0 = np.zeros(basis_size, dtype=complex)
psi0[0] = 1.0

result = sim.run(psi0, 0.0, 1.0, observables={"pop_atom_0": 0})
```

## GPU Execution

GPU execution is configured through `SolverConfig`:

```python
from sagittarius import SolverConfig

cfg = SolverConfig(use_gpu=True, gpu_backend="CUDA")
```

Supported backend names are currently `CUDA`, `AMDGPU`, and `Metal`, but maturity and test coverage are not identical across backends. CUDA is the main target of the provided container workflow; the devcontainer uses CUDA 12.8 and pins CUDA.jl 6.2.x for CUDA 12.8+/Blackwell compatibility. See [docs/reference/backends.md](docs/reference/backends.md) for the current maturity matrix, and use `doctor(backend="CUDA", initialize_backend=True)` before enabling GPU execution on a machine or container. The default container/PythonCall environment is CUDA-only; install AMDGPU.jl or Metal.jl only in separate backend-specific experimental environments.

## Runtime Diagnostics

The diagnostics API is safe to call before Julia is initialized:

```python
from sagittarius import backend_maturity, doctor, version_info

print(version_info())
print(backend_maturity())
print(doctor(backend="CUDA"))
```

`doctor()` reports container detection, backend maturity, runtime versions, build/source metadata, package versions, backend toolchain probes, basic GPU visibility, structured `issue_details`, backend `capabilities` with ABI/toolchain and parity-status fields, and schema version `doctor/v2.1`. `version_info()` returns schema `version-info/v1` while retaining compatibility fields such as `package_version`, `julia_version`, and `in_container`, plus host ABI metadata. Pass `initialize_backend=True` to also attempt Julia backend loading and return a `backend-probe/v2.1` payload with `checks`, `versions`, `devices`, `driver`, `runtime`, `errors`, and `abi`. Simulation results expose `metadata`, `diagnostics`, and a validated `run-manifest/v1` manifest; `SimulationResult.save()` always writes the `result-artifact/v1` envelope. Use `validate_run_manifest(result.manifest)` to check the manifest contract explicitly.

## MWIS Example

The `sagittarius_py/projects/mwis_udg` directory contains an application workflow for mapping maximum weighted independent set problems on unit-disk graphs to Rydberg analog simulation.

```bash
cd sagittarius_py/projects/mwis_udg
uv run python example_mwis.py
```

The project includes exact and heuristic classical baselines, benchmark scripts, and solution verification helpers. Use these examples as research scaffolding rather than as a finalized benchmark suite.

## Units and Conventions

| Quantity | Unit | Notes |
| :--- | :---: | :--- |
| Distance | micrometer | Atom coordinates and blockade distances. |
| Time | microsecond | Simulation intervals and pulse durations. |
| Frequency | rad / microsecond | Angular frequencies, including Rabi frequency and detuning. |
| Interaction coefficient | rad / microsecond * micrometer^6 | Van der Waals `C6` convention. |
| Decay and dephasing rates | 1 / microsecond | Open-system rates. |

Python atom indices are zero-based in user-facing APIs and follow `Register.atoms` order. Julia internals are one-based, and the Python SDK performs boundary conversion without reversing local pulse vectors. See [docs/api/pulse-and-indexing-contract.md](docs/api/pulse-and-indexing-contract.md) for local addressing validation, indexing semantics, and pulse input behavior.

## Verification

Run the Python test suite from the Python package directory:

```bash
cd sagittarius_py
uv run python -m pytest tests/
```

The tests cover API behavior, pulse handling, local addressing, physical invariants, analytic benchmarks, serialization, open-system workflows, GPU paths, and cluster orchestration. CUDA hardware tests are opt-in: set `SAGITTARIUS_ENABLE_GPU_TESTS=1` and ensure `doctor(backend="CUDA", initialize_backend=True)` passes before running `tests/test_gpu_acceleration.py`.

Performance scripts live under:

```text
sagittarius_py/tests/test_performance/
```

Benchmark results should be interpreted with the exact hardware, `version-info/v1` metadata, solver settings, and backend configuration used to generate them. Public performance statements should follow [docs/governance/performance-claims.md](docs/governance/performance-claims.md) and cite the relevant `benchmark-artifact/v1` JSON.

## Architecture

Sagittarius is organized around three layers:

1. Python SDK: ergonomic construction of registers, pulse sequences, solver configuration, result handling, plotting, and algorithm workflows.
2. Shared model layer: pulse representations, blockade-reduced basis semantics, observable definitions, and serialization contracts.
3. Julia backend: physics kernels, Hamiltonian construction, numerical solvers, GPU paths, and distributed execution.

The roadmap calls for a first-class Julia developer API alongside the Python SDK. The intent is not to force both languages to expose identical syntax, but to keep the physical semantics, defaults, result schemas, and benchmark fixtures consistent. See [docs/getting-started/dual-sdk-examples.md](docs/getting-started/dual-sdk-examples.md) for paired Python and Julia workflows.

## Development Notes

Recommended checks before submitting changes:

```bash
cd sagittarius_py
uv run python -m pytest tests/
```

For environment diagnostics:

```bash
cd sagittarius_py
uv run python check_env.py
uv run python - <<'PY'
from sagittarius import doctor
print(doctor(backend="CUDA"))
PY
```

For roadmap context, see [REQUIREMENTS.md](REQUIREMENTS.md). For container setup, see [docs/getting-started/containerization.md](docs/getting-started/containerization.md).

## Known Limitations

Sagittarius is an early research SDK. Important limitations include evolving APIs, Julia/PythonCall backend dependency, non-uniform GPU maturity, exponential full-basis scaling, incomplete CPU/GPU parity coverage, and benchmark reproducibility work still in progress. See [docs/reference/known-limitations.md](docs/reference/known-limitations.md) for the detailed list.

## License

Sagittarius is distributed under the MIT License. See [LICENSE](LICENSE).
