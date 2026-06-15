# Known Limitations

Sagittarius is an early research SDK. This page records practical limits and unsupported scenarios so examples, benchmarks, and hardware-facing studies can be interpreted correctly.

## API Stability

- The Python SDK and Julia developer API are still evolving. Names, defaults, result fields, and error behavior may change before a stable release.
- Scalar/list/dict/callable pulse inputs are supported today, but explicit typed pulse wrappers are still planned. See `docs/PULSE_CONTRACT.md` for the current contract.
- Python atom indices are zero-based and follow `Register.atoms` order. Julia internals are one-based. Cross-language golden tests are still planned.

## Backend and Environment

- Importing `sagittarius` is designed to stay lightweight, but simulations and pulse compilation require Julia through `juliacall`. A broken Julia/PythonCall environment will prevent backend execution.
- `doctor()` provides structured diagnostics, but it is not a substitute for hardware-backed parity testing.
- CUDA is the primary GPU development target and is marked experimental. AMDGPU and Metal are planned; they should not be treated as production-equivalent to CUDA. See `docs/BACKENDS.md`.
- Container images do not guarantee GPU availability. Host drivers, device passthrough, runtime compatibility, and backend package availability must be validated on the running machine.

## Scale and Performance

- Full Hilbert-space simulation scales as `2^N`; practical atom counts are limited by memory, solver cost, and observable collection.
- Blockade-reduced bases can reduce state space substantially, but basis generation and Hamiltonian construction are not yet fully cached or pattern-reused.
- GPU execution paths are still maturing. Buffer reuse, sparse pattern reuse, and CPU/GPU parity suites are planned work.
- Benchmark results are only meaningful with the exact hardware, `version-info/v1` metadata, backend settings, solver tolerances, and problem configuration used to produce them.

## Physics and Numerics

- Sagittarius models idealized Rydberg neutral-atom analog dynamics. It is not a calibrated hardware control stack.
- Units and conventions are documented in `README.md`; users are responsible for supplying parameters in those units.
- Open-system Lindblad and MCWF workflows are available, but expanded positivity, trace-preservation, and MCWF-vs-Lindblad ensemble sanity checks are planned.
- Reduced-basis simulations should be cross-checked against dense/full-basis evolution for small systems when introducing new physics assumptions.

## Data and Reproducibility

- Python `SimulationResult.save()` persists a `result-artifact/v1` envelope with data, metadata, diagnostics, and a validated `run-manifest/v1` manifest for SDK-generated simulation results. Cross-language Julia parity is still tracked under shared result schema work.
- Benchmark scripts are not yet a finalized reproducible artifact pipeline. JSON/CSV outputs, markdown tables, and linked diagnostics are planned; runtime build/container metadata is available through `version_info()` and simulation manifests.

## Unsupported or Future Scenarios

- Multi-node Slurm/MPI execution is future work.
- C++ FFI bindings are future work.
- Web dashboards and interactive result explorers are future work.
- Hardware calibration, pulse upload, device scheduling, and experiment execution are outside the current SDK scope.
