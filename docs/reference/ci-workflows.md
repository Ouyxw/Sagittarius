# CI Workflows

This document defines which GitHub Actions workflows run automatically, which are release gates, and how their evidence should be retained. Keep this page in sync with `.github/workflows/*.yml` when CI triggers or validation scope changes.

## Workflow Tiers

Sagittarius separates day-to-day pull-request validation from release-candidate installation validation. The fast tier should stay short enough for ordinary development, while the release tier intentionally exercises clean installs, JuliaPkg resolution, platform differences, TestPyPI, and optional GPU hardware.

| Workflow | Trigger | Runs on | Purpose | Expected use |
| :--- | :--- | :--- | :--- | :--- |
| `.github/workflows/pr-fast-ci.yml` | Automatic on pull requests to `develop/**` and `main`; automatic on direct pushes to `develop/**` as a fallback; manual on demand | `ubuntu-latest` | Fast documentation, metadata, artifact-content, and portable benchmark import checks. | Every feature, documentation, packaging, and CI PR; direct develop pushes are still discouraged but covered. |
| `.github/workflows/phase13-clean-artifact.yml` | Automatic on relevant pushes to `main`; manual on demand | `ubuntu-latest` | Clean wheel install plus uninstall/reinstall release smoke outside the source checkout. | Release-prep, packaging/backend changes, or manual verification before publication. |
| `.github/workflows/phase13-cross-platform.yml` | Manual only | Linux, macOS, Windows matrix | Release-candidate OS/Python/Julia artifact matrix with uploaded per-row evidence. | Run before marking cross-platform wheel evidence complete. |
| `.github/workflows/phase13-testpypi.yml` | Manual only, protected by the `testpypi` environment | `ubuntu-latest` | Build, verify candidate version, publish to TestPyPI through OIDC, verify a clean install, and retain release evidence. | Run only with a new candidate version after TestPyPI trusted publishing and publication policy are ready. |
| `.github/workflows/phase13-cuda-wheel.yml` | Manual only | Self-hosted Linux CUDA runner | Hardware-backed CUDA wheel smoke and CPU/CUDA parity with retained GPU and smoke-log evidence. | Run only when validating CUDA wheel support on real NVIDIA hardware. |

## Pull Request CI

Ordinary PRs should rely on `pr-fast-ci.yml`. It deliberately avoids JuliaPkg clean-environment release smokes and cross-platform matrix jobs because those can take many minutes per platform. Direct pushes to `develop/**` also run this workflow as a safety net, but feature work should still enter `develop/**` through PRs when branch protection is available.

The fast PR workflow currently runs:

```bash
uv run python -m pytest   tests/test_installation_docs.py   tests/test_benchmark_artifacts.py   tests/test_packaging_artifacts.py::test_python_package_metadata_is_release_ready   tests/test_packaging_artifacts.py::test_wheel_metadata_contains_release_fields   tests/test_packaging_artifacts.py::test_sdist_contains_readme_license_and_pyproject_metadata   tests/test_packaging_artifacts.py::test_wheel_contains_embedded_julia_backend   tests/test_packaging_artifacts.py::test_sdist_contains_embedded_julia_backend   -q
```

Feature PRs should add targeted tests for the changed subsystem in addition to relying on the automatic fast workflow. For example, Phase 15 sampling work should include sampling, serialization, manifest, and documentation tests in the PR validation notes.

## Release Gate CI

The following workflows are release gates and should not be required for every feature PR:

- `phase13-clean-artifact.yml`
- `phase13-cross-platform.yml`
- `phase13-testpypi.yml`
- `phase13-cuda-wheel.yml`

Run them for release candidates, package/backend changes, or when their specific evidence is needed. The cross-platform, TestPyPI, and CUDA workflows remain manual because they are expensive, depend on external services or hardware, and produce release evidence rather than ordinary development feedback.

## Evidence Retention

For release readiness, retain:

- workflow run URL;
- commit SHA and branch or tag;
- job status for every required matrix row;
- uploaded `phase13-cross-platform-<os>-py<python>-julia<julia>` artifacts;
- a `phase13-testpypi-<version>` artifact containing commit, ref, run URL, wheel/sdist SHA-256 digests, clean-install diagnostic, and TestPyPI JSON file hashes;
- a `phase13-cuda-wheel-<run-id>` artifact containing the GPU name/driver/memory capture, smoke log, commit, ref, run URL, runner OS, validation command, and required opt-in flags when CUDA support is being claimed.

Do not mark the Phase 13 cross-platform matrix gate complete in `REQUIREMENTS.md` until every documented matrix row has passed and its evidence is retained.

## Maintenance Rules

- Keep automatic PR workflows fast and deterministic.
- Keep release workflows explicit, auditable, and manually runnable.
- Update `docs/status.md`, `REQUIREMENTS.md`, and this document when workflow triggers, release gates, or evidence requirements change.
- Do not add `pull_request` triggers to `phase13-cross-platform.yml`, `phase13-testpypi.yml`, or `phase13-cuda-wheel.yml` without a deliberate release-process update.
