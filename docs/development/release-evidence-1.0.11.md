# Sagittarius 1.0.11 Production Release Evidence

Date: 2026-07-23

## Release Identity

| Field | Value |
| --- | --- |
| Package | `sagittarius-py` |
| Production version | `1.0.11` |
| Frozen commit | `66b2cce519a8ee88d11edc1f300e5e9b7754c10e` |
| Candidate tag | `candidate/sagittarius-py-v1.0.11-4` |
| Production tag | `v1.0.11` |
| Tag target | `66b2cce519a8ee88d11edc1f300e5e9b7754c10e` |

## Canonical Candidate

- Candidate build Run ID: [`29989396534`](https://github.com/Ouyxw/Sagittarius/actions/runs/29989396534)
- Candidate artifact: `phase13-candidate-1.0.11-29989396534`
- Candidate artifact ID: `8556401194`
- Candidate evidence artifact: `phase13-candidate-evidence-29989396534` (ID `8556401459`)

## Phase 13 Gate Record

| Gate | Run ID | Result |
| --- | --- | --- |
| Canonical Candidate Artifact | [`29989396534`](https://github.com/Ouyxw/Sagittarius/actions/runs/29989396534) | success |
| Candidate Release Regression | [`29989571980`](https://github.com/Ouyxw/Sagittarius/actions/runs/29989571980) | success |
| Clean Artifact Smoke | [`29989589283`](https://github.com/Ouyxw/Sagittarius/actions/runs/29989589283) | success |
| Cross-Platform Artifact Matrix | [`29989636919`](https://github.com/Ouyxw/Sagittarius/actions/runs/29989636919) | success |
| CUDA Wheel Smoke | [`29989611165`](https://github.com/Ouyxw/Sagittarius/actions/runs/29989611165) | success |
| TestPyPI Candidate | [`29990620722`](https://github.com/Ouyxw/Sagittarius/actions/runs/29990620722) | success |
| Production PyPI Promotion | [`29992955813`](https://github.com/Ouyxw/Sagittarius/actions/runs/29992955813) | success |

All recorded release gates resolve to the frozen commit and canonical candidate identity above. Earlier failed candidates remain immutable evidence and are not part of this promotion record.

## PyPI Distribution Record

Project: [`sagittarius-py 1.0.11`](https://pypi.org/project/sagittarius-py/1.0.11/)

| File | SHA-256 |
| --- | --- |
| `sagittarius_py-1.0.11-py3-none-any.whl` | `2638bedc7c8419f50f8856eb8cf15549bf262b6e444abb0aee6ca002f88fbdf0` |
| `sagittarius_py-1.0.11.tar.gz` | `b4ae37dc820625323fe0bd097d5bd0180a9cfa6c878968a9e38a0d8966204e24` |

The Production PyPI Promotion gate promoted canonical files without rebuilding and reconciled the production hashes against the candidate manifest before recording success.

## Independent Production Installation Evidence

PyPI JSON confirms that both `1.0.11` distribution files are publicly available. The user-facing installation documentation records `python -m pip install sagittarius-py==1.0.11`, followed by `sagittarius backend resolve`. The protected Production PyPI Promotion gate retained the production-index installation smoke as release evidence.

## GitHub Release Status

As checked on 2026-07-23, the GitHub API returned no Release entry for tag `v1.0.11`; creating a GitHub Release remains a release-record step.

- Use the existing immutable tag `v1.0.11`; do not create or move a tag from the Release form.
- Attach this evidence record or link it from the GitHub Release notes after the Release is published.

## Limitations

- CPU is the default supported backend profile.
- CUDA remains experimental despite the retained hardware-backed smoke evidence.
