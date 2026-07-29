# Experiment Configuration

Spec ID: `SPEC-API-007`
Status: `Current`
Roadmap: Phase 15
Version: `experiment-config/v1`
Last reviewed: 2026-07-29

`experiment-config/v1` is a JSON-only, reproducible declaration for one Python SDK simulation. The public workflow is `load_experiment_config()`, `run_experiment_config()`, and `save_experiment_config()`.

## Required shape

```json
{
  "schema_version": "experiment-config/v1",
  "register": {"atoms": [[0.0, 0.0]], "C6": 0.0},
  "pulse": {"omega": 1.0, "delta": 0.0},
  "solver": {"seed": 12, "saveat": [0.0, 0.5, 1.0]},
  "time_span": [0.0, 1.0],
  "initial_state": {"bitstring": "0"},
  "outputs": {"result": "result.json"}
}
```

`register.atoms` is in `Register.atoms` order. Pulse values use the existing scalar, local vector, local-index-map, and JSON pulse-AST forms. Solver keys are public `SolverConfig` fields. `initial_state.bitstring` has one character per atom in that same order and is rejected if it is forbidden by a blockade-reduced basis.

`observables` is required and uses the existing observable declaration format. Optional `readout` contains a positive `shots` count and optional non-negative seed; `outputs.samples` requires it. Outputs may additionally contain `manifest` and `samples`. Relative paths resolve relative to the loaded config file (or the current directory for an in-memory mapping).

## State preparation helpers

The public Python SDK provides `all_ground_state(simulation)`, `bitstring_state(simulation, bitstring)`, and `single_excitation_state(simulation, atom_index)`. Each returns a `PreparedState` that can be passed directly to `Simulation.run()`. Bitstrings use one character per atom in `Register.atoms` order.

For blockade-reduced simulations, a helper validates that the requested bitstring is represented by the reduced basis and rejects forbidden states before solver execution. Its `state-preparation/v1` metadata records the preparation type, bitstring, basis mode, basis size, basis index, and atom index where applicable. The metadata is retained in result `metadata`, `diagnostics`, and `run-manifest/v1` `initial_state.preparation`. Uniform-superposition preparation is not currently provided.

`experiment-config/v1` remains JSON-only and declares a basis state through `initial_state.bitstring`; it does not yet encode named helper forms.

## Reproducibility and limits

The schema excludes Python callables and arbitrary complex state vectors because they are not JSON-replayable. A completed run stores `manifest.source_config` with the source schema version, canonical-document SHA-256, source kind, and source path. The result artifact, optional standalone manifest, and optional samples therefore all link back to the same immutable config content.

`run_experiment_config()` requires declared observables: raw backend solver objects do not provide the stable `SimulationResult` artifact contract.
