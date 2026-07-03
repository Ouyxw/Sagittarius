# Benchmark Artifact Contracts

Status: `Planned contract`
Roadmap: Phase 16
Version: `benchmark-artifact-contracts/v1`
Last reviewed: 2026-07-02

This page defines the Phase 16 aggregate artifact expectations for benchmark suites. It does not replace existing `benchmark-artifact/v1`, `run-manifest/v1`, `result-artifact/v1`, `shared-result/v1`, or `version-info/v1` contracts. It defines how benchmark-family artifacts should use and link those contracts.

## Artifact Types

| Artifact | Purpose | Status |
| :--- | :--- | :--- |
| `benchmark-artifact/v1` | Generic performance and scaling benchmark rows. | Current where emitted by existing scripts. |
| `mwis-batch-verification/v1` | UDG/MWIS batch verification rows and exact-baseline comparison. | Current in project-specific form. |
| `benchmark-suite-artifact/v1` | Planned aggregate wrapper for Phase 16 family/tier runs. | Planned contract. |
| `run-manifest/v1` | Durable description of one simulation run. | Current where simulations emit artifacts. |
| `result-artifact/v1` | Simulation result data, metadata, diagnostics, and shared payload. | Current where result serialization is used. |

Existing scripts may continue emitting `benchmark-artifact/v1`. New Phase 16 family runners should either reuse that schema directly or wrap multiple artifacts in `benchmark-suite-artifact/v1`.

## Aggregate Shape

A `benchmark-suite-artifact/v1` document should use this top-level shape:

```json
{
  "schema_version": "benchmark-suite-artifact/v1",
  "artifact_type": "benchmark.suite",
  "suite_id": "phase16-physics-baselines",
  "family": "physics_baselines",
  "tier": "correctness",
  "protocol_version": "benchmark-protocol/v1",
  "generated_at": "2026-07-02T00:00:00Z",
  "source": {},
  "environment": {},
  "scenario_defaults": {},
  "rows": [],
  "summary": {},
  "diagnostics": []
}
```

## Required Row Fields

Every row should include:

- `row_id`: stable row identifier;
- `scenario_id`: scenario name including size, seed, and backend where useful;
- `family`: benchmark family;
- `tier`: benchmark tier;
- `status`: one of `passed`, `failed`, `skipped`, or `incomplete`;
- `stage`: setup, reference, solve, validation, artifact, reporting, or teardown;
- `problem`: problem type, atom count, geometry, graph metadata, or basis metadata;
- `solver`: method, tolerances, `adaptive`, `dt`, output grid, and effective settings;
- `backend`: CPU/CUDA/backend path and diagnostics summary;
- `observables`: observable names, count, and output sample count;
- `metrics`: correctness and performance metrics that apply to the row;
- `artifacts`: linked run manifest, result artifact, companion CSV, Markdown, or log paths;
- `failure`: structured failure object when `status` is not `passed`;
- `disclosure_status`: `local_only`, `reviewable`, or `release_grade`.

## Failure Rows

Failures are part of the benchmark result. A failed scale row is often more useful than silently omitting the case.

Failure rows should include:

- failure stage;
- exception type or diagnostic code;
- short message;
- remediation hint where available;
- timeout, memory, or GPU memory at failure where available;
- backend diagnostic issue code when backend setup is involved;
- whether retry is expected to be deterministic;
- whether the failure invalidates only one row or the whole suite.

## Metrics

Recommended correctness metrics:

- `max_abs_error`;
- `final_state_error`;
- `trace_error`;
- `min_density_eigenvalue`;
- `mwis_feasible`;
- `objective_value`;
- `objective_gap`;
- `approximation_ratio`;
- `cpu_cuda_max_abs_error`;
- `dense_reduced_max_abs_error`.

Recommended performance metrics:

- `runtime_seconds`;
- `runtime_median_seconds`;
- `runtime_p25_seconds`;
- `runtime_p75_seconds`;
- `runtime_min_seconds`;
- `runtime_max_seconds`;
- `process_peak_memory_mb`;
- `gpu_memory_peak_mb`;
- `basis_size`;
- `basis_pruning_ratio`;
- `trajectories_per_second`;
- `jobs_per_second`.

## Evidence Retention

For reviewable or release-grade evidence, retain:

- aggregate JSON artifact;
- companion CSV and Markdown reports where generated;
- run manifests and result artifacts;
- command used to generate the artifact;
- commit SHA and dirty-state flag;
- environment metadata;
- backend diagnostics;
- disclosure row when public wording is planned.

Local exploratory artifacts can be retained outside the repository, but any public or release-candidate evidence should be stored in a durable artifact location and referenced by path or URL in the review record.

## Compatibility Rules

Compatible changes may add optional fields or new metric names. Incompatible changes require a new schema version when they remove required fields, rename existing metric semantics, change status meanings, or alter how linked artifacts are resolved.
