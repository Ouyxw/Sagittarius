# Wheel-Installed Python Experiment Recipe

This guide verifies the Phase 15 wheel-installed recipe requirement with a
small UDG/MWIS workflow. The script is an external-project template, not a
packaged module: copy
[`workspace/examples/recipes/wheel_installed_mwis_udg.py`](../../../workspace/examples/recipes/wheel_installed_mwis_udg.py)
into your own project before running it. It imports only public `sagittarius`
APIs, NumPy, and the Python standard library.

The workflow is CPU-first and exploratory. Its exact three-node reference is
only an interpretation aid; it makes no optimization-performance or hardware
claim.

## Ubuntu WSL External Project

Create the project outside the Sagittarius checkout. `/tmp` is useful for a
clean smoke environment; use a persistent location for real experiment data.

```bash
PROJECT_DIR=/tmp/sagittarius-wheel-mwis
rm -rf "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/scripts"
cd "$PROJECT_DIR"
git init
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install sagittarius-py==1.0.11
sagittarius backend resolve
```

Copy the template from a source checkout or its reviewed repository location:

```bash
cp /path/to/Sagittarius/workspace/examples/recipes/wheel_installed_mwis_udg.py scripts/mwis_udg.py
python scripts/mwis_udg.py --output-dir artifacts/mwis-udg
```

The script writes:

- `mwis_udg_wheel.result.json`: the authoritative `result-artifact/v1` envelope;
- `mwis_udg_wheel.run-manifest.json`: an inspection copy of the embedded `run-manifest/v1`;
- `mwis_udg_wheel.measurement-samples.json`: deterministic `measurement-samples/v1` data for 64 shots.

Confirm that the installed wheel, rather than a nearby source checkout, owns
the Julia backend:

```bash
sagittarius doctor
```

The JSON report should identify `backend_source` as `package_resource`. Keep
the result artifact when using this numerical output in later analysis.

## Release Smoke Contract

The repository contains an opt-in test that creates a temporary external
project under `/tmp`, installs a built wheel, resolves the backend, copies this
recipe, and validates its artifacts with the installed package:

```bash
cd Sagittarius/sagittarius_py
SAGITTARIUS_RUN_WHEEL_RECIPE_SMOKE=1 \
  uv run python -m pytest \
  tests/test_packaging_artifacts.py::test_clean_venv_installed_wheel_mwis_recipe_smoke
```

The test is intentionally outside ordinary PR CI because it builds an artifact,
creates a clean environment, and initializes the Julia backend. It is suitable
for release-oriented validation and local installed-wheel diagnosis.
