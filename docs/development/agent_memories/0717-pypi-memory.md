# Phase 13 PyPI Release Memory — 2026-07-17

## Scope

The immediate goal is to complete the Sagittarius Phase 13 packaging and independent-installation release closure. Cloud adapter implementation is explicitly out of scope: the cloud-platform team will integrate with Sagittarius separately.

## Current Phase 13 State

The following repository capabilities already exist:

- Python wheel and sdist embed `sagittarius/julia/Sagittarius.jl`, including Julia project files and sources.
- Backend lookup prefers `SAGITTARIUS_JULIA_BACKEND_PATH`, then an editable/source checkout, then installed package resources. Clean wheel tests assert `backend_source == "package_resource"`.
- The default JuliaPkg profile is CPU-first; CUDA is an explicit optional backend profile installed with `sagittarius backend install cuda`.
- `phase13-clean-artifact.yml` exercises repo-external clean wheel installation and uninstall/reinstall smoke coverage.
- Cross-platform CPU matrix evidence is retained under `CI_artifacts/phase13-cross-platform-*`; roadmap records GitHub run `28577379030` as passing the five declared rows.
- TestPyPI and real-GPU CUDA workflows exist but remain manual external release gates. Production PyPI is still blocked.

Relevant files:

- `REQUIREMENTS.md`, Phase 13 (lines 141 onward)
- `.github/workflows/phase13-testpypi.yml`
- `.github/workflows/phase13-cuda-wheel.yml`
- `sagittarius_py/tests/test_packaging_artifacts.py`
- `docs/getting-started/python/pypi-publication.md`
- `docs/reference/ci-workflows.md`

## Intended Repository Changes (Not Applied)

The environment could not run `apply_patch`: it failed with a `bwrap` user-namespace creation error even when workspace write escalation was requested. No repository files were modified in this session.

When a writable patch environment is available, implement these scoped changes:

1. Harden `.github/workflows/phase13-testpypi.yml`.
   - Build wheel/sdist and verify the built package version equals the `expected-version` workflow input.
   - Remove `skip-existing: true` from the TestPyPI publish action. A release candidate must use a new version; otherwise a clean install could validate an older upload with the same version.
   - Create and upload a `phase13-testpypi-<version>` evidence artifact containing commit, ref, run URL, wheel/sdist SHA-256 digests, clean-install diagnostic, and hashes returned by `https://test.pypi.org/pypi/sagittarius-py/<version>/json`.
   - Keep the clean venv install outside the source checkout and verify `doctor()["backend_source"] == "package_resource"`.

2. Harden `.github/workflows/phase13-cuda-wheel.yml`.
   - Capture `nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader`.
   - Retain the CUDA wheel smoke log.
   - Generate and upload a `phase13-cuda-wheel-<run-id>` evidence artifact containing schema version, commit, ref, run URL, validation command, runner OS, and the required opt-in environment flags.
   - Keep CUDA experimental until this workflow passes on a real NVIDIA self-hosted runner.

3. Add static assertions in `sagittarius_py/tests/test_installation_docs.py` for these workflow safeguards, and update:
   - `docs/reference/ci-workflows.md`
   - `docs/getting-started/python/pypi-publication.md`
   - `REQUIREMENTS.md`

## External Gates and How to Execute Them

### TestPyPI

1. Create/configure TestPyPI trusted publishing for repository `SagittariusProject/Sagittarius` and workflow `phase13-testpypi.yml`; the workflow already requests `id-token: write`.
2. Alternative: configure a TestPyPI token as a GitHub Actions secret and explicitly wire it into the publish action if trusted publishing cannot be used.
3. Bump `sagittarius_py/pyproject.toml` to a new PEP 440 candidate version (for example `0.1.0rc1`). TestPyPI cannot overwrite the existing version.
4. In GitHub Actions, run “Phase 13 TestPyPI Candidate” and set `expected-version` to that exact version.
5. Retain run URL, commit SHA, TestPyPI package URL, install output, and uploaded evidence artifact.

### CUDA Hardware Evidence

1. Provision a real NVIDIA GPU Linux machine as a self-hosted GitHub Actions runner.
2. Apply labels `self-hosted`, `linux`, `x64`, and `cuda`, matching `.github/workflows/phase13-cuda-wheel.yml`.
3. Ensure `nvidia-smi`, Python 3.11, Julia 1.11, and outbound access to GitHub/Python/Julia package sources are available.
4. Run “Phase 13 CUDA Wheel Smoke” manually.
5. Retain the run URL, commit SHA, GPU driver/device details, smoke/parity logs, and uploaded CUDA evidence artifact.

### Production PyPI Approval

Before production publishing, obtain explicit approval for repository visibility, MIT licensing, README/documentation/project URLs, version/tag, and accidental-upload controls. Confirm the TestPyPI, clean artifact, cross-platform, and CUDA evidence applies to the same release candidate commit/tag. Do not repurpose the TestPyPI workflow directly for production PyPI without a separate reviewed production-release workflow.

## Constraints

- Do not advertise `pip install sagittarius-py` as a supported production path until every Phase 13 release gate is complete.
- CPU remains the default supported installation profile.
- CUDA must remain explicit and experimental until real hardware evidence is retained.
- Preserve existing schemas and package-resource diagnostics; no cloud adapter changes are authorized in this work item.
