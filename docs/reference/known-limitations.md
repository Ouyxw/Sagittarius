# Known Limitations

Sagittarius 1.0.0 is a stable research SDK. This page records practical limits and unsupported scenarios so examples, benchmarks, and hardware-facing studies can be interpreted correctly.

## API Stability

- Sagittarius 1.0.0 defines the supported Python SDK and Julia developer API surface. Future incompatible changes require a documented compatibility and versioning decision under [`SPEC-GOV-005-repository-versioning.md`](../governance/SPEC-GOV-005-repository-versioning.md).
- Explicit `GlobalPulse`, `LocalPulseVector`, and `CallablePulse` wrappers are supported, while scalar/list/dict/callable shorthand forms remain backward-compatible. See [`SPEC-API-001-pulse-and-indexing-contract.md`](../api/SPEC-API-001-pulse-and-indexing-contract.md) for the current contract.
- Python atom indices are zero-based and follow `Register.atoms` order. Julia internals are one-based; this boundary is documented in [`SPEC-API-002-python-julia-parity.md`](../api/SPEC-API-002-python-julia-parity.md) and covered by cross-language golden tests.

## Backend and Environment

- Importing `sagittarius` is designed to stay lightweight, but simulations and pulse compilation require Julia through `juliacall`. A broken Julia/PythonCall environment will prevent backend execution.
- `doctor()` provides structured diagnostics, ABI/toolchain capability summaries, and backend parity-status pointers, but it is not a substitute for hardware-backed numerical parity testing.
- CUDA is the primary GPU development target and is marked experimental. AMDGPU and Metal are planned; they should not be treated as production-equivalent to CUDA. See [`SPEC-BACKEND-001-backends.md`](SPEC-BACKEND-001-backends.md).
- Container images do not guarantee GPU availability. Host drivers, device passthrough, runtime compatibility, and backend package availability must be validated on the running machine.

## Scale and Performance

- Full Hilbert-space simulation scales as `2^N`; practical atom counts are limited by memory, solver cost, and observable collection.
- Blockade-reduced bases can reduce state space substantially, and repeated reduced-basis construction is cached by geometry/blockade metadata. The reduced basis is still an approximation that must be selected and validated against the problem's physical error budget.
- GPU execution paths are still maturing. Sparse pattern reuse, CUDA sparse value-buffer reuse, and CPU/GPU parity tests exist for the CUDA path, but CUDA remains experimental and AMDGPU/Metal are not parity-tested production backends.
- Benchmark results are only meaningful with the exact hardware, `version-info/v1` metadata, backend settings, solver tolerances, and problem configuration used to produce them.
- Raw MCWF trajectory retention scales with observable count, output time samples, and trajectory count. It is opt-in diagnostic data, so plan memory and artifact capacity before enabling it for large ensembles.
- Stored samples require a common finite time axis and the same trajectory count for every observable. `trajectory-data/v1` rejects mismatched shapes, time values, or observable ordering during save/load. Raw samples are intentionally absent from `shared-result/v1`.

## Physics and Numerics

- Sagittarius models idealized Rydberg neutral-atom analog dynamics. It is not a calibrated hardware control stack.
- Units and conventions are documented in [`physics/SPEC-PHYS-001-units.md`](../physics/SPEC-PHYS-001-units.md); users are responsible for supplying parameters in a consistent unit system.
- Open-system Lindblad and MCWF workflows are available, and `open_system_sanity_checks()` covers trace preservation, density-matrix positivity, and MCWF-vs-Lindblad observable agreement for small systems. New open-system assumptions should still be checked against problem-specific reference cases.
- Current open-system noise is limited to local Markovian Rydberg decay and pure dephasing. Custom Lindblad channels, correlated dephasing, collective decay, stochastic Hamiltonian noise, time-dependent rates, and readout errors are planned or unsupported; see [`SPEC-PHYS-004-noise-models.md`](../physics/SPEC-PHYS-004-noise-models.md).
- Reduced-basis simulations should be cross-checked against dense/full-basis evolution for small systems when introducing new physics assumptions.

## Visualization and Reporting

- Phase 19 visualization helpers are analysis tools, not hardware-calibration controls, numerical verification, or independent performance evidence. They require compatible Python-side result data and do not make unavailable observables or manifest fields available.
- Register and geometry views are two-dimensional. Basis and state diagnostics intentionally reject systems above their documented small-system limits rather than attempting unreadable or unsafe plots.
- Sweep helpers currently accept in-memory mappings with caller-supplied failed-run and manifest-link fields. There is no versioned user-facing sweep artifact schema, artifact-path resolver, or retained failure-row contract.
- Figure sidecars and reports preserve available provenance fields, but their classification is descriptive. A `benchmark_evidence` label or an artifact ID does not validate an artifact or authorize a public performance statement.
- Benchmark plotting functions can render ordinary dictionaries for diagnostic use. Before public use, users must validate and retain `benchmark-artifact/v1` evidence and follow the governance documents linked below.

## Data and Reproducibility

- Python `SimulationResult.save()` persists a `result-artifact/v1` envelope with data, metadata, diagnostics, a validated `run-manifest/v1` manifest for SDK-generated simulation results, and an embedded `shared-result/v1` payload. Julia-native result writers should emit the same shared payload shape for cross-language tooling.
- Benchmark scripts now emit `benchmark-artifact/v1` JSON with companion CSV and Markdown tables, runtime/build/backend metadata, process memory usage, and linked run manifests where available. Public performance statements should cite those artifacts, follow [`SPEC-GOV-001-performance-claims.md`](../governance/SPEC-GOV-001-performance-claims.md), and be tracked through [`SPEC-GOV-002-disclosure-control.md`](../governance/SPEC-GOV-002-disclosure-control.md); the benchmark set is still not a complete performance corpus.

## Unsupported or Future Scenarios

- Multi-node Slurm/MPI execution is future work.
- C++ FFI bindings are future work.
- Web dashboards and interactive result explorers are future work.
- Hardware calibration, pulse upload, device scheduling, and experiment execution are outside the current SDK scope.
