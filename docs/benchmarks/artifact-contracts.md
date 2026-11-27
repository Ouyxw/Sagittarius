# Benchmark Artifact Contracts

Status: `Mixed`
Roadmap: Phase 16
Version: `benchmark-artifact-contracts/v1`
Last reviewed: 2026-11-27

This page has two parallel parts: [Benchmarking V1](#benchmarking-v1) preserves the complete original document with nested headings; [Benchmarking V2](#benchmarking-v2) follows the same chapter organization for the planned P0–P1 work in [plan v2](plans/v2.md). V1 retains its original metadata, commands and evidence wording as the initial baseline. All seven P0/P1 V2 implementation/evidence scopes are tracked in plan v2; representation exclusions, reference gaps and recurring acceptance remain explicit. GOV-004 remains the policy authority, and the generation names do not rename artifact schemas.

## Benchmarking V1

Status: `Current`
Roadmap: Phase 16
Version: `benchmark-artifact-contracts/v1`
Last reviewed: 2026-08-12

This page defines the Phase 16 aggregate artifact expectations for benchmark suites. It does not replace existing `benchmark-artifact/v1`, `run-manifest/v1`, `result-artifact/v1`, `shared-result/v1`, or `version-info/v1` contracts. It defines how benchmark-family artifacts should use and link those contracts.

### Artifact Types

| Artifact | Purpose | Status |
| :--- | :--- | :--- |
| `benchmark-artifact/v1` | Generic benchmark rows; the Phase 16 single-scenario profile adds structured case, configuration, metrics, links, and failure fields compatibly. | Current where emitted by existing scripts. |
| `mwis-batch-verification/v1` | UDG/MWIS batch verification rows and exact-baseline comparison. | Current in project-specific form. |
| `benchmark-suite-artifact/v1` | Validated aggregate wrapper for one Phase 16 family/tier run, with retained success, failure, skipped, and incomplete rows. | Current. |
| `run-manifest/v1` | Durable description of one simulation run. | Current where simulations emit artifacts. |
| `result-artifact/v1` | Simulation result data, metadata, diagnostics, and shared payload. | Current where result serialization is used. |

The Phase 16 `optimization_aqc` runner additionally emits structured `benchmark-artifact/v1` rows and one `benchmark-suite-artifact/v1` aggregate per tier. Successful rows retain the deterministic graph/weights and ILP/AQC reference report; failed rows retain the scenario metadata and first-class failure context.

The opt-in CUDA/MWIS protocol emits separate `backend_performance` and `optimization_aqc` parity suites. Its rows retain the initialized CUDA doctor payload, device/driver/CUDA/Julia fields, cold/warm timing, GPU-memory snapshots, CPU/CUDA error, and either an opt-in skip, a CUDA-initialization failure, or a completed reference report.

The solver/path runner retains a measurement repeat index, warmup/repeat policy, representation/method, declared numerical reference gate, and result/manifest links for executed solver paths. The sweep/cluster runner links its checkpoint and final `sweep-artifact/v1`; benchmark aggregates remain governed evidence while the linked sweep envelope remains a resumable scientific-exploration artifact.

Existing scripts may continue emitting `benchmark-artifact/v1`. New Phase 16 family runners should use `write_benchmark_suite_artifact()` to aggregate validated rows in `benchmark-suite-artifact/v1`; existing scripts may continue emitting `benchmark-artifact/v1` directly.
The existing `benchmark_scaling.py`, `benchmark_gpu.py`, `benchmark_cluster.py`, and `benchmark_ablation.py` runners now emit this structured row profile while retaining their legacy flat metric fields for CSV and plotting compatibility.

### Aggregate Shape

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

### Required Row Fields

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

### Failure Rows
The SDK `benchmark_failure_context()` and `make_benchmark_failure_row()` classify timeout, memory exhaustion, CUDA initialization, reference mismatch, ILP, and unexpected execution failures. They retain exception type, failure stage, timeout, process-memory snapshot, optional GPU-memory value, backend probe, and remediation.


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

### Metrics

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

### Evidence Retention

The retained [Phase 16 closure archive](evidence/phase16-e171c584e8e67215f1e5fb00f6f908d2e434b10c/README.md) demonstrates the required directory layout and remains local/reviewable evidence unless separately promoted.

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

### Compatibility Rules

Compatible changes may add optional fields or new metric names. Incompatible changes require a new schema version when they remove required fields, rename existing metric semantics, change status meanings, or alter how linked artifacts are resolved.

## Benchmarking V2

Status: `Mixed`

Scaling has [retained local v2 acceptance evidence](evidence/p0-scaling-v2-2026-11-26/README.md): 42 scenarios and 210 eligible repeats, including all six N=20 geometry/radius configurations. This is bounded local numerical/software evidence; other suite targets and release/public-use gates remain separate.

Ablation has [local ablation evidence](evidence/p0-ablation-v2-2026-11-27/README.md): all 16 targeted CPU paths and 80 independent measured batches passed, including both reduced paths at N=20 (D=17711). Four full-dimension exclusions and five optional CUDA skips are retained. CUDA, recurring RC and public-use approval remain separate.

CUDA follow-up has [retained local hardware evidence](evidence/p0-ablation-cuda-v2-2026-11-27/README.md): all five ablation chain cases through N=20 passed, with 25 measured CPU/CUDA ODE pairs and 80 saved first/warm/measured result/manifest pairs. First-call initialization and diagonal-observable transfer fixes are included. The original CPU archive and its historical CUDA skips remain unchanged. CUDA stays experimental; this ablation-only archive is separate from the P1 GPU matrix below, recurring RC and public-use gates.


This generation defines the artifact work for the seven P0–P1 suites in [plan v2](plans/v2.md#artifact-and-compatibility-work). Scaling implements its compatible extensions with structured rows, suite validation, audit tooling and regression tests; GPU adds per-backend process records, qualified median ratios and saved-trajectory audits; other acceptance targets become executable contracts when their writers, readers and tests land together. The existing schema names and field responsibilities remain authoritative.

<a id="v2-artifact-types"></a>

The [P1 GPU local campaign](evidence/p1-gpu-v2-2026-11-27/README.md) completes the declared eight-case matrix: chains N=2,4,8,12,16,20, a 2x2 lattice and seeded two-node MWIS. All 40 measured CPU/CUDA pairs passed at 101 shared times after symmetric warmups; N=20 has D=17711. Separate backend memory, saved results/manifests, qualified median ratios and all companion values passed the backend-free audit. CUDA remains experimental; this is shared-workstation software/numerical evidence, not independent physical validation, recurring RC or public-use approval.

The [P1 MWIS/UDG local campaign](evidence/p1-mwis-v2-2026-11-27/README.md) completes all 40 frozen instances through N=20 (five seeds per size), with 200 eligible AQC and 200 eligible ILP measurements. Independent DOP853/refinement, raw-norm checks, exhaustive graph objectives and CBC problem/solution optimality gate the results. Actual AQC result/manifests, native solver logs, per-path memory and all companion statistics pass the saved-evidence audit. Short-schedule suboptimal candidates remain valid data; different solution guarantees prevent an AQC/ILP speedup interpretation. This is bounded local numerical/software evidence, separate from scientific validation, general algorithm quality and release/public-use approval.

The [P1 solver local campaign](evidence/p1-solver-v2-2026-11-27/README.md) completes all 39 declared sensitivity configurations across Rabi, the addressed chain and a linear ramp. All 312 first/warm/measured results and manifests are retained and audited; 38 configurations and 190/195 measured calls meet the frozen 1e-6 accuracy target. The coarse ramp RK4 T/100 case remains a failed accuracy row with all raw times/errors, as required by the plan. Independent stable references, raw norm checks, effective settings, per-configuration memory and error-versus-runtime companions support bounded local numerical characterization. Full-matrix all-accuracy-pass remains false; accepted characterization does not promote under-resolved times into performance comparisons or close scientific validation, recurring RC or public-use gates.

The [P1 observable local campaign](evidence/p1-observables-v2-2026-11-27/README.md) completes 52 cost configurations through reduced N=20 (D=17711) and 12 small full/reduced state-path fixtures. All 260 measured SDK calls and 476 saved results/manifests pass value/order, round-trip and independent-reference gates; five-seed MCWF samples use explicit simultaneous uncertainty bounds. Two empty-observable history controls, cross-order equality, attributable worker memory, frozen source/runtime and matching companions are audited after relocation. Counts/grids/orders are separate workloads; duplicate physical declarations are labeled. Timings include SDK construction/collection/manifest and provide no incremental-overhead subtraction. This closes bounded local numerical/software characterization, separate from physical validation, expanded open-system costs/convergence, recurring RC and public-use approval.

The [P1 open-system local campaign](evidence/p1-open-system-v2-2026-11-27/README.md) accounts for all 99 frozen rows: 85 pass and 14 resource exclusions remain explicit. All 375 eligible measured SDK calls, 916 first/warm/measured/statistical/correctness results and 63 separate tighter results are retained. Reduced N=20 (Rb=12.4 um, D=907) executes MCWF at 100/500/1000 trajectories with five separate seeds and target-size analytic decay controls. Independent small dense/analytic references, 67 raw-density histories, trace/positivity/coherence, seed uncertainty, runtime/throughput statistics, manifests and all companions pass original/relocated backend-free audits. Full N=20 Lindblad/full-space coverage and independent large interacting references remain open. This is bounded shared-workstation local evidence, separate from scientific validation, recurring RC and public-use approval.

### Artifact Types

| Artifact | V2 purpose | Implementation boundary |
| :--- | :--- | :--- |
| `benchmark-artifact/v1` | Retain independent measurements, references, configuration and failure context. | Extend existing structured rows compatibly and preserve flat metric meanings. |
| `benchmark-suite-artifact/v1` | Aggregate declared family/tier scenarios and their passed, failed, skipped and incomplete rows. | Add validated campaign summaries without hiding unexecuted targets. |
| `mwis-batch-verification/v1` | Existing exact-verification helper where applicable. | A timed-out incumbent is not an exact optimum. |
| `run-manifest/v1` | Actual executed simulation configuration and requested/effective settings. | Pure matvec work has benchmark inputs/reference reports rather than fabricated simulation manifests. |
| `result-artifact/v1` | Saved simulation results with metadata, diagnostics, manifest and shared payload. | Add actual AQC result provenance through the existing adapter boundary. |

Preserve current stems: `scaling_results`, `ablation_bench_results`, `gpu_bench_results`, `cuda_parity`, `mwis_gpu_parity`, and existing MWIS/solver/correctness outputs. Scaling now writes `scaling_results_suite` and `scaling_repeats.json`. Ablation writes `ablation_bench_results_suite` and `ablation_repeats.json`. GPU writes `gpu_bench_results_suite` and `gpu_repeats.json`. MWIS writes `mwis_aqc_performance`, `mwis_aqc_performance_suite` and `mwis_repeats.json`. Solver, observables and open-system now write `solver_sensitivity`, `observable_performance`, `open_system_performance` with suite aggregates and linked repeat/reference records. Historical stems and required schema meanings remain unchanged.

Ablation retains one aggregate row per size/path and a validated structured row
per measured batch in `ablation_repeats.json`. `metrics.measurements` retains
operation count, runtime, per-operation time, eligibility, reference errors,
finite/scale checks and saved `output_array` links. `reference_arrays` stores
basis/input/independent expected H*psi in NPZ; pure matvec rows do not invent
simulation manifests. Statistics identify eligible repeat row IDs, counts and
linear type-7 quantiles. `total_time_s`/`time_per_operation_s` remain first-batch
metrics; `median_batch_time_s` is the independent-repeat median. Construction,
first-operation, reference, warmup and doctor timings have distinct names.

`fixed-normalized-input-matvec/v2` identifies the revised fixed-input workload;
historical H^k*psi timing remains a separate workload. Frozen `campaign.json`,
per-path configs/checkpoints, exact implementation snapshots/hash inventory,
doctor/runtime projects and coverage support replay. `audit_ablation_campaign.py`
checks saved CPU outputs, configuration/statistics membership and companion
contracts, including after relocation. A required numerical gate or reference
failure excludes the repeat; a slow valid repeat is retained. Optional CUDA
solve rows carry their own manifests and scope. Matched CUDA follow-ups retain
nested `cpu`/`cuda` result-artifact and run-manifest links for first, warmup and
measured pairs. Pair metadata records execution order, independent CPU and CUDA
timings, finite/grid/backend/configuration gates and full trajectory error;
`statistics` summarizes eligible CUDA solves and `cpu_statistics` separately
summarizes their CPU references. The audit reloads both artifacts, validates
standalone manifests and recomputes the pair gates, membership and coverage.
Source snapshots/hash guards include the executed Julia backend, including
first-call initialization behavior. A fresh-process CUDA solve now loads the
optional backend before entering the solver in the current Julia world; a
failed first solve must remain a failure and cannot be accepted as warmup.
GPU snapshots remain separate from unavailable peak memory. The campaign
never produces CPU-matvec/CUDA-solve or CPU/CUDA solve ratios.

<a id="v2-aggregate-shape"></a>

The GPU scan writes `gpu_bench_results` and `gpu_bench_results_suite` in
JSON/CSV/Markdown, plus `gpu_repeats.json` and per-scenario `pairs.json`.
Each pair retains phase/index, stable ID, declared order, actual monotonic
call intervals, raw per-backend seconds, result/standalone-manifest links and
a full-grid gate. `metrics.statistics.CPU` and `.CUDA` retain separate
Hyndman-Fan type-7 summaries, exact eligible pair IDs and requested/completed/
eligible counts. `median_cpu_over_cuda` is `median(CPU runtime) / median(CUDA
runtime)` only with two warmups, five eligible measurements on each path and
successful scenario gates; otherwise it is null with a reason. Legacy
`t_cpu_s`/`t_gpu_s` remain the first measured calls; `speedup` is the qualified
median ratio. Historical one-call ratios have a different measurement scope.
Legacy combined `max_rss` is unavailable with an explicit reason; use separate
worker baseline/HWM byte records and sampled supervisor peaks. Device snapshots
never imply GPU peak. Initialization, construction and first solves are separate
single measurements; raw checkpoints retain elapsed times even on write failure.
`scripts/audit_gpu_campaign.py` checks saved results, standalone manifests,
frozen configs/source/runtime hashes, pair order, statistics and every companion
value without initializing either backend. These are compatible optional
extensions under existing schemas, not new required historical fields.

MWIS performance rows are frozen instances, never pools across seeds or sizes.
`metrics.paths.aqc` and `.ilp` retain their actual checkpoints, configuration,
supervision and per-call phase/ID/time/eligibility/artifacts. Separate
`metrics.statistics.aqc`/`.ilp` retain requested/completed/eligible counts,
exact member IDs and type-7 median/min/max/p25/p75; stopped calls remain raw
diagnostics and unproven ILP calls cannot qualify as time to an exact optimum.
Generation/setup, per-call model construction, post-processing, serialization and
independent-reference costs carry their actual measurement counts and scopes.
AQC outputs link real result/manifest sets; ILP links native logs and reference
reports rather than fabricated simulation manifests. Normalized final readout
is distinct from raw norm checked through Z0+2n0; full wavefunction history is
not retained by this performance tier. `quality_by_aqc_row_id` records the
candidate weight/feasibility, proven exact optimum, gap, approximation ratio and
mass over every optimal graph-feasible basis state. Unproven optimality leaves
exact metrics null with reasons, even if PuLP labels a time-limited incumbent
problem `Optimal`; solution status and native logs are retained separately.
Worker baseline/HWM includes initialization/reference/writes; the ILP Python
process memory excludes native CBC, whose peak is explicitly unavailable.
The [MWIS boundaries](plans/v2.md#implemented-mwisudg-measurement-boundaries)
and `scripts/audit_mwis_campaign.py` define recomputation and failure semantics.
Existing smoke/correctness/scaling IDs/stems and all schema names remain intact.

### Aggregate Shape

Use the existing validated `benchmark-suite-artifact/v1` envelope:

```json
{
  "schema_version": "benchmark-suite-artifact/v1",
  "artifact_type": "benchmark.suite",
  "suite_id": "phase16-scaling-performance",
  "family": "backend_performance",
  "tier": "scaling",
  "protocol_version": "benchmark-protocol/v1",
  "generated_at": "2026-11-26T00:00:00Z",
  "source": {},
  "environment": {},
  "scenario_defaults": {},
  "rows": [],
  "summary": {},
  "diagnostics": []
}
```

This illustrates the envelope; the scaling runner uses suite ID `phase16-p0-scaling-v2`. Retain per-repeat rows and the ordered campaign configuration. Finalize compatible placement of measurement summaries with validators: each summary must identify its input rows, statistic convention, eligible counts and unavailable values. Do not reinterpret existing deterministic summary fields. A configuration hash links to retained replay inputs rather than replacing them.

Scaling stores one aggregate row per declared scenario in both `scaling_results`
and its suite. `metrics.repeats` retains individual measurements and
`metrics.statistics` identifies eligible input row IDs, counts and quantiles;
`scaling_repeats.json` exposes those measurements as validated structured rows.
`campaign.json` retains replay inputs/hash, source snapshots, commands, limits,
reference policy and environment. Per-scenario checkpoints retain initialized
doctor, partial measurements and runtime project manifests. `coverage.json`
records missing successful matrix coverage. `scripts/audit_scaling_campaign.py`
checks schema, configuration/source hashes, companions, result/manifest pairs,
statistics and effective settings before evidence acceptance.

Legacy flat `N`, `basis_size`, `full_dim`, `time_s`, `max_rss` and
`max_rss_unit` are retained. `time_s` is the first measured SDK call;
`median_time_s` has distinct summary semantics. `metrics.memory` normalizes
kernel process HWM/RSS to bytes and keeps source units; the flat `max_rss`
retains the existing resource-module source value and unit. Both represent
scenario-process lifetime, including references, rather than solve-only memory.
The artifact envelope's `memory` is the supervisor's own process and is not
per-scenario memory. Absent child memory remains unavailable.

<a id="v2-required-row-fields"></a>

### Required Row Fields

Keep the V1 row fields and meanings. Implement the following campaign evidence in compatible fields or linked reports; these are planned retention requirements, not new mandatory fields for historical artifacts.

| Existing surface | V2 evidence |
| :--- | :--- |
| `row_id`, `scenario_id`, `family`, `tier` | Stable scenario/config identity, measurement identity and family/tier mapping. |
| `status`, `stage`, `failure` | Actual lifecycle outcome, failed gate, supervisor diagnostics and partial measurements. |
| `problem` | Exact register/graph/weights, pulses, initial state, basis dimension, pruning and configuration link/hash. |
| `solver` | Requested/effective method, tolerances, adaptive/dt, explicit output grid, seeds/trajectory settings where applicable. |
| `backend` | Actual implementation/workload, precision, threads, device/container/doctor and runtime versions. |
| `observables` | Actual ordered declarations, parameters, count and output samples. |
| `metrics` | Independent repeat index, warmup designation, batch operation count, timer scope, reference/error gate and applicable statistical/memory measures. |
| `artifacts` | Actual result/manifest, reference/config, convergence report, summary input rows and companion links. |
| `disclosure_status` | Existing classification only; promotion requires evidence and governance review. |

Keep `data`, `metadata`, `diagnostics`, `manifest` and `shared_result` responsibilities separate. Record requested, completed and eligible counts; retain missing metrics with reasons. For MWIS, retain ILP solver/version/limits/termination/optimality and incumbent/bound where exposed. Compute exact-gap, ratio and optimal-state probability only with a proven exact reference. For MCWF, retain execution mode and statistical seed-set identity separately from timing repeats.

<a id="v2-failure-rows"></a>

### Failure Rows

Use existing failure helpers and status meanings. The parent supervisor must preserve timeout/OOM/child-crash evidence even when a worker cannot finish writing an artifact. Keep collected metrics, scenario identity, limits, stage/code, exception, probe, remediation and relevant result/reference links.

- Preflight budget exclusions and disabled optional paths are skipped with context.
- Attempted solver, reference, backend or validation failures are failed.
- Interrupted campaigns or insufficient-repeat evidence are incomplete.
- All failed and excluded targets remain in the declared matrix; resource exclusion does not establish successful scale coverage.

Retain numerical failures and failed exact-reference attempts alongside valid AQC outcomes. A poor feasible objective is a measurement, while feasibility, mapping and numerical gates are recorded separately. Do not drop inconvenient rows to complete a suite.

<a id="v2-metrics"></a>

### Metrics

Use existing correctness metrics and add compatible measures only with documented definitions. Pilot-confirm and freeze numerical targets before the campaign: scaling/observable deterministic error initially 1e-8, full matvec relative error 1e-12, reduced matvec absolute error 1e-10, GPU parity/solver trajectory error 1e-6, and local-noise analytic/trace error 1e-6 with minimum density eigenvalue >=-1e-7. Each suite retains reference scope and limitations; stochastic checks use separately declared uncertainty criteria.

| Measurement | Definition and provenance |
| :--- | :--- |
| Repeated runtime | At least five independent eligible executions after two separate warmups by default; median/min/max/p25/p75, quantile convention, input row IDs and requested/completed/eligible counts. |
| Matvec runtime | Batch duration and per-operation duration; 50 operations per repeat by default. Batch count is separate from independent repeat count. |
| Setup/execution phases | Initialization/JIT, basis/operator construction, first/warm solve, collection, post-processing and serialization as actually measured. SDK and kernel timings have distinct scopes. |
| Memory | Value, source/normalized units, method, baseline, process/device and phase scope. Process-lifetime peak and GPU snapshots are distinct measures. |
| MWIS results | Feasibility/objective, proven exact reference, gap/ratio/optimal-state probability where available, separately timed AQC and ILP work. |
| Open-system statistics | MCWF/Lindblad errors, multi-seed uncertainty, actual completed trajectories and trajectories/sec; raw retention cost measured separately. |

Exclude warmups from summaries, preserve invalid rows, and retain slow valid repeats. Do not pool different workloads, sizes, precisions or statistical populations. Missing GPU peaks remain unavailable rather than inferred from before/after snapshots. Ratios require matched workload and accuracy; CPU matvec/CUDA solve ratios are invalid.

For the [seven-suite runtime outputs](plans/v2.md#runtime-reporting-requirements-for-all-seven-suites),
keep raw seconds, clock/timer scope, reset/cache policy, phase designation,
statistic input IDs and requested/completed/eligible counts in benchmark
`metrics` or linked records. Use compatible optional fields and reuse existing
type-7 statistics helpers. Do not move runtime statistics into simulation data
or change manifest meanings. Phase timings measured only once are not repeated
distributions; unavailable values retain reasons. Timeout elapsed time remains
diagnostic, separate from successful runtime distributions. Companion tables
must agree with the summary and expose raw-source links even if not every
nested record is printed in CSV/Markdown.

Suite-specific summaries include per-graph AQC/ILP phases and termination,
solver error-versus-runtime, observable output-policy context, and per-repeat
MCWF completed-trajectory throughput. GPU median ratios require matched
per-backend accuracy and at least five eligible measurements each. The
[derived P0 timing report](reports/p0-runtime-statistics-2026-11-27.md) preserves
existing flat first-repeat semantics and immutable source archives; its added
per-operation median is explicitly derived from batch median/operation count.
These requirements do not make new fields mandatory for historical artifacts.

<a id="v2-evidence-retention"></a>

### Evidence Retention

Archive the frozen ordered scenarios, required/optional scope, exact replay inputs/hash, reference/statistical criteria, limits/stop policy, commands and working directory; source identity, environment/thread settings and initialized diagnostics; raw measurements and failures; JSON/CSV/Markdown and aggregates; actual result/manifests, numerical references, convergence reports and test logs; and a checksum inventory.

Link the durable archive in the requirements matrices before advancing evidence status. Track runner implementation, campaign execution and reviewed acceptance separately. Scaling, MWIS/UDG and open-system N=20 targets require actual eligible execution for successful coverage; budget exclusions and large-case reference gaps remain visible. The initial archive remains V1 local evidence. Figures retain source artifact links and do not replace artifact validation or disclosure review.

<a id="v2-compatibility-rules"></a>

### Compatibility Rules

Benchmarking V2 is an execution/documentation generation, not a new artifact schema. Preserve `benchmark-artifact/v1`, `benchmark-suite-artifact/v1`, `run-manifest/v1`, `result-artifact/v1`, `shared-result/v1`, `version-info/v1`, `doctor/v2.1` and `event-taxonomy/v1` semantics. Add optional measurement fields compatibly; changes to required fields or meanings need coordinated version/reader/writer/validator/test/docs decisions.

Keep original V1 artifact stems, flat metric meanings and archives readable. Label the revised fixed-input matvec workload and never pool it with historical H^k*psi batches. A stored `release_grade` classification does not validate evidence or approve public wording. Apply GOV-001/GOV-002 and applicable prior-art review before public use.

### Implemented solver sensitivity records

`solver_sensitivity` and `solver_sensitivity_suite` use existing v1 envelopes;
legacy `solver_performance` correctness stems remain unchanged. A row is one
frozen physical fixture/method/tolerance/dt/grid configuration. `metrics.state`
retains doctor/runtime, setup/reference timing, process memory and all records;
`metrics.statistics` uses only eligible measured calls, with exact member IDs,
requested/completed/eligible counts and linear type-7 quantiles. First and warmup
calls remain separately labeled in `solver_repeats.json`. Runtime seconds are one
SDK call including construction/collection/manifest; state reset, reference/checks
and serialization stay outside. The performance CSV/Markdown gives method,
stepping, tolerances/dt, output count, error/gate, eligible count and all five timing
statistics; suite CSV retains full structured metrics. Source, runtime files,
references and every saved result/manifest are auditable after relocation.

Under-resolved calls retain diagnostic time/error but cannot qualify at an unmet
accuracy target. Short runs and timeouts are incomplete; memory/backend/reference
failures are failed; planned budget exclusions are skipped. Raw norm, observable
and normalized final-probability checks are distinct compatible optional metrics.
These fields add no required keys to historical artifacts and rename no schemas.

### Implemented observable collection contract

The [observable boundaries](plans/v2.md#implemented-observable-matrix-and-measurement-boundaries)
define 52 one-axis/combined cost configurations through reduced N=20 and 12
small full/reduced state-path fixtures. Ten single types stay separate from mixed
sets; uniquely named duplicate declarations are labeled collection workloads.
Independent probability references, nonlinear connected-correlation semantics,
MWIS penalties and explicit MCWF uncertainty apply before cost interpretation.
Result data, manifest declaration/metadata order, shared names/series and round
trips are checked outside the SDK timer. Ordered declaration lists preserve
identity through canonical campaign JSON. Empty-observable history controls are
retained separately; no incremental-overhead subtraction or evaluation-only cost
is claimed. First/warm/measured calls, measured-only type-7 summaries, attributable
worker memory, real result/manifest/reference links and matching companions are
recomputable by the backend-free audit. Correctness-only rows retain unavailable
runtime statistics with reasons, and MCWF raw samples keep their own storage
policy. Existing schema names and unsupported observable/backend scope remain.


Open-system additionally retains `metrics.throughput_statistics` (per-repeat
completed trajectories divided by seconds, summarized separately from runtime),
`metrics.convergence`, five-seed raw membership and `convergence.json` with
pooled absolute bounds and cross-count comparisons. Lindblad trajectory count/
throughput are unavailable with reasons. `store_trajectories=False` costs and the
one opt-in raw-storage workload have separate identities. Raw density histories,
analytic/dense arrays and tighter controls are linked outside SDK timing;
large interacting reference gaps are explicit. Requested/effective counts and
seeds come from actual manifests; completion inference from successful ensemble
return is labeled. The audit replays deterministic/stochastic/density checks,
statistics, source/runtime hashes and all companions after relocation without
Julia. `coverage.json` distinguishes every declared row accounted for, successful
N=20 reduced MCWF coverage and still-excluded full/density scopes. These are
optional compatible benchmark extensions, not new required historical fields.


Final open-system acceptance additionally emits `lindblad_mcwf.json` and
`acceptance.json` from `scripts/accept_open_system_campaign.py`. This backend-free
review wraps the original measurement audit, directly compares every retained
matching Lindblad/MCWF workload and preserves missing density-reference reasons.
Individual/tighter calls and five-seed pooled comparisons use the predeclared
simultaneous rule, with both deterministic numerical floors. Separate review
source hashes/snapshots document analysis code without rewriting the frozen
measurement source identity or numerical outputs. These review companions are
compatible suite-specific additions; no required historical schema changes.
