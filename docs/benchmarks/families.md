# Benchmark Families

Status: `Mixed`
Roadmap: Phase 16
Version: `benchmark-families/v1`
Last reviewed: 2026-11-27

This page has two parallel parts: [Benchmarking V1](#benchmarking-v1) preserves the complete original document with nested headings; [Benchmarking V2](#benchmarking-v2) follows the same chapter organization for the planned P0–P1 work in [plan v2](plans/v2.md). V1 retains its original metadata, commands and evidence wording as the initial baseline. V2 scaling, ablation and GPU implementation/evidence are tracked in plan v2; other suite targets remain planned until acceptance. GOV-004 remains the policy authority, and the generation names do not rename artifact schemas.

## Benchmarking V1

Status: `Done`
Roadmap: Phase 16
Version: `benchmark-families/v1`
Last reviewed: 2026-08-12

This page defines the benchmark-family protocols for Phase 16. A family is a stable group of scenarios with shared correctness gates, metadata, and interpretation rules.

### Family Summary

| Family | Initial scenarios | Primary evidence |
| :--- | :--- | :--- |
| Physics baselines | Single-atom Rabi, two-atom blockade, Landau-Zener sweep, dense-vs-reduced small chains. | Analytic or dense-reference errors, basis sizes, solver metadata, artifacts. |
| Cold-atom dynamics | Rydberg chains, local addressing, Z2 ordering, 2D pattern formation. | Observable trajectories, correlations, blockade violations, backend metadata. |
| Open-system dynamics | Lindblad decay/dephasing, MCWF-vs-Lindblad, decoherence impact. | Trace and positivity checks, trajectory variance, runtime/memory scaling, seed metadata. |
| Optimization/AQC | UDG/MWIS, weighted MWIS, schedule sensitivity, structured graph families. | Feasibility, exact optimum where available, objective value, approximation ratio. |
| Backend performance | Dense/sparse/reduced ablation, CPU/CUDA parity, solver sensitivity, CUDA cached path. | Runtime, memory, GPU memory, max trajectory error, bounded speedup statements. |
| Sweep/cluster execution | Parameter sweeps, phase-diagram scans, cluster throughput. | Jobs/sec, resumability, per-run manifest links, aggregate artifacts, failure rows. |

### Physics Baselines

Purpose: prove that basic neutral-atom dynamics and reduced-basis behavior are physically and numerically coherent.

Initial protocol items:

- Rabi oscillation validates drive amplitude, duration, unit convention, and population transfer shape.
- Two-atom blockade validates interaction strength, blockade radius expectations, and double-excitation suppression.
- Landau-Zener sweep validates detuning-ramp handling, adiabatic-transfer behavior, and solver sensitivity.
- Small-chain full-vs-reduced validation compares full Hilbert-space results to blockade-reduced results.

Required evidence:

- scenario ID and physical parameter table;
- analytic or dense-reference output where feasible;
- max trajectory deviation and final-state deviation;
- solver method, tolerances, output grid, and basis mode;
- run manifest and result artifact path when a simulation artifact is emitted.

Current correctness runner: `tests/test_performance/benchmark_physics_correctness.py` records analytic Rabi and ideal-blockade errors, finite-sweep Landau-Zener final-state error against the stated asymptotic formula, and a static small-chain exact projected dense matrix-exponential comparison. The small-chain check verifies the reduced Hamiltonian and evolution against the projection of the dense Hamiltonian; it does not claim physical equivalence between finite-interaction full-basis and hard-blockade trajectories.

### Cold-Atom Dynamics

Purpose: exercise realistic neutral-atom array workflows beyond toy baselines.

Initial protocol items:

- chain excitation profiles under global and local addressing;
- local-addressing sparse dictionary stress cases;
- Z2 or antiferromagnetic ordering dynamics;
- 2D array pattern formation with blockade diagnostics.

Current correctness runner: `tests/test_performance/benchmark_phase16_validation.py` emits one row per CPU case: 3-atom global chain, 3-atom vector/dictionary local addressing, 4-atom alternating-detuning Z2 chain, and a 2x2 array. Each uses a small projected dense matrix-exponential reference with absolute tolerance `1e-8`. These rows establish only small-system solver and pulse/geometry correctness, not a physical pattern-formation or scalability claim.

Required evidence:

- atom geometry and atom-ordering metadata;
- pulse schedule and addressing map;
- observable declarations and output sample count;
- pair-correlation or blockade-violation metrics when the observable API supports them;
- solver/backend metadata and failure diagnostics.

### Open-System Dynamics

Purpose: validate and characterize theory-noise and trajectory workflows.

Initial protocol items:

- Lindblad decay and dephasing on small systems;
- MCWF-vs-Lindblad agreement as trajectory count increases;
- decoherence impact on blockade and ordering scenarios;
- future Phase 14 custom noise and stochastic Hamiltonian scenarios.

Current correctness runner: `tests/test_performance/benchmark_phase16_validation.py` emits fixed-seed (`20260811`) one-atom decay-plus-dephasing rows for 100 and 500 MCWF trajectories. They retain analytic decay expectation, Lindblad trace and positivity errors, MCWF-vs-Lindblad error, and require the 500-trajectory error not to exceed the 100-trajectory error. This is a small-system correctness check; multi-atom decoherence studies and trajectory runtime/memory scaling remain future work.

Required evidence:

- noise model, rates, and affected atoms or weights;
- trace-preservation and density-matrix positivity checks;
- trajectory count, seed metadata, and convergence summary;
- runtime and memory scaling for trajectory count;
- explicit unsupported-combination failures.

### Optimization/AQC

Purpose: validate UDG/MWIS mappings and optimization-like schedules without overstating algorithmic capability.

Initial protocol items:

- seeded UDG generation;
- small exact ILP baseline comparison;
- weighted MWIS objective evaluation;
- schedule sensitivity over drive and detuning ramps;
- final bitstring sampling once Phase 15 readout APIs land.

Current correctness runner: `tests/test_performance/benchmark_mwis_aqc.py` runs deterministic weighted UDG cases across `smoke` (2 nodes), `correctness` (3/4 nodes), and bounded `scaling` (2/4/6 nodes) tiers. Each row retains the seeded edge list, node weights, graph hash, AQC schedule, exact PuLP/CBC objective, feasibility, objective gap, approximation ratio, final-state optimal-solution probability, and a reference report. Per-scenario ILP or solver exceptions remain failed rows. These CPU cases validate the mapping and evidence contract only; their runtime and approximation outputs are not general AQC performance claims.

Required evidence:

- graph seed, geometry, radius, weights, and edge list hash;
- exact baseline method and exact objective where tractable;
- feasibility, objective value, objective gap, approximation ratio, and success probability when sampling exists;
- schedule metadata and solver settings;
- failure rows for ILP failure, infeasible output, timeout, or memory failure.

### Backend Performance

Purpose: characterize execution paths and backend behavior under bounded scenarios.

Initial protocol items:

- dense vs sparse vs reduced ablation;
- CPU vs CUDA parity and timing;
- solver method sensitivity;
- CUDA cached sparse-buffer path;
- first-run setup cost vs warmed execution cost.

Current CUDA protocol: `tests/test_performance/benchmark_cuda_mwis_protocol.py` is opt-in (`SAGITTARIUS_ENABLE_GPU_TESTS=1`) and calls `doctor(backend="CUDA", initialize_backend=True)` before importing or executing CUDA paths. It emits a small CPU/CUDA chain parity row and a seeded weighted-MWIS CPU/CUDA row with device, driver, CUDA.jl/runtime, and Julia metadata; cold/warm timing; GPU-memory snapshots; parity error; and structured skipped/doctor/runtime failure rows. It is local diagnostic evidence only.

Current solver/path protocol: `tests/test_performance/benchmark_solver_performance.py` repeats full dense, full sparse, reduced matrix-free, and reduced sparse matvec paths; it records a skipped cached-GPU row until the opt-in CUDA protocol validates that backend. Full-path repeated matvec comparison uses a `1e-12` relative-error gate with its absolute error and scale retained; reduced paths use `1e-10` absolute error. Tsit5, Vern9, and fixed-step RK4 trajectories use a high-accuracy Tsit5 trajectory reference with a `1e-6` gate and retain result/manifest links.

Required evidence:

- backend diagnostics before execution;
- CPU and accelerator hardware metadata;
- effective solver method and backend path;
- runtime, process memory, GPU memory where available, and validation metric;
- separate rows for backend initialization failure and numerical mismatch.

### Sweep/Cluster Execution

Purpose: validate batch execution, resumability, and aggregate evidence production.

Initial protocol items:

- parameter sweeps over `omega`, `delta`, blockade radius, geometry, noise, solver settings, and observables;
- phase-diagram scan scaffolding;
- `ParallelSimulation` throughput;
- future cluster execution through Phase 18 deployment work.

Current local protocol: `tests/test_performance/benchmark_sweep_cluster.py` checkpoints a `sweep-artifact/v1`, executes pending omega values through `ParallelSimulation.map()`, persists per-item result and manifest links, then writes a benchmark aggregate and suite row for each requested worker count. Passing `--resume-from` retries only the artifact's pending/running/failed IDs. This exercises local Julia `Distributed` workers and deterministic kernel correctness; it does not establish multi-node deployment or physics-solver throughput.

Required evidence:

- sweep config hash and parameter grid;
- per-run manifest or result artifact links;
- aggregate artifact row for every completed, skipped, and failed run;
- resumability metadata and restart behavior;
- throughput metrics only when correctness and artifact completeness pass.

## Benchmarking V2

Status: `Mixed`

Scaling has [retained local v2 acceptance evidence](evidence/p0-scaling-v2-2026-11-26/README.md): 42 scenarios and 210 eligible repeats, including all six N=20 geometry/radius configurations. This is bounded local numerical/software evidence; other suite targets and release/public-use gates remain separate.

Ablation has [local ablation evidence](evidence/p0-ablation-v2-2026-11-27/README.md): all 16 targeted CPU paths and 80 independent measured batches passed, including both reduced paths at N=20 (D=17711). Four full-dimension exclusions and five optional CUDA skips are retained. CUDA, recurring RC and public-use approval remain separate.

CUDA follow-up has [retained local hardware evidence](evidence/p0-ablation-cuda-v2-2026-11-27/README.md): all five ablation chain cases through N=20 passed, with 25 measured CPU/CUDA ODE pairs and 80 saved first/warm/measured result/manifest pairs. First-call initialization and diagonal-observable transfer fixes are included. The original CPU archive and its historical CUDA skips remain unchanged. CUDA stays experimental; this ablation-only archive is separate from the P1 GPU matrix below, recurring RC and public-use gates.


This generation maps the seven suites in [plan v2](plans/v2.md) into the existing family taxonomy. Matrices, thresholds and delivery batches remain defined by that plan. Current V1 evidence is preserved separately; no V2 measurement is completed by this document.

<a id="v2-family-summary"></a>

The [P1 GPU local campaign](evidence/p1-gpu-v2-2026-11-27/README.md) completes the declared eight-case matrix: chains N=2,4,8,12,16,20, a 2x2 lattice and seeded two-node MWIS. All 40 measured CPU/CUDA pairs passed at 101 shared times after symmetric warmups; N=20 has D=17711. Separate backend memory, saved results/manifests, qualified median ratios and all companion values passed the backend-free audit. CUDA remains experimental; this is shared-workstation software/numerical evidence, not independent physical validation, recurring RC or public-use approval.

### Family Summary

| Family | V2 scope | Acceptance evidence |
| :--- | :--- | :--- |
| Physics baselines | Small analytic/projected-dense controls for measured execution paths. | Independent reference errors, frozen tolerances and source/result links. |
| Cold-atom dynamics | Existing global/local/Z2/2D fixtures used as bounded geometry/addressing controls. | Retained references and applicable Python/Julia semantic checks. |
| Open-system dynamics | P1 local-noise Lindblad/MCWF costs and convergence through declared N=20 targets. | Analytic/dense references, multi-seed uncertainty, resource limits and manifests. |
| Optimization/AQC | P1 weighted MWIS/UDG through N=20 with repeated AQC/ILP work. | Actual instances, exact status, feasibility/objective/probability metrics and result provenance. |
| Backend performance | P0 scaling/ablation and P1 GPU/solver/observable matrices. | Matched workload/accuracy, independent repeats, attributable memory and effective configuration. |
| Sweep/cluster execution | Retain the existing local baseline; no new P2 implementation in this plan. | Existing V1 checkpoint/resume evidence and explicit Phase 18 boundary. |

<a id="v2-physics-baselines"></a>

### Physics Baselines

Purpose: provide independent numerical controls before performance interpretation.

Protocol items:

- Reuse analytic Rabi and ideal-blockade fixtures and the existing Landau-Zener control with its stated finite-sweep/reference limitations.
- For scaling N<=8, validate the reduced Hamiltonian/trajectory against an independently constructed projected dense reference; start with observable error <=1e-8, then pilot-confirm and freeze.
- For constant solver fixtures use analytic or matrix-exponential references; for time-dependent fixtures verify a tighter reference using another method or refinement.
- Separate reduced implementation parity from any finite-interaction full-space approximation claim and error budget.

Required evidence includes reference input/configuration, errors and tolerances, basis/order/units, pulse/solver/output settings, applicable golden-test logs and actual result/manifest/reference links. Larger tighter-tolerance checks retain their reference limitations and do not imply independent physical validation.

<a id="v2-cold-atom-dynamics"></a>

### Cold-Atom Dynamics

Purpose: preserve geometry and addressing controls used by V2 suites without reopening the initial closure or asserting new pattern-formation results.

Protocol items:

- Retain V1 three-atom global/local chains, four-atom Z2 and 2x2 fixtures and their projected-dense evidence.
- Apply atom-order/local-addressing and observable-order checks to the new scaling, GPU and observable matrices.
- Include chain/rectangular geometry and three radius/spacing ratios in P0 scaling, plus the small 2x2 GPU parity case.

Retain actual coordinates, pulse/addressing declarations, basis/radius, output times, effective settings and failures. Multi-atom ordering/decoherence interpretation remains separate from runtime characterization. The detailed scaling shapes and N=20 target are in [P0 scaling](plans/v2.md#p0-scaling).

<a id="v2-open-system-dynamics"></a>

### Open-System Dynamics

Purpose: characterize implemented local Markovian decay/dephasing through [P1 open-system](plans/v2.md#p1-open-system), with separate numerical, statistical and resource evidence.

| Axis | V2 matrix |
| :--- | :--- |
| Target N | 1,2,4,6,8,10,12,16,20 |
| Paths/basis | CPU Lindblad and MCWF; full/reduced as resources and model permit |
| Models | Decay only, pure dephasing only, combined; scalar anchor and small per-atom-rate fixture |
| Trajectories | 100,500,1000; five retained statistical seeds separately from timing repeats |
| Output | 101 shared explicit times; site populations and a frozen supported total/pair set |

Use existing one-atom excited-state decay on [0,2], a coherent/driven dephasing reference and a frozen interacting reduced chain. Initial rate anchors are gamma=0.5 and gamma_phi=0.125 in declared units. Start analytic/trace targets at 1e-6 and minimum density eigenvalue at -1e-7. Check Hermiticity/trace/positivity on saved reference states outside measured solve timing. Population-only undriven decay is insufficient for dephasing.

Require multi-seed MCWF/Lindblad checks at shared times where tractable, with frozen uncertainty/multiplicity criteria. Do not generalize V1's fixed-seed sensitivity wording into a per-seed monotonic rule. At larger N retain tighter-solver/trajectory checks, analytic special-case controls and interacting-reference gaps. Preflight D and D^2 including temporary/output memory; a budget-excluded N=20 Lindblad row leaves that scope open.

The new performance runner is planned; preserve the existing one-atom correctness runner. Default raw trajectory storage off and measure opt-in retention separately. Keep actual serial/threaded execution mode, requested/effective seeds/counts, rates, memory, throughput, failures and result/manifests. P2 custom/correlated/collective/stochastic noise remains dependent on Phase 14 and outside V2's P0–P1 scope.

<a id="v2-optimizationaqc"></a>

### Optimization/AQC

Purpose: extend bounded weighted UDG/MWIS measurement through [P1 MWIS/UDG](plans/v2.md#p1-mwisudg), preserving current correctness fixtures and interpreting quality outcomes separately from implementation correctness.

Use N=2,4,6,8,10,12,16,20, initially five instances per size with seeds 101–105, density parameter 0.8, Rb=1.0 and the runner's retained weight range. Freeze the existing sin-squared schedule anchor with duration 0.15 after pilot numerical checks. Retain actual coordinates, edges, weights, graph hash and measured degree/density, not just generator parameters.

Independently repeat AQC and ILP on each fixed instance, separating generation, setup/model construction, solve, post-processing and serialization. Record PuLP/CBC version, threads, limits and optimality/termination status. Request exact references through N=20; if optimality is unproven retain the incumbent/bound where available and mark exact metrics unavailable. Small brute-force checks verify ILP/objective/bitstring mappings and probability sums.

Retain feasibility, candidate weight, exact gap/ratio and probability mass across all optimal sets where the optimum is proven. Poor feasible objectives remain valid results; numerical/mapping and feasibility gates remain explicit. Add actual AQC result/manifest provenance compatibly. Keep current tier outputs and use the planned `mwis_aqc_performance` artifact/suite for expanded measurements. Broad schedule searches, planted families and distribution-wide optimization claims remain later work.

<a id="v2-backend-performance"></a>

### Backend Performance

Purpose: complete P0 scaling/ablation and P1 GPU/solver/observable characterization under frozen numerical accuracy and workload definitions.

| Suite | V2 matrix and implementation | Reference/interpretation gate |
| :--- | :--- | :--- |
| `scaling` | Implemented: N=2,4,6,8,12,16,20; chain and declared rectangular shapes; Rb/a=1.1,1.5,2.1. | Small projected-dense and larger sensitivity checks; actual D/pruning, setup/solve/memory and resource rows. |
| `ablation` | Implemented four Python CPU matvec paths at N=4,8,12; reduced N=16,20 under budget; separate optional CUDA ODE with matched CPU trajectory gates and saved manifests. | Fixed seeded normalized H*psi, independent dense/projected references at N<=8 and analytic transition action above; full relative error 1e-12, reduced absolute error 1e-10 and finite gates. Two warmups/five batches, construction/dense intermediates, supervised memory/failures and saved-output audit. |
| `gpu` | Implemented chain parity N=2,4,8, 2x2 geometry, performance chain N=12,16,20 and seeded two-node MWIS parity. | Initialized doctor/opt-in, 101 shared times, separate CPU/CUDA workers, two warmups/five measurements, synchronized SDK timing, per-scenario error <=1e-6 and qualified median ratios. |
| `solver` | Rabi, addressed chain and time-dependent ramp; Tsit5/Vern9 reltol=1e-6,1e-8,1e-10; RK4 dt=T/100,T/200,T/400; 21/101/501 output points. | Legal method/stepping combinations, verified tighter/independent references, common times and error target initially 1e-6. |
| `observables` | Ten implemented diagonal types; 1/4/16/64 declarations; original/reverse/fixed permutation; 21/101/501 points; bounded N=4,8,12,16,20 cost series. | Independent probability/occupation references initially <=1e-8, basis/index/order and saved metadata, comparable output/storage policy. |

Use two warmups and at least five independent measurements by default. Matvec's default 50 operations is a batch count; never use it as the independent repeat count. CPU NumPy/SciPy matvec performance does not characterize Julia solver internals. Do not form matvec/ODE speedups or compare numerical methods at different eligible accuracy levels.

Observable correctness covers small full/reduced Schrodinger and representative Lindblad/MCWF states. Mixed and single-type workloads retain every declaration; duplicate named outputs are labeled. Empty-observable runs saving full state history are a different storage workload. Off-diagonal observables and unsupported backend combinations remain outside scope.

All rows retain effective settings, requested/output metadata, numerical gates, hardware/backend/runtime, source/result links and attributable memory; GPU snapshots remain distinct from peaks. Full fixture values, reference policies and planned output stems are in [plan v2](plans/v2.md).

All seven suites use the plan's [runtime reporting requirements](plans/v2.md#runtime-reporting-requirements-for-all-seven-suites).
Backend reports pair per-configuration runtime distributions with numerical
errors; solver reports include error-versus-runtime, and observable reports
identify output/storage policy before estimating added cost. Optimization
reports separate AQC/ILP solve distributions per frozen graph and retain exact
termination/quality. Open-system reports separate Lindblad/MCWF time and MCWF
completed-trajectories-per-second samples from multi-seed convergence. Each
summary retains counts, statistic membership and median/min/max/p25/p75.
The [P0 timing report](reports/p0-runtime-statistics-2026-11-27.md) exposes
retained scaling/ablation statistics without changing evidence status or
deriving CPU-matvec/CUDA-solve ratios.

<a id="v2-sweepcluster-execution"></a>

### Sweep/Cluster Execution

Purpose: preserve the existing local checkpoint/resume evidence while keeping new work aligned to P0–P1 scope.

V2 adds no cluster/sweep implementation or new throughput campaign. Retain V1 `ParallelSimulation` deterministic-map artifacts and the distinction between scientific `sweep-artifact/v1` and governed benchmark evidence. Physics-solver sweep and multi-node deployment remain in the requirements P2/Phase 18 scope.

Any reused sweep/checkpoint links must resolve and preserve item IDs, statuses, failures and result/manifests. Do not cite the existing local mapping workload as end-to-end physics-solver or multi-node scaling evidence. Campaign aggregation in V2 is not a new distributed scheduler.
