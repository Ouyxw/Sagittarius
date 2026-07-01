# Python Package Installation Status

The Python SDK is not yet published as an independent PyPI package. Do not advertise `pip install sagittarius-py` as a supported user installation path until Phase 13 release-readiness criteria are met.

## Supported Today

The supported Python installation model is a complete source checkout followed by Python dependency synchronization and JuliaPkg resolution:

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

Editable installs still depend on the configured source checkout for Python code updates and should not be treated as a released wheel-install equivalent.

## Local Artifact Status

Local wheel and source-distribution builds now include the embedded Julia backend under `sagittarius/julia/Sagittarius.jl`, including `Project.toml`, `Manifest.toml`, and `src/*.jl`. Packaging tests verify those artifact contents and run an installed-wheel smoke test from outside the repository using the `package_resource` backend source. Editable/source installs continue to prefer the adjacent `source_checkout` backend for development.

## Release Artifact Smoke Test

Run the opt-in release smoke test before treating a local wheel as release-candidate material:

```bash
cd sagittarius_py
SAGITTARIUS_RUN_RELEASE_ARTIFACT_SMOKE=1 \
  uv run python -m pytest tests/test_packaging_artifacts.py::test_clean_venv_installed_wheel_release_smoke
```

The smoke test builds wheel/sdist artifacts, creates a clean seeded virtual environment outside the source tree, installs the built wheel with the venv's `python -m pip install`, runs `python -m juliapkg resolve`, runs a one-atom CPU simulation, saves a result artifact, and validates the result artifact schema, run manifest schema, shared-result schema, doctor `backend_source`, and version metadata.

## Not Supported Yet for Python Users

The following are planned Phase 13 outcomes, not current installation promises:

- independent `pip install sagittarius-py` from PyPI;
- user-facing backend setup commands such as `sagittarius backend resolve` or `sagittarius backend install cuda`;
- clean-environment wheel/sdist CI smoke tests across the declared Python, Julia, and operating-system matrix;
- uninstall/reinstall smoke tests for released wheel workflows.

## Python Wheel and Source Distribution Criteria

A release artifact is ready only after these checks pass:

- `pip install <built-wheel>` succeeds in a clean virtual environment outside the source repository;
- `import sagittarius` remains lightweight and does not initialize or download Julia packages;
- `python -m juliapkg resolve` succeeds from the clean environment;
- a CPU one-atom simulation succeeds after explicit backend resolution with no source checkout present;
- result artifacts, run manifests, shared results, doctor output, and version metadata identify the embedded `package_resource` backend correctly;
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

## Julia Native Users

Python wheels are not the Julia-native installation path. Julia users should depend on `Sagittarius.jl` directly with `Pkg.develop(path=...)` today, and with `Pkg.add(...)` only after a future Julia package registration. See [Julia projects](../julia/projects.md).
