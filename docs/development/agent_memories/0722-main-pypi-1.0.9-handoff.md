# Sagittarius 1.0.9 Restart Handoff

Date: 2026-07-22

## Current Repository State

- Resume work from `main`.
- `main` is at merge commit `22b5d11` (PR #3), containing public-tree cleanup commit `b387d22`.
- `dev` was created from pre-cleanup commit `e6b3341` and retains `workspace/`, development/governance/reference documents, and archived experiments.
- Cleanup validation passed: retained Markdown links, 17 focused tests, and the complete Python test suite.
- Core files under `Sagittarius.jl/src/` and `sagittarius_py/sagittarius/` were not changed by cleanup.

## Decisions Already Approved

- Keep the existing GitHub repository and make it public when release preparation is complete.
- GitHub should retain only `main` and `dev`; no new feature development starts before 1.0.9 publication.
- `main` is the release baseline. `dev` is the later-development anchor.
- Public `main` documentation is limited to `docs/api/`, `docs/getting-started/`, `docs/physics/`, and `docs/README.md`.
- Apache-2.0 is the release license.
- The first production PyPI release should be `1.0.9`.
- Keep `scripts/phase13_candidate_artifact.py`; release workflows depend on it.

## Current 1.0.9 Blockers

- Package and Julia versions remain `1.0.8` in:
  - `sagittarius_py/pyproject.toml`
  - `Sagittarius.jl/Project.toml`
  - `sagittarius_py/sagittarius/julia/Sagittarius.jl/Project.toml`
  - `sagittarius_py/sagittarius/runtime.py` fallback
  - `sagittarius_py/uv.lock`
- Phase 13 workflow defaults and the candidate-tag default remain at `1.0.8`.
- `docs/getting-started/python/package-installation.md` has a trailing double period after the protected-workflow sentence.
- GitHub still has many remote feature/release branches. Delete all remote branches except `main` and `dev` only after final contribution/history review.
- Configure repository visibility, TestPyPI Trusted Publisher, PyPI pending Trusted Publisher, and the `testpypi` / `pypi-production` GitHub environments before upload.

## External Index State Checked on 2026-07-22

- TestPyPI `sagittarius-py` currently contains releases through `1.0.8`; `1.0.9` is available.
- Production PyPI `https://pypi.org/pypi/sagittarius-py/json` returned 404, so the production project does not yet exist.

## Next Steps

1. Return to `main` and confirm a clean worktree.
2. Finish remote branch cleanup and repository/security review; make the repository public before production publication.
3. Configure Trusted Publishing and executable GitHub environment approvals.
4. Update the five version locations, run `uv lock`, update every Phase 13 workflow default to `1.0.9`, and set the candidate default to `candidate/sagittarius-py-v1.0.9-1`.
5. Preserve documentation statements that identify MIT TestPyPI 1.0.8 as historical evidence; do not globally replace every `1.0.8` string.
6. Run the full Python suite, Julia/native smoke as applicable, packaging tests, wheel/sdist build, and `twine check`.
7. Commit the frozen release configuration to `main` and record its full SHA.
8. Create and push annotated tag `candidate/sagittarius-py-v1.0.9-1` on that exact SHA.
9. Run `Phase 13 Canonical Candidate Artifact` with version `1.0.9` and that candidate tag. Record the Run ID and artifact name `phase13-candidate-1.0.9-<run-id>`.
10. Reuse the same Run ID, artifact name, full SHA, version, and candidate tag for release regression, clean artifact, cross-platform, CUDA wheel, and TestPyPI workflows.
11. After all gates pass, create annotated production tag `v1.0.9` on the same SHA.
12. Run `Phase 13 Production PyPI Promotion` with the canonical candidate inputs and `production-tag=v1.0.9`; approve the `pypi-production` environment.
13. Verify production hashes and clean installation, create the GitHub Release, retain evidence, and update public installation docs from pending to released.

## Resume Command

After restart, ask the agent to restore context from this file, then run:

```bash
git switch main
git status --short
git log -3 --oneline --decorate
```
