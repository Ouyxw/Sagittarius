# Local Installation and Workspace Layout

This guide describes how to clone, install, test, and use Sagittarius directly on a local machine without Docker or a development container.

## Prerequisites

Install Git, a Python version supported by `sagittarius_py/pyproject.toml`, Julia 1.10.3 or newer, and `uv` (recommended) or another Python environment manager. CUDA is not required for CPU simulations or the regular CPU test suite.

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

Do not separate `Sagittarius.jl` from `sagittarius_py`. The Python runtime locates the Julia backend relative to the checked-out repository:

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

Without `uv`:

```bash
cd sagittarius_py
python -m pip install -e .
python -m juliapkg resolve
```

If Julia is installed but cannot be found automatically, specify its executable before resolving:

```bash
export PYTHON_JULIACALL_EXE=/absolute/path/to/julia
```

Windows PowerShell:

```powershell
$env:PYTHON_JULIACALL_EXE = "C:\absolute\path\to\julia.exe"
```

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

For long-running experiments, keep the research project separate and let it manage its own Python environment:

```text
~/workspace/
|-- Sagittarius/
`-- my_experiment/
    |-- pyproject.toml
    |-- scripts/
    |   `-- rabi_simulation.py
    |-- results/
    `-- README.md
```

Initialize the experiment once, add the local Sagittarius checkout as an editable dependency, and resolve Julia packages inside the experiment environment:

```bash
cd ~/workspace/my_experiment
uv init
uv add --editable ../Sagittarius/sagittarius_py
uv run python -m juliapkg resolve
```

Run `juliapkg resolve` from `my_experiment`, not from the Sagittarius development environment. Each uv project has its own Python environment and JuliaCall project selection. The editable dependency allows JuliaPkg to discover `../Sagittarius/sagittarius_py/juliapkg.json` and install the Julia packages required by Sagittarius for this experiment. Although the first backend call may trigger resolution implicitly, resolving during setup exposes Julia discovery, network, and package compatibility failures before a simulation starts.

The current `juliapkg.json` also includes CUDA.jl. Consequently, this resolution may install Julia CUDA packages even for CPU-only experiments; separating the default CPU dependency profile from optional GPU setup is planned packaging work.

The generated `pyproject.toml` records the local source dependency through a uv source entry equivalent to:

```toml
[project]
dependencies = [
    "sagittarius-py",
]

[tool.uv.sources]
sagittarius-py = { path = "../Sagittarius/sagittarius_py", editable = true }
```

After this one-time setup, run experiment scripts with a short, project-local command:

```bash
cd ~/workspace/my_experiment
uv run python scripts/rabi_simulation.py
```

This is preferred over invoking the full path to `Sagittarius/sagittarius_py/.venv/bin/python`: the experiment records its own dependencies, receives an isolated environment, and remains straightforward to reproduce. Because the current editable installation locates the Julia backend from the source repository, keep the complete `Sagittarius/` checkout in the configured relative location. Moving it requires updating the uv source path and running `uv sync` again.

The location and name of `~/workspace` are arbitrary; only the Sagittarius repository internal directory layout and the configured editable dependency path are significant.
