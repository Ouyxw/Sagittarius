# Sagittarius 1.0.9 Production Release Evidence

Date: 2026-07-22

## Release Identity

| Field | Value |
| --- | --- |
| Package | `sagittarius-py` |
| Production version | `1.0.9` |
| Frozen commit | `f6f476170992c1990760692d5d5d559b6fc2982f` |
| Candidate tag | `candidate/sagittarius-py-v1.0.9-1` |
| Production tag | `v1.0.9` |
| Tag target | `f6f476170992c1990760692d5d5d559b6fc2982f` |

## Canonical Candidate

- Candidate build Run ID: [`29899337946`](https://github.com/Ouyxw/Sagittarius/actions/runs/29899337946)
- Candidate artifact: `phase13-candidate-1.0.9-29899337946`
- Candidate artifact ID: `8521239739`
- Candidate evidence artifact: `phase13-candidate-evidence-29899337946` (ID `8521240217`)

## Phase 13 Gate Record

| Gate | Run ID | Result |
| --- | --- | --- |
| Canonical Candidate Artifact | [`29899337946`](https://github.com/Ouyxw/Sagittarius/actions/runs/29899337946) | success |
| Candidate Release Regression | [`29899542150`](https://github.com/Ouyxw/Sagittarius/actions/runs/29899542150) | success |
| Clean Artifact Smoke | [`29899577252`](https://github.com/Ouyxw/Sagittarius/actions/runs/29899577252) | success |
| Cross-Platform Artifact Matrix | [`29899599154`](https://github.com/Ouyxw/Sagittarius/actions/runs/29899599154) | success |
| CUDA Wheel Smoke | [`29899623730`](https://github.com/Ouyxw/Sagittarius/actions/runs/29899623730) | success |
| TestPyPI Candidate | [`29900637622`](https://github.com/Ouyxw/Sagittarius/actions/runs/29900637622) | success |
| Production PyPI Promotion | [`29901350084`](https://github.com/Ouyxw/Sagittarius/actions/runs/29901350084) | success |

All recorded gates use the frozen commit and the canonical candidate identity above.

## PyPI Distribution Record

Project: [`sagittarius-py 1.0.9`](https://pypi.org/project/sagittarius-py/1.0.9/)

| File | SHA-256 |
| --- | --- |
| `sagittarius_py-1.0.9-py3-none-any.whl` | `ea69da9ecdf0feb75716acabd1356fc3efd8e9806ac1062a4a065b04f465471d` |
| `sagittarius_py-1.0.9.tar.gz` | `a554443b650dd62abe2c83c11b3334d0cbc4750d78e71a74635df561c1cd9262` |

The Production PyPI Promotion gate reconciled the published distribution hashes against the canonical candidate manifest before recording success.

## Independent Production Installation Evidence

The release operator completed a repository-external installation smoke in a Python 3.12 virtual environment:

- `python -m pip install sagittarius-py` installed `sagittarius-py-1.0.9` from PyPI.
- `sagittarius.version_info()` reported package version `1.0.9` and embedded Sagittarius.jl version `1.0.9`.
- The Julia backend path was installed package data and reported source `package_resource`.
- `sagittarius backend resolve` completed with return code `0`.

This confirms production-index installation and backend dependency resolution outside a source checkout.

## GitHub Release Status

As checked on 2026-07-22, the GitHub API returned no Release entry for tag `v1.0.9`; creating the GitHub Release remains a required release-record step.

- Use existing immutable tag `v1.0.9`; do not create or move a tag from the Release form.
- Attach this evidence record or link it from the Release notes after the Release is published.

## Limitations

- CPU is the default supported backend profile.
- CUDA validation passed its release gate, but CUDA remains experimental and must not be described as stable.

## Source Records

- Git tags and frozen commit: `f6f476170992c1990760692d5d5d559b6fc2982f`
- Candidate artifact: `phase13-candidate-1.0.9-29899337946`
- Gate evidence: GitHub Actions run URLs in the table above
- Published hashes: PyPI JSON for `sagittarius-py` version `1.0.9`
