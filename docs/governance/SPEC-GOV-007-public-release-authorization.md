# Public Open-Source Release Authorization

Spec ID: `SPEC-GOV-007`
Status: `Policy`
Roadmap: Phase 13
Version: `public-release-authorization/v1`
Last reviewed: 2026-07-22

This record defines the authorization and evidence required before Sagittarius is
made public and its verified Python release candidate is promoted to production
PyPI. It supplements
[`SPEC-GOV-002-disclosure-control.md`](SPEC-GOV-002-disclosure-control.md) and
[`SPEC-GOV-006-release-candidate-governance.md`](SPEC-GOV-006-release-candidate-governance.md).
It is an engineering governance record, not legal advice.

## Decision Scope

The intended disclosure is the complete `Ouyxw/Sagittarius` monorepo, including
the Julia SDK, Python SDK, documentation, CI workflows, and retained public
release records, under the Apache License 2.0. Sagittarius is not split for
this release: Python distributions embed the Julia backend and source
development refers to the monorepo.

Visibility change is not authorization to publish to production PyPI. Publication
remains subject to every Phase 13 gate, protected-environment approval,
canonical-artifact verification, published-hash reconciliation, and clean
production-index smoke required by `SPEC-GOV-006`.

## Authorization Record

Complete this table in the pull request that approves public disclosure. Do not
mark the decision approved until every field is complete and approvals are
recorded in GitHub.

| Field | Required record |
| :--- | :--- |
| Decision status | `Draft`, `Approved`, `Delayed`, or `Withdrawn` |
| Intended public date | `YYYY-MM-DD` |
| Repository and visibility | `Ouyxw/Sagittarius`; private to public, full monorepo and Git history |
| License | Apache-2.0; root `LICENSE` and `sagittarius_py/LICENSE` reviewed for identity |
| Owner/approver | GitHub account or authorized organization role |
| Independent reviewer | GitHub account different from the production-release operator |
| Production-release operator | GitHub account permitted to trigger the production workflow |
| Disclosure register | Link to the corresponding `SPEC-GOV-002` row or issue |
| Release candidate | Version, tag, commit SHA, canonical artifact, and evidence links |
| Exceptions | Approved exclusions, deferrals, or risk acceptance; otherwise `None` |

## Required Pre-Publication Review

- [ ] The complete reachable Git history was scanned for credentials, tokens,
      private endpoints, sensitive logs, data, and non-redistributable material.
- [ ] Repository files and generated release content were reviewed for public
      links, licensing, documentation, issue tracking, and known limitations.
- [ ] `README.md` and `sagittarius_py/README.md` do not claim production PyPI
      publication has already occurred.
- [ ] `SECURITY.md`, contribution guidance, a maintainer contact route, and
      citation guidance are present or their approved deferral is recorded.
- [ ] Public claims were checked against `SPEC-GOV-001`, `SPEC-GOV-002`,
      `SPEC-GOV-003`, and `docs/reference/known-limitations.md`.
- [ ] No release artifact or release/candidate tag was rebuilt, moved, or
      overwritten during the disclosure review.

## GitHub Approval and Execution Controls

This pull request requires approval from the owner/approver and independent
reviewer. A production-release operator must never approve their own deployment.
After the repository is public and before creating the production tag, configure
the `pypi-production` environment to:

1. Require reviewers, including someone other than the expected release operator.
2. Prevent self-review.
3. Restrict deployments to protected release tags matching `v*`.
4. Disable administrator bypass where available.
5. Retain a no-upload approval exercise showing the release operator cannot
   self-approve and receives no production credentials before approval.

Keep the GitHub Actions Trusted Publisher bound to the reviewed production
workflow and `pypi-production` environment. Do not use a long-lived PyPI API
token to bypass these controls.

## Completion Record

After the visibility change, record the public repository URL, actual public
date, approving pull request, disclosure-register link, environment-control
evidence, and follow-up issues here or in the linked release record. After
production publication, record PyPI URLs, hashes, clean-index smoke evidence,
release tag, and release notes as required by `SPEC-GOV-006`.
