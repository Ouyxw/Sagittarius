# Benchmark Tiers

Status: `Mixed`
Roadmap: Phase 16
Version: `benchmark-tiers/v1`
Last reviewed: 2026-11-27

This page has two parallel parts: [Benchmarking V1](#benchmarking-v1) preserves the complete original document with nested headings; [Benchmarking V2](#benchmarking-v2) follows the same chapter organization for the planned P0–P1 work in [plan v2](plans/v2.md). V1 retains its original metadata, commands and evidence wording as the initial baseline. V2 scaling and ablation implementation/evidence are tracked in plan v2; other suite targets remain planned until acceptance. GOV-004 remains the policy authority, and the generation names do not rename artifact schemas.

## Benchmarking V1

Status: `Done`
Roadmap: Phase 16
Version: `benchmark-tiers/v1`
Last reviewed: 2026-08-12

Sagittarius benchmarks are grouped by tier so that developers can run the right amount of evidence for the task. Tiers are cumulative in discipline but not always cumulative in cost. A stress-tier run does not replace correctness-tier evidence.

### Tier Summary

| Tier | Purpose | Expected cost | Default CI policy |
| :--- | :--- | :--- | :--- |
| Smoke | Fast sanity checks for command wiring and artifact creation. | Seconds to a few minutes. | Optional PR CI when relevant. |
| Correctness | Validate physics, solver, and optimization outputs against references. | Minutes to tens of minutes. | Local or manual CI unless small enough for PR. |
| Parity | Compare CPU/CUDA, dense/reduced, Python/Julia, or solver methods. | Minutes to hours depending on backend. | Manual or self-hosted where hardware is needed. |
| Scaling | Increase size or workload until timeout, memory pressure, or numerical failure. | Hardware dependent. | Manual, release-candidate, or local evidence. |
| Stress | Hardware-specific limit finding and failure characterization. | Potentially long running. | Manual only. |

### Runnable Commands and Outputs

Run commands from `sagittarius_py`. The following commands implement the tiers above and make the expected evidence location explicit.

| Tier | Command | Output |
| :--- | :--- | :--- |
| Smoke | `uv run python tests/test_performance/benchmark_physics_smoke.py --output-dir benchmark-output` | `physics_smoke` single-scenario artifacts and `physics_smoke_suite`. |
| Correctness | `uv run python tests/test_performance/benchmark_phase16_validation.py --output-dir benchmark-output` | `cold_atom_dynamics` and `open_system_dynamics` artifacts with matching suite aggregates. |
| Correctness | `uv run python tests/test_performance/benchmark_mwis_aqc.py --tier correctness --output-dir benchmark-output` | `mwis_aqc_correctness` artifacts and suite with deterministic ILP/AQC reference rows. |
| Parity | `SAGITTARIUS_ENABLE_GPU_TESTS=1 uv run python tests/test_performance/benchmark_cuda_mwis_protocol.py --output-dir benchmark-output` | `cuda_parity` and `mwis_gpu_parity` artifacts/suites, including retained skipped or doctor-failure rows. |
| Scaling | `uv run python tests/test_performance/benchmark_scaling.py` | `scaling_results` JSON/CSV/Markdown in the working directory; no suite wrapper. |
| Stress | `uv run python tests/test_performance/benchmark_ablation.py --atom-count 12 --repeats 50 --output-dir benchmark-output` | `ablation_bench_results` JSON/CSV/Markdown, including structured failure context where a path cannot run. |

The local, resumable sweep runner is also a scaling evidence path: `uv run python tests/test_performance/benchmark_sweep_cluster.py --output-dir benchmark-output` writes `sweep_cluster` and `sweep_cluster_suite` plus its `sweep-artifact/v1` checkpoint and final aggregate.

### Smoke Tier

Goal: prove the benchmark command, scenario selection, diagnostics, and artifact writing path work.

Minimum requirements:

- one small deterministic scenario;
- one seed where randomness is involved;
- CPU-first path unless the benchmark explicitly targets backend probing;
- artifact output with at least one successful row or one structured failure row;
- no public performance interpretation.

Recommended examples:

- one-atom Rabi smoke;
- two-atom blockade smoke;
- tiny UDG/MWIS instance with exact baseline;
- CUDA doctor and one tiny CPU/CUDA parity row on local GPU hardware.
Current implementation: `tests/test_performance/benchmark_physics_smoke.py` runs deterministic CPU Rabi and two-atom blockade scenarios, retaining a structured `benchmark-artifact/v1` row for every success or failure.


### Correctness Tier

Goal: establish that the scenario has a trustworthy reference before runtime or scaling is interpreted.

Minimum requirements:

- analytic, dense, exact ILP, or declared tighter-solver reference;
- fixed seeds and fixed output grid where applicable;
- explicit tolerance policy;
- failure rows for reference mismatch, solver failure, or artifact write failure;
- linked run manifests or result artifacts when simulations produce durable results.

Correctness metrics may include max absolute trajectory error, final-state error, trace error, positivity violations, MWIS feasibility, exact objective gap, and reduced-vs-full observable deviation.

Current implementation: `tests/test_performance/benchmark_physics_correctness.py` runs deterministic CPU Rabi, ideal two-atom blockade, Landau-Zener, and small-chain projected dense-vs-reduced cases. It records each reference kind and tolerance in row metrics, retains successful SDK result/manifest artifacts, and writes a durable dense-reference report for the static chain check.

### Parity Tier

Goal: compare two execution paths under one scenario definition.

Supported parity modes:

- CPU vs CUDA;
- full dense vs reduced basis;
- dense vs sparse Hamiltonian path;
- Python vs Julia public API path;
- solver method sensitivity such as `Tsit5`, `Vern9`, and fixed-step `RK4`;
- Lindblad vs MCWF statistical agreement on small systems.

Minimum requirements:

- shared scenario ID and seed;
- shared pulse schedule, solver target tolerances, and output grid;
- declared metric used for comparison;
- both paths' diagnostics and effective configuration;
- bounded interpretation when parity does not imply equivalence for all systems.

### Scaling Tier

Goal: characterize how runtime, memory, basis size, and failure modes change as workload increases.

Scaling axes may include:

- atom count;
- graph density or UDG radius;
- basis mode and blockade radius;
- output sample count;
- observable count;
- trajectory count;
- solver tolerance;
- backend and device;
- parameter-sweep width.

Minimum requirements:

- monotonic scenario IDs such as `mwis_udg_n16_seed3`;
- explicit timeout and memory policy;
- rows for timeout, out-of-memory, numerical failure, backend initialization failure, and validation failure;
- no claim that a failure-free subset is the scale limit unless failed rows are also reported.

### Stress Tier

Goal: find practical local limits and diagnose boundary behavior on a specific machine.

Stress-tier results are local-first. They are valuable for development but are not public claims unless promoted through the release-grade evidence process.

Minimum requirements:

- hardware model, driver/runtime versions, and container status;
- timeout and memory limit;
- explicit stop condition;
- structured failure rows;
- separate notes for first-run setup cost and warmed execution cost;
- no cross-machine comparison without governance review.

A local RTX 5070 Ti can be used for Sagittarius CUDA benchmark development when `doctor(backend="CUDA")` passes, but artifact wording must say exactly that device and environment produced the result.

## Benchmarking V2

Status: `Mixed`

Scaling has [retained local v2 acceptance evidence](evidence/p0-scaling-v2-2026-11-26/README.md): 42 scenarios and 210 eligible repeats, including all six N=20 geometry/radius configurations. This is bounded local numerical/software evidence; other suite targets and release/public-use gates remain separate.

Ablation has [local ablation evidence](evidence/p0-ablation-v2-2026-11-27/README.md): all 16 targeted CPU paths and 80 independent measured batches passed, including both reduced paths at N=20 (D=17711). Four full-dimension exclusions and five optional CUDA skips are retained. CUDA, recurring RC and public-use approval remain separate.

CUDA follow-up has [retained local hardware evidence](evidence/p0-ablation-cuda-v2-2026-11-27/README.md): all five ablation chain cases through N=20 passed, with 25 measured CPU/CUDA ODE pairs and 80 saved first/warm/measured result/manifest pairs. First-call initialization and diagonal-observable transfer fixes are included. The original CPU archive and its historical CUDA skips remain unchanged. CUDA stays experimental; the full P1 GPU matrix, recurring RC and public-use gates remain separate.


This generation applies the same five tiers to [plan v2](plans/v2.md). It distinguishes planned runner work from verified executable commands and keeps the initial V1 evidence complete. Long campaigns remain manual, RC or self-hosted work.

<a id="v2-tier-summary"></a>

### Tier Summary

| Tier | V2 purpose | Expected cost | CI policy |
| :--- | :--- | :--- | :--- |
| Smoke | Verify each changed runner, configuration, artifact and controlled failure path. | Bounded small CPU cases. | Appropriate PR smoke only. |
| Correctness | Analytic/dense/exact, basis/index/order, solver and local-noise reference gates. | Small reference fixtures. | CPU regression where bounded; broader checks manual. |
| Parity | Matched CPU/CUDA, Python/Julia, representation/method and MCWF/Lindblad checks. | Scenario dependent. | CUDA opt-in on actual initialized hardware. |
| Scaling | Frozen size/geometry/radius/grid/count/trajectory axes and independent measurements. | Resource dependent, targets through N=20 where declared. | Manual/RC; every declared row retained. |
| Stress | Representation/hardware resource and numerical failure boundaries. | Potentially long running. | Manual only with explicit stop policy. |

<a id="v2-runnable-commands-and-outputs"></a>

### Runnable Commands and Outputs

The V1 commands are retained as historical baseline. Scaling and ablation now have V2 CLI support; other entries below remain implementation targets until their runners and smoke evidence exist.

| Suite | Existing or planned entry point | V2 outputs and readiness |
| :--- | :--- | :--- |
| Scaling | Implemented `benchmark_scaling.py` CLI; positional Python function retained. | `scaling_results` and `scaling_results_suite` JSON/CSV/Markdown; `scaling_repeats.json`, campaign/checkpoints and coverage. |
| Ablation | Implemented `benchmark_ablation.py` CLI; single-N positional function retained. | `ablation_bench_results` and `_suite` JSON/CSV/Markdown, `ablation_repeats.json`, frozen configs/checkpoints, saved numerical arrays and coverage/audit. `--repeats` counts operations; `--repeat-count` counts independent batches. |
| GPU | Existing `benchmark_gpu.py` adopts doctor/opt-in discipline from `benchmark_cuda_mwis_protocol.py`. | Preserve `gpu_bench_results`, `cuda_parity`, `mwis_gpu_parity`; planned scan aggregate and repeated matched measurements. |
| MWIS/UDG | Existing `benchmark_mwis_aqc.py` and adapter need expanded matrix/provenance. | Preserve initial tier outputs; planned `mwis_aqc_performance` and suite. |
| Solver | Existing `benchmark_solver_performance.py` needs sensitivity and timer work. | Preserve correctness outputs; planned `solver_sensitivity` and suite. |
| Observables | Planned `benchmark_observables.py`. | Planned `observable_performance` and suite; runner/flags not implemented. |
| Open-system | Planned `benchmark_open_system_performance.py`. | Planned `open_system_performance` and suite; preserve existing one-atom correctness runner. |

Run from `sagittarius_py` after source/editable installation:

```bash
# Full 42-scenario matrix, including N=20; unique output directory per campaign.
uv run python tests/test_performance/benchmark_scaling.py \
  --output-dir benchmark-output/scaling-v2 \
  --timeout-seconds 600 --memory-limit-mb 4096

# Bounded real-backend smoke with the same two warmups/five measured repeats.
uv run python tests/test_performance/benchmark_scaling.py \
  --sizes 2 --geometries chain --radii 1.1 \
  --output-dir benchmark-output/scaling-v2-smoke
```

Scaling supports `--sizes`, `--geometries chain rectangle`, `--radii` (Rb/a),
repeatable `--scenario ID`, `--warmups`, `--repeat-count`, `--timeout-seconds`,
`--memory-limit-mb`, `--observable-atol` and `--output-dir`. Defaults are the
plan matrix, two warmups, five repeats, 600 seconds, 4096 MiB and 1e-8.
Changing the accuracy target must be a predeclared pilot decision. Short counts
remain incomplete diagnostics; CLI exit 0 requires every selected row to pass.
A subset smoke does not pass full-matrix coverage. RSS supervision currently
requires Linux `/proc`; unsupported platforms retain failed setup rows.

The Python function `benchmark_scaling(n_max=16, blockade_radius=5.0,
output_dir=".")` retains consecutive chain N=2..n_max and absolute radius;
zero radius retains full basis. New keyword controls select the v2 axes.
Named runtime statistics are separate from the legacy single-call `time_s`.
To audit the frozen source, configuration, companions and saved runs from the
repository root:

```bash
sagittarius_py/.venv/bin/python scripts/audit_scaling_campaign.py \
  sagittarius_py/benchmark-output/scaling-v2
```

Use `--allow-partial` only to audit diagnostic/subset artifacts; its report
still records missing successful v2 scenarios.

Ablation full CPU matrix and acceptance audit, from `sagittarius_py`:

```bash
uv run python tests/test_performance/benchmark_ablation.py \
  --sizes 4 8 12 16 20 --repeats 50 --repeat-count 5 --warmups 2 \
  --memory-limit-mb 9216 --timeout-seconds 600 \
  --output-dir benchmark-output/ablation-v2
.venv/bin/python ../scripts/audit_ablation_campaign.py benchmark-output/ablation-v2
```

Use `--atom-count 4` for a single-size smoke. Shorter `--repeat-count 1
--warmups 1 --repeats 3` runs remain incomplete diagnostic pilot evidence;
audit them with `--allow-partial`. The output directory must be empty.
CUDA additionally requires `--include-gpu` and `SAGITTARIUS_ENABLE_GPU_TESTS=1`;
it measures a separate ODE workload with matched CPU trajectory gates. A
CUDA-only follow-up preserves the old CPU archive:

```bash
SAGITTARIUS_ENABLE_GPU_TESTS=1 uv run python tests/test_performance/benchmark_ablation.py \
  --sizes 4 8 12 16 20 --modes reduced_sparse_gpu_cached --include-gpu \
  --repeat-count 5 --warmups 2 --cuda-parity-atol 1e-6 \
  --memory-limit-mb 9216 --timeout-seconds 600 \
  --output-dir benchmark-output/ablation-cuda-v2
.venv/bin/python ../scripts/audit_ablation_campaign.py benchmark-output/ablation-cuda-v2
```

Use an installed CUDA 6.2.0 environment that passes initialized doctor. A host
whose sandbox hides the GPU requires execution with actual device access;
a sandbox skip/failure is not CUDA validation. Both CPU/CUDA ODE paths retain
first/warm/repeated reset-state solves, 101-point trajectory parity and results
with manifests. The audit independently records CPU-matvec and CUDA coverage;
a CUDA-only run cannot close missing CPU matrix coverage. No runtime ratio is
produced. Other P1 GPU geometry/application/performance requirements remain open.

The full ablation matrix declares 25 rows: 16 targeted CPU paths, four full-dimension
exclusions above N=12 and five optional CUDA paths. Reduced sparse N=20
has D=17711 with a dense construction intermediate and needs its declared
memory budget. CPU results cannot characterize Julia solver internals.

All V2 performance commands eventually expose or retain frozen scenarios, output location, warmup/independent-repeat policy and numerical resource limits. Do not assume a shared flag exists on current scripts. Public examples must retain source-checkout execution and GPU opt-in requirements.

<a id="v2-smoke-tier"></a>

### Smoke Tier

Goal: verify the implemented V2 entry point and evidence path before expensive campaigns.

Minimum requirements:

- One small deterministic CPU scenario per changed runner with a retained config/command and numerical sanity gate.
- Valid JSON/CSV/Markdown, aggregate where implemented, actual result/manifest/reference links and reload validation.
- Controlled skip, numerical failure and supervisor timeout/crash checks with retained context.
- Warmup/measurement count and timer-boundary checks; no exact wall-clock assertions or speedup requirements.

CUDA setup/parity smoke is separate and requires `SAGITTARIUS_ENABLE_GPU_TESTS=1` plus successful initialized doctor. Passing CPU smoke does not close hardware evidence.

<a id="v2-correctness-tier"></a>

### Correctness Tier

Goal: establish frozen accuracy/reference gates before performance summaries qualify.

Use small analytic Rabi/blockade/decay, projected-dense scaling/ablation, exact-MWIS with small brute force, independent observable values/order, solver sensitivity and coherent/driven dephasing references. Retain requested/effective settings, stable shared times, error metric/tolerance, finite-value results and applicable Python/Julia golden logs. Pilot-confirm thresholds before campaign freeze; preserve mismatches as failed rows.

Numerical targets and exact fixtures are defined per suite in [plan v2](plans/v2.md). Independent references, solver refinement, statistical uncertainty and physical approximation errors have separate meanings. Under-resolved solver cases remain visible but cannot rank performance at an unmet accuracy target.

<a id="v2-parity-tier"></a>

### Parity Tier

Goal: compare execution paths under the same declared scenario and compatible accuracy.

- CPU/CUDA: identical basis/input/precision, pulse, solver/output/observable policy; warm both paths, synchronize GPU and retain per-size trajectory parity.
- Full/projected/reduced and dense/sparse: verify the intended operator/state mapping and disclose approximation/dimension differences.
- Python/Julia: preserve atom/bitstring ordering, addressing, effective solver and serialized metadata.
- Solver methods: compare shared output times and verified references; use legal adaptive Tsit5/Vern9 or fixed RK4 settings.
- MCWF/Lindblad: use declared multi-seed uncertainty and common times; more trajectories need not improve every seed monotonically.

Retain both paths' diagnostics, results/manifests/reference reports and unavailable combinations. CPU matvec and CUDA ODE solve are separate workloads and cannot yield a parity-based speedup.

<a id="v2-scaling-tier"></a>

### Scaling Tier

Goal: execute the declared performance matrices with repeatable measurement and retained resource boundaries.

| Suite/axis | Target coverage |
| :--- | :--- |
| Scaling atoms/geometry/radius | N=2,4,6,8,12,16,20; chains/declared rectangles; Rb/a=1.1,1.5,2.1. |
| MWIS instances | N=2,4,6,8,10,12,16,20; five frozen weighted instances per size; independent AQC/ILP repeats. |
| Open-system | N=1,2,4,6,8,10,12,16,20; separate Lindblad/MCWF resource limits; 100/500/1000 trajectories. |
| GPU/reduced ablation | Bounded N=20 extensions with per-size CPU/CUDA gates or reduced-path references as applicable. |
| Solver/observable cost | Declared tolerance/step/grid and type/count/order matrices; 21/101/501 output points. |

Freeze the scenario list, exact replay inputs/hash, reference/statistical policy, limits and stop conditions. Use two warmups and at least five independent eligible measurements by default; retain all raw rows and statistic membership. Separate setup/solve/serialization, process-lifetime peaks and GPU snapshots. Preflight D, D^2 and dense intermediate allocations and preserve all budget exclusions/attempted failures.

Do not expand every axis into an unbounded Cartesian product; use plan-defined anchor scans and selected combinations. Record lower measured limits and large-case reference gaps. A skipped N=20 row documents an unexecuted target and leaves successful coverage open.

Performance-tier acceptance for all seven suites includes the plan's
[suite-specific timing outputs](plans/v2.md#runtime-reporting-requirements-for-all-seven-suites):
explicit timer scope, per-configuration raw records, median/min/max/p25/p75,
eligible counts/membership and matching companion summaries. Include numerical
error, graph-quality or stochastic-uncertainty context as applicable. Smoke,
correctness-only controls and rejection tests do not require a five-repeat
performance campaign. Existing [P0 distributions](reports/p0-runtime-statistics-2026-11-27.md)
can be tabulated without rerunning computation; no new P1 flags or runner
completion are implied by these documentation requirements.

<a id="v2-stress-tier"></a>

### Stress Tier

Goal: characterize practical representation/hardware limits with retained failure evidence.

Declare timeout, memory budget, stop condition, retry policy and process/device ownership before execution. Keep backend initialization, first-solve and warmed timing distinct, with attributable hardware/runtime/container/commit metadata. A parent supervisor records timeout/OOM/crash outcomes even if the child cannot write its final artifact.

Full dense/sparse construction, Lindblad D-by-D storage, reduced paths and MCWF each have their own budget. Do not attempt allocations already known to exceed it. Preserve raw failures and partial data; a failure-free subset is not a complete scale-limit result. Stress work does not replace small correctness gates, the declared performance campaign or public governance review. P2 advanced cluster/noise work stays outside this V2 plan.
