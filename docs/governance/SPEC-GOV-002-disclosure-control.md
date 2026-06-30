# Disclosure Control

Spec ID: `SPEC-GOV-002`
Status: `Policy`
Roadmap: Phase 10
Version: `disclosure-control-policy/v1`
Last reviewed: 2026-06-30


This tracker records planned and completed public disclosures that may affect Sagittarius patent strategy, performance claims, or prior-art positioning. It is an engineering control document, not legal advice. Use it before publishing release notes, benchmark reports, papers, talks, blog posts, demo videos, public repositories, or hardware-demo materials.

## Required Review Fields

Every planned disclosure should record:

- planned public date and actual public date;
- disclosure type, such as release, benchmark report, paper draft, talk, demo, or external repository update;
- owner and reviewers;
- public location or target venue;
- related commits, tags, branches, or artifact paths;
- whether performance claims are present and whether they cite `benchmark-artifact/v1` or `mwis-batch-verification/v1` evidence;
- whether Rydberg/MWIS mapping, neutral-atom tooling, or patent-sensitive implementation details are discussed;
- prior-art review status and link to [`SPEC-GOV-003-prior-art-notes.md`](SPEC-GOV-003-prior-art-notes.md) updates;
- decision: approved, approved with edits, delayed, or withdrawn.

## Disclosure Register

| ID | Status | Planned public date | Actual public date | Type | Owner | Public target | Scope | Evidence / artifacts | Review notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DISC-0001 | Template | YYYY-MM-DD | TBD | Benchmark report | TBD | TBD | Example: CUDA ablation report for specific hardware/configuration. | `benchmark-artifact/v1` path, `version-info/v1`, run manifests. | Complete performance and prior-art review before publication. |

Status values:

- `Draft`: disclosure exists but has not been reviewed.
- `Needs edits`: review found wording, artifact, prior-art, or date issues.
- `Approved`: cleared for the stated target and date.
- `Published`: publicly available; actual public date is filled in.
- `Delayed`: intentionally held for patent, artifact, or review reasons.
- `Withdrawn`: no longer planned.
- `Template`: example row only.

## Review Workflow

1. Create a disclosure row before sharing material outside the project team.
2. Attach artifacts or links for any measurement, including `benchmark-artifact/v1`, `mwis-batch-verification/v1`, `run-manifest/v1`, `shared-result/v1`, and `version-info/v1` where relevant.
3. Check performance wording against [`SPEC-GOV-001-performance-claims.md`](SPEC-GOV-001-performance-claims.md).
4. Check physics, MWIS, simulator, and neutral-atom tooling language against [`SPEC-GOV-003-prior-art-notes.md`](SPEC-GOV-003-prior-art-notes.md).
5. Remove or rewrite claims that frame known Rydberg/MWIS mappings, blockade physics, pulse-level neutral-atom programming, or generic sparse/GPU methods as Sagittarius inventions.
6. Record the decision and any required edits in the disclosure row.
7. After publication, fill in the actual public date and public URL/path.

## Trigger Examples

Create or update a row for:

- a GitHub release, tagged package release, or public branch that materially changes public API, benchmark claims, or hardware-facing workflows;
- a benchmark report, plot, generated Markdown table, or README section that cites performance numbers;
- a blog post, paper draft, slide deck, conference submission, or demo script;
- public discussion of reduced-basis cache behavior, sparse pattern reuse, CUDA value-buffer reuse, cross-language schemas, or result/benchmark artifacts;
- external sharing of MWIS/UDG examples, AQC-vs-ILP results, or hardware-demo preparation material.

No row is needed for purely internal commits that do not leave the private workspace, but a row should be created before those changes are included in a public release or public-facing report.

## Minimum Approval Checklist

Before marking a disclosure `Approved`:

- all performance statements cite artifact paths or generated artifact stems;
- hardware, versions, problem sizes, solver settings, tolerances, and backend diagnostics are named for measurements;
- prior-art-sensitive claims have been checked and rewritten using bounded wording;
- the public target and date are explicit;
- the owner has confirmed whether a patent/legal review is needed before publication;
- known limitations and backend maturity are not contradicted.

## Relationship to Other Phase 10 Documents

- [`SPEC-GOV-001-performance-claims.md`](SPEC-GOV-001-performance-claims.md) defines how measured performance can be stated.
- [`SPEC-GOV-003-prior-art-notes.md`](SPEC-GOV-003-prior-art-notes.md) defines which Rydberg/MWIS and neutral-atom concepts should be treated as background rather than Sagittarius-specific invention.
- [`known-limitations.md`](../reference/known-limitations.md) defines constraints that public disclosures should not contradict.
- [`dual-sdk-examples.md`](../getting-started/dual-sdk-examples.md) and [`minimal-examples.md`](../getting-started/minimal-examples.md) provide safer example material that should still be reviewed if published outside the repository context.
