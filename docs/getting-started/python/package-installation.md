# Python Package Installation Status

The Python SDK is not yet published as an independent PyPI package. Do not advertise `pip install sagittarius-py` as a supported user installation path until Phase 13 release-readiness criteria are met. See [PyPI publication policy](pypi-publication.md) and [Python compatibility matrix](compatibility-matrix.md) for TestPyPI, platform, and production-release gates.

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

## CI Workflow Policy

Ordinary pull requests use the lightweight automatic PR workflow. Clean wheel, cross-platform, TestPyPI, and CUDA workflows are release gates and are either `main`-only or manual. See [CI workflows](../../reference/ci-workflows.md) for the authoritative trigger matrix, release evidence requirements, and maintenance rules.

## Release Artifact Smoke Test

Run the opt-in release smoke tests before treating a local wheel as release-candidate material:

```bash
cd sagittarius_py
SAGITTARIUS_RUN_RELEASE_ARTIFACT_SMOKE=1 \
  uv run python -m pytest \
  tests/test_packaging_artifacts.py::test_clean_venv_installed_wheel_release_smoke \
  tests/test_packaging_artifacts.py::test_clean_venv_installed_wheel_uninstall_reinstall_smoke
```

The smoke tests build wheel/sdist artifacts, create clean seeded virtual environments outside the source tree, install the built wheel with the venv's `python -m pip install`, run the installed `sagittarius backend resolve` command, run a one-atom CPU simulation, save a result artifact, and validate the result artifact schema, run manifest schema, shared-result schema, doctor `backend_source`, and version metadata. The uninstall/reinstall smoke additionally uninstalls the wheel, verifies the package is no longer importable, reinstalls the same wheel, reruns backend resolution, and confirms the reinstalled package still uses the embedded `package_resource` backend rather than a stale source checkout.

## Not Supported Yet for Python Users

The following are planned Phase 13 outcomes, not current installation promises:

- independent `pip install sagittarius-py` from PyPI;
- passing evidence from the cross-platform wheel/sdist matrix workflow across the declared Python, Julia, and operating-system rows;
- successful TestPyPI publication and clean install evidence;
- hardware-backed CUDA wheel smoke execution on a real GPU runner;
- passing release-candidate evidence from the clean wheel and uninstall/reinstall smokes.

## Python Wheel and Source Distribution Criteria

A release artifact is ready only after these checks pass:

- `pip install <built-wheel>` succeeds in a clean virtual environment outside the source repository;
- `import sagittarius` remains lightweight and does not initialize or download Julia packages;
- `sagittarius backend resolve` succeeds from the clean environment;
- a CPU one-atom simulation succeeds after explicit backend resolution with no source checkout present;
- result artifacts, run manifests, shared results, doctor output, and version metadata identify the embedded `package_resource` backend correctly;
- uninstalling and reinstalling the same wheel outside the source repository still resolves the embedded `package_resource` backend;
- the wheel and sdist contain `Sagittarius.jl/Project.toml`, Julia source files, and required runtime metadata;
- default CPU installation does not require CUDA.jl, an NVIDIA driver, or GPU hardware;
- unsupported or missing Julia installations produce documented, actionable diagnostics;
- wheel and sdist pass metadata checks, including `twine check`;
- Ubuntu CI runs the clean artifact and uninstall/reinstall smokes; the manual cross-platform matrix workflow, TestPyPI install evidence, and hardware-backed CUDA wheel smoke evidence must still pass before release claims.

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

For local wheel smoke environments, upgrade by reinstalling the same built wheel into the target virtual environment, then rerun backend resolution from outside the source checkout:

```bash
python -m pip install --force-reinstall dist/sagittarius_py-<version>-py3-none-any.whl
sagittarius backend resolve
```

To verify release-candidate reinstall behavior, uninstall the package, confirm it is no longer importable, reinstall the wheel, and rerun a minimal CPU simulation. The automated uninstall/reinstall smoke performs this sequence in a clean repo-external virtual environment.

For local virtual environments, uninstall the editable Python package with the environment manager that installed it, for example:

```bash
python -m pip uninstall sagittarius-py
```

Julia packages resolved by JuliaPkg live in Julia/PythonCall-managed environments and are not removed by uninstalling the editable Python package. Remove those environments only when you are sure no other project depends on them.

## Julia Native Users

Python wheels are not the Julia-native installation path. Julia users should depend on `Sagittarius.jl` directly with `Pkg.develop(path=...)` today, and with `Pkg.add(...)` only after a future Julia package registration. See [Julia projects](../julia/projects.md).
