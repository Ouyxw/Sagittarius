# Installation Overview

Sagittarius currently supports source-based installation from a complete repository checkout. A standalone PyPI installation is not supported yet, and `pip install sagittarius-py` should not be advertised until the Phase 13 wheel and source-distribution criteria are met.

Use this page as the installation map:

| Task | Guide |
| :--- | :--- |
| Install and test the Sagittarius repository itself. | [Source installation](source-installation.md) |
| Use Sagittarius from an independent Python experiment. | [Python experiment projects](python-experiment-projects.md) |
| Use `Sagittarius.jl` from an independent Julia project. | [Julia user projects](julia-projects.md) |
| Resolve Julia packages, choose a Julia executable, or prepare CPU/GPU backends. | [Backend setup](backend-setup.md) |
| Understand wheel, sdist, editable install, upgrade, and uninstall status. | [Package installation status](package-installation.md) |
| Use Docker or VS Code Dev Containers. | [Containerized development](containerization.md) |

## Current Support Boundary

The supported baseline is:

```bash
git clone <repository_url> Sagittarius
cd Sagittarius/sagittarius_py
uv sync
uv run python -m juliapkg resolve
```

The Python SDK currently locates the Julia backend relative to the checked-out repository, so `Sagittarius.jl/` and `sagittarius_py/` must remain together. Editable installs are useful for development and local experiments, but they still depend on the source checkout layout.

Phase 13 packaging work will make a relocatable wheel possible by packaging the Julia backend sources and project metadata inside the Python artifact. Until that work is complete, moving or deleting the source checkout can break editable installations.
