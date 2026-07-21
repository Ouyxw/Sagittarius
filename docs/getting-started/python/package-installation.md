# Python Package Installation

This is the authoritative guide for Python package installation. Sagittarius is preparing a production PyPI promotion, but it is not published on production PyPI yet. Do not run or advertise `pip install sagittarius-py` as a current consumer-install command. After publication, this guide will state the released version and production install command.

## Developer Source Installation

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

## Planned Production Installation

After a successful production upload and production-index smoke, the consumer path will be a version-pinned PyPI installation followed by backend resolution:

```bash
python -m pip install sagittarius-py==<released-version>
sagittarius backend resolve
sagittarius doctor
```

Do not substitute a candidate version for `<released-version>` or use this command before publication. The expected doctor report identifies `backend_source` as `package_resource`. The default package profile is CPU-first; CUDA remains an explicit experimental backend profile and requires its own setup.

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

## Publication Status

The current canonical candidate has passed its candidate build, release regression, clean-artifact, cross-platform, TestPyPI, and CUDA-wheel gates. CUDA remains experimental. Production publication is still pending a separately reviewed and protected promotion workflow that uploads the same canonical files, reconciles production file hashes with the candidate manifest, and records a clean production-index installation smoke. See the [PyPI publication policy](pypi-publication.md).

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
- the canonical candidate passes the candidate build, regression, clean-artifact, cross-platform, TestPyPI, and CUDA-wheel gates; before publication, a protected exact-file promotion, production hash reconciliation, and production-index smoke remain required.

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
