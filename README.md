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
- Global and local pulse controls for Rabi frequency and detuning.
- Pulse helpers including constant, ramp, piecewise, Gaussian, Blackman, and sinc shapes.
- Schrodinger, Lindblad, and Monte Carlo trajectory workflows.
- JSON serialization for simulation results.
- GPU execution paths for supported backends, with CUDA as the primary containerized development target.
- Distributed parameter sweeps through `ParallelSimulation`.
- MWIS/UDG example workflows with classical baselines.

See [REQUIREMENTS.md](REQUIREMENTS.md) for the current development roadmap and planned hardening work.

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
|-- docs/                    # Development and deployment notes
|-- REQUIREMENTS.md          # Roadmap and production requirements
`-- README.md
```

Some repository cleanup is still planned. In particular, temporary debug scripts and scratch files may move into `examples/`, `scripts/`, or test fixtures as the project hardens.

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

The Python package currently depends on Julia through `juliacall`. The first run may resolve Julia packages and precompile dependencies.

### Containerized Development

A Docker/VS Code devcontainer workflow is documented in [docs/CONTAINERIZATION.md](docs/CONTAINERIZATION.md). The container is the recommended path for CUDA-oriented development because it pins the main system dependencies and configures GPU access for supported hosts.

After entering the container, validate the environment with:

```bash
cd sagittarius_py
uv run python check_env.py
```

A container image does not guarantee that a GPU backend is available at runtime. GPU passthrough, host drivers, and backend-specific Julia packages still need to be checked on the running machine.

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
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

reg = Register([
    Atom(0.0, 0.0, 0.0),
    Atom(0.5, 0.0, 0.0),
    Atom(1.0, 0.0, 0.0),
], C6=100.0)

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

Supported backend names are currently `CUDA`, `AMDGPU`, and `Metal`, but maturity and test coverage are not identical across backends. CUDA is the main target of the provided container workflow. Backend capability detection and clearer maturity documentation are part of the production hardening roadmap.

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

Python atom indices are zero-based in user-facing APIs. Julia internals are one-based. Indexing semantics are a documented roadmap item because cross-language consistency matters for local addressing, observables, and reduced-basis mappings.

## Verification

Run the Python test suite from the Python package directory:

```bash
cd sagittarius_py
uv run python -m pytest tests/
```

The tests cover API behavior, pulse handling, local addressing, physical invariants, analytic benchmarks, serialization, open-system workflows, GPU paths, and cluster orchestration. Some hardware-dependent tests may require a configured GPU runtime.

Performance scripts live under:

```text
sagittarius_py/tests/test_performance/
```

Benchmark results should be interpreted with the exact hardware, Julia/Python versions, solver settings, and backend configuration used to generate them.

## Architecture

Sagittarius is organized around three layers:

1. Python SDK: ergonomic construction of registers, pulse sequences, solver configuration, result handling, plotting, and algorithm workflows.
2. Shared model layer: pulse representations, blockade-reduced basis semantics, observable definitions, and serialization contracts.
3. Julia backend: physics kernels, Hamiltonian construction, numerical solvers, GPU paths, and distributed execution.

The roadmap calls for a first-class Julia developer API alongside the Python SDK. The intent is not to force both languages to expose identical syntax, but to keep the physical semantics, defaults, result schemas, and benchmark fixtures consistent.

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
```

For roadmap context, see [REQUIREMENTS.md](REQUIREMENTS.md). For container setup, see [docs/CONTAINERIZATION.md](docs/CONTAINERIZATION.md).

## Known Limitations

- The public API is still changing.
- Lazy backend initialization and formal backend capability detection are planned but not complete.
- GPU backend maturity is not uniform across CUDA, AMDGPU, and Metal.
- Cross-language Python/Julia parity tests are planned as part of the dual SDK work.
- Benchmark claims should be tied to reproducible scripts and recorded environment metadata.

## License

The existing project documentation states that Sagittarius is distributed under the MIT License. Add or verify the repository license file before public distribution.
