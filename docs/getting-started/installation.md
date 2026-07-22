# Installation Overview

Sagittarius `1.0.10` is available on production PyPI. Python users should install it in a virtual environment with `python -m pip install sagittarius-py==1.0.10`; a complete repository checkout remains the supported path for contributors and source development.

Use this page as the installation map. Python and Julia user paths are split into language-specific subdirectories under `getting-started/`.

| Task | Guide |
| :--- | :--- |
| Install and test the Python SDK from a source checkout (developer path). | [Python source installation](python/source-installation.md) |
| Use Sagittarius from an independent Python experiment. | [Python experiment projects](python/experiment-projects.md) |
| Install the released Python package, or understand wheel, sdist, editable install, upgrade, and uninstall status. | [Python package installation](python/package-installation.md) |
| Resolve Julia packages, choose a Julia executable, or prepare Python CPU/GPU backend execution. | [Python backend setup](python/backend-setup.md) |
| Use `Sagittarius.jl` from an independent Julia project. | [Julia projects](julia/projects.md) |
| Prepare native Julia runtime and backend execution. | [Julia backend setup](julia/backend-setup.md) |
| Run quick Python verification examples. | [Python minimal examples](python/minimal-examples.md) |
| Run quick Julia-native verification examples. | [Julia minimal examples](julia/minimal-examples.md) |

## Current Support Boundary

The supported Python consumer baseline is:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install sagittarius-py==1.0.10
sagittarius backend resolve
```

The Python contributor baseline is:

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

Phase 13 packaging embeds the Julia backend sources and project metadata in Python artifacts. The MIT TestPyPI `1.0.8` candidate remains historical evidence and cannot be promoted after the Apache-2.0 licensing decision. Apache-2.0 `1.0.10` passed the candidate, regression, clean-artifact, cross-platform, TestPyPI, CUDA-wheel, and protected production-promotion gates; production-file hashes were reconciled and a clean production-index smoke was retained. CUDA remains experimental. The embedded copy does not replace `Sagittarius.jl` as the native Julia entry point.
