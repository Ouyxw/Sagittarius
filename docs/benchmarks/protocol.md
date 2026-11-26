# Phase 16 Benchmark Protocol

Status: `Mixed`
Roadmap: Phase 16
Version: `benchmark-protocol/v1`
Last reviewed: 2026-11-26

This page has two parallel parts: [Benchmarking V1](#benchmarking-v1) preserves the complete original document with nested headings; [Benchmarking V2](#benchmarking-v2) follows the same chapter organization for the planned P0–P1 work in [plan v2](plans/v2.md). V1 retains its original metadata, commands and evidence wording as the initial baseline. V2 remains planned until its implementation and retained evidence pass acceptance. GOV-004 remains the policy authority, and the generation names do not rename artifact schemas.

## Benchmarking V1

Status: `Done`
Roadmap: Phase 16
Version: `benchmark-protocol/v1`
Last reviewed: 2026-08-12

This protocol defines how Sagittarius Phase 16 benchmarks should be selected, run, recorded, and interpreted. It is intentionally separate from installation validation. Installation CI proves that the package can be installed and smoke-tested. Benchmark protocols produce scientific, correctness, and performance evidence under explicit configurations.

For concrete commands and expected artifact stems, use the [runnable tier guide](README.md#runnable-tier-guide) and [tier command table](tiers.md#runnable-commands-and-outputs). This protocol remains the execution and evidence-interpretation contract for those runners.

### Scope

Phase 16 benchmark work covers:

- physics baseline checks such as Rabi oscillation, Rydberg blockade, Landau-Zener sweeps, and dense-vs-reduced validation;
- cold-atom dynamics such as chain excitation profiles, local addressing, Z2 ordering, and 2D pattern formation;
- open-system dynamics such as Lindblad, MCWF, decay, dephasing, and trajectory convergence;
- UDG/MWIS and weighted MWIS optimization workflows with exact baselines where tractable;
- solver and backend performance, including dense, sparse, reduced, CPU, CUDA, and solver-method sensitivity;
- parameter-sweep and cluster-oriented benchmark aggregation.

Out of scope for Phase 16:

- package installation readiness, which belongs to Phase 13;
- hardware-control or calibrated device claims;
- public quantum-speedup claims;
- unreviewed cross-machine performance comparisons.

### Execution Stages

1. Choose the benchmark family and tier from [`families.md`](families.md) and [`tiers.md`](tiers.md).
2. Freeze the scenario: problem size, geometry, seed, pulse schedule, solver settings, observables, backend, and timeout.
3. Run environment diagnostics before benchmark execution, including `doctor()` where backend behavior matters.
4. Run warmup iterations separately from measured iterations.
5. Validate correctness gates before interpreting timing, memory, GPU, or scaling metrics.
6. Emit aggregate artifacts following [`artifact-contracts.md`](artifact-contracts.md).
7. Preserve failed cases as benchmark rows with diagnostic context.
8. Classify evidence as exploratory, reviewable, or release-grade.
9. For public use, review wording against governance documents and create or update the disclosure row.

### Required Pre-Run Record

Every benchmark run should record:

- git commit and dirty state;
- Python, Julia, Sagittarius Python package, and Sagittarius.jl versions when available;
- operating system, CPU model, total memory, container status, and accelerator device when available;
- benchmark family, tier, scenario ID, and protocol version;
- exact command and working directory;
- environment variables that affect solver, backend, threading, or GPU behavior;
- timeout policy and failure policy;
- artifact output directory.

### Warmup and Measurement Rules

Recommended defaults:

- 1 to 3 warmup runs for each scenario;
- at least 5 measured repeats for release-grade runtime claims;
- separate first-run CUDA setup timing from warmed execution timing when initialization cost is material;
- record median, min, max, p25, and p75 for repeated runtime rows;
- record peak process memory where available;
- record GPU memory before and after CUDA scenarios when the runtime exposes it;
- treat incomplete metadata or failed correctness validation as diagnostic output, not performance evidence.

### Correctness Before Performance

Performance numbers are interpretable only after the relevant correctness checks pass:

- analytic reference for simple Rabi, blockade, and Landau-Zener cases where feasible;
- dense reference for small full-vs-reduced comparisons;
- exact ILP or declared exact solver for small MWIS instances;
- CPU/CUDA parity for GPU timing claims where the same scenario is tractable on both paths;
- Lindblad trace and positivity checks for open-system density-matrix runs;
- MCWF convergence sanity checks against Lindblad results on small systems;
- solver-method sensitivity check for scenarios known to be numerically stiff.

### Evidence Classification

| Evidence class | Minimum requirements | Typical use |
| :--- | :--- | :--- |
| Exploratory local | Scenario command, commit, local hardware notes, and failure/success status. | Developer investigation and local RTX 5070 Ti probing. |
| Reviewable project | Structured aggregate artifact, run manifests or result artifacts, diagnostics, correctness checks, and failure rows. | Internal planning and release candidate review. |
| Release-grade | Reviewable project evidence plus repeated measurements, governance review, disclosure row, and bounded wording. | Public release notes, README updates, reports, or papers. |

### Reporting Boundary

Benchmark reports must use bounded wording. A valid report names artifact path, commit, hardware, backend, scenario, solver settings, and metric name. Avoid general claims such as "CUDA is faster" or "Sagittarius solves MWIS efficiently" unless the claim is explicitly bounded to one artifact and scenario.

## Benchmarking V2

Status: `Planned contract`

This generation applies the [P0–P1 implementation plan v2](plans/v2.md). It defines acceptance discipline for planned campaigns; current runners still need the specified implementation work. GOV-004 remains the policy authority. Benchmarking V2 does not rename artifact schemas or reclassify the initial archive.

<a id="v2-scope"></a>

### Scope

Cover the two P0 suites (`scaling`, `ablation`) and five P1 suites (`gpu`, `mwis_udg`, `solver`, `observables`, `open_system`). Scaling, MWIS/UDG and open-system target N=20 with representation-specific resource limits; GPU uses a bounded chain scan through N=20. Other axes cover geometry/radius, solver tolerance/step/grid, observable type/count/order and trajectory count.

Keep testing, software verification, numerical verification and scientific validation distinct. Small physics/cold-atom fixtures provide numerical references for these campaigns. P2 noise/cluster implementation, Phase 14 models, Phase 18 deployment, installation validation, hardware calibration and general quantum-speedup claims remain outside this plan.

<a id="v2-execution-stages"></a>

### Execution Stages

1. Select suite/tier and its [planned matrix](plans/v2.md); retain required and optional scenarios in deterministic order.
2. Pilot references and numerical/statistical targets, then freeze exact inputs, config hash, seed sets, accuracy criteria, resource limits and stop policy before governed measurement.
3. Run initialized diagnostics and resource preflight. CUDA additionally requires `SAGITTARIUS_ENABLE_GPU_TESTS=1` and successful initialized CUDA doctor.
4. Supervise one process per scenario/path for attributable memory/failures; measure setup and warm the actual workload separately.
5. Execute at least five independent measurements after two warmups by default, resetting inputs. Synchronize CUDA at both timing boundaries.
6. Stop the solve timer before reference checks, serialization and reporting; retain outputs and gate results for each repeat.
7. Write compatible per-repeat and aggregate evidence, including skipped/failed/incomplete rows and statistics membership.
8. Audit configuration, test/reference coverage, artifact links/checksums and missing scope before recording acceptance milestones.
9. Repeat P0 campaigns for each RC; rerun affected P1 work on triggering changes and perform public governance review separately.

<a id="v2-required-pre-run-record"></a>

### Required Pre-Run Record

Retain the full replayable campaign configuration and its hash, ordered scenario IDs, required/optional scope, commands/working directory, plan/protocol versions and output destination. Record reference kind/configuration, numerical tolerances, statistical seed set/uncertainty policy, time-point multiplicity treatment, wall-time/memory limits and stop/failure policy.

Each scenario includes coordinates/atom order, graph/weights where applicable, C6, units, pulse parameters, initial state, basis/radius, actual basis dimension, precision, solver/requested output grid, observable declarations and noise rates. Retain requested/effective solver, grid, seeds and trajectory settings from execution. Record commit/dirty state, language/package/runtime versions, OS/CPU/memory/container, CPU/BLAS/Julia threads and backend/device/driver/doctor metadata.

Plan defaults and matrix values require a retained freeze record before measurement. A hash without the actual values is insufficient. Document cache policy, validation/preflight warming effects and any approved campaign-scope revision.

<a id="v2-warmup-and-measurement-rules"></a>

### Warmup and Measurement Rules

Use two warmups and at least five independent measured executions per frozen scenario/path by default. The default matvec batch is 50 operations, independently recorded; preserve legacy `repeats` semantics when adding controls. Reset initial state and fixed seeded input for every execution. V2 matvec uses fixed normalized H*psi input rather than growing H^k*psi and carries a distinct workload label.

Time initialization/JIT, basis/operator construction, first solve and warmed execution separately where material. A first solve after initialized doctor is not process-cold startup. Define whether the SDK solve includes host/device transfers and observable collection. Exclude reference work, validation, serialization and reports from solve runtime. Match CPU/CUDA inputs, precision, effective solver, numerical accuracy, explicit times and warmups; alternate measured order and synchronize CUDA before and after timing.

Retain every raw measurement and its warmup/eligible designation. Compute median/min/max/p25/p75 with declared quantile convention, source row IDs and requested/completed/eligible counts. Do not remove slow valid repeats or pool different configurations. Fixed-seed timing repeats measure execution variability; independent seed studies measure sampling variability.

Preflight state/construction/output memory and time budgets. A supervised child process records attributable lifetime peak including setup/warmup, baseline and method. Repeated `max_rss` snapshots from a shared process are not independent peaks. GPU snapshots are not peaks; retain unavailable values explicitly. The parent keeps failure rows if a child times out, crashes or exhausts memory.

For stochastic convergence, freeze seed lists, observables, confidence/error criteria and time-point multiplicity treatment. More trajectories need not reduce every seed's error. Keep fixed-seed serial/threaded execution mode and requested/effective trajectory settings. Raw trajectory storage is opt-in and its cost is a separate workload.

<a id="v2-correctness-before-performance"></a>

### Correctness Before Performance

| Suite | Applicable V2 gates |
| :--- | :--- |
| Scaling | N<=8 projected-dense Hamiltonian/trajectory references and larger tighter-solver sensitivity; record full-space approximation errors separately when claimed. |
| Ablation | Independent full/projected-dense references, finite values and error scales; same input/workload within compared representation groups. |
| GPU | Full declared observable trajectories on identical explicit times, effective configuration and per-size CPU/CUDA parity before a runtime ratio. |
| MWIS/UDG | Small brute-force/ILP validation, mapping/bitstring/objective/probability checks, feasibility and proven optimality for exact metrics. |
| Solver | Analytic/dense or independently verified tighter references; tolerance/step refinement at common times; under-resolved runs retain failed accuracy gates. |
| Observables | Independent values, atom/basis mapping, declaration order and saved metadata; matching output/storage policy for cost comparisons. |
| Open-system | Analytic decay and coherence/driven dephasing, saved-time trace/Hermiticity/positivity, multi-seed MCWF/Lindblad and tighter-solver checks. |

Retain applicable Python/Julia golden-test evidence. Projected parity verifies a reduced implementation and does not establish finite-interaction full-space physical equivalence. Large cases without independent references retain explicit gaps. Resource exclusions leave successful coverage open. MWIS quality outcomes remain results; an ILP timeout incumbent is not an exact optimum. Undriven population decay alone does not validate pure dephasing.

<a id="v2-evidence-classification"></a>

### Evidence Classification

| Evidence class | V2 acceptance requirement | Use |
| :--- | :--- | :--- |
| Exploratory local | Pilot inputs, command, source/environment and actual status; failed gates remain diagnostic. | Tune references/configuration before campaign freeze. |
| Reviewable project | Frozen matrix, repeated raw/aggregate measurements, references/golden tests, actual results/manifests, initialized diagnostics and all failure/exclusion rows. | Internal review or an explicitly bounded campaign milestone. |
| Release-grade | Reviewable evidence plus sufficient eligible repeats, governance/disclosure review and bounded wording. | Public use for reviewed scenarios and metrics. |

Track implemented runner, executed campaign and reviewed evidence separately. A classification label, figure, planned N=20 row or resource exclusion cannot substitute for measured coverage. Preserve V1 initial closure and its evidence limits.

<a id="v2-reporting-boundary"></a>

### Reporting Boundary

Name artifact/archive, source commit, versions, hardware/backend/container, exact scenario/basis, solver/accuracy, observable/output policy and metric scope. Report the ratio of matched runtime medians only after per-scenario parity and accuracy gates pass. CPU matvec/CUDA ODE solve and unmatched storage workloads cannot yield meaningful speedups.

Report lower measured limits, failed rows, unavailable exact references and uncertainty alongside successful results. Apply GOV-001/GOV-002 and applicable prior-art review before external use. Reconcile requirements/status, [plan v2](plans/v2.md), the benchmark index and versioned family/tier/artifact sections when scope or evidence changes. Every RC reruns and archives both P0 suites; affected P1 scope reruns on the triggers in GOV-004.
