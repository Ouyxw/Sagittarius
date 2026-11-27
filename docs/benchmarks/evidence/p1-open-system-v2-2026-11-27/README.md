# P1 open-system V2 local evidence — 2026-11-27

Status: bounded local campaign accepted by original/relocated automated audits.
Classification: shared-workstation `local_only`; no release/public approval.

All **99 declared rows are accounted for: 85 passed, 14 resource exclusions**.
There are 89 cost configurations and ten correctness controls; 75 costs execute
with two warmups/five eligible measurements, yielding **375 measured calls**.
Ten correctness controls and 315 separate statistical-seed calls pass. The audit
checks **916 regular SDK results plus 63 tighter result/manifest pairs**,
and **67 raw density histories**. No attempted final-campaign failure,
incomplete row, or slow-valid-repeat exclusion is hidden.

The [plan](../../plans/v2.md#p1-open-system), [campaign](campaign.json),
[coverage](coverage.json), [audit](audit.json), [final acceptance](acceptance.json), [convergence](convergence.json),
[direct Lindblad/MCWF checks](lindblad_mcwf.json),
[raw call records](open_system_repeats.json),
[performance table](open_system_performance.md) and
[suite table](open_system_performance_suite.md) retain exact scope and membership.
Complete results/manifests, raw/reference arrays, worker logs/checkpoints,
frozen source/runtime files and internal checksums are in
[archive identity and parts](archive-identity.json) ([campaign.tar.xz.part-00](campaign.tar.xz.part-00), [campaign.tar.xz.part-01](campaign.tar.xz.part-01), [campaign.tar.xz.part-02](campaign.tar.xz.part-02)). Original short pilots and startup/source-freeze
failures are in [pilots.tar.xz](pilots.tar.xz), separate from accepted evidence.
[Commands](validation/commands.txt), [measurement source index](source-index.json),
[review source index](review-source-index.json), validation
logs and the outer [checksum inventory](SHA256SUMS) remain reviewable.

## Actual N=20 coverage

| Path/count | D | Eligible | Median SDK seconds | Median trajectories/s |
| --- | ---: | ---: | ---: | ---: |
| mcwf/100 | 907 | 5 | 5.92210825 | 16.8858784 |
| mcwf/500 | 907 | 5 | 25.4543474 | 19.64301 |
| mcwf/1000 | 907 | 5 | 48.8025112 | 20.4907488 |

These are separate fixed-seed, serial, end-to-end workloads. Complete runtime
median/min/max/p25/p75 and throughput distributions, exact measured member IDs,
counts and unavailable reasons are retained in matching JSON/CSV/Markdown.
Different N/D, basis, counts, rates, seeds or storage policies are not pooled.
No Lindblad throughput or speedup is inferred.

The chain has a=4 um, Rb=12.4 um (three-site exclusion), C6=100 rad*um^6/us,
omega=2*pi rad/us, delta=.3 rad/us, all-ground state, T=.05 us, complex128,
adaptive Tsit5 1e-8/1e-10 and 101 explicit times. N=20 has D=907, not the
D17711 radius used by the scaling/observable suites. Gamma=.5/us and
projector dephasing gamma_phi=.125/us are combined for the size series. Decay/
dephasing-only and per-site rates have bounded one/two-atom controls; the latter
multiply rates by 1+i/2 and 1+i/3. One separate N=2/K500 workload exports raw
samples. Correctness controls cover analytic bitstring decay at every target
size and raw one-atom (g+r)/sqrt(2) coherence decay on [0,2]. All physical inputs,
LSB basis/atom mapping and supported linear site/total/pair declarations are frozen.

## References and uncertainty

Small D<=64 references independently assemble H/local jumps and integrate the
master equation with SciPy DOP853 at 1e-11/1e-13 and 1e-12/1e-14; stability is
<=1e-9. Analytic population exp(-gamma*t) and coherence
exp[-(gamma+gamma_phi)*t/2] provide distinct controls. Separate tighter SDK
Lindblad executions save all 101 raw densities for deterministic error <=1e-6,
trace/Hermiticity <=1e-6 and minimum eigenvalue >=-1e-7. Maximum density/reference
error is 6.58995081e-12, maximum trace error
8.8817842e-16, minimum eigenvalue -1.17488689e-13.
Validation/history storage/eigendecomposition is outside primary execution timing.

Timing repeats fix seed20260811; five **separate** seed calls use
20260811–20260815. Two-sided Hoeffding bounds at alpha=1e-6 union over all frozen
scenarios, observables, 101 times and 32 comparison/call slots per configuration.
Ranges are one for site/pair and N for total population. Five-seed pooled means
use 5*K samples; cross-count pooled comparisons sum their bounds. Stochastic
tighter references add their own K-trajectory uncertainty. Standard errors are
descriptive; no seed-wise monotonic error or relative precision is asserted.
All 45 available cross-count comparisons pass. Raw storage
also checks finite K-by-101 shapes and sample-mean/SDK-average agreement <=1e-12.

Direct saved Lindblad/MCWF review additionally checks 54
matched configurations (708 individual/tighter comparisons
and 54 pooled five-seed comparisons). It matches geometry,
basis, pulses, rates, solver and grids; exported raw samples do not change the
physical observable comparison. References use retained measured Lindblad values
or the worker's untimed raw Lindblad history. The same frozen 32-slot union rule
and two 1e-6 numerical floors apply. Unavailable matching Lindblad paths remain
explicit (9 configurations: budget exclusions or
separate analytic special-case controls). Measurement sources/outputs are
immutable; this saved-data review has its own retained source identity and tests.

Larger interacting rows use tighter same-method Lindblad/MCWF and multi-seed
consistency, **not an independent interacting oracle**. Analytic target-size decay
controls establish a special-case check, not general interacting/model validation.

## Timing, resources and exclusions

Fresh Linux workers enforce 1800s timeout, 4096MiB sampled RSS and predeclared
LindbladD256/MCWF D1024 validation/time caps. Preflight includes a 2GiB JIT reserve,
D-squared density histories/workspaces, state/jump/mapping/ensemble output and
nominal full-space MCWF readout metadata allocations. Requested/effective Julia/
BLAS/OpenMP/MKL counts are retained; child thread environment is one. RSS polling
at 50ms is not a hard address-space limit; lifetime HWM includes doctor,
references, checks and writes. Memory is attributable per configuration process.

Primary time covers one reset-state `Simulation.run`, including validation,
construction, collection and manifest generation. Reset/wrapper creation,
references, gates, serialization and reporting are excluded. First workload call
follows initialized doctor/setup/reference/tighter controls and is not process-cold.
Fixed seeds select `EnsembleSerial`; no unseeded/threaded throughput is claimed.
Completed trajectory count is inferred from successful SDK ensemble return and
actual manifest K; no public independent progress counter is exposed.

Fourteen exclusions remain: full Lindblad N=10/12/16/20, reduced Lindblad N=20,
and full MCWF at N=12/16/20 for all three counts. Full N=20 complex128 density
storage alone is 16TiB; no unsafe allocation is attempted. Full-matrix all-success
is **false**. All required small reference/analytic controls and applicable reduced
N=20 MCWF workloads pass bounded acceptance. Excluded scopes remain open.

Current MCWF results export no final sampling state and their nominal readout
manifest enumerates full bitstrings even for reduced execution. This costs
memory/storage and is not the executed basis or a probability distribution;
actual execution basis is checked independently and recorded in solver/initial
metadata. This benchmark preserves SDK behavior. Raw-export off still allocates
internal ODE histories and ensemble outputs; the retained-trajectory cost is a
separate workload.

## Validation and replay

All 88 distinct targeted tests pass across retained regressions and the final
28-test frozen-runner pass, five cross-path unit checks and one real per-atom reduced-noise review test. Tests include original one-atom runner compatibility,
MCWF, solver settings, Python/Julia golden, artifact/serialization/row/suite/
failure contracts and docs. Corruption tests cover raw coherence/initial state,
seeds/manifests, convergence and companion reports. Backend initialization is
monkeypatched to fail during an audit to verify backend-free replay. The initial
final-test regex mismatch reflects an earlier correct rejection by the new
initial-state gate; corrected expectation passes. Original failures remain logs.
Full Python suite, GPU, packaging, isolated host, physical/blockade validation,
recurring RC and public-use/disclosure approval are not established.

```bash
sha256sum -c SHA256SUMS
mkdir -p /tmp/open-system-replay
# Run from this evidence directory; extract the complete retained layout.
cat campaign.tar.xz.part-* > /tmp/open-system-v2-2026-11-27-campaign.tar.xz
tar -xJf /tmp/open-system-v2-2026-11-27-campaign.tar.xz -C /tmp/open-system-replay
cd /tmp/open-system-replay/open-system-v2-final-2026-11-27
sha256sum -c SHA256SUMS
# Return to this source checkout (adjust the path on another machine):
cd /home/oyxw/Sagittarius/sagittarius_py
uv run python ../scripts/accept_open_system_campaign.py \
  /tmp/open-system-replay/open-system-v2-final-2026-11-27
```

Archived absolute artifact paths retain their original identity. The auditor maps
them into the supplied archive root; it checks source/runtime hashes, real saved
outputs, reference/seed/density gates, raw membership, throughput, companions
and every retained result/manifest link after relocation without Julia. No
source rebuild, wheel installation or scientific claim follows from archive replay.
