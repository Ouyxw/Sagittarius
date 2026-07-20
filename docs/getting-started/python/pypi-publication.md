# PyPI Publication Policy

Sagittarius is not published on production PyPI yet. Treat every package artifact as public source distribution material because the Python wheel and sdist include the embedded Julia backend under `sagittarius/julia/Sagittarius.jl`.

## Required Order

1. Confirm the repository visibility and MIT license plan is approved.
2. Build wheel and sdist from a clean checkout.
3. Run artifact metadata checks, including `twine check` over both files.
4. Publish the exact release candidate to TestPyPI only.
5. Install the TestPyPI candidate into a fresh environment outside the source checkout.
6. Run `sagittarius backend resolve` and the minimal CPU smoke from the installed package.
7. Complete uninstall/reinstall, cross-platform matrix, and GPU evidence gates before production PyPI.

Production PyPI upload remains blocked until the Phase 13 release-readiness table marks every PyPI gate complete.

## Manual TestPyPI Workflow

The repository includes `.github/workflows/phase13-testpypi.yml` as a manual workflow, protected by the GitHub `testpypi` environment. It builds wheel and sdist artifacts, verifies that both contain the requested version, runs metadata checks, publishes to TestPyPI with GitHub OIDC trusted publishing, and verifies installation from TestPyPI in a clean virtual environment. It deliberately fails if that version already exists; each candidate must use a new PEP 440 version.

The configured pending publisher must match GitHub owner `Ouyxw`, repository `Sagittarius`, workflow `phase13-testpypi.yml`, project `sagittarius-py`, and environment `testpypi`. No TestPyPI API token is required or should be stored for this path. Each successful run uploads a `phase13-testpypi-<version>` evidence artifact with release identity, distribution hashes, the clean-install diagnostic, and TestPyPI file hashes.

## Accidental Upload Prevention

Do not configure production PyPI credentials until the publication checklist is approved. TestPyPI validation must use the test package index and must not imply production release support.
