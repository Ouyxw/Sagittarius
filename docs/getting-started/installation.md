# Installation Overview

Sagittarius is preparing its first production PyPI promotion. The package is not available on production PyPI yet, so do not advertise or run an unqualified `pip install sagittarius-py` command as a current installation path. Until publication completes, a complete repository checkout is the supported path for users and contributors.

Use this page as the installation map. Python and Julia user paths are split into language-specific subdirectories under `getting-started/`.

| Task | Guide |
| :--- | :--- |
| Install and test the Python SDK from a source checkout (developer path). | [Python source installation](python/source-installation.md) |
| Use Sagittarius from an independent Python experiment. | [Python experiment projects](python/experiment-projects.md) |
| Install a released Python package after publication, or understand wheel, sdist, editable install, upgrade, and uninstall status. | [Python package installation](python/package-installation.md) |
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

The Python SDK resolves the Julia backend through an explicit lookup order: `SAGITTARIUS_JULIA_BACKEND_PATH` for environment overrides, an adjacent editable/source checkout, and packaged backend resources embedded under `sagittarius/julia/Sagittarius.jl`. Editable source installs prefer the checkout so Julia source edits take effect immediately; wheel installs use the packaged backend resource when no adjacent checkout exists. Julia-native users depend on `Sagittarius.jl` directly and do not need the Python wheel path.

Phase 13 packaging embeds the Julia backend sources and project metadata in Python artifacts. The current canonical candidate has passed its candidate, regression, clean-artifact, cross-platform, TestPyPI, and CUDA-wheel validation gates; CUDA nevertheless remains experimental. The separately reviewed, protected production-promotion workflow is implemented; its approved run must still reconcile production-file hashes and retain a clean production-index smoke before publication. The embedded copy does not replace `Sagittarius.jl` as the native Julia entry point.
