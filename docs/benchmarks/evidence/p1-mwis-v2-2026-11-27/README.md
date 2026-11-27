# P1 MWIS/UDG v2 local evidence — 2026-11-27

Status: Runner implemented; all 40 declared instances executed; original and relocated automated acceptance passed.

The [v2 MWIS/UDG matrix](../../plans/v2.md#p1-mwisudg) completed N=2,4,6,8,10,12,16,20
with five frozen weighted UDG instances per size (seeds 101–105). All **200 measured
AQC calls and 200 measured ILP calls** qualified. Both paths retain first executions,
two warmups and five measured executions per instance: **320 AQC result/manifest sets
and 320 CBC exact-reference records**. Every CBC solve proved optimality and matched
independent exhaustive graph objectives. All five N=20 cases ran successfully, with
D=9240–53760; full dimension 1048576. No final scenario failed, skipped or remained incomplete.

The [audit](audit.json) checks all saved numerical outputs and exact references.
Maximum trajectory/final-probability numerical error is 8.41542979745924e-09 at a frozen 1e-6 gate;
maximum raw-state norm error is 8.676439344768028e-09. Independent DOP853 refinement must agree
within 1e-9. Original [raw repeats](mwis_repeats.json), [coverage](coverage.json),
[source/configuration](campaign.json) and [commands](validation/commands.json) are retained.

| N / seed | D | AQC median (s) | ILP median (s) | Exact weight | Candidate weight | Objective ratio | Optimal-state mass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 / 101 | 3 | 2.03414812 | 0.00198675902 | 1.46136284 | 0 | 0 | 0.0531733206 |
| 2 / 102 | 3 | 2.11385489 | 0.002013233 | 1.41191839 | 0 | 0 | 0.0531583293 |
| 2 / 103 | 4 | 2.09928768 | 0.00187032399 | 2.14278608 | 0 | 0 | 0.00291304368 |
| 2 / 104 | 4 | 2.04452517 | 0.00179482202 | 2.48498867 | 0 | 0 | 0.002922135 |
| 2 / 105 | 3 | 2.03909243 | 0.00196823402 | 1.10300812 | 0 | 0 | 0.0530148231 |
| 4 / 101 | 8 | 2.07785407 | 0.002230154 | 2.82703652 | 0 | 0 | 0.00282523306 |
| 4 / 102 | 12 | 2.04988128 | 0.00201421999 | 4.08128934 | 0 | 0 | 0.000155398368 |
| 4 / 103 | 8 | 2.10275571 | 0.002518925 | 2.42177279 | 0 | 0 | 0.00281374926 |
| 4 / 104 | 10 | 2.04926093 | 0.001945494 | 3.75413729 | 0 | 0 | 0.000156632037 |
| 4 / 105 | 10 | 2.05282904 | 0.00199766702 | 3.72130484 | 0 | 0 | 0.000156269814 |
| 6 / 101 | 22 | 2.11560911 | 0.00243393902 | 5.35758944 | 0 | 0 | 8.40757972e-06 |
| 6 / 102 | 36 | 2.07713991 | 0.00202390601 | 5.16244413 | 0 | 0 | 8.22727252e-06 |
| 6 / 103 | 26 | 2.08818085 | 0.00207505698 | 4.60443782 | 0 | 0 | 8.33255778e-06 |
| 6 / 104 | 22 | 2.10519907 | 0.00205888099 | 3.80896638 | 0 | 0 | 0.000152269042 |
| 6 / 105 | 24 | 2.02352338 | 0.00225698701 | 4.76440973 | 0 | 0 | 8.32799402e-06 |
| 8 / 101 | 44 | 2.03762342 | 0.00273413298 | 5.35758944 | 0 | 0 | 8.17375923e-06 |
| 8 / 102 | 72 | 2.11229094 | 0.00225235202 | 6.62192729 | 0 | 0 | 4.45660071e-07 |
| 8 / 103 | 78 | 2.06311752 | 0.00229905502 | 5.83634523 | 0 | 0 | 4.43183767e-07 |
| 8 / 104 | 80 | 2.10320442 | 0.00254486699 | 6.10834452 | 0 | 0 | 4.43536139e-07 |
| 8 / 105 | 56 | 2.03975526 | 0.00238340601 | 5.08359435 | 0 | 0 | 7.98588717e-06 |
| 10 / 101 | 264 | 2.04991379 | 0.00237802402 | 8.48959156 | 0 | 0 | 2.35011716e-08 |
| 10 / 102 | 120 | 2.21460844 | 0.00347695901 | 6.62192729 | 0 | 0 | 4.29985495e-07 |
| 10 / 103 | 204 | 2.11019352 | 0.00272848801 | 6.9036877 | 0 | 0 | 2.33983242e-08 |
| 10 / 104 | 180 | 2.16799186 | 0.00348095701 | 7.39578126 | 0 | 0 | 2.3762714e-08 |
| 10 / 105 | 96 | 2.10413799 | 0.00387081399 | 5.40243952 | 0 | 0 | 7.81293549e-06 |
| 12 / 101 | 432 | 2.10938865 | 0.00388688 | 8.62711907 | 0 | 0 | 2.29534483e-08 |
| 12 / 102 | 330 | 2.10240508 | 0.00285438501 | 6.65176302 | 0 | 0 | 4.0710854e-07 |
| 12 / 103 | 564 | 2.1873518 | 0.00254402301 | 8.01267725 | 0 | 0 | 1.2425939e-09 |
| 12 / 104 | 352 | 2.1114934 | 0.003160594 | 7.58173895 | 0 | 0 | 2.29137441e-08 |
| 12 / 105 | 200 | 2.1477959 | 0.00373404298 | 6.5889806 | 0 | 0 | 4.2189717e-07 |
| 16 / 101 | 2664 | 2.36662417 | 0.00400815401 | 11.3171304 | 0 | 0 | 6.53619348e-11 |
| 16 / 102 | 3200 | 2.29268172 | 0.00282243799 | 11.5654506 | 0 | 0 | 3.59436195e-12 |
| 16 / 103 | 3120 | 2.37184311 | 0.00335858899 | 10.8930505 | 0 | 0 | 3.62281032e-12 |
| 16 / 104 | 2880 | 2.29257793 | 0.00320398499 | 10.1981999 | 0 | 0 | 6.47990628e-11 |
| 16 / 105 | 816 | 2.13408936 | 0.00421113 | 7.88158412 | 0 | 0 | 2.19124157e-08 |
| 20 / 101 | 27360 | 4.20212913 | 0.00292898901 | 15.0208083 | 0 | 0 | 1.02506703e-14 |
| 20 / 102 | 17480 | 3.35769543 | 0.003839415 | 14.2969291 | 0 | 0 | 1.0291861e-14 |
| 20 / 103 | 53760 | 5.94709306 | 0.00271081901 | 14.3244007 | 0 | 0 | 5.44608812e-16 |
| 20 / 104 | 17280 | 3.373331 | 0.003635701 | 13.2417534 | 0 | 0 | 1.85569437e-13 |
| 20 / 105 | 9240 | 2.82917507 | 0.004535224 | 11.8344311 | 0 | 0 | 3.36530739e-12 |

Each line is a different frozen graph, not a timing replicate of another graph.
The [complete timing table](mwis_aqc_performance.md) gives median/min/max/p25/p75,
counts, quality and numerical gates; matching [JSON](mwis_aqc_performance.json) and
[CSV](mwis_aqc_performance.csv) identify raw membership and path evidence. The
[suite](mwis_aqc_performance_suite.json) has matching [CSV](mwis_aqc_performance_suite.csv)
and [Markdown](mwis_aqc_performance_suite.md). Phase/ID/path, raw times, eligibility,
results/manifests and solver reports are retained for every first/warm/measured call.
No slow valid repeat was excluded and no runtimes were pooled across graph instances.

At this short .15-duration anchor, the most-probable AQC candidate had weight zero in
40/40 instances. These feasible but suboptimal outputs remain valid measurements;
optimal output was not an acceptance requirement. Optimal-state mass sums normalized
probabilities across all graph-feasible states within the frozen 1e-9 objective tolerance
of the proven optimum. Very small masses have an absolute numerical gate, not a
relative-precision guarantee. AQC simulation and exact ILP provide different guarantees;
**no optimization speedup follows from their time ratio or from quantum schedule duration**.

## Frozen configuration and actual result provenance

- Baseline `feature/benchmarking@58dfd10`, initially clean; campaign source tree dirty. Exact [config hash](campaign.json): `9e1995d01461933a75d97086d9f981a3e3bfd643af02cd3c84d3e69951009472`. No commit, merge, release or public disclosure was performed.
- Same Linux/WSL host, CPU model `Intel(R) Core(TM) i7-14700KF`; no affinity, exclusive-load or governor controls. Julia 1.13.4, Python 3.11.15, SDK Python/Julia 1.0.8, SciPy 1.17.1, PuLP 3.3.2, CBC 2.10.3. Initialized CPU doctors, Python/Julia runtime metadata, native CBC command/version/binary hashes and runtime Project/Manifest files remain retained. CPU-only execution; no CUDA acceptance is claimed by this campaign.
- Generator density parameter .8, Rb=1 um, weights [1,1.5], C6=1 rad*um^6/us. Actual coordinates, node iteration order, edges, weights, canonical graph hash, measured degree and edge density are frozen; the generator parameter is not the measured edge density.
- Original sin-squared omega_max=2*pi rad/us, delta ramps from -2*omega_max to weight*2*pi, duration .15 us; complex128 all-ground state reset before each call. Atom i is bit i (LSB); persisted bitstring labels are in atom order. The SDK basis is compared to a separately enumerated graph-feasible basis; graph edges must match actual strict-radius blockade edges.
- AQC: adaptive Tsit5, reltol=1e-8, abstol=1e-10, dt=None, 101 identical explicit times, pop0 and ground-plus Pauli Z on atom 0. SDK final readout is normalized; raw norm is separately recovered through Z0+2n0 and checked at 1e-6, so normalization cannot hide raw-state norm drift.
- The independent reference builds the sparse Hamiltonian directly from graph-feasible bitstrings and explicit finite interactions/time-dependent drives, using SciPy DOP853 at rtol=1e-12/atol=1e-14. A second 1e-10/1e-12 integration checks stability at every instance. SDK trajectory, Z0, final probability and raw-norm gates apply to every saved call; no Julia Hamiltonian/pulse compiler/solver is reused by this reference.
- Small N<=8 full 2^N enumeration independently checks the recursive feasible basis. Exhaustive feasible-state objectives verify CBC at all target sizes. These verify the executed reduced model and combinatorial mapping, not the physical blockade approximation or calibration.
- The source-project adapter adds `prepare_simulation()`, actual-result `solve_result()` (pop0 by default) and persisted normalized-readout `decode_result()`. Legacy `solve_full()` preserves raw |psi|^2 tuple semantics; initial smoke/correctness/scaling IDs and default three-tier execution are unchanged. Performance must run separately in its own new output directory.

## Timers, exact termination and resources

Each graph/path has its own fresh supervised process. AQC first execution follows
initialized CPU doctor and setup; it is not process-cold initialization. Subsequent calls
reuse the simulation/JIT context but reset the recorded all-ground input. SDK operator
and pulse construction remains inside each `Simulation.run`; pop0/Z0 collection and
manifest creation are also included. Graph generation, adapter/setup/state reset,
independent references, checks/decoding and result/report writes are outside the primary
timer. First solve, two actual-scenario warmups and five measurements remain separate.

Each ILP call rebuilds a fresh binary model and disables CBC warm start. Model
construction is timed separately. `model.solve(CBC)` timing includes PuLP model-file
writes, native subprocess startup/IPC, CBC solve and solution parsing. Verification,
objective computation and reference-report writes are outside it. CBC uses one thread,
seed 1234, zero relative/absolute MIP gaps and a 30-second elapsed-time limit. Actual
native flags and output remain in every solver log. Generation/setup/reference and
per-call model, post-processing and serialization costs retain their actual counts;
single setup measurements are not repeated-runtime distributions.

PuLP `problem_status=Optimal` can describe a time-limited integer incumbent. Exact
reference eligibility therefore requires optimal problem **and** optimal solution
status, binary feasibility and exhaustive-objective agreement. Incumbents, exposed
printed bounds, termination, native logs and missing-data reasons survive nonoptimal
termination. Without a proven optimum exact gap/ratio/optimal-state mass remain null;
AQC results are preserved. CBC timeout elapsed time never becomes time to a proven optimum.

All Julia/BLAS/OpenMP/MKL thread requests are one; effective Julia/BLAS counts are
audited. Limits are 600 seconds per path and 4096 MiB sampled worker RSS. AQC preflight
reserves 2 GiB for runtime/JIT plus sparse maps, workspaces and reference histories.
Worker baseline and HWM are normalized from Linux /proc kB to bytes; 50ms polling is
not a hard allocation cap. AQC lifetime memory includes initialization, references and
serialization. ILP Python-worker memory excludes native CBC subprocess memory;
**native CBC peak is unavailable** with an explicit reason. Process groups are terminated
on limit/interruption and checkpoints/stopped timers are retained.

This is a shared workstation. Documentation/pilot archival work and other host users
can overlap; no CPU-load isolation or current-release controlled performance baseline
is asserted. Historical single-run/raw-history/default-grid tier timings, different
Julia/source environments and this explicit-grid observable workload cannot be pooled.

## Tests, failures and evidence review

- [17 final MWIS tests](validation/mwis-tests-final.log), no skips: legacy adapter/tier/batch compatibility, real result/manifest round trip, independent dense-vs-sparse reference, all-optimum probability/feasibility, CBC problem-versus-solution optimality, timer statistics, timeout/memory retention, NaN handling and saved-manifest tampering detection.
- [49 backend/golden/artifact regressions](validation/backend-contract-regression.log), no skips: Python/Julia golden checks, solver configuration, serialization, observables/invariants and benchmark row/suite/failure contracts.
- [Original/relocated audit](audit.json), independent reference recomputation, [additional report/phase/memory checks](validation/report-checks.json), retained source comparison, complete checksum verification, [five documentation tests](validation/documentation-tests.log), [documentation validation](validation/documentation.log) and exact preservation of four historical V1 chapters.
- [Original short pilots](pilots.tar.gz) and [diagnostic history](validation/diagnostic-history.json) remain separate. Pilot 03 validated the largest case at N=20 D=53760 and audited six AQC plus six ILP records; one-warmup/one-repeat rows correctly remained incomplete.
- [Initial regression failure](validation/mwis-tests-initial-failure.log) exposed that no-observable execution returns a Julia ODESolution rather than a SimulationResult. The compatible raw tuple path was restored before the final campaign; the new result outlet explicitly collects observables. The original pilot snapshots retain the intermediate source. Failed tests/pilot timings are not filtered or pooled into final measurements.

This is software testing and independent numerical/combinatorial verification of the
executed reduced model. It does not establish scientific validity, full-space equivalence,
distribution-wide optimization quality, general quantum advantage, CUDA, clean-wheel/
container support, recurring RC acceptance or independent public-performance approval.
Broader/longer schedules and structured graph families remain separate work.

## Replay and backend-free saved-evidence audit

[Commands](validation/commands.json) and [environment](validation/environment.sh) retain
the exact source/editable setup and writable depot overlay. The existing isolated Julia
environment is a replay input, not a clean-install support claim. From `sagittarius_py`:

```bash
uv run --no-sync python tests/test_performance/benchmark_mwis_aqc.py --tier performance \
  --sizes 2 4 6 8 10 12 16 20 --seeds 101 102 103 104 105 \
  --warmups 2 --repeat-count 5 --timeout-seconds 600 --memory-limit-mb 4096 \
  --ilp-time-limit 30 --numerical-atol 1e-6 \
  --output-dir benchmark-output/p1-mwis-v2-2026-11-27
.venv/bin/python ../scripts/audit_mwis_campaign.py benchmark-output/p1-mwis-v2-2026-11-27
```

The complete [campaign archive](campaign.tar.gz) retains all raw results/manifests,
CBC logs/reference reports/model LPs, numerical arrays, path configs/checkpoints,
source snapshots, Python lockfile, Julia runtime projects, companions and an internal
SHA256 inventory. Outer [checksums](SHA256SUMS) cover compressed originals, visible
summaries, validation and source snapshots. Absolute links relocate by campaign prefix;
no Julia/CBC execution is needed for saved-evidence review. From the repository root:

```bash
mkdir -p /tmp/sagittarius-p1-mwis-evidence
tar -xzf docs/benchmarks/evidence/p1-mwis-v2-2026-11-27/campaign.tar.gz \
  -C /tmp/sagittarius-p1-mwis-evidence
(cd /tmp/sagittarius-p1-mwis-evidence/campaign && sha256sum -c SHA256SUMS)
sagittarius_py/.venv/bin/python scripts/audit_mwis_campaign.py \
  /tmp/sagittarius-p1-mwis-evidence/campaign
python3 docs/benchmarks/evidence/p1-mwis-v2-2026-11-27/validation/report-checks.py \
  /tmp/sagittarius-p1-mwis-evidence/campaign
```
