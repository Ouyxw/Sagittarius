# P1 solver sensitivity v2 local evidence — 2026-11-27

Status: Runner implemented; all 39 configurations executed; original and relocated saved-output audit and bounded characterization acceptance passed.

The [v2 solver matrix](../../plans/v2.md#p1-solver) has 13 configurations each for
analytic one-atom Rabi, the existing three-atom addressed chain and an explicit
three-atom linear drive/detuning ramp. Both adaptive methods scan paired
1e-6/1e-8, 1e-8/1e-10 and 1e-10/1e-12 tolerances at 101 times. RK4 scans
T/100, T/200 and T/400. Tsit5 anchor grid scans use 21/101/501 times; combined
controls are Vern9/tight/501 and RK4/T400/21. This is not a Cartesian product.

All **312 SDK calls** retain results/manifests, raw timing and numerical gates:
first execution, two warmups and five measured calls per configuration.
**38/39 configurations and 190/195 measured calls meet the frozen
1e-6 target.** The coarse ramp RK4 T/100 row is fully measured but fails accuracy;
all five measured times remain ineligible diagnostics. Maximum error across all
calls is 1.6501632661980459e-06, maximum raw norm drift 3.7427904064912809e-07.
No row was filtered and no accuracy target was relaxed. Output-grid refinement
is distinct from integration-step refinement; no strictly monotonic error/runtime
trend is required.

The [saved-output audit](audit.json) recomputes every result's observable,
normalized final-probability and raw-state norm errors, effective solver/grid,
statistics/member IDs, complete companions, source/runtime hashes and relocated
links. [Characterization acceptance](acceptance.json) applies the explicit
[review policy](validation/acceptance-policy.json) with nine accurate tight/fine
controls and no missing calls or backend/reference/resource/write failures.
This policy operationalizes plan v2's under-resolution rule. Its [freeze record](validation/policy-freeze.json)
is after the first nine Rabi configurations and before ramp measurement; the
workload, numerical thresholds and measured settings are unchanged.
`full_v2_matrix_passed` remains **false**; local characterization acceptance does
not promote the under-resolved row into a successful accuracy/performance claim.

## Error versus runtime

The [complete table](solver_sensitivity.md), [JSON](solver_sensitivity.json) and
[CSV](solver_sensitivity.csv) retain all five timing statistics, eligible counts,
method, stepping, tolerances/dt, actual D, output count, error/gate and memory.
The [suite](solver_sensitivity_suite.json) has matching [CSV](solver_sensitivity_suite.csv)
and [Markdown](solver_sensitivity_suite.md); [raw records](solver_repeats.json)
identify every first/warm/measured call. No different configurations are pooled.

| Configuration | D | Eligible | Median SDK seconds | Maximum error | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| rabi-tsit5-tol6-g101 | 2 | 5 | 2.11158903 | 9.09800544e-08 | passed |
| rabi-tsit5-tol8-g101 | 2 | 5 | 2.11989933 | 8.81051676e-10 | passed |
| rabi-tsit5-tol10-g101 | 2 | 5 | 2.07390756 | 1.05079834e-11 | passed |
| rabi-vern9-tol6-g101 | 2 | 5 | 2.22355285 | 2.49608334e-10 | passed |
| rabi-vern9-tol8-g101 | 2 | 5 | 2.26717572 | 7.95619126e-12 | passed |
| rabi-vern9-tol10-g101 | 2 | 5 | 2.19508197 | 5.98632255e-13 | passed |
| rabi-rk4-s100-g101 | 2 | 5 | 1.93546463 | 3.9275274e-08 | passed |
| rabi-rk4-s200-g101 | 2 | 5 | 1.93229957 | 2.44825471e-09 | passed |
| rabi-rk4-s400-g101 | 2 | 5 | 1.9944952 | 1.52800217e-10 | passed |
| rabi-tsit5-tol8-g21 | 2 | 5 | 2.14378693 | 7.2261036e-10 | passed |
| rabi-tsit5-tol8-g501 | 2 | 5 | 2.1335172 | 9.8807057e-10 | passed |
| rabi-vern9-tol10-g501 | 2 | 5 | 2.27780955 | 1.08696385e-12 | passed |
| rabi-rk4-s400-g21 | 2 | 5 | 1.95573296 | 1.51866353e-10 | passed |
| addressed-tsit5-tol6-g101 | 5 | 5 | 2.07117176 | 1.16329169e-12 | passed |
| addressed-tsit5-tol8-g101 | 5 | 5 | 2.07325973 | 2.34257058e-14 | passed |
| addressed-tsit5-tol10-g101 | 5 | 5 | 2.07711134 | 2.33146835e-15 | passed |
| addressed-vern9-tol6-g101 | 5 | 5 | 2.20420209 | 5.44009282e-15 | passed |
| addressed-vern9-tol8-g101 | 5 | 5 | 2.26796249 | 2.33146835e-15 | passed |
| addressed-vern9-tol10-g101 | 5 | 5 | 2.26229588 | 2.88657986e-15 | passed |
| addressed-rk4-s100-g101 | 5 | 5 | 1.93154353 | 1.04360964e-14 | passed |
| addressed-rk4-s200-g101 | 5 | 5 | 1.9383017 | 2.77555756e-15 | passed |
| addressed-rk4-s400-g101 | 5 | 5 | 1.95151439 | 1.77635684e-15 | passed |
| addressed-tsit5-tol8-g21 | 5 | 5 | 2.08485134 | 2.34257058e-14 | passed |
| addressed-tsit5-tol8-g501 | 5 | 5 | 2.10937916 | 2.49800181e-14 | passed |
| addressed-vern9-tol10-g501 | 5 | 5 | 2.17881235 | 3.10862447e-15 | passed |
| addressed-rk4-s400-g21 | 5 | 5 | 1.89968225 | 1.55431223e-15 | passed |
| ramp-tsit5-tol6-g101 | 5 | 5 | 2.08615077 | 1.52409026e-07 | passed |
| ramp-tsit5-tol8-g101 | 5 | 5 | 2.02159387 | 8.25167434e-10 | passed |
| ramp-tsit5-tol10-g101 | 5 | 5 | 2.06556635 | 8.0997431e-12 | passed |
| ramp-vern9-tol6-g101 | 5 | 5 | 2.23412299 | 1.96899818e-08 | passed |
| ramp-vern9-tol8-g101 | 5 | 5 | 2.16425017 | 1.65959468e-10 | passed |
| ramp-vern9-tol10-g101 | 5 | 5 | 2.13952464 | 1.07169829e-12 | passed |
| ramp-rk4-s100-g101 | 5 | 0 | unavailable | 1.65016327e-06 | failed |
| ramp-rk4-s200-g101 | 5 | 5 | 1.93187643 | 1.01141508e-07 | passed |
| ramp-rk4-s400-g101 | 5 | 5 | 1.95854439 | 6.25317448e-09 | passed |
| ramp-tsit5-tol8-g21 | 5 | 5 | 2.19989538 | 5.8656896e-10 | passed |
| ramp-tsit5-tol8-g501 | 5 | 5 | 2.16161159 | 8.77308115e-10 | passed |
| ramp-vern9-tol10-g501 | 5 | 5 | 2.33724438 | 1.11788356e-12 | passed |
| ramp-rk4-s400-g21 | 5 | 5 | 1.95288285 | 6.25317448e-09 | passed |

The coarse ramp row's raw runtime remains in JSON; its accuracy-qualified median
is unavailable because no measured call passed. First/warm calls are separately
labeled and never included in measured distributions. Statistics use linear
Hyndman-Fan type-7 quantiles and retain exact member IDs and requested/completed/
eligible counts. Slow valid calls remain eligible.

## Physics and independent references

- Rabi: N=1, C6=0, Rb=0, omega=2*pi, delta=0, T=1; analytic sin-squared checked against eigendecomposition.
- Addressed chain: N=3, spacing=.5, C6=10, Rb=.6, omega=[.2,.3,.25], delta=[-.1,0,.1], T=.3; D=5. Independent ascending-bit basis and projected matrix, eigendecomposition and SciPy matrix exponential checks.
- Ramp: N=3, spacing=4, C6=100, Rb=4.4, T=1; omega [0,0,0] to [4*pi,3*pi,2*pi], delta [-4,-3,-2] to [4,3,2]; D=5. Independent SciPy DOP853 at 1e-12/1e-14, cross-checked with RK45 at the same tighter tolerances. Reference stability gate is 1e-9 and precedes measurement.
- Coordinates, full pulse parameters, all-ground initial state, atom-i/LSB basis order, solver/grid and units are frozen in [campaign.json](campaign.json). Lengths are um, times us, angular frequencies rad/us, C6 rad*um^6/us. Precision is complex128, with no random seed because evolution is deterministic.
- `pop0` plus ground-plus Pauli `z0` checks raw norm via z0+2*pop0, preventing normalized final probabilities from hiding drift. Observable, final-probability and raw norm gates are each 1e-6. These verify the executed reduced model, not the physical blockade approximation or calibration.

## Timing, resources and provenance

The timer surrounds only `Simulation.run`, including validation, pulse/operator
construction, observable collection and manifest creation. State reset, independent
references, checks and serialization are outside. Doctor/setup/reference times,
first execution and per-call validation/serialization times remain separate.
First execution follows initialized doctor and setup; it is not process-cold.
No isolated Julia integration-kernel cost or general method speedup is claimed.

Every configuration has its own supervised Linux process. Limits are 600 seconds
and 4096 MiB sampled RSS; construction/reference/output estimates include a 2 GiB
Julia/JIT reserve. Memory is process-lifetime HWM including initialization,
references and writes, with baseline after doctor. Units/source max_rss and /proc
byte normalization remain explicit. RSS sampled every 50 ms is not a hard cap.
Requested Julia/BLAS/OpenMP/MKL threads are one; effective counts, Python BLAS
context and Julia Project/Manifest hashes are retained for each worker.

Baseline is `feature/benchmarking@781a09e`, initially clean; measured source is
dirty and frozen by [source hashes](source-index.json). Configuration SHA256 is
`2932fec7d96fae6b603a6cecff04024a1c178f38b728d9bdfc0e18dee1a2b43d`. CPU model is `Intel(R) Core(TM) i7-14700KF`.
This is a shared Linux/WSL workstation with no affinity or exclusive-load controls;
documentation and archival activity may overlap. The source/editable isolated
Julia environment and writable depot overlay are replay inputs, not clean-install
or current-release qualification. SDK/Julia physics/solver implementation and
artifact schema names are unchanged. No commit, merge or publication was made.

## Validation and retained failures

- [17 backend-free contract tests](validation/unit-tests.log), [28 backend/golden regressions](validation/backend-contract-regression.log), and [21 artifact/documentation regressions](validation/artifact-documentation-tests.log) passed with no skips. The 17-test command deselects the separately executed real-backend integration test. Effective solver configuration, original path checks, result serialization and Python/Julia golden tests remain covered.
- [Deterministic timer regression](validation/timer-boundary-test.log) passed: simulated slow serialization is excluded from all three legacy solver-method timings.
- Real ramp integration verifies eight saved outputs, isolated audit without Julia initialization, and rejection of corrupted CSV, Markdown, manifest, reference and source snapshots.
- [Original/relocated audit and review](validation/relocated-acceptance.json), complete internal checksum verification, source comparison, [V1 preservation](validation/v1-preservation.json), [documentation validation](validation/documentation.log) and final diff checks are retained.
- [Original pilots](pilots.tar.gz) and [diagnostic history](validation/diagnostic-history.json) retain the first failed benchmark declarations/full-space basis handling and the second short run. Short runs correctly remain incomplete; their times are not pooled with final evidence. The final coarse ramp numerical failure remains inside the complete campaign as required.

This is software testing and independent numerical verification of three bounded
models. Scientific/model/blockade validation, stiff-system and broader scenario
coverage, CUDA, full Python-suite execution, clean-wheel/container support,
recurring RC and independent public-performance approval remain outside this slice.

## Replay and relocated audit

[Commands](validation/commands.json) and [environment](validation/environment.sh)
retain the exact source/editable setup. From `sagittarius_py`, run the command
recorded in `campaign.json` in a new output directory. The sensitivity CLI exits
nonzero when any accuracy gate fails; a nonzero exit does not erase the measured
under-resolved case. The default legacy correctness tier/stems remain compatible.

The [complete campaign archive](campaign.tar.gz) includes every saved result,
manifest, reference, config/checkpoint, log, frozen source, Python lockfile, Julia
runtime project, companion and internal checksum inventory. [Outer checksums](SHA256SUMS)
cover the archive, pilots, visible reports and validation. From repository root:

```bash
mkdir -p /tmp/sagittarius-p1-solver-evidence
tar -xzf docs/benchmarks/evidence/p1-solver-v2-2026-11-27/campaign.tar.gz \
  -C /tmp/sagittarius-p1-solver-evidence
(cd /tmp/sagittarius-p1-solver-evidence/campaign && sha256sum -c SHA256SUMS)
sagittarius_py/.venv/bin/python scripts/audit_solver_campaign.py \
  /tmp/sagittarius-p1-solver-evidence/campaign --allow-partial
sagittarius_py/.venv/bin/python \
  docs/benchmarks/evidence/p1-solver-v2-2026-11-27/validation/review.py \
  /tmp/sagittarius-p1-solver-evidence/campaign \
  --output /tmp/p1-solver-relocated-acceptance.json
```

`--allow-partial` allows structural auditing of under-resolved/selected campaigns;
it does not claim all configurations passed accuracy. The explicit review applies
the stricter full-matrix characterization policy. Absolute result paths relocate
by the recorded campaign prefix; no Julia execution is needed for saved review.
