# Event Taxonomy

Sagittarius uses a stable event taxonomy for runtime logs, diagnostics, run manifests, and cross-language Python/Julia observability. The Python package exposes the catalog through `sagittarius.event_taxonomy()` and individual entries through `sagittarius.get_event_spec(name)`.

Schema version: `event-taxonomy/v1`

## Severity Conventions

| Severity | Meaning | Python logging level |
| :--- | :--- | :---: |
| `debug` | Development-only detail that is not expected in normal production runs. | `DEBUG` |
| `info` | Normal lifecycle event for setup, diagnostics, solver progress, or artifact creation. | `INFO` |
| `warning` | Recoverable condition that may affect performance, fidelity, or reproducibility. | `WARNING` |
| `error` | Operation failed or produced unavailable runtime state with remediation guidance. | `ERROR` |
| `critical` | Process-level failure where continuing may corrupt results or environment state. | `CRITICAL` |

## Compatibility Rules

- Event IDs are stable once published and must not be reused for a different semantic meaning.
- Event names are stable `snake_case` labels suitable for filtering logs and manifests.
- Required payload fields are additive only across compatible schema updates. Removing or changing the meaning of a required field requires a new schema version.
- Optional payload fields may be added without a schema bump when their names do not conflict with existing semantics.
- Default severity may become more severe only for correctness or safety issues.
- `reserved` entries document planned cross-language events before all emitters exist; they keep their assigned IDs.

## Catalog

| Event ID | Name | Component | Severity | Status | Required Fields | Optional Fields |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| `SAG-EVT-0001` | `backend_init_start` | runtime | `info` | active | `setup` | - |
| `SAG-EVT-0002` | `backend_init_finish` | runtime | `info` | active | `julia_version` | - |
| `SAG-EVT-0003` | `backend_init_failed` | runtime | `error` | active | `code`, `message` | - |
| `SAG-EVT-0004` | `doctor_report` | runtime | `info` | active | `backend`, `available`, `issues` | - |
| `SAG-EVT-0005` | `solver_start` | solver | `info` | active | `backend`, `use_gpu`, `reltol`, `abstol`, `blockade_radius` | `method`, `use_mc` |
| `SAG-EVT-0006` | `solver_finish` | solver | `info` | active | `result_type`, `basis_size` | `backend` |
| `SAG-EVT-0007` | `cluster_setup_start` | cluster | `info` | active | `n_workers` | - |
| `SAG-EVT-0008` | `cluster_setup_finish` | cluster | `info` | active | `n_workers` | - |
| `SAG-EVT-0009` | `backend_selected` | runtime | `info` | reserved | `backend`, `use_gpu` | - |
| `SAG-EVT-0010` | `basis_generated` | physics | `info` | active | `atom_count`, `basis_size`, `full_basis_size`, `blockade_radius` | `reduced_basis_pruning_ratio` |
| `SAG-EVT-0011` | `hamiltonian_built` | physics | `info` | active | `atom_count`, `basis_size`, `use_gpu` | `backend`, `nnz` |
| `SAG-EVT-0012` | `gpu_allocation` | runtime | `info` | reserved | `backend`, `ok` | `bytes`, `device`, `code`, `message` |
| `SAG-EVT-0013` | `failure_diagnostic` | runtime | `error` | reserved | `code`, `message`, `remediation` | `backend`, `severity` |

## Log Payload Shape

Cataloged events emitted through Python `sagittarius.runtime.log_event()` and Julia `Sagittarius.StructuredLogging.log_event()` include these common fields. Julia solver, cluster, and physics helpers emit the relevant cataloged events automatically.

```json
{
  "event": "solver_start",
  "event_id": "SAG-EVT-0005",
  "event_schema": "event-taxonomy/v1",
  "severity": "info"
}
```

When JSON logging is disabled, the same event ID and severity are included in the text log details. Unknown extension events are still accepted by `log_event()`, but they are emitted without a stable `event_id` and are not valid for reproducible manifests.
