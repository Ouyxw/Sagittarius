# Python Source Installation

This guide describes the currently supported Python installation baseline: install and test the Python SDK from a complete Sagittarius source checkout, then resolve Julia dependencies in that Python environment.

## Prerequisites

Install Git, a Python version supported by `sagittarius_py/pyproject.toml`, and `uv` or another Python environment manager. Julia 1.10.3 or newer is required for backend execution, but JuliaPkg may download a compatible Julia runtime while resolving the Python environment.

CUDA is not required for CPU simulations or the regular CPU test suite.

## Clone the Repository

```bash
mkdir -p ~/workspace
cd ~/workspace
git clone <repository_url> Sagittarius
cd Sagittarius
```

The current Python runtime still expects the repository checkout to keep `Sagittarius.jl/` and `sagittarius_py/` together:

```text
Sagittarius/
|-- Sagittarius.jl/
|-- sagittarius_py/
|-- docs/
|-- examples/
`-- scripts/
```

No `WORKSPACE` environment variable is required.

## Install the Python SDK and Julia Dependencies

From the repository root:

```bash
cd sagittarius_py
uv sync
uv run python -m juliapkg resolve
```

Without `uv`, use an editable development install:

```bash
cd sagittarius_py
python -m pip install -e .
python -m juliapkg resolve
```

This `pip install -e .` workflow is development-only. It still depends on the repository layout and is not equivalent to a relocatable wheel or independent PyPI install. Independent `pip install sagittarius-py` from PyPI is not supported yet.

If Julia is installed but cannot be found automatically, specify its executable before resolving:

```bash
export PYTHON_JULIACALL_EXE=/absolute/path/to/julia
```

Windows PowerShell:

```powershell
$env:PYTHON_JULIACALL_EXE = "C:\absolute\path\to\julia.exe"
```

See [Python backend setup](backend-setup.md) for Julia executable discovery, JuliaPkg runtime notes, and CPU/GPU backend setup.

## Verify the Local Installation

```bash
cd sagittarius_py
uv run python check_env.py
uv run python -m pytest tests/
```

CPU tests do not require an NVIDIA GPU. CUDA tests are opt-in and require a compatible local driver, CUDA runtime, Julia CUDA packages, and visible GPU device.

## User Script Location

For short examples that belong with the repository, create an `examples/` directory at the repository root:

```text
Sagittarius/
|-- examples/
|   `-- rabi_simulation.py
|-- Sagittarius.jl/
`-- sagittarius_py/
```

Run an example from the repository root:

```bash
uv run --project sagittarius_py python examples/rabi_simulation.py
```

For long-running work, keep the research project outside the Sagittarius repository. See [Python experiment projects](experiment-projects.md).
