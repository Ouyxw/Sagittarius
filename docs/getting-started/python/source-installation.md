# Python Source Installation

This guide describes the Python developer path: install and test the SDK from a complete Sagittarius source checkout, then resolve Julia dependencies in that Python environment. For the released PyPI package, use [Python package installation](package-installation.md).

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

A complete checkout keeps the canonical Julia-native backend beside the Python package. In editable/source mode, the Python runtime prefers this adjacent checkout so Julia source edits take effect immediately; wheel installs use the packaged backend resource embedded under `sagittarius/julia/Sagittarius.jl`:

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

This `pip install -e .` workflow is development-only. It still depends on the editable source checkout for Python code updates and is not equivalent to a released package install. Local wheel artifacts embed the Julia backend. For ordinary consumer use, install `sagittarius-py==1.0.9` from PyPI as described in [Python package installation](package-installation.md).

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
uv run sagittarius doctor
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
