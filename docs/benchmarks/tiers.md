# Benchmark Tiers

Status: `Planned contract`
Roadmap: Phase 16
Version: `benchmark-tiers/v1`
Last reviewed: 2026-07-02

Sagittarius benchmarks are grouped by tier so that developers can run the right amount of evidence for the task. Tiers are cumulative in discipline but not always cumulative in cost. A stress-tier run does not replace correctness-tier evidence.

## Tier Summary

| Tier | Purpose | Expected cost | Default CI policy |
| :--- | :--- | :--- | :--- |
| Smoke | Fast sanity checks for command wiring and artifact creation. | Seconds to a few minutes. | Optional PR CI when relevant. |
| Correctness | Validate physics, solver, and optimization outputs against references. | Minutes to tens of minutes. | Local or manual CI unless small enough for PR. |
| Parity | Compare CPU/CUDA, dense/reduced, Python/Julia, or solver methods. | Minutes to hours depending on backend. | Manual or self-hosted where hardware is needed. |
| Scaling | Increase size or workload until timeout, memory pressure, or numerical failure. | Hardware dependent. | Manual, release-candidate, or local evidence. |
| Stress | Hardware-specific limit finding and failure characterization. | Potentially long running. | Manual only. |

## Smoke Tier

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

## Correctness Tier

Goal: establish that the scenario has a trustworthy reference before runtime or scaling is interpreted.

Minimum requirements:

- analytic, dense, exact ILP, or declared tighter-solver reference;
- fixed seeds and fixed output grid where applicable;
- explicit tolerance policy;
- failure rows for reference mismatch, solver failure, or artifact write failure;
- linked run manifests or result artifacts when simulations produce durable results.

Correctness metrics may include max absolute trajectory error, final-state error, trace error, positivity violations, MWIS feasibility, exact objective gap, and reduced-vs-full observable deviation.

## Parity Tier

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

## Scaling Tier

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

## Stress Tier

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
