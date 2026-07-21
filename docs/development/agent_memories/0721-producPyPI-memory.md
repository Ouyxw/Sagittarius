# Phase 13 Production PyPI Promotion Memory — 2026-07-21

## Current Release State

- `main`, `origin/main`, and annotated tag `v1.0.7` point to commit `e2975d2` (`fix(cuda): parse backend profile specs in Julia`).
- The repository worktree was clean when this memory was written.
- The `v1.0.7` canonical-candidate release gates have all passed, as reported by the release operator:
  - Phase 13 Canonical Candidate Artifact
  - Phase 13 Candidate Release Regression
  - Phase 13 Clean Artifact Smoke
  - Phase 13 Cross-Platform Artifact Matrix
  - Phase 13 TestPyPI Candidate
  - Phase 13 CUDA Wheel Smoke

CUDA remains **experimental** despite the CUDA wheel smoke passing. CPU remains the default supported profile.

## Recent CI and Packaging Fixes

The following Phase 13 control-plane fixes have been incorporated through the historical candidate tags:

- A canonical candidate artifact is built once and consumers download and verify its manifest.
- Candidate download verification uses the workspace destination so relative manifest paths remain correct under `uv --directory`.
- Python 3.10 artifact verification receives TOML support through the locked Python environment.
- The backend-free regression excludes GPU-only project tests; GPU validation belongs to the explicit CUDA runner.
- Julia native `Pkg.test()` has `Test` declared in `[extras]` and `[targets]`.
- CUDA backend profile installation serializes package specs as JSON and parses them in Julia. This fixes the Julia 1.11 failure `syntax: { } vector syntax is discontinued` caused by embedding Python/JSON dictionaries directly in Julia source.

The local CUDA diagnosis established that the hardware and `CUDA.jl 6.2.0` were functional; the failure was profile-install source generation, not runner hardware or package availability.

## Production PyPI Decision

Do **not** immediately promote the existing `v1.0.7` artifact to production PyPI.

Although its gates passed, both `README.md` and `sagittarius_py/README.md` still state that independent production PyPI installation is unsupported and contain stale TestPyPI candidate guidance. `sagittarius_py/README.md` is package metadata and is embedded in the wheel/sdist, so it becomes the public PyPI project description.

Publishing `v1.0.7` would therefore create a public documentation contradiction. A post-tag documentation commit cannot repair the README embedded in an already-built `1.0.7` artifact.

## Required Next Release Sequence

1. Update the user-facing Python documentation before creating the production-promotion workflow/run:
   - Keep `README.md` and `sagittarius_py/README.md` aligned.
   - Make `docs/getting-started/python/package-installation.md` the authoritative Python package-install guide.
   - Update `docs/getting-started/installation.md` and `docs/getting-started/python/source-installation.md` so source installation is clearly the developer path, while package installation is the release path.
   - Remove stale `sagittarius-py==1.0.0` TestPyPI examples and no-longer-true "production unsupported" wording.
   - Update `docs/getting-started/python/experiment-projects.md` and the Python compatibility matrix.
   - Preserve explicit CUDA setup and experimental-status language; do not claim CUDA is stable merely because its smoke gate passed.
   - Update the release-facing records: `REQUIREMENTS.md`, `docs/status.md`, `docs/reference/ci-workflows.md`, `docs/getting-started/python/pypi-publication.md`, and `docs/governance/SPEC-GOV-006-release-candidate-governance.md`.
   - Keep CI run IDs, artifact hashes, and evidence links in governance/release records, not in the user-facing README.
2. Bump the package and Julia versions to `1.0.8`, refresh the lockfile as required, commit, and create immutable tag `v1.0.8`.
3. Build a new `1.0.8` canonical candidate and rerun every Phase 13 gate listed above. The README change must be present in the wheel/sdist that is validated and later promoted.
4. Add a separately reviewed, protected production PyPI promotion workflow. It must promote only the verified canonical candidate rather than rebuilding from a mutable checkout.
5. After a successful production upload, reconcile PyPI's published wheel/sdist hashes against the canonical manifest and run a clean production-index install smoke outside the checkout.
6. Only after those publication checks succeed, change wording from release-pending to "available on PyPI", record the release evidence, and create the public release entry if authorized.

## Documentation Wording Constraint

Before publication, documentation may describe the intended production install command and release prerequisites, but it must not state that the package is already available on production PyPI. After publication, use the exact released version in examples or an intentionally chosen supported upgrade command, and retain source checkout instructions for contributors.

## Guardrails

- Never move or overwrite existing release tags; use the next patch version for every changed candidate.
- Do not use the TestPyPI workflow as the production publisher. Production requires a distinct reviewed workflow and explicit approval.
- Production promotion must retain the canonical-artifact contract, manifest verification, published-hash reconciliation, and clean-environment smoke evidence.
- Preserve existing diagnostic and artifact schemas. No cloud adapter work is in scope.
