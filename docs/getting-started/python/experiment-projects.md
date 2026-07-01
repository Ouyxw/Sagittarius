# Python Experiment Projects

Long-running experiments should live outside the Sagittarius repository and manage their own Python environment. This keeps experiment dependencies, scripts, and results reproducible without mixing them into package source directories.

## Recommended Layout

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

The location and name of `~/workspace` are arbitrary. The important parts are the Sagittarius repository internal layout and the configured editable dependency path.

## Initialize the Experiment

Initialize the experiment once, add the local Sagittarius checkout as an editable dependency, and resolve Julia packages inside the experiment environment:

```bash
cd ~/workspace/my_experiment
uv init
uv add --editable ../Sagittarius/sagittarius_py
uv run python -m juliapkg resolve
```

Run `juliapkg resolve` from `my_experiment`, not from the Sagittarius development environment. Each uv project has its own Python environment and JuliaCall project selection. The editable dependency allows JuliaPkg to discover the packaged `sagittarius/juliapkg.json` file and install the Julia packages required by Sagittarius for this experiment.

Although the first backend call may trigger resolution implicitly, resolving during setup exposes Julia discovery, network, and package compatibility failures before a simulation starts.

If the experiment environment was created before the packaged JuliaPkg configuration was available, refresh the editable installation before resolving again:

```bash
cd ~/workspace/my_experiment
uv sync --reinstall-package sagittarius-py
uv run python -m juliapkg resolve
```

## Current Editable-Install Notes

The generated `pyproject.toml` records the local source dependency through a uv source entry equivalent to:

```toml
[project]
dependencies = [
    "sagittarius-py",
]

[tool.uv.sources]
sagittarius-py = { path = "../Sagittarius/sagittarius_py", editable = true }
```

Editable experiment environments load the adjacent `Sagittarius.jl` checkout first, so Julia backend edits in the repository take effect without rebuilding a wheel. The editable dependency also points to the local checkout for Python source updates, so moving the checkout requires updating the uv source path and running `uv sync` again. Local wheel artifacts embed the Julia backend and use `package_resource` when installed away from the checkout; independent PyPI installation remains gated by Phase 13 release-readiness work. See [Python package installation status](package-installation.md).

## Run Experiment Scripts

After one-time setup, run experiment scripts with a project-local command:

```bash
cd ~/workspace/my_experiment
uv run python scripts/rabi_simulation.py
```

This is preferred over invoking the full path to `Sagittarius/sagittarius_py/.venv/bin/python`: the experiment records its own dependencies, receives an isolated environment, and remains straightforward to reproduce.

## CPU and GPU Notes

The default `juliapkg.json` is CPU-first: `uv run python -m juliapkg resolve` installs the Julia packages needed for CPU simulations without CUDA.jl, an NVIDIA driver, or GPU hardware. CUDA setup is explicit and experimental; see [Python backend setup](backend-setup.md) for the current CPU/GPU boundary.
