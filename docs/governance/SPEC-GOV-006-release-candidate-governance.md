# Release Candidate and Publication Governance

Spec ID: `SPEC-GOV-006`
Status: `Policy`
Roadmap: Phase 13
Version: `release-candidate-governance/v1`
Last reviewed: 2026-07-20


This document defines how Sagittarius turns reviewed source into a frozen Python
release candidate, validates that candidate, and promotes the validated files to
production PyPI. It supplements
[`SPEC-GOV-005-repository-versioning.md`](SPEC-GOV-005-repository-versioning.md)
and
[`pypi-publication.md`](../getting-started/python/pypi-publication.md).

## Decision Summary

Sagittarius uses `main` as the integration and release lineage. Feature branches
are temporary implementation branches, not version identities. A release is
identified by an immutable source commit, version, tag, wheel and sdist digests,
and retained gate evidence.

The required release path is:

```text
reviewed feature branches
          |
          v
        main
          |
          v
frozen candidate commit and tag
          |
          v
build wheel and sdist once
          |
          +--> metadata and content checks
          +--> clean CPU install and reinstall
          +--> cross-platform matrix
          +--> TestPyPI installed-package smoke
          `--> real-hardware CUDA smoke and parity
                    |
                    v
       approve and promote the same files
                    |
                    v
              production PyPI
```

Production publication is forbidden when any required gate refers to a different
source commit, package version, wheel digest, or sdist digest from the files being
published.

## Branch Model

The normal branch model is a lightweight GitHub Flow:

- `main` is the only permanent integration branch and must remain buildable and
  testable.
- `feature/<topic>`, `fix/<topic>`, and `docs/<topic>` are short-lived branches
  merged through reviewed pull requests.
- Ordinary feature branch names do not contain a package version. The target
  version can change while a feature is under review.
- `release/<major>.<minor>` is created only when an older stable series must be
  maintained while `main` has moved to a newer incompatible series.
- A release branch is not required for every patch release and must not become a
  second development integration branch.
- Merged, duplicated, superseded, and abandoned branches are deleted after their
  unique commits and retained evidence have been accounted for.

Direct production publication from a feature or development branch is not
allowed. A candidate commit must be contained in `main` before its artifacts can
be approved for production.

## Versions and Tags

The Python version in `sagittarius_py/pyproject.toml` and Julia version in
`Sagittarius.jl/Project.toml` normally advance together when the embedded Julia
backend or shared semantics change. Schema versions remain independent.

Tags follow these rules:

- Tags used as release identities are immutable after they are pushed.
- A candidate tag may identify a frozen build before final approval, for example
  `candidate/sagittarius-py-v1.0.7-1`.
- The production tag uses `v<version>`, for example `v1.0.7`, and points to the
  exact source commit used to build the published files.
- The candidate and production tags may point to the same commit after all gates
  pass.
- If a frozen final-version candidate fails and its source must change, do not
  move its tag or overwrite its distributions. Freeze a new version or candidate
  identity.
- If PEP 440 prerelease versions are used, the package version and tag must agree,
  for example package `1.1.0rc1` and tag `v1.1.0rc1`.

When an existing candidate tag was created on a feature branch, either merge
without rewriting the tagged commit so it becomes part of `main`, or abandon
that candidate and freeze a new identity from the final `main` commit. A squash
merge rewrites commit identity and therefore invalidates a tag attached to the
pre-merge commit as a production source identity.

## Candidate Freeze Record

Before executing release gates, record:

- package name and intended version;
- candidate tag and full commit SHA;
- whether the worktree was clean;
- Python and Julia package versions;
- schema versions exposed by the candidate;
- release scope, linked requirements, and included pull requests;
- known limitations and unresolved non-blocking defects;
- disclosure review status;
- build command and build environment;
- wheel and sdist filenames, sizes, and SHA-256 digests.

Changing source, dependency locks, embedded Julia files, packaging metadata, or
artifact contents invalidates the freeze. A new candidate record and applicable
gate evidence are then required.

## Build Once and Promote the Same Files

The wheel and sdist are the release subjects, not merely by-products of a branch.
Sagittarius should build the candidate distribution set once in a clean job and
make downstream gates consume those retained files.

Each downstream workflow must verify:

- expected package version;
- source commit and candidate tag;
- wheel and sdist SHA-256 digests;
- Python and embedded Julia version parity when required;
- artifact-content allowlist and denylist;
- the relevant evidence schema and gate result.

TestPyPI, clean-install, cross-platform, and CUDA jobs must not silently rebuild
independent candidate files and treat them as equivalent. If a platform-specific
rebuild is ever required, it is a separate distribution with its own filename,
digest, provenance, and gate matrix.

Production publication promotes the previously validated files. Rebuilding after
approval requires a new freeze and new evidence.

## Package and Documentation Boundary

PyPI artifacts are public distribution material. The wheel should contain only
the Python runtime package, required embedded Julia backend, license, README, and
packaging metadata. The sdist should contain only the source and metadata required
to reproduce that package build.

Artifact tests must positively require necessary files and reject unintended
content, including:

- repository and CI configuration;
- editor settings;
- tests not intentionally shipped as package data;
- internal agent memories and prompt material;
- debug scripts and scratch workspaces;
- local result, benchmark, and CI evidence directories;
- credentials, environment files, tokens, and private keys.

The PyPI README and stable user documentation describe only released behavior.
Development documentation from `main` must be marked as unreleased or published
under a separate `dev` version. Internal development material must not appear in
the user documentation navigation.

Artifact exclusion is not a repository disclosure control. If the source
repository becomes public, its tracked files and Git history require a separate
review under
[`SPEC-GOV-002-disclosure-control.md`](SPEC-GOV-002-disclosure-control.md).
Patent-related, credential-bearing, private, or otherwise restricted content
must be resolved before repository publication.

## Gate Model

### Pull Request and Pre-Merge Gates

The following establish merge readiness:

- scoped review and documented release impact;
- fast CI and affected subsystem tests;
- Python/Julia parity checks for shared semantic changes;
- documentation, schema, and known-limitation updates;
- package metadata and artifact-content checks for packaging changes;
- no unresolved release-blocking correctness defects.

A CUDA run on a feature or candidate branch is useful pre-merge risk screening,
especially for changes to CUDA profiles, solver dispatch, embedded Julia code, or
GPU diagnostics. It is not by itself final publication evidence if the merge
changes the source commit or the final artifact digest.

### Frozen Candidate Release Gates

The final distribution set must pass all gates applicable to the claimed support:

| Gate | Required evidence |
| :--- | :--- |
| Metadata and contents | Version checks, `twine check`, required-file allowlist, forbidden-file denylist, wheel/sdist digests. |
| Clean CPU installation | Repository-external install, backend resolution, one-atom simulation, artifact/schema checks, uninstall/reinstall. |
| Cross-platform | Every declared OS/Python/Julia row with commit, version, distribution digest, command, and result. |
| TestPyPI | Installed-package diagnostic and CPU smoke for the uploaded files, plus TestPyPI file digests. |
| CUDA hardware | Real NVIDIA runner identity, GPU/driver/runtime diagnostics, CUDA setup, CPU/CUDA parity, result metadata, log, and tested wheel digest. |
| Disclosure and approval | Repository visibility, license, documentation, public claims, known limitations, and production environment approval. |

The CUDA release gate is closed only when it tests the same wheel digest intended
for production. A pre-merge CUDA pass may be reused only when the tested commit
and artifact remain unchanged and the commit is incorporated into `main` without
rewriting. Otherwise rerun CUDA against the final retained artifact.

CUDA remains experimental until the required real-hardware evidence is retained.
A missing GPU runner does not block ordinary feature integration when the PR is
otherwise safe; it blocks the production claim and production release gate.

## Workflow Identity Requirements

Manual release workflows must reject an invocation when release identity is
ambiguous. Before publication they should enforce:

- the selected ref is the approved candidate tag or an explicitly approved full
  commit SHA;
- the full SHA is contained in `main`;
- workflow input, Python version, Julia version, and tag agree;
- the expected distribution filenames and digests match the freeze record;
- evidence names include the package version or run identity;
- protected GitHub environments separate TestPyPI and production PyPI approval;
- production credentials are unavailable to ordinary branch workflows.

Workflow evidence must retain the run URL, ref, full commit SHA, distribution
digests, runner identity, validation command, gate result, and relevant diagnostic
or result artifacts. Failed gate artifacts are evidence and must not be filtered
out.

## Current CI Gap Register

The following register reflects the workflows and tests present on 2026-07-20.
`Done` means the CI control is implemented, not that a final candidate has passed
it. `Mixed` means part of the control or historical evidence exists but final
closure still has missing implementation or execution evidence.

| CI capability | Status | Current implementation or required closure |
| :--- | :--- | :--- |
| Canonical candidate build | Done | `phase13-candidate-artifact.yml` builds wheel and sdist once and records identity, filenames, sizes, versions, and SHA-256 digests in `phase13-candidate-artifact/v1`. |
| Ref and version identity guard | Done | The candidate job requires a version-bearing immutable tag, exact checkout/tag/full-SHA agreement, containment in `origin/main`, a clean tree, and matching Python, canonical Julia, and embedded Julia versions. |
| Cross-workflow artifact reuse | Done | Manual clean-install, cross-platform, TestPyPI, and CUDA jobs download the selected candidate run and reject manifest, filename, size, version, tag, commit, or digest disagreement. The automatic `main` clean smoke remains a branch diagnostic rather than frozen-candidate evidence. |
| Artifact forbidden-content tests | Done | Wheel and sdist tests reject repository configuration, internal development paths, debug files, scratch/evidence paths, environment files, and private-key suffixes. |
| Clean sdist installation | Done | Clean and matrix release jobs install the retained sdist outside the repository and run backend resolution, package-resource, schema, and one-atom CPU checks. |
| Full Python release regression | Planned | Run the complete Python test suite for the frozen candidate, separating backend-free and Julia-backed jobs where useful. The fast PR subset is not sufficient release evidence. |
| Julia-native regression | Planned | Establish a Julia `test/` suite and run `Pkg.test()` before claiming a simultaneous stable Julia-native release. Python-driven backend tests do not replace native package tests. |
| Final-candidate platform and service evidence | Mixed | Rerun clean CPU, every declared platform row, the strengthened TestPyPI CPU smoke, and real-hardware CUDA parity for the final commit and distribution digests. Earlier runs remain historical evidence only. |
| Digest reconciliation | Mixed | Canonical downloads are verified locally and TestPyPI file hashes must exactly equal the manifest. Production upload and post-publication digest reconciliation remain unavailable. |
| Failure evidence retention | Done | Candidate, clean, matrix, TestPyPI, and CUDA jobs use unconditional status/evidence steps and retain available logs, identities, manifests, diagnostics, and partial results. |
| Production publication and post-install smoke | Planned | Add a separately protected production workflow that promotes the validated files, then installs the pinned version from production PyPI outside the repository and records the result. |

The current CUDA smoke and parity test is implemented; its missing work is a
successful real-NVIDIA execution against the final candidate wheel. The current
cross-platform matrix has historical passing evidence, and the current TestPyPI
workflow has earlier clean-install evidence, but neither closes a later candidate
unless commit and distribution digests match.

The following supply-chain checks are recommended hardening after the blocking
identity and regression gaps above are closed:

- Markdown link or documentation build checks;
- dependency vulnerability and license checks;
- secret scanning;
- an SBOM and artifact attestation;
- pinning third-party GitHub Actions to reviewed immutable commit SHAs.

These controls support public release quality, but they must not be reported as
substitutes for software, numerical, parity, installation, or hardware
verification.

## Production Approval Checklist

Before production PyPI upload, the release owner confirms:

- [ ] Release scope is frozen and the candidate commit is contained in `main`.
- [ ] Candidate tag, package versions, and release record agree.
- [ ] The worktree used for the build was clean.
- [ ] Wheel and sdist contents passed required and forbidden content checks.
- [ ] Wheel and sdist SHA-256 digests are recorded.
- [ ] The complete Python release regression passed for the frozen candidate.
- [ ] Required Julia-backed parity tests passed; `Pkg.test()` passed when a
      stable Julia-native release is being claimed.
- [ ] Clean CPU install and uninstall/reinstall evidence passed.
- [ ] A clean installation and CPU smoke from the retained sdist passed.
- [ ] Every claimed cross-platform row passed for the candidate distributions.
- [ ] TestPyPI installed-package CPU evidence passed for the candidate files.
- [ ] TestPyPI file digests equal the canonical candidate digests.
- [ ] Real-hardware CUDA evidence passed for the candidate wheel when CUDA support
      is included in the release claim.
- [ ] Required failure evidence was retained rather than discarded.
- [ ] Known limitations and CUDA maturity wording match the evidence.
- [ ] Repository visibility, MIT licensing, project URLs, issue tracker, README,
      user docs, and disclosure review are approved.
- [ ] Production publishing uses a protected environment and the exact validated
      files.
- [ ] Release notes link the commit, tags, digests, evidence, compatibility
      information, and known limitations.

Publishing is prohibited while any required item is incomplete.

## Post-Publication Record

Retain the production PyPI URLs and file hashes, GitHub release URL, tags, source
commit, candidate freeze record, all gate evidence, approval decision, and release
notes. Verify a clean installation from production PyPI after index propagation.

Published PyPI files and Git tags are immutable release records. If a release is
defective, publish a corrected version. Yank a release only when necessary and
record the reason; do not replace its files or move its tag.

## Current Branch Transition Snapshot

This snapshot records the migration identified on 2026-07-20. It is operational
context, not the permanent branch model.

| Branch or ref | Disposition before production release |
| :--- | :--- |
| `feature/v1.0.0-pypi` | Treat as the current integration candidate. Review its combined Phase 13, sampling, visualization, documentation, and version changes; incorporate the approved history into `main`; stop using it as a permanent release line. |
| `develop/v.1.0.0` | Already contained in the candidate. Retire after the approved work is incorporated into `main`. |
| `feature/v1.0.0-visual` and `feature/v1.0.0-visualization` | Duplicate refs at the same commit and contained in the candidate. Retire after integration. |
| `feature/v1.0.0-save`, `feature/v1.0.0-standardlization`, `feature/v1.0.0-logging`, `feature/v1.0.0-verification` | Account for any local-only state, then retire because their remote work is contained in later history. |
| `release/v1.0.0` | Obsolete as a release line and not the current candidate source. Confirm the local-only commit is retained in approved history, then retire the branch. |
| `feature/v1.0.0-benchmarking` | Local alias of `main`; retire after confirming no worktree depends on it. |
| `feature/v1.0.0-patent` | Review its unique commit under disclosure and patent controls. Do not merge it into a public release by default. |
| `feature/v1.0.0-test` | Review its unique commits and either cherry-pick useful tests or archive the branch. |
| `analog-sdk` | Review and extract its unique historical change if still needed, then archive the stale line. |
| `v1.0.1`, `v1.0.2` | Do not move the pushed tags. Determine whether each frozen candidate is retained or abandoned. A production tag must identify approved source contained in `main` and the exact published distributions. |

Do not delete branches until unique commits, local-only commits, open pull requests,
and retained CI evidence have been checked. Branch deletion is repository cleanup,
not a substitute for a release record.

## Maintenance Triggers

Update this policy when any of the following changes:

- permanent branch model or tag naming;
- Python/Julia version coordination;
- candidate freeze or production approval rules;
- wheel/sdist content policy;
- TestPyPI, CUDA, cross-platform, or clean-install release gates;
- evidence identity, retention, or promotion workflow;
- repository visibility or disclosure requirements.
