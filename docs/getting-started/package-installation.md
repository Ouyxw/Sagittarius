# Package Installation Status

Sagittarius is not yet published as an independent PyPI package. Do not advertise `pip install sagittarius-py` as a supported user installation path until Phase 13 release-readiness criteria are met.

## Supported Today

The supported installation model is a complete source checkout followed by Python dependency synchronization and JuliaPkg resolution:

```bash
git clone <repository_url> Sagittarius
cd Sagittarius/sagittarius_py
uv sync
uv run python -m juliapkg resolve
```

For development, an editable install is also supported:

```bash
cd Sagittarius/sagittarius_py
python -m pip install -e .
python -m juliapkg resolve
```

Editable installs still depend on the repository layout. They are not relocatable and should not be treated as a wheel-install equivalent.

## Not Supported Yet

The following are planned Phase 13 outcomes, not current installation promises:

- independent `pip install sagittarius-py` from PyPI;
- a relocatable wheel that works after the source checkout is moved or deleted;
- a source distribution that packages all required Julia backend files and metadata;
- default CPU installation that avoids CUDA.jl resolution entirely;
- user-facing backend setup commands such as `sagittarius backend resolve` or `sagittarius backend install cuda`;
- clean-environment wheel/sdist CI smoke tests across the declared Python, Julia, and operating-system matrix.

## Wheel and Source Distribution Criteria

A release artifact is ready only after these checks pass:

- `pip install <built-wheel>` succeeds in a clean virtual environment outside the source repository;
- `import sagittarius` remains lightweight and does not initialize or download Julia packages;
- a CPU one-atom simulation succeeds after explicit backend resolution with no source checkout present;
- moving or deleting the original repository does not break the installed wheel;
- the wheel and sdist contain `Sagittarius.jl/Project.toml`, Julia source files, and required runtime metadata;
- default CPU installation does not require CUDA.jl, an NVIDIA driver, or GPU hardware;
- unsupported or missing Julia installations produce documented, actionable diagnostics;
- CI tests installation artifacts across the declared compatibility matrix.

## Upgrade and Uninstall Guidance

For source checkouts, upgrade by pulling or replacing the repository, then rerun environment synchronization and JuliaPkg resolution:

```bash
cd Sagittarius/sagittarius_py
uv sync
uv run python -m juliapkg resolve
```

For editable experiment projects, update the uv source path if the checkout moves, then rerun:

```bash
cd ~/workspace/my_experiment
uv sync --reinstall-package sagittarius-py
uv run python -m juliapkg resolve
```

For local virtual environments, uninstall the editable Python package with the environment manager that installed it, for example:

```bash
python -m pip uninstall sagittarius-py
```

Julia packages resolved by JuliaPkg live in Julia/PythonCall-managed environments and are not removed by uninstalling the editable Python package. Remove those environments only when you are sure no other project depends on them.
