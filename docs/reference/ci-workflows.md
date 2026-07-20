# CI Workflows

This document defines which GitHub Actions workflows run automatically, which are release gates, and how their evidence should be retained. Keep this page in sync with `.github/workflows/*.yml` when CI triggers or validation scope changes.

## Workflow Tiers

Sagittarius separates day-to-day pull-request validation from release-candidate installation validation. The fast tier should stay short enough for ordinary development, while the release tier intentionally exercises clean installs, JuliaPkg resolution, platform differences, TestPyPI, and optional GPU hardware.

The authoritative candidate identity and build-once promotion requirements live
in [`SPEC-GOV-006-release-candidate-governance.md`](../governance/SPEC-GOV-006-release-candidate-governance.md).
The current workflows retain useful per-run evidence, but production publication
must remain blocked until every required workflow consumes or verifies the same
frozen distribution digests.

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

A branch CUDA run is pre-merge risk screening. It becomes final publication
evidence only when the tested commit and wheel digest are unchanged, the commit
is contained in `main`, and that exact wheel is the production candidate.

## Known Release-Gate Gaps

The existing workflows implement useful tests, but they do not yet form a closed
production release pipeline:

| Gap | Current behavior | Required CI change |
| :--- | :--- | :--- |
| Canonical build | TestPyPI builds explicitly; clean, matrix, and CUDA tests build through their local pytest fixture. | Add one candidate build artifact and freeze manifest. |
| Candidate identity | Manual workflows accept the selected branch and do not require containment in `main` or agreement among tag, Python, and Julia versions. | Add an early identity guard shared by every release workflow. |
| Digest reuse | Workflows record some identities independently but do not all consume or reconcile the same wheel/sdist digests. | Download the canonical files and fail on any digest mismatch. |
| Artifact denylist | Packaging tests assert required content but do not reject all internal or sensitive paths. | Add wheel and sdist forbidden-content tests. |
| Sdist installation | The sdist is inspected and checked by `twine`, but release smoke installs the wheel only. | Install from the retained sdist in a clean external environment and run the CPU smoke. |
| Full regression | Fast PR CI runs a selected packaging/documentation subset; no release workflow runs the complete Python suite. | Add backend-free and Julia-backed full release-regression jobs. |
| Julia-native tests | No Julia `test/` suite or `Pkg.test()` CI job is present. | Add native Julia tests before a stable Julia-native release is claimed. |
| Final external evidence | Cross-platform evidence applies to an earlier commit; strengthened TestPyPI and real-hardware CUDA evidence remain pending for the final candidate. | Rerun every applicable gate for the frozen commit and canonical distributions. |
| Failure artifacts | Cross-platform evidence is written only after success, and clean-smoke evidence is not uploaded as a release bundle. | Upload logs and partial diagnostics with `if: always()`. |
| Production promotion | No protected production PyPI workflow or production-index install smoke exists. | Promote the validated files and verify a pinned external installation after publication. |

Until these gaps close, a workflow pass is component evidence, not approval of a
production distribution set. Supply-chain hardening should subsequently add
documentation link/build checks, dependency and license review, secret scanning,
SBOM/attestation generation, and immutable action pinning.

## Evidence Retention

For release readiness, retain:

- workflow run URL;
- commit SHA and branch or tag;
- job status for every required matrix row;
- uploaded `phase13-cross-platform-<os>-py<python>-julia<julia>` artifacts;
- a `phase13-testpypi-<version>` artifact containing commit, ref, run URL, wheel/sdist SHA-256 digests, clean-install diagnostic, installed-package CPU result artifact with schema checks, and TestPyPI JSON file hashes;
- a `phase13-cuda-wheel-<run-id>` artifact containing the GPU name/driver/memory capture, smoke log, commit, ref, run URL, runner OS, validation command, and required opt-in flags when CUDA support is being claimed.

Do not mark the Phase 13 cross-platform matrix gate complete in `REQUIREMENTS.md` until every documented matrix row has passed and its evidence is retained.

## Maintenance Rules

- Keep automatic PR workflows fast and deterministic.
- Keep release workflows explicit, auditable, and manually runnable.
- Update `docs/status.md`, `REQUIREMENTS.md`, and this document when workflow triggers, release gates, or evidence requirements change.
- Do not add `pull_request` triggers to `phase13-cross-platform.yml`, `phase13-testpypi.yml`, or `phase13-cuda-wheel.yml` without a deliberate release-process update.
