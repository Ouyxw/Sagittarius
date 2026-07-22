# CI Workflows

This document defines which GitHub Actions workflows run automatically, which are release gates, and how their evidence should be retained. Keep this page in sync with `.github/workflows/*.yml` when CI triggers or validation scope changes.

## Workflow Tiers

Sagittarius separates day-to-day pull-request validation from release-candidate installation validation. The fast tier should stay short enough for ordinary development, while the release tier intentionally exercises clean installs, JuliaPkg resolution, platform differences, TestPyPI, and optional GPU hardware.

The authoritative candidate identity and build-once promotion requirements live
in [`SPEC-GOV-006-release-candidate-governance.md`](../governance/SPEC-GOV-006-release-candidate-governance.md).
The release workflows now share one manifest-bound candidate distribution set.
The production-promotion workflow is implemented but unexecuted; production publication remains blocked until a newly frozen candidate passes every gate and the workflow records production digest reconciliation and a production-index smoke.

| Workflow | Trigger | Runs on | Purpose | Expected use |
| :--- | :--- | :--- | :--- | :--- |
| `.github/workflows/pr-fast-ci.yml` | Automatic on pull requests to `develop/**` and `main`; automatic on direct pushes to `develop/**` as a fallback; manual on demand | `ubuntu-latest` | Fast documentation, metadata, artifact-content, and portable benchmark import checks. | Every feature, documentation, packaging, and CI PR; direct develop pushes are still discouraged but covered. |
| `.github/workflows/phase13-candidate-artifact.yml` | Manual only | `ubuntu-latest` | Validate tag/commit/`main`/version identity, build wheel and sdist once, apply content checks, and record `phase13-candidate-artifact/v1`. | Run first for a frozen candidate; pass its run ID and artifact name to every downstream gate. |
| `.github/workflows/phase13-release-regression.yml` | Manual only | `ubuntu-latest` | Manifest-bound backend-free Python, Julia-backed Python, and native Julia `Pkg.test()` regression. | Run after the canonical build and before external publication gates. |
| `.github/workflows/phase13-clean-artifact.yml` | Automatic on relevant pushes to `main`; manual on demand | `ubuntu-latest` | Automatic branch diagnostic or canonical-candidate clean wheel, sdist, and uninstall/reinstall smoke outside the checkout. | Use the manual canonical path for final-candidate evidence; automatic `main` runs are diagnostics. |
| `.github/workflows/phase13-cross-platform.yml` | Manual only | Linux, macOS, Windows matrix | Release-candidate OS/Python/Julia artifact matrix with uploaded per-row evidence. | Run before marking cross-platform wheel evidence complete. |
| `.github/workflows/phase13-testpypi.yml` | Manual only, protected by the `testpypi` environment | `ubuntu-latest` | Verify and publish the canonical files through OIDC, reconcile TestPyPI hashes, verify a clean install, and retain release evidence. | Run only with a new candidate version after TestPyPI trusted publishing and publication policy are ready. |
| `.github/workflows/phase13-cuda-wheel.yml` | Manual only | Self-hosted Linux CUDA runner | Hardware-backed CUDA wheel smoke and CPU/CUDA parity with retained GPU and smoke-log evidence. | Run only when validating CUDA wheel support on real NVIDIA hardware. |
| `.github/workflows/phase13-production-pypi.yml` | Manual only, protected by the `pypi-production` environment | `ubuntu-latest` | Promote the manifest-verified canonical wheel and sdist through OIDC, reconcile production hashes, and retain a clean production-index smoke. | Run only after all 1.0.8 candidate gates pass and production approval is granted. |

## Pull Request CI

Ordinary PRs should rely on `pr-fast-ci.yml`. It deliberately avoids JuliaPkg clean-environment release smokes and cross-platform matrix jobs because those can take many minutes per platform. Direct pushes to `develop/**` also run this workflow as a safety net, but feature work should still enter `develop/**` through PRs when branch protection is available.

The fast PR workflow currently runs:

```bash
uv run python -m pytest   tests/test_installation_docs.py   tests/test_benchmark_artifacts.py   tests/test_packaging_artifacts.py::test_python_package_metadata_is_release_ready   tests/test_packaging_artifacts.py::test_wheel_metadata_contains_release_fields   tests/test_packaging_artifacts.py::test_sdist_contains_readme_license_and_pyproject_metadata   tests/test_packaging_artifacts.py::test_wheel_contains_embedded_julia_backend   tests/test_packaging_artifacts.py::test_sdist_contains_embedded_julia_backend   tests/test_packaging_artifacts.py::test_wheel_excludes_forbidden_release_content   tests/test_packaging_artifacts.py::test_sdist_excludes_forbidden_release_content   tests/test_packaging_artifacts.py::test_candidate_manifest_records_and_verifies_distributions   -q
```

Feature PRs should add targeted tests for the changed subsystem in addition to relying on the automatic fast workflow. For example, Phase 15 sampling work should include sampling, serialization, manifest, and documentation tests in the PR validation notes.

## Release Gate CI

The following workflows are release gates and should not be required for every feature PR:

- `phase13-candidate-artifact.yml`
- `phase13-release-regression.yml`
- `phase13-clean-artifact.yml`
- `phase13-cross-platform.yml`
- `phase13-testpypi.yml`
- `phase13-cuda-wheel.yml`

Run `phase13-candidate-artifact.yml` first with the immutable candidate tag and
expected version. Supply its run ID, artifact name, full commit, version, and tag
to the manual regression, clean, matrix, TestPyPI, and CUDA workflows. Every regression job downloads and verifies the same manifest-bound distributions before validation begins.

A branch CUDA run is pre-merge risk screening. It becomes final publication
evidence only when the tested commit and wheel digest are unchanged, the commit
is contained in `main`, and that exact wheel is the production candidate.

## Remaining Release-Gate Gaps

Canonical identity, build-once reuse, artifact denylist, retained-sdist smoke,
TestPyPI digest reconciliation, and current-gate failure uploads are implemented.
The production pipeline remains open on these items:

| Gap | Current behavior | Required CI change or evidence |
| :--- | :--- | :--- |
| Final regression evidence | The manifest-bound backend-free Python, Julia-backed Python, and native Julia `Pkg.test()` gates passed for the current canonical candidate. | Rerun them for every new candidate and retain their evidence. |
| Final external evidence | Clean artifact, every declared matrix row, TestPyPI, and real-hardware CUDA gates passed for the current canonical candidate. | Rerun every applicable gate when the candidate commit or distribution digests change. |
| Production digest reconciliation | The protected production workflow compares PyPI JSON hashes with the manifest after upload. | Execute it only for the frozen candidate and retain its evidence artifact. |
| Production promotion | The protected workflow downloads and verifies canonical files; it never rebuilds distributions. | Complete environment approval and the production-index smoke for the frozen candidate. |

Until these gaps close, implemented controls and individual passes do not approve
a production distribution set. Supply-chain hardening should subsequently add
documentation link/build checks, dependency and license review, secret scanning,
SBOM/attestation generation, and immutable action pinning.

## Evidence Retention

For release readiness, retain:

- workflow run URL;
- commit SHA and branch or tag;
- job status for every required matrix row;
- the canonical candidate artifact and its `candidate-manifest.json`;
- unconditional job-result and available log/diagnostic artifacts from failed
  candidate, clean, matrix, TestPyPI, or CUDA gates;
- uploaded `phase13-cross-platform-<os>-py<python>-julia<julia>` artifacts;
- a `phase13-testpypi-<version>` artifact containing commit, ref, run URL, wheel/sdist SHA-256 digests, clean-install diagnostic, installed-package CPU result artifact with schema checks, and TestPyPI JSON file hashes;
- a `phase13-cuda-wheel-<run-id>` artifact containing the GPU name/driver/memory capture, smoke log, commit, ref, run URL, runner OS, validation command, and required opt-in flags when CUDA support is being claimed.

Do not mark the Phase 13 cross-platform matrix gate complete in `docs/development/requirements.md` until every documented matrix row has passed and its evidence is retained.

## Maintenance Rules

- Keep automatic PR workflows fast and deterministic.
- Keep release workflows explicit, auditable, and manually runnable.
- Update `docs/development/status.md`, `docs/development/requirements.md`, and this document when workflow triggers, release gates, or evidence requirements change.
- Do not add `pull_request` triggers to `phase13-cross-platform.yml`, `phase13-testpypi.yml`, or `phase13-cuda-wheel.yml` without a deliberate release-process update.
