# Sagittarius 1.0.10 Production Release Evidence

Date: 2026-07-22

## Release Identity

| Field | Value |
| --- | --- |
| Package | `sagittarius-py` |
| Production version | `1.0.10` |
| Frozen commit | `a5be2777360e81ab00e4a56c88b49fb22a3df86e` |
| Candidate tag | `candidate/sagittarius-py-v1.0.10-1` |
| Production tag | `v1.0.10` |
| Tag target | `a5be2777360e81ab00e4a56c88b49fb22a3df86e` |

## Canonical Candidate

- Candidate build Run ID: [`29906225856`](https://github.com/Ouyxw/Sagittarius/actions/runs/29906225856)
- Candidate artifact: `phase13-candidate-1.0.10-29906225856`
- Candidate artifact ID: `8523936506`
- Candidate evidence artifact: `phase13-candidate-evidence-29906225856` (ID `8523936803`)

## Phase 13 Gate Record

| Gate | Run ID | Result |
| --- | --- | --- |
| Canonical Candidate Artifact | [`29906225856`](https://github.com/Ouyxw/Sagittarius/actions/runs/29906225856) | success |
| Candidate Release Regression | [`29906430034`](https://github.com/Ouyxw/Sagittarius/actions/runs/29906430034) | success |
| Clean Artifact Smoke | [`29906613911`](https://github.com/Ouyxw/Sagittarius/actions/runs/29906613911) | success |
| Cross-Platform Artifact Matrix | [`29906642197`](https://github.com/Ouyxw/Sagittarius/actions/runs/29906642197) | success |
| CUDA Wheel Smoke | [`29906671692`](https://github.com/Ouyxw/Sagittarius/actions/runs/29906671692) | success |
| TestPyPI Candidate | [`29908050753`](https://github.com/Ouyxw/Sagittarius/actions/runs/29908050753) | success |
| Production PyPI Promotion | [`29908906977`](https://github.com/Ouyxw/Sagittarius/actions/runs/29908906977) | success |

All recorded gates use the frozen commit and the canonical candidate identity above.

## PyPI Distribution Record

Project: [`sagittarius-py 1.0.10`](https://pypi.org/project/sagittarius-py/1.0.10/)

| File | SHA-256 |
| --- | --- |
| `sagittarius_py-1.0.10-py3-none-any.whl` | `e9f18eefed0f6e494ad7b5e671198f58aad2b77a7b51de64ecef97617ee7d7db` |
| `sagittarius_py-1.0.10.tar.gz` | `8521be2219001ef242ff44def59685562ef5ea6fae9adefe792a91340c2552bd` |

The Production PyPI Promotion gate reconciled the published distribution hashes against the canonical candidate manifest before recording success.

## Independent Production Installation Evidence

PyPI JSON confirms that both 1.0.10 distribution files are publicly available. The user-facing installation documentation records the production command `python -m pip install sagittarius-py==1.0.10` and the backend resolution command `sagittarius backend resolve`. A separate repository-external command transcript is not included in this evidence record.

## GitHub Release Status

As checked on 2026-07-22, the GitHub API returned no Release entry for tag `v1.0.10`; creating the GitHub Release remains a release-record step.

- Use existing immutable tag `v1.0.10`; do not create or move a tag from the Release form.
- Attach this evidence record or link it from the Release notes after the Release is published.

## Limitations

- CPU is the default supported backend profile.
