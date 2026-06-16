# Python SDK Parity Contract

Sagittarius maintains the following contract between the Python SDK and the Julia-native API for shared simulation semantics. Python remains the ergonomic front door, but these behaviors must stay equivalent unless a breaking schema/version note says otherwise. For paired examples that apply this contract, see `docs/DUAL_SDK_EXAMPLES.md`.

## Covered Semantics

- Atom order is the order supplied by `Register.atoms`. Python atom indices are zero-based; Julia atom indices are one-based at the API boundary.
- Bitstrings use atom `i` as bit `i` in Python and bit `i - 1` in Julia. Basis states are sorted ascending by integer bitstring.
- A Python local pulse dict defaults unspecified atoms to `0.0` and maps key `0` to Julia atom `1`, key `1` to Julia atom `2`, and so on.
- Scalar pulses broadcast to every atom in both SDKs. Local pulse vectors preserve register order.
- Full and blockade-reduced Hamiltonians must match elementwise for the same register, pulse values, detuning values, C6, and blockade radius.
- Reduced-basis observables, Lindblad jump operators, MCWF trajectories, and Hamiltonian evolution must use the same reduced basis ordering and bitstring-to-index mapping.
- Solver defaults exposed by Python must map to equivalent Julia solver calls for method, tolerances, time span, initial state, blockade radius, and observable indexing.
- Python `SimulationResult` fields and run manifests must describe the same physical run semantics used by Julia: register geometry, pulse configuration, solver settings, basis size, backend, event taxonomy IDs, and initial state norm.
- Validation errors at the Python boundary should fail before backend initialization when invalid user input can be detected without Julia execution.

## Golden Test Scope

Cross-language golden tests cover small systems where dense comparisons are cheap:

- Full-basis Hamiltonian parity.
- Blockade-reduced basis and reduced Hamiltonian parity.
- Zero-based Python local addressing parity with one-based Julia atom order.
- Observable trajectory parity between Python `Simulation.run()` and direct Julia `solve_schrodinger()`.
- Python result manifest fields for golden runs.

Large-scale performance, GPU backend parity, and stochastic MCWF convergence are covered by dedicated benchmark/parity suites rather than this contract test file.
