# Package Installation Status

Python package installation status lives under the Python getting-started section. Julia-native users should use the Julia project guide.

## Current Guides

- [Python package installation status](python/package-installation.md)
- [Python source installation](python/source-installation.md)
- [Python backend setup](python/backend-setup.md)
- [Julia projects](julia/projects.md)

## Release Artifact Readiness

Local wheel and source-distribution artifacts can be built from `sagittarius_py/` and are tested to contain the embedded Julia backend under `sagittarius/julia/Sagittarius.jl`. The release smoke test is opt-in because it creates a clean virtual environment, installs the built wheel, runs `python -m juliapkg resolve`, initializes Julia, runs a one-atom CPU simulation, and validates the saved result artifact, run manifest, doctor output, and version metadata.

```bash
cd sagittarius_py
SAGITTARIUS_RUN_RELEASE_ARTIFACT_SMOKE=1 \
  uv run python -m pytest tests/test_packaging_artifacts.py::test_clean_venv_installed_wheel_release_smoke
```

This is a local release-readiness gate, not PyPI publication approval. PyPI remains blocked until backend setup commands, clean CI execution, uninstall/reinstall smoke tests, package metadata review, and the cross-platform support matrix are complete.

The old path is kept as a compatibility entry so existing links continue to land on the right language-specific guide.
