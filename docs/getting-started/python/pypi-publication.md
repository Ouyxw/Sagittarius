# PyPI Publication Policy

Sagittarius is not published on production PyPI yet. The TestPyPI `1.0.8` candidate was distributed under MIT and is not eligible for production promotion after the Apache-2.0 licensing decision. Freeze a new `1.0.9` candidate and rerun every Phase 13 gate before production publication. Treat every package artifact as public source distribution material because the Python wheel and sdist include the embedded Julia backend under `sagittarius/julia/Sagittarius.jl`.

The candidate commit, tag, distribution digests, branch integration, CUDA timing,
and build-once promotion rules are defined by
[`SPEC-GOV-006-release-candidate-governance.md`](../../governance/SPEC-GOV-006-release-candidate-governance.md).

## Required Order

1. Confirm the repository visibility and Apache-2.0 license plan is approved.
2. Run `phase13-candidate-artifact.yml` for the immutable candidate tag. It
   requires the commit to be contained in `main`, checks version/tag/source
   agreement and a clean checkout, then builds wheel and sdist once.
3. Retain its `phase13-candidate-artifact/v1` manifest and canonical files.
4. Run metadata, forbidden-content, complete Python regression, Julia-backed
   parity, clean wheel, uninstall/reinstall, and clean sdist-install checks.
5. Make every downstream job consume or verify the same retained distributions.
6. Publish the exact release candidate to TestPyPI only.
7. Install the TestPyPI candidate into a fresh environment outside the source
   checkout and reconcile the index file digests with the candidate record.
8. Run `sagittarius backend resolve` and the minimal CPU smoke from the installed
   package.
9. Complete the final-candidate cross-platform matrix and real-hardware CUDA
   evidence gates before production PyPI.
10. Promote the exact wheel and sdist whose recorded digests passed the required
    gates; do not rebuild for production publication.
11. Install the pinned version from production PyPI outside the repository and
    retain the post-publication smoke evidence.

The separately reviewed, protected production workflow is implemented but unexecuted. Production PyPI upload remains blocked until it promotes a newly validated canonical candidate, reconciles production file hashes with the manifest, and retains a clean production-index smoke.

## Remaining CI Preconditions

The MIT TestPyPI `1.0.8` candidate passed candidate-artifact, regression, clean-artifact, cross-platform, TestPyPI, and CUDA-wheel gates as historical evidence. It cannot be promoted after the Apache-2.0 licensing decision. Apache-2.0 `1.0.9` is not yet frozen and must repeat every applicable gate. Only then may the protected production publisher promote the verified files, reconcile published hashes against the new candidate manifest, and retain a pinned production-index clean install. CUDA remains experimental and must not be described as stable in release materials.

## Historical TestPyPI Evidence

The MIT TestPyPI `1.0.8` evidence is retained as historical release-governance evidence only; it is not a consumer installation path and does not authorize a production upload. It passed the strengthened installed-package CPU smoke, including result-artifact, manifest, shared-result, and `package_resource` backend checks. Retain its versioned evidence artifact with the release record, but do not reuse it for Apache-2.0 `1.0.9`.

## Manual TestPyPI Workflow

The repository includes `.github/workflows/phase13-testpypi.yml` as a manual workflow protected by the GitHub `testpypi` environment. It downloads and verifies the canonical wheel and sdist instead of rebuilding, publishes those files through OIDC, runs the clean installed-package CPU smoke, and requires TestPyPI file hashes to equal the candidate manifest. It deliberately fails if that version already exists; each candidate must use a new PEP 440 version.

The configured pending publisher must match GitHub owner `Ouyxw`, repository `Sagittarius`, workflow `phase13-testpypi.yml`, project `sagittarius-py`, and environment `testpypi`. No TestPyPI API token is required or should be stored for this path. Each successful run uploads a `phase13-testpypi-<version>` evidence artifact with release identity, distribution hashes, the clean-install diagnostic, TestPyPI CPU result artifact, and TestPyPI file hashes.

## Accidental Upload Prevention

Do not configure production PyPI credentials outside the separately reviewed and protected production workflow. TestPyPI validation must use the test package index and must not imply production release support.
