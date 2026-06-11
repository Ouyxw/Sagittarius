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
- Benchmark results are only meaningful with the exact hardware, package versions, backend settings, solver tolerances, and problem configuration used to produce them.

## Physics and Numerics

- Sagittarius models idealized Rydberg neutral-atom analog dynamics. It is not a calibrated hardware control stack.
- Units and conventions are documented in `README.md`; users are responsible for supplying parameters in those units.
- Open-system Lindblad and MCWF workflows are available, but expanded positivity, trace-preservation, and MCWF-vs-Lindblad ensemble sanity checks are planned.
- Reduced-basis simulations should be cross-checked against dense/full-basis evolution for small systems when introducing new physics assumptions.

## Data and Reproducibility

- `SimulationResult.save()` can persist data, metadata, and diagnostics, but the full run manifest and artifact envelope are tracked in the Observability & Reproducibility roadmap phase.
- Benchmark scripts are not yet a finalized reproducible artifact pipeline. JSON/CSV outputs, markdown tables, linked diagnostics, and build/container metadata are planned.

## Unsupported or Future Scenarios

- Multi-node Slurm/MPI execution is future work.
- C++ FFI bindings are future work.
- Web dashboards and interactive result explorers are future work.
- Hardware calibration, pulse upload, device scheduling, and experiment execution are outside the current SDK scope.
