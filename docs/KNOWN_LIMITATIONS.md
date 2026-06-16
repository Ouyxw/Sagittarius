# Known Limitations

Sagittarius is an early research SDK. This page records practical limits and unsupported scenarios so examples, benchmarks, and hardware-facing studies can be interpreted correctly.

## API Stability

- The Python SDK and Julia developer API are still evolving. Names, defaults, result fields, and error behavior may change before a stable release.
- Scalar/list/dict/callable pulse inputs are supported today, but explicit typed pulse wrappers are still planned. See `docs/PULSE_CONTRACT.md` for the current contract.
- Python atom indices are zero-based and follow `Register.atoms` order. Julia internals are one-based; this boundary is documented in `docs/PYTHON_JULIA_PARITY.md` and covered by cross-language golden tests.

## Backend and Environment

- Importing `sagittarius` is designed to stay lightweight, but simulations and pulse compilation require Julia through `juliacall`. A broken Julia/PythonCall environment will prevent backend execution.
- `doctor()` provides structured diagnostics, but it is not a substitute for hardware-backed parity testing.
- CUDA is the primary GPU development target and is marked experimental. AMDGPU and Metal are planned; they should not be treated as production-equivalent to CUDA. See `docs/BACKENDS.md`.
- Container images do not guarantee GPU availability. Host drivers, device passthrough, runtime compatibility, and backend package availability must be validated on the running machine.

## Scale and Performance

- Full Hilbert-space simulation scales as `2^N`; practical atom counts are limited by memory, solver cost, and observable collection.
- Blockade-reduced bases can reduce state space substantially. Basis generation is not yet cached; full and reduced sparse Hamiltonians reuse their CSC pattern once constructed.
- GPU execution paths are still maturing. Sparse pattern reuse, CUDA sparse value-buffer reuse, and CPU/GPU parity tests exist; broader backend buffer reuse remains planned work.
- Benchmark results are only meaningful with the exact hardware, `version-info/v1` metadata, backend settings, solver tolerances, and problem configuration used to produce them.

## Physics and Numerics

- Sagittarius models idealized Rydberg neutral-atom analog dynamics. It is not a calibrated hardware control stack.
- Units and conventions are documented in `README.md`; users are responsible for supplying parameters in those units.
- Open-system Lindblad and MCWF workflows are available, but expanded positivity, trace-preservation, and MCWF-vs-Lindblad ensemble sanity checks are planned.
- Reduced-basis simulations should be cross-checked against dense/full-basis evolution for small systems when introducing new physics assumptions.

## Data and Reproducibility

- Python `SimulationResult.save()` persists a `result-artifact/v1` envelope with data, metadata, diagnostics, a validated `run-manifest/v1` manifest for SDK-generated simulation results, and an embedded `shared-result/v1` payload. Julia-native result writers should emit the same shared payload shape for cross-language tooling.
- Benchmark scripts now emit `benchmark-artifact/v1` JSON with companion CSV and Markdown tables, runtime/build/backend metadata, process memory usage, and linked run manifests where available. The benchmark set includes scaling, GPU, cluster, and ablation scripts but is still not a complete performance-claims corpus; Phase 10 tracks benchmark-backed public claims.

## Unsupported or Future Scenarios

- Multi-node Slurm/MPI execution is future work.
- C++ FFI bindings are future work.
- Web dashboards and interactive result explorers are future work.
- Hardware calibration, pulse upload, device scheduling, and experiment execution are outside the current SDK scope.
