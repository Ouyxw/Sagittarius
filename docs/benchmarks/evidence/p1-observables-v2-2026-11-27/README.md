# P1 observables v2 local evidence — 2026-11-27

Status: Runner implemented; all 64 rows executed; original and relocated automated acceptance passed.

The [declared observable matrix](../../plans/v2.md#p1-observables) completes
**52 cost configurations and 12 correctness fixtures**. All **260 measured
SDK calls** qualify after separate first execution and two warmups per cost
configuration. All **476 saved result/manifest pairs** are audited: 416 cost
calls and 60 correctness calls (30 deterministic, 30 seeded stochastic).
No row failed, skipped or remained incomplete. Reduced N=20 has D=17711;
full dimension is 1048576, not the executed state size.

The [audit](audit.json) recomputes every saved output against independent
references and verifies type/parameter/order, normalized grids, actual solver
settings, raw MCWF sample means, bounds, measured statistics, companions, hashes
and relocated links. Maximum deterministic observable error is
7.3852035598065413e-12 (gate 1e-8); maximum independent
reference state-stability error is 4.2460065325116453e-13
(gate 1e-10). It checks 120 named cross-order pairs and
two retained empty-observable state-history controls. MCWF has an explicit
simultaneous stochastic bound, not the deterministic 1e-8 claim.

## Matrix and runtime results

Per N=4,8,12,16,20, the reduced chain anchor has mixed count4/grid101/original;
one-axis scans vary counts 1/16/64, grids21/501 and reverse/permuted order.
Ten N=4 count-one single-type runs are separate. Combined cases are
N=4/count64/grid501/permuted and N=20/count16/grid501/reverse. This is not a
Cartesian product. Counts16/64 repeat a ten-type catalog under unique names,
with 6/54 duplicate physical declarations, labeled duplicate-output collection
workloads that add no physical information. Permutation seed is 1234.

The [complete table](observable_performance.md), [JSON](observable_performance.json)
and [CSV](observable_performance.csv) report actual N/D, collection/count/order,
output count and policy, gates, all five runtime statistics, counts and memory.
The [suite](observable_performance_suite.json) has matching [CSV](observable_performance_suite.csv)
and [Markdown](observable_performance_suite.md); [raw records](observable_repeats.json)
retain every call and its actual order/seed/result links. Correctness fixture rows
use a canonical original declaration list but execute all three recorded orders;
they have unavailable performance distributions with a reason.

| Cost configuration | D | Eligible | Median SDK seconds | Maximum error |
| --- | ---: | ---: | ---: | ---: |
| performance-n4-reduced-evolving-mixed-c4-g101-original | 8 | 5 | 0.150834399 | 4.2432724e-13 |
| performance-n4-reduced-evolving-mixed-c1-g101-original | 8 | 5 | 0.148559517 | 1.37362344e-13 |
| performance-n4-reduced-evolving-mixed-c16-g101-original | 8 | 5 | 0.143169542 | 4.2432724e-13 |
| performance-n4-reduced-evolving-mixed-c64-g101-original | 8 | 5 | 0.161582877 | 4.2432724e-13 |
| performance-n4-reduced-evolving-mixed-c4-g21-original | 8 | 5 | 0.151922195 | 4.24216218e-13 |
| performance-n4-reduced-evolving-mixed-c4-g501-original | 8 | 5 | 0.140935613 | 4.70179451e-13 |
| performance-n4-reduced-evolving-mixed-c4-g101-reverse | 8 | 5 | 0.155909745 | 4.2432724e-13 |
| performance-n4-reduced-evolving-mixed-c4-g101-permuted | 8 | 5 | 0.167398006 | 4.2432724e-13 |
| performance-n8-reduced-evolving-mixed-c4-g101-original | 55 | 5 | 0.165018962 | 4.54747351e-13 |
| performance-n8-reduced-evolving-mixed-c1-g101-original | 55 | 5 | 0.156910887 | 7.48290319e-14 |
| performance-n8-reduced-evolving-mixed-c16-g101-original | 55 | 5 | 0.199041354 | 5.28688204e-13 |
| performance-n8-reduced-evolving-mixed-c64-g101-original | 55 | 5 | 0.163645212 | 5.28688204e-13 |
| performance-n8-reduced-evolving-mixed-c4-g21-original | 55 | 5 | 0.140659134 | 4.06563672e-13 |
| performance-n8-reduced-evolving-mixed-c4-g501-original | 55 | 5 | 0.15568949 | 5.28910249e-13 |
| performance-n8-reduced-evolving-mixed-c4-g101-reverse | 55 | 5 | 0.170689734 | 4.54747351e-13 |
| performance-n8-reduced-evolving-mixed-c4-g101-permuted | 55 | 5 | 0.140671779 | 4.54747351e-13 |
| performance-n12-reduced-evolving-mixed-c4-g101-original | 377 | 5 | 0.206242236 | 5.10258502e-13 |
| performance-n12-reduced-evolving-mixed-c1-g101-original | 377 | 5 | 0.237836489 | 5.64270852e-14 |
| performance-n12-reduced-evolving-mixed-c16-g101-original | 377 | 5 | 0.232880974 | 7.67386155e-13 |
| performance-n12-reduced-evolving-mixed-c64-g101-original | 377 | 5 | 0.261057309 | 7.67386155e-13 |
| performance-n12-reduced-evolving-mixed-c4-g21-original | 377 | 5 | 0.182876978 | 4.92272889e-13 |
| performance-n12-reduced-evolving-mixed-c4-g501-original | 377 | 5 | 0.199064456 | 5.60884672e-13 |
| performance-n12-reduced-evolving-mixed-c4-g101-reverse | 377 | 5 | 0.218651379 | 5.10258502e-13 |
| performance-n12-reduced-evolving-mixed-c4-g101-permuted | 377 | 5 | 0.283711333 | 5.10258502e-13 |
| performance-n16-reduced-evolving-mixed-c4-g101-original | 2584 | 5 | 0.611403508 | 1.23012711e-12 |
| performance-n16-reduced-evolving-mixed-c1-g101-original | 2584 | 5 | 0.603132168 | 8.33499936e-14 |
| performance-n16-reduced-evolving-mixed-c16-g101-original | 2584 | 5 | 0.69903259 | 2.35900188e-12 |
| performance-n16-reduced-evolving-mixed-c64-g101-original | 2584 | 5 | 1.06764105 | 2.35900188e-12 |
| performance-n16-reduced-evolving-mixed-c4-g21-original | 2584 | 5 | 0.574065162 | 1.0742518e-12 |
| performance-n16-reduced-evolving-mixed-c4-g501-original | 2584 | 5 | 0.851293743 | 1.31361588e-12 |
| performance-n16-reduced-evolving-mixed-c4-g101-reverse | 2584 | 5 | 0.66707498 | 1.23012711e-12 |
| performance-n16-reduced-evolving-mixed-c4-g101-permuted | 2584 | 5 | 0.613725028 | 1.23012711e-12 |
| performance-n20-reduced-evolving-mixed-c4-g101-original | 17711 | 5 | 4.08827927 | 3.02025072e-12 |
| performance-n20-reduced-evolving-mixed-c1-g101-original | 17711 | 5 | 3.80129702 | 1.60454983e-13 |
| performance-n20-reduced-evolving-mixed-c16-g101-original | 17711 | 5 | 4.81079014 | 6.59028387e-12 |
| performance-n20-reduced-evolving-mixed-c64-g101-original | 17711 | 5 | 7.10750379 | 6.59028387e-12 |
| performance-n20-reduced-evolving-mixed-c4-g21-original | 17711 | 5 | 3.7889956 | 2.97717406e-12 |
| performance-n20-reduced-evolving-mixed-c4-g501-original | 17711 | 5 | 5.36306303 | 3.32400774e-12 |
| performance-n20-reduced-evolving-mixed-c4-g101-reverse | 17711 | 5 | 4.03581995 | 3.02025072e-12 |
| performance-n20-reduced-evolving-mixed-c4-g101-permuted | 17711 | 5 | 4.28226557 | 3.02025072e-12 |
| performance-n4-reduced-evolving-rydberg_population-c1-g101-original | 8 | 5 | 0.148809613 | 1.37362344e-13 |
| performance-n4-reduced-evolving-total_rydberg_population-c1-g101-original | 8 | 5 | 0.137379508 | 4.2432724e-13 |
| performance-n4-reduced-evolving-pair_correlation-c1-g101-original | 8 | 5 | 0.14527354 | 5.63576963e-14 |
| performance-n4-reduced-evolving-connected_pair_correlation-c1-g101-original | 8 | 5 | 0.144714401 | 1.29132816e-14 |
| performance-n4-reduced-evolving-blockade_violation-c1-g101-original | 8 | 5 | 0.156620538 | 5.63576963e-14 |
| performance-n4-reduced-evolving-bitstring_probability-c1-g101-original | 8 | 5 | 0.203178646 | 5.63576963e-14 |
| performance-n4-reduced-evolving-mwis_cost-c1-g101-original | 8 | 5 | 0.137853699 | 2.78888024e-13 |
| performance-n4-reduced-evolving-pauli_z-c1-g101-original | 8 | 5 | 0.165481403 | 3.59268171e-13 |
| performance-n4-reduced-evolving-pauli_zz-c1-g101-original | 8 | 5 | 0.185287319 | 4.08673095e-13 |
| performance-n4-reduced-evolving-parity-c1-g101-original | 8 | 5 | 0.29152834 | 3.74311693e-13 |
| performance-n4-reduced-evolving-mixed-c64-g501-permuted | 8 | 5 | 0.326257737 | 4.70179451e-13 |
| performance-n20-reduced-evolving-mixed-c16-g501-reverse | 17711 | 5 | 8.38432799 | 7.38520356e-12 |

Each cost configuration resets the same state and retains first execution,
two warmups and five independent measurements. Median/min/max/p25/p75 use
eligible measured calls only, linear Hyndman-Fan type-7 quantiles and exact
member IDs/requested/completed/eligible counts. No slow valid repeat is removed,
and different N/D, declarations, grids or orders are never pooled.

## Independent references and state-path scope

- Cost/evolving anchor: chain spacing4 um, C6=100 rad*um^6/us, Rb=4.4 um, omega=2*pi rad/us, delta=.3 rad/us, T=.15 us, complex128 all-ground state. Tsit5 is adaptive, dt=None, reltol=1e-11/abstol=1e-13: a declared suite accuracy override. Grids contain endpoints and 21/101/501 explicit times.
- The ten supported diagonal types are population, total population, pair, connected pair, blockade violation, bitstring probability, MWIS reward-minus-penalty, ground-plus Pauli Z/ZZ and parity. Every support/edge/weight/penalty/convention is frozen in [campaign.json](campaign.json). Python indices are zero-based, Julia constructors one-based; basis integers ascend and atom i is bit i (LSB).
- Independent NumPy occupation/probability formulas include connected subtraction and MWIS penalty4.25, weights1+.125*i, edges[[0,1],[0,N-1]]. An independently assembled sparse projected H is evolved by SciPy sparse exponentiation; dense eigendecomposition at N<=8 and sparse DOP853 1e-12/1e-14 above N=8 verify state stability at 1e-10 before SDK measurement. Only reference values/final probabilities/basis are retained; independent state generation is outside primary timing and can be replayed without Julia.
- Twelve N=3 full/reduced fixtures cover static ground and two-excitation bitstrings, a nontrivial normalized distribution sqrt((k+1)/sum(k+1))*exp(.3i*k), a small evolving state, Lindblad and MCWF. Each tests original/reverse/permuted declarations, metadata, shared payload and artifact round trips. Static/decay H is zero; gamma=.4/us, T=.5us, with atoms0/2 initially excited. Analytic independent product-decay probabilities supply the noise reference.
- MCWF retains 500 trajectories for each seed20260811–20260815 in each order and basis (30 calls). Its callbacks evaluate each normalized trajectory then average. The connected covariance is zero for these bitstring decay trajectories; it is not formed by subtracting ensemble means. Other types use exact reachable bitstring ranges and simultaneous Hoeffding absolute bounds at alpha=1e-6 over 10 types,21 times,5 seeds,3 orders,2 bases. Raw trajectory shapes/order and sample-mean/SDK-average agreement <=1e-12 are separate gates. This is a bounded stochastic correctness check, not a trajectory convergence/cost campaign or relative-precision guarantee.

## Timers, empty output and resources

The primary workload is one `Simulation.run`, including validation,
operator/observable construction, collection and manifest creation. Reset,
reference generation/stability, value/order checks, reloads and result/report
writes are outside. Doctor/setup/reference and per-call serialization/validation
times remain distinct. First solve follows initialized doctor and reference/setup;
it is not process-cold initialization. No isolated integration/collection kernel,
evaluation-only workload or incremental-observable overhead is reported.

Two small empty-observable calls retain actual ODE history arrays. Empty SDK
results expose full state history; observable SDK results expose named series
and supported final readout. Their different exposed output contracts cannot
establish a matched overhead baseline. The implementation does not claim internal
ODE history is eliminated by selecting observables. Raw MCWF samples are retained
only for correctness and remain a separate storage policy from cost runs.

Each cost configuration or correctness fixture has a fresh supervised Linux
worker, default 900s timeout and 4096MiB sampled RSS budget. Preflight includes
2GiB Julia/JIT reserve, mappings/workspaces, reference histories and outputs.
Process-lifetime HWM includes doctor, reference and writes; baseline is after
initialized doctor. Units and raw max_rss remain explicit; 50ms RSS sampling is
not a hard address-space cap. Julia/BLAS/OpenMP/MKL requests are one, with effective
thread/provider counts and runtime Project/Manifest hashes retained.

This is one shared Linux/WSL workstation, with no affinity or exclusive-load
controls. Documentation/archival activity can overlap. The existing source/editable
Julia environment and writable depot overlay are replay inputs, not clean-install
or released-wheel qualification. Project/library schemas and SDK/Julia solver/
observable implementations are unchanged; API/physics docs clarify existing MCWF
nonlinear semantics. Physical/model/blockade validation, off-diagonal/coherence/
entanglement, CUDA, full Python-suite execution, expanded open-system cost and
convergence, recurring RC and independent public-use approval remain separate.

## Source, checks and replay

Baseline `feature/benchmarking@bb8725f`, initially clean; measured source is dirty
and frozen by [source hashes](source-index.json). Config SHA256:
`8103db53dc73a3056243253ceec656cf2eebc0f50fbc145a0835a2891953a2c7`. CPU model: `Intel(R) Core(TM) i7-14700KF`.
All frozen source/configuration files match handoff; runtime project identity is
constant. No commit, merge or publication was requested or made.

[Commands](validation/commands.json) and [environment](validation/environment.sh)
retain the exact setup. [23 backend-free tests](validation/unit-tests.log),
[6 marked backend/golden tests](validation/backend-tests.log),
[32 observable/serialization/artifact regressions](validation/artifact-tests.log),
[10 solver tests](validation/solver-tests.log) and [5 documentation tests](validation/documentation-tests-final.log)
passed. The marked command deselects unmarked tests, which are run separately;
no skips are treated as backend evidence. The real cost integration audits eight
saved results and rejects CSV/Markdown/manifest/order/source tampering without
initializing Julia. Original/relocated audits, checksums, [source/phase checks](validation/report-checks.json),
[documentation validation](validation/documentation.log) and exact historical
[V1 preservation](validation/v1-preservation.json) are retained.

[Both original pilots](pilots.tar.gz) and their [history](validation/diagnostic-history.json)
remain separate: all selected correctness controls pass, while zero-warmup/one-repeat
cost rows correctly remain incomplete despite small numerical errors. Pilot times
are not pooled with final measurements.

The [complete archive](campaign.tar.gz) includes every raw result/manifest,
MCWF trajectory sample, empty-history array, reference, config/checkpoint/log,
frozen source/lockfile, Julia runtime project, companion and internal checksum
inventory. [Outer checksums](SHA256SUMS) cover the archive, pilots, visible summaries
and validation. From repository root:

```bash
mkdir -p /tmp/sagittarius-p1-observables-evidence
tar -xzf docs/benchmarks/evidence/p1-observables-v2-2026-11-27/campaign.tar.gz \
  -C /tmp/sagittarius-p1-observables-evidence
(cd /tmp/sagittarius-p1-observables-evidence/campaign && sha256sum -c SHA256SUMS)
sagittarius_py/.venv/bin/python scripts/audit_observable_campaign.py \
  /tmp/sagittarius-p1-observables-evidence/campaign
```

Use a new output directory when replaying `campaign.json`'s measurement command.
`--tier correctness`/`performance` and repeated `--scenario` select frozen subsets;
`--allow-partial` permits auditing those subsets without full-matrix claims.
Absolute artifact paths relocate by the recorded campaign prefix; saved-evidence
review recomputes independent references and initializes no Julia backend.
