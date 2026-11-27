# P0 runtime statistics from retained v2 evidence

Status: Derived local diagnostic report; original campaign archives unchanged
Roadmap: Phase 16 P0 scaling and ablation
Version: `p0-runtime-report/v1` (document version, not an artifact schema)
Last reviewed: 2026-11-27

This report makes the existing timing distributions visible alongside the
[seven-suite runtime requirements](../plans/v2.md#runtime-reporting-requirements-for-all-seven-suites).
It reorganizes retained measurements; no simulations or hardware tests were
rerun. Times refer to each campaign's frozen source/environment, not necessarily
the current checkout. All values below are wall-clock seconds unless stated.

## Sources and verification

| Campaign | Source and retained acceptance | Timed evidence |
| --- | --- | --- |
| Scaling, 2026-11-26 | [Archive](../evidence/p0-scaling-v2-2026-11-26/README.md), [suite JSON](../evidence/p0-scaling-v2-2026-11-26/scaling_results_suite.json), [raw repeats](../evidence/p0-scaling-v2-2026-11-26/scaling_repeats.json), [original audit](../evidence/p0-scaling-v2-2026-11-26/audit.json) | 42 passed scenarios, 210 eligible SDK calls; two warmups and five measurements each |
| Ablation CPU, 2026-11-27 | [Archive](../evidence/p0-ablation-v2-2026-11-27/README.md), [suite JSON](../evidence/p0-ablation-v2-2026-11-27/ablation_bench_results_suite.json), [raw repeats](../evidence/p0-ablation-v2-2026-11-27/ablation_repeats.json), [original audit](../evidence/p0-ablation-v2-2026-11-27/audit.json) | 16 passed paths, 80 eligible batches; two warmups and five batches of 50 operations each; nine skips retained |
| Ablation CUDA follow-up, 2026-11-27 | [Archive](../evidence/p0-ablation-cuda-v2-2026-11-27/README.md), [compressed original suite](../evidence/p0-ablation-cuda-v2-2026-11-27/campaign.tar.gz), [raw pairs](../evidence/p0-ablation-cuda-v2-2026-11-27/ablation_repeats.json), [original audit](../evidence/p0-ablation-cuda-v2-2026-11-27/audit.json) | Five passed sizes, 25 measured pairs; first solves and two warmup pairs per size also retained |

All three original audits record `contract_audit_passed=true`. During this
documentation update, the five statistics below were independently recomputed
from eligible non-warmup raw records and checked against every saved summary,
including CUDA's separate `cpu_statistics`. Counts and statistic membership
were checked. This report does not repeat the original saved-trajectory or
saved-matvec numerical audits; those results remain linked above.

For replay, group raw records by `scenario_id`, select `status=passed`,
`metrics.eligible=true`, `metrics.warmup=false`, and follow the suite's statistic
member IDs. Use `metrics.runtime_seconds`; CUDA paired CPU values use
`metrics.cpu_runtime_seconds`. The CUDA suite's CPU IDs `matched-cpu-repeat-i`
map to the same scenario's pair with `metrics.repeat_index=i`. Recompute linear
Hyndman-Fan type-7 quantiles: sort x, let h=(n-1)q, and interpolate adjacent
values at floor(h) and ceil(h). Do not round before computing statistics.
Tables round only their displayed values to nine significant digits; every row
has five eligible measurements. Exact IDs/values remain in the source JSON.

The host was an Intel Core i7-14700KF Linux/WSL shared workstation; runtime
metadata records Python 3.11.15, Julia 1.13.4 and SDK 1.0.8 with one effective
Julia/BLAS thread. CUDA used an RTX 5070 Ti; driver/runtime and CUDA.jl versions
are retained in its archive. Source identities differ: scaling baseline
`efef3754237b28b61e0829edf164088597ffc13a`, CPU ablation baseline
`d4f4cea0c255d984246f12014d3b906bdc6e722f`, CUDA baseline `11f22d2`, each with
retained dirty-source snapshots. Their measurements are not pooled.

## Scaling

One timed execution is an end-to-end `Simulation.run` call, including SDK
validation, operator construction, observable collection and manifest creation.
External numerical checks, serialization and reporting are excluded. The frozen
anchor uses a=4 um, C6=100 rad*um^6/us, omega=2*pi rad/us, delta=0, all-ground
initial state, Tsit5 adaptive reltol=1e-8/abstol=1e-10, duration 0.5 us and 101
explicit output times collecting pop0. D is the actual reduced basis dimension;
2^N is the full dimension. Scenario IDs encode geometry, Rb/a and N.
All 42 scenarios passed the frozen observable-error gate 1e-8: N<=8 uses
independent projected-dense checks, while N>8 uses tighter same-method
sensitivity. Saved maximum observable error is 1.5280641196824263e-9;
per-scenario errors and reference types remain in the linked suite.

| Scenario ID | N | D | Median s | Min s | Max s | p25 s | p75 s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| chain-r1.1-n2 | 2 | 3 | 0.224815356 | 0.183025897 | 0.261193555 | 0.209389118 | 0.242245095 |
| chain-r1.1-n4 | 4 | 8 | 0.187831644 | 0.181381949 | 0.260676835 | 0.185960139 | 0.216729818 |
| chain-r1.1-n6 | 6 | 21 | 0.213234481 | 0.195095743 | 0.284186259 | 0.208509388 | 0.240686559 |
| chain-r1.1-n8 | 8 | 55 | 0.235245884 | 0.197482546 | 0.284400182 | 0.201652918 | 0.251805419 |
| chain-r1.1-n12 | 12 | 377 | 0.258252299 | 0.21795449 | 0.272704132 | 0.228981715 | 0.258615924 |
| chain-r1.1-n16 | 16 | 2584 | 0.582136447 | 0.517960714 | 0.699240293 | 0.552624404 | 0.59872955 |
| chain-r1.1-n20 | 20 | 17711 | 3.52641004 | 3.49866457 | 3.63768144 | 3.51041353 | 3.6286102 |
| chain-r1.5-n2 | 2 | 3 | 0.181698138 | 0.178381285 | 0.215027192 | 0.181108647 | 0.189815604 |
| chain-r1.5-n4 | 4 | 8 | 0.215114013 | 0.185980652 | 0.245568218 | 0.197992479 | 0.236202268 |
| chain-r1.5-n6 | 6 | 21 | 0.198539128 | 0.185747806 | 0.250939105 | 0.19731125 | 0.205963188 |
| chain-r1.5-n8 | 8 | 55 | 0.221183857 | 0.188779929 | 0.412540413 | 0.193280386 | 0.252423654 |
| chain-r1.5-n12 | 12 | 377 | 0.227769983 | 0.210755344 | 0.358053627 | 0.218362321 | 0.264695785 |
| chain-r1.5-n16 | 16 | 2584 | 0.568731912 | 0.552521366 | 0.649441242 | 0.552627385 | 0.621074318 |
| chain-r1.5-n20 | 20 | 17711 | 3.51153507 | 3.40341127 | 3.59681703 | 3.50037615 | 3.52669277 |
| chain-r2.1-n2 | 2 | 3 | 0.184322138 | 0.182175127 | 0.227753307 | 0.182354244 | 0.189031866 |
| chain-r2.1-n4 | 4 | 6 | 0.225060685 | 0.186020891 | 0.260466824 | 0.202344243 | 0.232928903 |
| chain-r2.1-n6 | 6 | 13 | 0.224922193 | 0.184224625 | 0.367067162 | 0.209633188 | 0.277150176 |
| chain-r2.1-n8 | 8 | 28 | 0.199354539 | 0.185689268 | 0.251802533 | 0.188606475 | 0.209027971 |
| chain-r2.1-n12 | 12 | 129 | 0.204106458 | 0.190720669 | 0.346188246 | 0.19708658 | 0.218456323 |
| chain-r2.1-n16 | 16 | 595 | 0.260216815 | 0.23809566 | 0.330815102 | 0.244415853 | 0.290354491 |
| chain-r2.1-n20 | 20 | 2745 | 0.60511941 | 0.574867137 | 0.778788769 | 0.593205063 | 0.655334089 |
| rectangle-r1.1-n2 | 2 | 3 | 0.193090809 | 0.183785571 | 0.289016306 | 0.187199197 | 0.251562245 |
| rectangle-r1.1-n4 | 4 | 7 | 0.218551212 | 0.188377359 | 0.312519611 | 0.189515568 | 0.265686121 |
| rectangle-r1.1-n6 | 6 | 17 | 0.206122915 | 0.186534456 | 0.255735545 | 0.198640224 | 0.209470975 |
| rectangle-r1.1-n8 | 8 | 41 | 0.232824843 | 0.186817405 | 0.247442296 | 0.194439296 | 0.239914709 |
| rectangle-r1.1-n12 | 12 | 227 | 0.212655238 | 0.201676883 | 0.274019195 | 0.20337109 | 0.247774326 |
| rectangle-r1.1-n16 | 16 | 1234 | 0.340450547 | 0.333885547 | 0.435434758 | 0.334162408 | 0.374541956 |
| rectangle-r1.1-n20 | 20 | 6743 | 1.35795161 | 1.2630813 | 1.41585262 | 1.28397403 | 1.40250602 |
| rectangle-r1.5-n2 | 2 | 3 | 0.222316827 | 0.191165018 | 0.370237617 | 0.195049659 | 0.234020214 |
| rectangle-r1.5-n4 | 4 | 5 | 0.190853452 | 0.184956407 | 0.255082237 | 0.187340464 | 0.208052741 |
| rectangle-r1.5-n6 | 6 | 11 | 0.211173498 | 0.198419209 | 0.220076414 | 0.201120157 | 0.217659499 |
| rectangle-r1.5-n8 | 8 | 21 | 0.221722163 | 0.204074864 | 0.225714272 | 0.218075545 | 0.225256472 |
| rectangle-r1.5-n12 | 12 | 93 | 0.22340177 | 0.193523474 | 0.300359986 | 0.222842607 | 0.266235057 |
| rectangle-r1.5-n16 | 16 | 314 | 0.216718575 | 0.20262047 | 0.268518846 | 0.210762357 | 0.225270337 |
| rectangle-r1.5-n20 | 20 | 1213 | 0.382497078 | 0.360984355 | 0.453261827 | 0.374265215 | 0.40091325 |
| rectangle-r2.1-n2 | 2 | 3 | 0.211309908 | 0.181979502 | 0.242589684 | 0.188166256 | 0.220173728 |
| rectangle-r2.1-n4 | 4 | 5 | 0.195815432 | 0.19249663 | 0.248773013 | 0.195784753 | 0.247597238 |
| rectangle-r2.1-n6 | 6 | 9 | 0.193182481 | 0.178839307 | 0.240782647 | 0.179738693 | 0.197493859 |
| rectangle-r2.1-n8 | 8 | 17 | 0.258295346 | 0.19152357 | 0.312965309 | 0.227596169 | 0.310068797 |
| rectangle-r2.1-n12 | 12 | 48 | 0.190685932 | 0.184524514 | 0.252030377 | 0.186330064 | 0.21501216 |
| rectangle-r2.1-n16 | 16 | 146 | 0.208404602 | 0.195573612 | 0.227781367 | 0.207705094 | 0.220759666 |
| rectangle-r2.1-n20 | 20 | 437 | 0.260307878 | 0.23149497 | 0.28213513 | 0.233469965 | 0.281456694 |

Separate setup measurements remain in each suite row's `metrics.timing`:
`python_setup_seconds`, `initialized_doctor_seconds`,
`basis_construction_seconds`, `first_solve_seconds` and `reference_seconds`.
Warmups are in `metrics.warmups`; they are excluded from the table. These setup
values were measured once per scenario, not five times. Legacy `time_s` is the
first measured call, whereas `median_time_s` summarizes eligible calls.

## Ablation CPU

Each batch performs 50 H*psi operations on the same normalized complex128 input
(seed 1234), using Python/NumPy/SciPy. Construction, independent references,
validation and writes are excluded from batch time. Anchor: chain a=2 um,
Rb=3 um, C6=100 rad*um^6/us, omega=2*pi rad/us, delta=0.
The last column is derived as median batch seconds / 50, converted to
microseconds; it is not the legacy first-batch `time_per_operation_s`.
Full and reduced representations have different dimensions and approximation
semantics. No cross-representation speedup is inferred here.
All 16 rows passed finite-value and numerical gates: full max relative error
<=1e-12 using scale max(1,max(abs(reference))), reduced max absolute error
<=1e-10. Independent small dense and larger analytic-action reference scopes
are retained in the linked suite and original audit.

| Scenario ID | N | Executed D | Batch median s | Min s | Max s | p25 s | p75 s | Median us/op |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| chain-n4-full_dense | 4 | 16 | 1.71629945e-05 | 1.69060077e-05 | 1.73250155e-05 | 1.6926002e-05 | 1.7192011e-05 | 0.34325989 |
| chain-n4-full_sparse | 4 | 16 | 0.000123288017 | 0.000114202005 | 0.000129466993 | 0.000115166011 | 0.000129043998 | 2.46576034 |
| chain-n4-reduced_matrix_free | 4 | 8 | 0.000453400018 | 0.000433423003 | 0.000586818001 | 0.000445206999 | 0.000519894995 | 9.06800036 |
| chain-n4-reduced_sparse | 4 | 8 | 0.000120640994 | 0.000107118976 | 0.000130575005 | 0.000109336979 | 0.000124779996 | 2.41281989 |
| chain-n8-full_dense | 8 | 256 | 0.000497203 | 0.000493483996 | 0.000509530015 | 0.000493877014 | 0.000502846 | 9.94406 |
| chain-n8-full_sparse | 8 | 256 | 0.000205815013 | 0.000203591015 | 0.000249425997 | 0.000203697011 | 0.000221758994 | 4.11630026 |
| chain-n8-reduced_matrix_free | 8 | 55 | 0.00521909201 | 0.00514610601 | 0.005402126 | 0.00517399301 | 0.00522679201 | 104.38184 |
| chain-n8-reduced_sparse | 8 | 55 | 0.000126774015 | 0.000123033009 | 0.000430581014 | 0.00012511501 | 0.000133663998 | 2.53548031 |
| chain-n12-full_dense | 12 | 4096 | 0.209337041 | 0.205777521 | 0.228889069 | 0.207684055 | 0.217838442 | 4186.74082 |
| chain-n12-full_sparse | 12 | 4096 | 0.001977954 | 0.00195698399 | 0.00210471201 | 0.00197780802 | 0.00202907299 | 39.55908 |
| chain-n12-reduced_matrix_free | 12 | 377 | 0.057711743 | 0.056816638 | 0.058325785 | 0.057073269 | 0.057746732 | 1154.23486 |
| chain-n12-reduced_sparse | 12 | 377 | 0.00022863 | 0.000227584009 | 0.000262057991 | 0.000228001998 | 0.000241732982 | 4.57260001 |
| chain-n16-reduced_matrix_free | 16 | 2584 | 0.580886189 | 0.575129565 | 0.58264933 | 0.579378066 | 0.581941733 | 11617.7238 |
| chain-n16-reduced_sparse | 16 | 2584 | 0.00104894699 | 0.001032481 | 0.001069914 | 0.00104667898 | 0.001049799 | 20.9789397 |
| chain-n20-reduced_matrix_free | 20 | 17711 | 5.50170209 | 5.39467154 | 5.56340409 | 5.46794267 | 5.52870064 | 110034.042 |
| chain-n20-reduced_sparse | 20 | 17711 | 0.00849571801 | 0.00825242 | 0.009092589 | 0.00826269601 | 0.00878495802 | 169.91436 |

Basis/operator construction, reference and first-operation costs remain in
`metrics.timing`; initialized CPU doctor has its own timing field. The batch
distribution excludes these phases. Sparse construction still materializes
dense intermediates. `total_time_s` and `time_per_operation_s` describe the first
measured batch; repeated statistics have distinct semantics. The workload is
`fixed-normalized-input-matvec/v2`, separate from historical H^k*psi timings.

The nine original CPU-campaign exclusions remain accounted for:

| Scenarios | Status | Reason |
| --- | --- | --- |
| N=16,20 full_dense and full_sparse (four rows) | skipped | Full dimension exceeds the 4096 guard |
| N=4,8,12,16,20 reduced_sparse_gpu_cached (five rows) | skipped | Optional CUDA disabled in the original CPU campaign |

The CUDA follow-up below supplements these historical skips; it does not alter
their original rows or establish full-space N=16,20 execution.

## Ablation CUDA follow-up

These are SDK ODE solve times, separate from the CPU matvec workload. Both
backends reset the all-ground complex128 state and use the same chain, basis,
Tsit5 adaptive reltol=1e-8/abstol=1e-10, duration 0.2 us, pop0 observable and
101 explicit times. SDK validation, pulse/operator construction, transfers,
observable collection and manifest creation are included. CUDA synchronization
brackets its timer. Reference checks and writes are excluded. Sparse cache
reuse occurs within a solve, while SDK construction repeats across calls.

Each size has five eligible paired measurements with alternating execution
order, following separate first solves and two warmup pairs. Each pair passed
full-trajectory/configuration/backend gates at max absolute error <=1e-6.
CPU and CUDA distributions are shown separately without deriving a ratio.

| Scenario ID | N | D | Backend | Median s | Min s | Max s | p25 s | p75 s |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| chain-n4-reduced_sparse_gpu_cached | 4 | 8 | CPU | 0.249814695 | 0.17499907 | 0.33876392 | 0.220761088 | 0.255533383 |
| chain-n4-reduced_sparse_gpu_cached | 4 | 8 | CUDA | 0.391585623 | 0.331433598 | 0.435457018 | 0.347281326 | 0.395496578 |
| chain-n8-reduced_sparse_gpu_cached | 8 | 55 | CPU | 0.210738636 | 0.170987429 | 0.229185543 | 0.176877636 | 0.219853655 |
| chain-n8-reduced_sparse_gpu_cached | 8 | 55 | CUDA | 0.455271436 | 0.418087293 | 0.651339259 | 0.422897517 | 0.474632987 |
| chain-n12-reduced_sparse_gpu_cached | 12 | 377 | CPU | 0.28691572 | 0.18694107 | 0.363921109 | 0.267381699 | 0.303699037 |
| chain-n12-reduced_sparse_gpu_cached | 12 | 377 | CUDA | 0.56621523 | 0.438342375 | 0.86653496 | 0.452693115 | 0.608617284 |
| chain-n16-reduced_sparse_gpu_cached | 16 | 2584 | CPU | 0.343618972 | 0.325392569 | 0.376322368 | 0.34308969 | 0.349736965 |
| chain-n16-reduced_sparse_gpu_cached | 16 | 2584 | CUDA | 0.554232681 | 0.542450414 | 0.612711476 | 0.542896635 | 0.595650074 |
| chain-n20-reduced_sparse_gpu_cached | 20 | 17711 | CPU | 1.81431629 | 1.67255609 | 1.90167743 | 1.68893975 | 1.82922484 |
| chain-n20-reduced_sparse_gpu_cached | 20 | 17711 | CUDA | 1.74092851 | 1.6926319 | 1.87170513 | 1.73345481 | 1.85927774 |

First/warmup timings, pair gates/order, CPU measurements and CUDA snapshots are
retained in the compressed suite/checkpoints. Failed pilots and the interrupted
earlier campaign remain in their original archives and are not pooled here.
Case RSS includes both CPU references and CUDA execution; it is not separate
per-backend allocation evidence. Device before/after snapshots are not peaks.

## Source fingerprints

These SHA256 values identify the exact report inputs. Each campaign's original
`SHA256SUMS` and complete compressed artifacts remain authoritative for its
full evidence inventory. This report is outside those immutable archives.

| Source | SHA256 |
| --- | --- |
| [p0-scaling-v2-2026-11-26/scaling_results_suite.json](../evidence/p0-scaling-v2-2026-11-26/scaling_results_suite.json) | `cb925fb1b374e29fca26a8ad13f0e8a6a7f93aeaf28dde0e8018f665982a34e0` |
| [p0-scaling-v2-2026-11-26/scaling_repeats.json](../evidence/p0-scaling-v2-2026-11-26/scaling_repeats.json) | `07d7c26c6e9fec4a5f919531ce27619fdd64e2ca4454d23ee394144a39fc076a` |
| [p0-ablation-v2-2026-11-27/ablation_bench_results_suite.json](../evidence/p0-ablation-v2-2026-11-27/ablation_bench_results_suite.json) | `0e1dcfffee1b7405d97d16c7a1b546bfd3c16b500ec3c911ec409cc3b821eb9e` |
| [p0-ablation-v2-2026-11-27/ablation_repeats.json](../evidence/p0-ablation-v2-2026-11-27/ablation_repeats.json) | `e5c4ce3b1f5b5853b859283def92cc9486a3f2afeabfa0d1f9b7d650119cea07` |
| [p0-ablation-cuda-v2-2026-11-27/campaign.tar.gz](../evidence/p0-ablation-cuda-v2-2026-11-27/campaign.tar.gz) | `4fc462c3bb5b2868b8a0266e2b7f6a646ea5b9f5a9e6f624818d626522962739` |
| [p0-ablation-cuda-v2-2026-11-27/ablation_repeats.json](../evidence/p0-ablation-cuda-v2-2026-11-27/ablation_repeats.json) | `10c4148d1ecbb4aac690a1382ab46f8d6f602b7a82e4d05c3b5aea5be4f721e1` |

## Interpretation and rerun policy

Validation overlapped early measurements on a shared workstation; host/GPU
load was not isolated. These are local diagnostic timing distributions, not a
general performance, scaling-law or speedup claim. Small projected/dense or
CPU/CUDA parity and larger same-method sensitivity retain their original
reference limitations; they do not establish independent physical validation.
Full P1 GPU coverage remains open, and CUDA remains experimental.

Formatting additional tables/figures or recomputing statistics from these raw
records requires no simulation rerun. Auditing the retained evidence is distinct
from rerunning the benchmark. A baseline for current code or changed workloads,
hardware/dependencies/timer boundaries needs measurements for the affected scope;
a controlled performance comparison requires appropriate host-load isolation.
Each RC still reruns both P0 suites under
[GOV-004](../../governance/SPEC-GOV-004-benchmarking-plan.md#release-cadence).
Public use separately requires
[performance-claim](../../governance/SPEC-GOV-001-performance-claims.md) and
[disclosure](../../governance/SPEC-GOV-002-disclosure-control.md) review.
