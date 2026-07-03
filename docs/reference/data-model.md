# Data Model

Status: `Current`
Roadmap: Phase 1, Phase 6, Phase 8, Phase 10, Phase 11, Phase 12, Phase 14, Phase 15
Version: `data-model/v1`
Last reviewed: 2026-07-03


This page summarizes the Sagittarius data model across user-facing Python objects, Julia physics objects, runtime diagnostics, manifests, and persistent artifacts. For module boundaries, see [`architecture-overview.md`](architecture-overview.md). For schema design practice, see [`development-sop.md`](development-sop.md).

## Model Layers

```text
User declarations
    Register, Atom, PulseSequence, Pulse, SolverConfig, observables
        |
        v
Validated runtime model
    normalized pulses, validated indices, solver settings, backend diagnostics
        |
        v
Julia physics model
    Register, BasisContext, Hamiltonian, jump operators, solver state
        |
        v
Result model
    SimulationResult(data, metadata, diagnostics, manifest)
        |
        v
Persistent artifacts
    result-artifact/v1, shared-result/v1, benchmark-artifact/v1
```

## User-Facing Domain Objects

| Object | Layer | Purpose | Notes |
| :--- | :--- | :--- | :--- |
| `Atom` | Python and Julia | Position of a neutral atom in 3D space. | Python examples use `Atom(x, y, z)`; Julia also exports `Atom`. |
| `Register` | Python and Julia | Ordered atom collection plus interaction coefficient `C6`. | Python atom indices are zero-based in `Register.atoms` order. |
| `Pulse` / `PulseNode` | Python and Julia | Time-dependent pulse declarations. | Includes constants, ramps, Gaussian, Blackman, sinc, sin-squared, and piecewise forms. |
| `PulseSequence` | Python | User-facing omega/delta pulse container. | Accepts scalar, local vector, dict, callable, and explicit pulse wrapper forms under the pulse contract. |
| `SolverConfig` | Python | Solver, basis, backend, open-system, and GPU options. | Carries `method`, `adaptive`, `dt`, seed, and output-grid contracts with requested/effective metadata. |
| `Simulation` | Python | Coordinates validation, backend calls, solver execution, diagnostics, and result wrapping. | Main lifecycle object. |
| `SimulationResult` | Python | In-memory result plus metadata, diagnostics, manifest, save/load helpers. | Writes `result-artifact/v1`, embeds `shared-result/v1`, and exposes final-state readout sampling when a distribution is available. |

Pulse and indexing details are defined in [`SPEC-API-001-pulse-and-indexing-contract.md`](../api/SPEC-API-001-pulse-and-indexing-contract.md).

## Julia Physics Objects

| Object | Purpose |
| :--- | :--- |
| `Atom` | Julia-side atom coordinate representation. |
| `Register` | Julia-side ordered atom collection and `C6`. |
| `BasisContext` | Shared full/reduced basis mapping context used by Hamiltonians, observables, jump operators, and MCWF trajectories. |
| `RydbergHamiltonian` | Matrix-free or sparse-compatible Hamiltonian representation. |
| `RydbergOperator` | Full-basis Rydberg operator representation. |
| `ReducedRydbergOperator` | Reduced-basis operator representation. |
| Jump operators | Local decay and dephasing operators for open-system paths; planned extensions include correlated and custom channels. |

The `BasisContext` is the key data-model object for reduced-basis consistency. Any feature that interprets bitstrings, state indices, observables, or jump operators must use the same basis context as the Hamiltonian.

## Indexing and Bitstring Semantics

Sagittarius uses a strict cross-language indexing contract:

- Python user-facing atom indices are zero-based.
- Python atom order is `Register.atoms` order.
- Julia internals are one-based.
- Local pulse vectors are interpreted in register order and are not reversed.
- Bitstrings and reduced-basis indices must be mapped through the active full or reduced basis context.

See [`SPEC-API-002-python-julia-parity.md`](../api/SPEC-API-002-python-julia-parity.md) for parity rules and golden-test scope.

## Runtime Configuration Model

`SolverConfig` currently carries:

- `method`, `adaptive`, `dt`, `reltol`, and `abstol`;
- `blockade_radius`;
- local open-system rates such as `gamma` and `gamma_phi`;
- MCWF settings such as `use_mc` and `n_trajectories`;
- GPU settings such as `use_gpu` and `gpu_backend`.

Important distinction:

| Config kind | Meaning |
| :--- | :--- |
| Requested configuration | What the user passed to Python. |
| Normalized configuration | Python-validated and canonicalized values. |
| Effective configuration | What the backend actually used. |

Phase 12 solver fields and Phase 15 seed/output-grid fields are represented through `SolverConfig`, diagnostics, run manifests, and result artifacts. Effective solver metadata records `effective_method`, `effective_adaptive`, and `effective_dt`; effective output metadata records `effective_saveat`. Phase 15 readout metadata records final bitstring distributions, represented basis bitstrings, reduced-basis forbidden-bitstring exclusion, and sampling support.

## Result Object Model

`SimulationResult` has four primary sections:

| Section | Meaning |
| :--- | :--- |
| `data` | Numeric result series such as `t` and observable trajectories. |
| `metadata` | Result type, runtime metadata, basis information, and related descriptive fields. |
| `diagnostics` | Backend report, issue details, capability summaries, and runtime diagnostics. |
| `manifest` | `run-manifest/v1` reproducibility record for the run. |

Readout-capable results store `metadata.readout.final_bitstring_probabilities` and expose it through `SimulationResult.final_bitstring_distribution()`. `SimulationResult.sample(shots, seed=...)` draws reproducible shot counts from that stored final-state distribution and returns a `measurement-samples/v1` dictionary.

`SimulationResult.to_shared_result()` projects the result into the stable `shared-result/v1` payload documented in [`SPEC-DATA-001-shared-result-schema.md`](SPEC-DATA-001-shared-result-schema.md).

## Artifact Inventory

| Artifact or schema | Current role |
| :--- | :--- |
| `event-taxonomy/v1` | Stable event ID and payload catalog. |
| `doctor/v2.1` | Lightweight runtime and backend diagnostics report. |
| `backend-probe/v2.1` | Initialized backend probe report. |
| `version-info/v1` | Runtime, package, git, build, container, and backend metadata, including Julia backend source (`env_override`, `source_checkout`, or `package_resource`). |
| `run-manifest/v1` | Per-simulation reproducibility manifest. |
| `result-artifact/v1` | Persistent `SimulationResult` envelope. |
| `shared-result/v1` | Language-neutral result payload. |
| `benchmark-artifact/v1` | Structured performance measurement artifact. |
| `mwis-batch-verification/v1` | MWIS batch verification report shape. |

## Result Artifact Shape

A saved simulation result follows this conceptual structure:

```json
{
  "schema_version": "result-artifact/v1",
  "artifact_type": "sagittarius.result",
  "data": {},
  "metadata": {},
  "diagnostics": {},
  "manifest": {},
  "shared_result": {}
}
```

The embedded `shared_result` is intended to be the stable minimal payload for cross-language and downstream tooling. The envelope preserves richer Python compatibility fields.

## Run Manifest Responsibilities

A `run-manifest/v1` should describe:

- register geometry and atom count;
- pulse declarations for omega and delta;
- solver options and backend settings;
- time span and observables;
- initial state basis size;
- backend diagnostics, including selected Julia backend source metadata;
- version and runtime metadata;
- random and trajectory metadata where applicable;
- event taxonomy schema and emitted event IDs.

Manifests should describe the physical and numerical run semantics, not only the raw Python call.

## Benchmark and Governance Data

Benchmark data is separate from ordinary simulation result data.

- Simulation artifacts answer: what happened in one run?
- Benchmark artifacts answer: what was measured across scenarios, repeats, hardware, and versions?
- Governance documents answer: how may those measurements be stated publicly?

See [`SPEC-GOV-004-benchmarking-plan.md`](../governance/SPEC-GOV-004-benchmarking-plan.md) and [`SPEC-GOV-001-performance-claims.md`](../governance/SPEC-GOV-001-performance-claims.md).

## Planned Data-Model Extensions

| Roadmap | Planned model changes |
| :--- | :--- |
| Phase 11 | Typed observable declarations and observable metadata in manifests and artifacts. |
| Phase 12 | Implemented effective solver method, adaptive/fixed-step settings, and `dt` metadata. |
| Phase 14 | Noise model metadata, custom Lindblad declarations, correlated noise, stochastic realization metadata. |
| Phase 15 | Implemented seed and output-grid metadata; planned sampling results, experiment configs, and sweep artifacts. |
| Phase 16 | Optional readout noise and interop/export metadata. |

## Maintenance Triggers

Update this page when:

- public Python objects or Julia physics objects change;
- manifest, result artifact, shared result, benchmark artifact, or diagnostics schemas change;
- indexing or bitstring semantics change;
- new solver paths, observables, noise models, sampling APIs, or sweep artifacts are added;
- Python/Julia parity contracts change.
