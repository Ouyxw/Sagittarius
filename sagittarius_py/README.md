# Sagittarius

Sagittarius is a research SDK for classical simulation of Rydberg neutral-atom analog dynamics. It combines a Julia physics and solver backend with a Python SDK for experiment-oriented pulse studies and algorithm prototypes.

The project is under active development. APIs, backend support, and benchmark results may change unless covered by tests and documented artifacts. Sagittarius is a simulation layer, not a calibrated hardware control stack.

## Capabilities

- 2D and 3D atom registers, including chains, square lattices, and unit-disk graphs.
- Full and Rydberg-blockade-reduced Hilbert spaces.
- Global and local Rabi-frequency and detuning controls.
- Constant, ramp, piecewise, Gaussian, Blackman, sinc, and sine-squared pulses.
- Schrodinger, Lindblad, and Monte Carlo wave-function evolution.
- Per-atom Rydberg populations and parameter sweeps.
- CPU execution and experimental GPU backends, with CUDA as the primary target.
- Python and Julia APIs with shared physical semantics.
- Runtime diagnostics and versioned result serialization.
- MWIS-on-unit-disk-graph examples with classical baselines.

See [REQUIREMENTS.md](REQUIREMENTS.md) for the roadmap and [known limitations](docs/reference/known-limitations.md) for current constraints.

## Repository Layout

```text
Sagittarius/
|-- Sagittarius.jl/          # Julia backend
|-- sagittarius_py/          # Python SDK and tests
|-- docs/                    # User and developer documentation
|-- examples/                # Short user-facing examples
`-- scripts/                 # Repository maintenance tools
```

Keep long-running experiments in a separate project rather than under this repository.

## Installation

Requirements: Git, Julia 1.10.3 or newer, a Python version supported by `sagittarius_py/pyproject.toml`, and optionally `uv`.

For contributors and local development, use a complete source checkout followed by Python dependency synchronization and JuliaPkg resolution. Editable/source installs prefer the top-level `Sagittarius.jl/` backend so Julia edits take effect immediately, while released wheels use the embedded backend under `sagittarius/julia/Sagittarius.jl`.

```bash
git clone <repository_url> Sagittarius
cd Sagittarius/sagittarius_py
uv sync
uv run python -m juliapkg resolve
```

Without `uv`:

```bash
cd Sagittarius/sagittarius_py
python -m pip install -e .
python -m juliapkg resolve
```

The `pip install -e .` path is development-only and still depends on the editable source checkout for Python code updates. A production PyPI release is being prepared but is not published yet; do not use an unqualified `pip install sagittarius-py` command until the release record says that the package is available. Once published, the authoritative consumer-install instructions will be in the [Python package installation guide](docs/getting-started/python/package-installation.md).

For source installs, backend setup, package-release status, container setup, and environment troubleshooting, see the [installation overview](docs/getting-started/installation.md). Python-specific setup lives under [docs/getting-started/python](docs/getting-started/python/source-installation.md); Julia-native setup lives under [docs/getting-started/julia](docs/getting-started/julia/projects.md).

### Independent Python Projects

```bash
mkdir -p ~/workspace/my_experiment
cd ~/workspace/my_experiment
uv init
uv add --editable ../Sagittarius/sagittarius_py
uv run python -m juliapkg resolve
uv run python scripts/rabi_simulation.py
```

### Independent Julia Projects

```bash
mkdir -p ~/workspace/my_julia_experiment/scripts
cd ~/workspace/my_julia_experiment
julia --project=. -e 'using Pkg; Pkg.develop(path="../Sagittarius/Sagittarius.jl"); Pkg.instantiate()'
julia --project=. scripts/rabi_simulation.jl
```

Use `--project=.` instead of modifying `JULIA_LOAD_PATH`. The [Julia projects guide](docs/getting-started/julia/projects.md) contains the recommended layout and a Julia example.

## Python Quick Start

This example runs a one-atom Rabi oscillation and records the Rydberg population:

```python
import numpy as np
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

reg = Register([Atom(0.0, 0.0, 0.0)], C6=0.0)
sim = Simulation(
    reg,
    PulseSequence(omega=2.0 * np.pi, delta=0.0),
    SolverConfig(reltol=1e-7, abstol=1e-7),
)

psi0 = np.array([1.0, 0.0], dtype=complex)
result = sim.run(psi0, 0.0, 0.5, observables={"pop_atom_0": 0})
print(result.to_pandas().tail())
```

For a reduced basis, set `SolverConfig(blockade_radius=...)` and allocate the initial state using the size returned by `sim.validate()`. See the [Python minimal examples](docs/getting-started/python/minimal-examples.md) for complete full- and reduced-basis workflows.

Solver selection is explicit through `SolverConfig(method=...)`. The default is adaptive `Tsit5`; `Vern9` is available for higher-accuracy adaptive checks; fixed-step `RK4` requires `SolverConfig(method="RK4", adaptive=False, dt=...)`. Run manifests record both requested and effective solver settings.

## Julia Quick Start

```julia
using Sagittarius

reg = chain_register(3; spacing=0.5, C6=100.0)
context = reduced_basis_context(reg; blockade_radius=0.6)
H = hamiltonian(reg, fill(1.0, 3), zeros(3); basis_context=context)

println("Reduced basis size: ", length(context.basis))
```

See the [Julia native API](docs/api/SPEC-API-003-julia-native-api.md) and [dual-SDK examples](docs/getting-started/dual-sdk-examples.md).

## Physical Units and Indexing

Numeric inputs do not carry units. Coordinates, times, angular frequencies, interaction coefficients, and decay rates must use one consistent unit system. See [physical units and parameter selection](docs/physics/SPEC-PHYS-001-units.md) for `blockade_radius`, `C6`, pulse parameters, and open-system rates.

Python atom indices are zero-based and follow `Register.atoms` order; Julia indices are one-based. See the [pulse and indexing contract](docs/api/SPEC-API-001-pulse-and-indexing-contract.md).

## GPU and Diagnostics

Enable GPU execution through `SolverConfig`:

```python
cfg = SolverConfig(use_gpu=True, gpu_backend="CUDA")
```

Backend names include `CUDA`, `AMDGPU`, and `Metal`, but support and test coverage differ. Check the [backend maturity matrix](docs/reference/SPEC-BACKEND-001-backends.md) before use.

```python
from sagittarius import backend_maturity, doctor, version_info

print(version_info())
print(backend_maturity())
print(doctor(backend="CUDA", initialize_backend=True))
```

CUDA is the primary containerized development target, but remains experimental. GPU execution still requires compatible host drivers, runtime libraries, and device passthrough.

## MWIS Example

The `sagittarius_py/projects/mwis_udg/` project demonstrates maximum weighted independent set workflows on unit-disk graphs:

```bash
cd sagittarius_py/projects/mwis_udg
uv run python example_mwis.py
```

It is research scaffolding, not a finalized benchmark suite.

## Verification

```bash
cd sagittarius_py
uv run python check_env.py
uv run python -m pytest tests/
```

CPU tests do not require CUDA. GPU tests are opt-in and require a working backend. Performance results must include the hardware, solver settings, backend configuration, and version metadata described in the [performance claims policy](docs/governance/SPEC-GOV-001-performance-claims.md).

## Documentation

- [Installation overview](docs/getting-started/installation.md)
- [Python minimal examples](docs/getting-started/python/minimal-examples.md)
- [Julia minimal examples](docs/getting-started/julia/minimal-examples.md)
- [Physical units and parameter selection](docs/physics/SPEC-PHYS-001-units.md)
- [Python/Julia parity contract](docs/api/SPEC-API-002-python-julia-parity.md)
- [Backend support](docs/reference/SPEC-BACKEND-001-backends.md)
- [Known limitations](docs/reference/known-limitations.md)
- [Containerized development](docs/getting-started/containerization.md)

## License

Sagittarius is distributed under the [MIT License](LICENSE).
