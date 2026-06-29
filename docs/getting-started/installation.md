# Local Installation and Workspace Layout

This guide describes how to clone, install, test, and use Sagittarius directly on a local machine without Docker or a development container.

## Prerequisites

Install Git, a Python version supported by `sagittarius_py/pyproject.toml`, and `uv`
(recommended) or another Python environment manager. Julia 1.10.3 or newer is required,
but JuliaPkg may download a compatible Julia runtime while resolving the Python environment.
That runtime is not necessarily added to the shell `PATH`. CUDA is not required for CPU
simulations or the regular CPU test suite.

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

### JuliaPkg Runtime Is Not on `PATH`

If `uv run python -m juliapkg resolve` succeeds but the shell reports
`julia: command not found`, do not install a second Julia runtime immediately. First query
the executable selected by JuliaPkg:

```bash
cd Sagittarius/sagittarius_py
uv run python -c 'import juliapkg, shutil; exe = juliapkg.executable(); print(shutil.which(exe) or exe)'
```

Use the printed absolute path in Julia commands:

```bash
JULIA_EXE=/absolute/path/printed/above
"$JULIA_EXE" --version
```

If the command cannot query JuliaPkg, locate a downloaded executable directly:

```bash
find "$HOME/.julia" -type f -path '*/bin/julia'
```

JuliaPkg and Juliaup commonly place versioned runtimes below `~/.julia`. Avoid documenting
or scripting a fixed version path because it changes after a Julia upgrade. To make the
selected executable available as `julia`, add its `bin` directory to `PATH`, then restart
the shell or source its startup file:

```bash
export PATH="/absolute/path/to/julia/bin:$PATH"
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

Run `juliapkg resolve` from `my_experiment`, not from the Sagittarius development environment. Each uv project has its own Python environment and JuliaCall project selection. The editable dependency allows JuliaPkg to discover the packaged `sagittarius/juliapkg.json` file and install the Julia packages required by Sagittarius for this experiment. Although the first backend call may trigger resolution implicitly, resolving during setup exposes Julia discovery, network, and package compatibility failures before a simulation starts.

If the experiment environment was created before the packaged JuliaPkg configuration was available, refresh the editable installation before resolving again:

```bash
cd ~/workspace/my_experiment
uv sync --reinstall-package sagittarius-py
uv run python -m juliapkg resolve
```

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

### Julia User Projects

Julia users should also keep long-running experiments outside the Sagittarius repository and give each experiment its own Julia project:

```text
~/workspace/
|-- Sagittarius/
`-- my_julia_experiment/
    |-- Project.toml
    |-- Manifest.toml
    |-- scripts/
    |   `-- rabi_simulation.jl
    |-- results/
    `-- notebooks/
```

Initialize the project and register the local Sagittarius checkout as a development dependency.
This workflow needs a Julia executable in the current shell. Setting `PYTHON_JULIACALL_EXE`
for Python/JuliaCall, or exporting `PATH` only inside `Sagittarius/sagittarius_py`, does not
make `julia` available in a separate experiment shell. Either install Julia on `PATH`, or
carry the absolute executable path reported by JuliaPkg into the experiment shell:

```bash
mkdir -p ~/workspace/my_julia_experiment/scripts
cd ~/workspace/my_julia_experiment

JULIA_EXE=$(cd ../Sagittarius/sagittarius_py && uv run python -c 'import juliapkg, shutil; exe = juliapkg.executable(); print(shutil.which(exe) or exe)')
"$JULIA_EXE" --version

"$JULIA_EXE" --project=. -e '
using Pkg
Pkg.develop(path="../Sagittarius/Sagittarius.jl")
Pkg.instantiate()
Pkg.precompile()
using Sagittarius
println("Sagittarius loaded successfully")
'
```

`Pkg.develop` records Sagittarius in the experiment's `Project.toml` and `Manifest.toml` while continuing to load source code from the local checkout. It is not necessary to modify `JULIA_LOAD_PATH` or copy `Sagittarius.jl` into the experiment.
Because `--project=.` already activates the current directory, an additional
`Pkg.activate(".")` call is unnecessary.

A minimal `scripts/rabi_simulation.jl` can use the package directly:

```julia
using Sagittarius

reg = chain_register(3; spacing=0.5, C6=100.0)
context = reduced_basis_context(reg; blockade_radius=0.6)

H = hamiltonian(
    reg,
    fill(1.0, 3),
    zeros(3);
    basis_context=context,
)

println("Reduced basis size: ", length(context.basis))
```

Run scripts from the experiment root with its project activated:

```bash
cd ~/workspace/my_julia_experiment
JULIA_EXE=$(cd ../Sagittarius/sagittarius_py && uv run python -c 'import juliapkg, shutil; exe = juliapkg.executable(); print(shutil.which(exe) or exe)')
"$JULIA_EXE" --project=. scripts/rabi_simulation.jl
```

Always using `--project=.` prevents dependencies from being taken accidentally from the global Julia environment. If you prefer to type `julia` directly, add the executable `bin` directory to `PATH` in the current shell or shell startup file as described in [JuliaPkg Runtime Is Not on `PATH`](#juliapkg-runtime-is-not-on-path). Keep experiment scripts in the experiment `scripts/` directory; `Sagittarius/scripts/` remains reserved for repository maintenance and debugging. If the Sagittarius checkout moves, update its path with `Pkg.develop(path="...")` from the experiment environment and run `Pkg.instantiate()` again.

If you are already inside a nested script directory, keep using the resolved executable and point `--project` back to the experiment root. For example, from `my_julia_experiment/scripts/dual_sdk`:

```bash
"$JULIA_EXE" --project=../.. algo_prototyping.jl
```

A successful `"$JULIA_EXE" --version` does not mean the bare `julia` command is on `PATH`. These two commands use different lookup paths:

```bash
"$JULIA_EXE" --version   # uses the explicit executable path
julia --version          # requires a julia command on PATH
```

To make `julia` available in the current shell, prepend the executable directory to `PATH`:

```bash
export PATH="$(dirname "$JULIA_EXE"):$PATH"
julia --version
```

Add that `export PATH=...` line to your shell startup file, such as `~/.bashrc`, only if you want it to persist for future terminals.
