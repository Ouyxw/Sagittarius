# Installation Overview

Sagittarius currently supports source-based installation from a complete repository checkout. A standalone PyPI installation is not supported yet, and `pip install sagittarius-py` should not be advertised until the Phase 13 wheel and source-distribution criteria are met.

Use this page as the installation map. Python and Julia user paths are split into language-specific subdirectories under `getting-started/`.

| Task | Guide |
| :--- | :--- |
| Install and test the Python SDK from a source checkout. | [Python source installation](python/source-installation.md) |
| Use Sagittarius from an independent Python experiment. | [Python experiment projects](python/experiment-projects.md) |
| Understand Python wheel, sdist, editable install, upgrade, and uninstall status. | [Python package installation status](python/package-installation.md) |
| Resolve Julia packages, choose a Julia executable, or prepare Python CPU/GPU backend execution. | [Python backend setup](python/backend-setup.md) |
| Use `Sagittarius.jl` from an independent Julia project. | [Julia projects](julia/projects.md) |
| Prepare native Julia runtime and backend execution. | [Julia backend setup](julia/backend-setup.md) |
| Run quick Python verification examples. | [Python minimal examples](python/minimal-examples.md) |
| Run quick Julia-native verification examples. | [Julia minimal examples](julia/minimal-examples.md) |
| Compare equivalent Python and Julia workflows. | [Dual SDK examples](dual-sdk-examples.md) |
| Use Docker or VS Code Dev Containers. | [Containerized development](containerization.md) |

## Current Support Boundary

The supported Python baseline is:

```bash
git clone <repository_url> Sagittarius
cd Sagittarius/sagittarius_py
uv sync
uv run python -m juliapkg resolve
```

The supported Julia-native baseline is:

```bash
git clone <repository_url> Sagittarius
mkdir -p my_julia_experiment
cd my_julia_experiment
julia --project=. -e 'using Pkg; Pkg.develop(path="../Sagittarius/Sagittarius.jl"); Pkg.instantiate()'
```

The Python SDK currently locates the Julia backend relative to the checked-out repository, so `Sagittarius.jl/` and `sagittarius_py/` must remain together for Python source/editable installs. Julia-native users depend on `Sagittarius.jl/` directly and do not need the Python wheel path.

Phase 13 packaging work will make a relocatable Python wheel possible by packaging the Julia backend sources and project metadata inside the Python artifact. That does not replace `Sagittarius.jl` as the native Julia entry point.
