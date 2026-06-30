# Development SOP for Logging and Contracts

Status: `Current`
Roadmap: Phase 6, Phase 8, Phase 10
Version: `development-sop/v1`
Last reviewed: 2026-06-30


This page summarizes the Sagittarius logging and contract design as a reusable operating procedure for other software, simulation, and algorithm projects.

The core principle is:

```text
Turn runtime behavior into named, versioned, validated, persisted, and auditable facts instead of relying on free-form logs, undocumented exceptions, or README prose.
```

## Design Model

Sagittarius separates runtime behavior into stable contract surfaces:

| Surface | Sagittarius example | Purpose |
| :--- | :--- | :--- |
| Event contract | `event-taxonomy/v1` | Defines stable runtime events, event IDs, severities, and payload fields. |
| Diagnostic contract | `doctor/v2.1`, backend probes, issue codes | Makes environment and backend failures machine-readable and actionable. |
| Run manifest contract | `run-manifest/v1` | Records how a result was produced, including requested and effective configuration. |
| Result artifact contract | `result-artifact/v1` | Persists result data together with metadata, diagnostics, manifests, and shared payloads. |
| Shared result contract | `shared-result/v1` | Provides a language-neutral result payload for Python, Julia, and downstream tools. |
| Benchmark contract | `benchmark-artifact/v1` | Makes performance measurements reproducible and claim-ready. |
| Governance contract | performance claims, disclosure control, prior-art notes | Binds public statements to artifacts and review rules. |

These surfaces should evolve independently but point to one another through stable schema names, event IDs, artifact paths, and manifest fields.

## SOP 1: Define System Boundaries First

Before designing logs or schemas, identify the project boundaries that need stable interpretation.

Typical boundaries:

- API boundary;
- input configuration boundary;
- runtime/backend boundary;
- solver or algorithm boundary;
- artifact boundary;
- benchmark boundary;
- public-claim boundary.

For each boundary, answer:

- What is the input?
- What is the output?
- How does failure appear?
- Does this need a schema version?
- Should it be persisted?
- Does it need cross-language, cross-process, or cross-machine compatibility?

If a boundary produces information that affects reproducibility, correctness, or public interpretation, it should become a contract rather than an informal convention.

## SOP 2: Create an Event Taxonomy

Do not let runtime logging grow as unstructured strings. Define a catalog of stable events.

Example event names:

```text
config_load_start
config_load_failed
solver_start
solver_finish
artifact_written
validation_failed
failure_diagnostic
```

Every event should define:

- stable event ID;
- stable event name;
- component;
- default severity;
- status such as `active` or `reserved`;
- required payload fields;
- optional payload fields.

Compatibility rules:

- event IDs must not be reused for a different meaning;
- event names should be stable filter keys;
- required fields are additive only within a compatible schema version;
- removing a field or changing its meaning requires a new schema version;
- optional fields may be added when they do not conflict with existing semantics;
- severity may become more severe for correctness or safety issues;
- reserved events may document planned cross-language or backend behavior before all emitters exist.

Text logs can still exist, but structured event payloads are the authoritative contract.

## SOP 3: Standardize Severity

Use severity levels consistently across languages and components.

| Severity | Meaning |
| :--- | :--- |
| `debug` | Development-only detail that normal users do not need. |
| `info` | Normal lifecycle event such as setup, solver progress, or artifact creation. |
| `warning` | Recoverable condition that may affect performance, fidelity, or reproducibility. |
| `error` | The current operation failed or produced unavailable runtime state. |
| `critical` | Continuing may corrupt results, environment state, or downstream artifacts. |

A warning should not mean "ignore this." It should mean "this result may require extra interpretation."

## SOP 4: Normalize Failures into Diagnostics

Avoid opaque errors such as:

```text
RuntimeError("Backend failed")
```

Prefer structured diagnostics:

```json
{
  "code": "GPU_DEVICE_NOT_FOUND",
  "message": "No CUDA device was visible to the runtime.",
  "remediation": "Check driver installation, container GPU passthrough, and backend setup.",
  "backend": "CUDA",
  "severity": "error"
}
```

A diagnostic should include:

- machine-readable `code`;
- human-readable `message`;
- actionable `remediation`;
- relevant component or backend;
- severity;
- optional raw cause when safe to expose.

The same diagnostic should be usable in logs, exceptions, manifests, artifacts, and support reports.

## SOP 5: Attach a Run Manifest to Every Result

A result should answer how it was produced without requiring the original process to still exist.

Recommended manifest fields:

- input configuration;
- normalized configuration;
- requested configuration;
- effective configuration;
- software versions;
- git commit and dirty state;
- runtime and hardware metadata;
- random seeds and trajectory metadata;
- solver or algorithm settings;
- backend settings and diagnostics;
- schema versions;
- event IDs emitted during the run;
- artifact paths.

Always distinguish requested and effective configuration. If a user requested `method="RK4"` but the backend used `Tsit5`, the manifest must record the effective truth rather than the user's intent.

## SOP 6: Separate Data, Metadata, Diagnostics, and Manifest

A durable artifact should separate concerns instead of placing all fields in one flat dictionary.

Recommended shape:

```json
{
  "schema_version": "result-artifact/v1",
  "artifact_type": "project.result",
  "data": {},
  "metadata": {},
  "diagnostics": {},
  "manifest": {},
  "shared_result": {}
}
```

Responsibilities:

| Field | Responsibility |
| :--- | :--- |
| `data` | Values users analyze directly. |
| `metadata` | Units, labels, shapes, semantic descriptions, and result-type information. |
| `diagnostics` | Runtime, backend, environment, warning, and failure information. |
| `manifest` | Reproducibility information and requested/effective configuration. |
| `shared_result` | Minimal language-neutral payload for downstream tooling. |

This makes artifacts easier to validate, migrate, and inspect.

## SOP 7: Version Every Schema

Version contract schemas independently from package versions.

Examples:

```text
event-taxonomy/v1
doctor/v2.1
run-manifest/v1
result-artifact/v1
shared-result/v1
benchmark-artifact/v1
```

Guidelines:

- writers should emit the current schema version;
- readers should preserve compatibility with supported older versions;
- adding optional fields can usually remain compatible;
- changing required fields or field meanings requires a new schema version;
- schema names should appear inside artifacts, logs, and documentation.

## SOP 8: Reuse Names Across Logs, Manifests, Tests, and Docs

Use one vocabulary across the system.

Avoid this drift:

```text
log event: solver_start
manifest field: run_begin
test helper: simulation_started
```

Prefer a shared name such as `solver_start` everywhere. This reduces documentation drift, improves searchability, and makes cross-language behavior easier to test.

## SOP 9: Reserve Future Events and Contracts Explicitly

Use a `reserved` status for planned events or contracts when the design needs to be coordinated before all implementations exist.

Rules:

- `reserved` means the semantic slot is assigned;
- `reserved` does not mean the behavior is implemented;
- `active` means at least one emitter or writer exists;
- documentation must not describe reserved behavior as available.

This is useful for projects with multiple SDKs, backends, or execution environments that land at different times.

## SOP 10: Make Benchmarks Artifact-Based

Benchmark scripts should not only print Markdown tables. They should emit structured artifacts.

A benchmark row should record:

- benchmark name and scenario;
- problem size;
- input parameters;
- backend and hardware;
- solver or algorithm settings;
- tolerances or accuracy controls;
- runtime metric names;
- memory metric names;
- repeat and warmup information;
- version metadata;
- linked run manifests;
- generated report paths.

Public performance statements should cite artifact paths or generated report stems. Local benchmark notes without current artifacts should be treated as historical diagnostics.

## SOP 11: Govern Public Claims

Separate internal observations from public claims.

Suggested levels:

| Level | Meaning |
| :--- | :--- |
| Internal diagnostic | Useful during development, not externally citable. |
| Local benchmark | A machine-specific measurement, not a project-wide claim. |
| Release artifact | Reproducible evidence for a specific version/configuration. |
| Public claim | External wording that must cite artifacts and known limitations. |
| Paper or demo statement | Public claim plus domain/prior-art review. |

Recommended wording:

```text
In artifact <path>, benchmark <name> measured <metric> on <hardware>
for <problem/config>.
```

Avoid unbounded claims such as:

- "GPU is faster";
- "scales linearly";
- "production ready";
- "efficiently solves large instances";
- "demonstrates speedup".

## SOP 12: Maintain a Documentation Status Table

Track every contract document in a status table with:

- spec ID where applicable;
- document path;
- purpose;
- roadmap link;
- status;
- update trigger.

This table tells maintainers which documents must change when APIs, artifacts, schemas, benchmarks, or public wording change.

## Minimal Adoption Plan

A new project does not need the full Sagittarius system on day one. Start with:

1. `event-taxonomy/v1` for structured logs.
2. `result-artifact/v1` for saved outputs.
3. `run-manifest/v1` for reproducibility metadata.
4. Diagnostic issue codes with remediation.
5. Benchmark artifacts instead of ad hoc timing tables.
6. Public claim rules tied to artifact evidence.
7. A documentation status table with update triggers.

## Transfer Checklist

Use this checklist when applying the SOP to another project:

- Define the stable runtime and artifact boundaries.
- Create an event catalog before logs spread across the codebase.
- Assign stable event IDs and severity conventions.
- Normalize errors into diagnostics with codes and remediation.
- Store requested and effective configuration separately.
- Persist results as versioned artifacts.
- Keep shared payloads language-neutral when multiple runtimes exist.
- Require benchmark scripts to emit structured artifacts.
- Tie public performance or capability claims to artifact evidence.
- Track every contract document in a status table.

## Summary Principles

- Logging is event-based, not string-based.
- Failures are diagnostic objects, not only exceptions.
- Results are durable artifacts, not only in-memory objects.
- Manifests record provenance, requested config, and effective config.
- Schemas are versioned independently from package releases.
- Public claims are evidence-backed and bounded by known limitations.
