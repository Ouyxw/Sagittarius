# Source Installation

This guide describes how to clone, install, test, and use Sagittarius directly on a local machine without Docker or a development container.

## Prerequisites

Install Git, a Python version supported by `sagittarius_py/pyproject.toml`, and `uv` (recommended) or another Python environment manager. Julia 1.10.3 or newer is required, but JuliaPkg may download a compatible Julia runtime while resolving the Python environment. That runtime is not necessarily added to the shell `PATH`.

CUDA is not required for CPU simulations or the regular CPU test suite.

## Workspace Location

Sagittarius does not require `/workspace` or `/workspaces`. These are container conventions, not application configuration. Clone the repository into any writable local directory:

```bash
mkdir -p ~/workspace
cd ~/workspace
git clone <repository_url> Sagittarius
cd Sagittarius
```

Windows PowerShell example:

```powershell
New-Item -ItemType Directory -Force "$HOME\workspace"
Set-Location "$HOME\workspace"
git clone <repository_url> Sagittarius
Set-Location Sagittarius
```

Do not separate `Sagittarius.jl` from `sagittarius_py`. The current Python runtime locates the Julia backend relative to the checked-out repository:

```text
Sagittarius/
|-- Sagittarius.jl/
|-- sagittarius_py/
|-- docs/
|-- examples/          # optional user-facing examples
`-- scripts/           # repository maintenance/debug tools
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

This `pip install -e .` workflow is development-only. It still depends on the repository layout and is not equivalent to a relocatable wheel or independent PyPI install.

If Julia is installed but cannot be found automatically, specify its executable before resolving:

```bash
export PYTHON_JULIACALL_EXE=/absolute/path/to/julia
```

Windows PowerShell:

```powershell
$env:PYTHON_JULIACALL_EXE = "C:\absolute\path\to\julia.exe"
```

See [Backend setup](backend-setup.md) for Julia executable discovery, JuliaPkg runtime notes, and CPU/GPU backend setup.

## Verify the Local Installation

Run the environment check and complete Python test suite:

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

Do not place user scripts inside:

- `sagittarius_py/sagittarius/`, which contains Python package source;
- `Sagittarius.jl/src/`, which contains Julia backend source;
- `scripts/`, unless the script is a repository maintenance or debugging tool.

For long-running work, keep the research project outside the Sagittarius repository. See [Python experiment projects](python-experiment-projects.md) or [Julia user projects](julia-projects.md).
