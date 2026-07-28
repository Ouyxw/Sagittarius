# Scientific Parameter Sweep Artifact

Spec ID: `SPEC-API-008`
Status: `Current`
Roadmap: Phase 15
Version: `sweep-artifact/v1`
Last reviewed: 2026-07-28

`sweep-artifact/v1` persists scientific exploration sweeps. It is intentionally distinct from `benchmark-artifact/v1`: it records parameter studies and resumability, not governed performance or verification evidence.

Each artifact contains a JSON `base_config`, named `axes` (`name`, dotted experiment-config `path`, and candidate `values`), and one item per parameter combination. Every item records its stable ID, all axis values, status (`pending`, `running`, `succeeded`, or `failed`), attempt count, result path, run-manifest path, and structured failure record. Succeeded items require both links; failed items require a failure record.

`resumability` uses `sweep-resume/v1`, listing completed IDs and retryable pending/running/failed IDs. `resume_item_ids()` returns this retry set. Save/load functions preserve the artifact path for a later process.

Use `make_sweep_artifact()`, `validate_sweep_artifact()`, `save_sweep_artifact()`, and `load_sweep_artifact()`. Do not use this artifact to make performance, scalability, hardware, or correctness claims; those require `benchmark-artifact/v1` and the governance workflow.
