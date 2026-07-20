# PyPI Publication Policy

Sagittarius is not published on production PyPI yet. Treat every package artifact as public source distribution material because the Python wheel and sdist include the embedded Julia backend under `sagittarius/julia/Sagittarius.jl`.

The candidate commit, tag, distribution digests, branch integration, CUDA timing,
and build-once promotion rules are defined by
[`SPEC-GOV-006-release-candidate-governance.md`](../../governance/SPEC-GOV-006-release-candidate-governance.md).

## Required Order

1. Confirm the repository visibility and MIT license plan is approved.
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

Production PyPI upload remains blocked until the Phase 13 release-readiness table marks every PyPI gate complete.

## Remaining CI Preconditions

Canonical build-once distributions, ref/version/`main` identity enforcement,
digest-verified reuse, wheel/sdist denylist checks, clean retained-sdist
installation, TestPyPI digest reconciliation, and unconditional current-gate
evidence uploads are implemented. Remaining CI work is complete Python release
regression, native Julia `Pkg.test()` coverage, a protected production publisher,
production digest reconciliation, and a production-index installation smoke.

The existing cross-platform pass applies to its recorded historical commit. The
strengthened TestPyPI CPU smoke and the real-hardware CUDA smoke must run against
the final candidate distributions. Earlier or independently rebuilt artifacts do
not close those gates.

## Validated TestPyPI Candidate

The trusted-publishing workflow successfully published and clean-installed `sagittarius-py==1.0.0` from TestPyPI. This is clean-install evidence only; it does not authorize a production PyPI upload. The workflow now also executes a one-atom CPU simulation from the installed package, validates its result artifact, manifest, shared-result schema, and `package_resource` backend source, and retains that result as evidence. Because `1.0.0` predates this CPU-smoke gate, the next frozen candidate must pass the strengthened workflow. External users evaluating that candidate should use the documented version-pinned, dual-index command in [Python package installation status](package-installation.md). Retain the corresponding `phase13-testpypi-1.0.0` evidence artifact with the release record.

## Manual TestPyPI Workflow

The repository includes `.github/workflows/phase13-testpypi.yml` as a manual workflow protected by the GitHub `testpypi` environment. It downloads and verifies the canonical wheel and sdist instead of rebuilding, publishes those files through OIDC, runs the clean installed-package CPU smoke, and requires TestPyPI file hashes to equal the candidate manifest. It deliberately fails if that version already exists; each candidate must use a new PEP 440 version.

The configured pending publisher must match GitHub owner `Ouyxw`, repository `Sagittarius`, workflow `phase13-testpypi.yml`, project `sagittarius-py`, and environment `testpypi`. No TestPyPI API token is required or should be stored for this path. Each successful run uploads a `phase13-testpypi-<version>` evidence artifact with release identity, distribution hashes, the clean-install diagnostic, TestPyPI CPU result artifact, and TestPyPI file hashes.

## Accidental Upload Prevention

Do not configure production PyPI credentials until the publication checklist is approved. TestPyPI validation must use the test package index and must not imply production release support.
