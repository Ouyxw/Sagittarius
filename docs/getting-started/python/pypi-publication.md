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

The repository includes `.github/workflows/phase13-testpypi.yml` as a manual workflow. It builds artifacts, runs metadata checks, publishes to TestPyPI, and verifies installation from TestPyPI in a clean virtual environment. It requires a configured TestPyPI trusted publisher or token secret before use.

## Accidental Upload Prevention

Do not configure production PyPI credentials until the publication checklist is approved. TestPyPI validation must use the test package index and must not imply production release support.
