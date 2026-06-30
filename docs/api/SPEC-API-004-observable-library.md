# Observable Library Contract

Spec ID: `SPEC-API-004`
Status: `Mixed`
Roadmap: Phase 11
Version: `observable-library-contract/v1`
Last reviewed: 2026-06-30


This page defines the Phase 11 diagonal observable-library contract. The first-scope diagonal declarations below are implemented; off-diagonal observables remain future work. The backward-compatible surface remains:

- Julia: diagonal observable constructors such as `RydbergPopulation`, `TotalRydbergPopulation`, `PairCorrelation`, `BitstringProbability`, `MWISCost`, `PauliZ`, `PauliZZ`, and `Parity` return solver-compatible callables.
- Python: `observables={"name": atom_index}` remains valid shorthand for single-atom Rydberg populations, and typed declarations such as `{"type": "pair_correlation", "atoms": [0, 1]}` are supported.

The Phase 11 work extends that surface into a typed observable library while preserving the current shorthand.

## Design Goals

Observable constructors must return solver-compatible callables with the stable Julia signature:

```julia
(state, t, integrator) -> Float64
```

Each observable must interpret wavefunction vectors, Lindblad density matrices, and reduced-basis states consistently. Reduced-basis observables must use the same `BasisContext` as Hamiltonians, jump operators, and MCWF trajectories.

The first implementation scope is diagonal occupation and bitstring observables. These are stable across full and reduced bases and directly support Rydberg blockade, AQC, and MWIS workflows. Off-diagonal observables such as Pauli-X, Pauli-Y, coherence, non-diagonal energy expectation, and entanglement measures remain future work unless explicit basis-mapping tests are added with the implementation.

## Current Compatibility

The existing Python shorthand remains valid and is equivalent to a typed single-atom Rydberg-population declaration:

```python
observables = {"pop0": 0}
```

Equivalent Phase 11 declaration:

```python
observables = {
    "pop0": {"type": "rydberg_population", "atom": 0},
}
```

Python atom indices are zero-based in `Register.atoms` order. Julia API calls use one-based atom indices. The Python boundary converts indices before constructing Julia observables.

## First-Scope Observable Types

| Type ID | Meaning | Required parameters | Julia constructor target |
| :--- | :--- | :--- | :--- |
| `rydberg_population` | Single-site `n_i` expectation. | `atom` | `RydbergPopulation` |
| `total_rydberg_population` | Sum of all or selected `n_i` expectations. | optional `atoms` | `TotalRydbergPopulation` |
| `pair_correlation` | `n_i n_j` expectation. | `atoms` with two entries | `PairCorrelation` |
| `connected_pair_correlation` | `<n_i n_j> - <n_i><n_j>`. | `atoms` with two entries | `ConnectedPairCorrelation` |
| `blockade_violation` | Sum of `n_i n_j` over constrained edges. | `edges` | `BlockadeViolation` |
| `bitstring_probability` | Probability of a target bitstring. | `bitstring` | `BitstringProbability` |
| `mwis_cost` | Weighted reward minus edge-violation penalty. | `weights`, `edges`, `penalty` | `MWISCost` |
| `pauli_z` | Signed `Z_i` derived from occupation. | `atom`, optional `convention` | `PauliZ` |
| `pauli_zz` | Two-site `Z_i Z_j` expectation. | `atoms` with two entries, optional `convention` | `PauliZZ` |
| `parity` | Product of signed Z values over atoms. | `atoms`, optional `convention` | `Parity` |

The physical meaning and recommended use cases for these quantities are documented in [`SPEC-PHYS-003-observables.md`](../physics/SPEC-PHYS-003-observables.md).

## Python Declaration Format

Phase 11 Python declarations accept a mapping from output series name to either the existing integer shorthand or a typed declaration object:

```python
observables = {
    "center": {"type": "rydberg_population", "atom": 1},
    "total": {"type": "total_rydberg_population"},
    "edge_0_1": {"type": "pair_correlation", "atoms": [0, 1]},
    "violations": {"type": "blockade_violation", "edges": [[0, 1], [1, 2]]},
    "target": {"type": "bitstring_probability", "bitstring": "101"},
    "cost": {
        "type": "mwis_cost",
        "weights": [1.0, 1.2, 0.9],
        "edges": [[0, 1], [1, 2]],
        "penalty": 4.0,
    },
    "parity_all": {"type": "parity", "atoms": [0, 1, 2], "convention": "ground_plus"},
}
```

Declaration order is the insertion order of the Python mapping. Result series, `observable_names`, and serialized metadata must preserve that order.

## Julia Constructor Contract

Julia constructors accept one-based atom indices and return callable observables. Constructors that need basis information must accept `basis_context`; reduced-basis code should prefer that argument over passing raw basis arrays.

```julia
context = reduced_basis_context(reg; blockade_radius=0.6)
obs = Dict(
    "pop1" => RydbergPopulation(1, length(reg.atoms); basis_context=context),
    "total" => TotalRydbergPopulation(length(reg.atoms); basis_context=context),
    "edge" => PairCorrelation((1, 2), length(reg.atoms); basis_context=context),
)
```

All first-scope constructors must return `Float64` for supported state types. Unsupported state/backend combinations must fail with a validation or diagnostic error; they must not return a silent placeholder value.

## Basis and State Rules

For wavefunctions, diagonal observables use `abs2(state[k])`. For density matrices, they use `real(state[k, k])`. For reduced bases, `k` maps through the shared `BasisContext.basis` bitstring ordering.

Required state handling:

| Solver path | Requirement |
| :--- | :--- |
| Schrodinger CPU | Supported for first-scope observables. |
| Lindblad CPU | Supported for first-scope diagonal observables on density matrices. |
| MCWF CPU | Supported for first-scope observables on normalized trajectory wavefunctions. |
| CUDA Schrodinger | Supported where vectorized GPU implementations exist, otherwise rejected with a documented diagnostic. |
| AMDGPU / Metal | Planned backend names only; observable support must not be implied before parity tests exist. |

## Metadata Contract

Phase 11 result artifacts and run manifests preserve both compatibility and typed metadata. The existing `solver.observables` field may continue to hold shorthand-compatible data, but typed declarations should also be recorded in a stable metadata list:

```json
{
  "observables": [
    {
      "name": "edge_0_1",
      "type": "pair_correlation",
      "parameters": {"atoms": [0, 1]},
      "basis_mode": "reduced",
      "declaration_index": 0
    }
  ]
}
```

Metadata must include observable name, type identifier, validated parameters, atom indices, edge lists where applicable, basis mode, and declaration order. `shared-result/v1` should continue to expose `observable_names` and result series; typed observable metadata belongs in the linked run manifest or a compatible metadata extension.

## Validation Rules

Validation should run before backend initialization whenever possible. Invalid declarations should raise actionable validation errors that identify the observable name and rejected field.

Required validation:

- observable names must be strings and unique by mapping construction;
- `type` must be a supported observable type ID;
- atom indices must be integers in Python zero-based range or Julia one-based range, depending on API surface;
- edge endpoints must be valid atom indices and two-element pairs;
- `bitstring` must fit the register atom count and may be a string such as `"101"` or a non-negative integer within basis bounds;
- `weights` length must match atom count or the explicitly selected atom set;
- `penalty` must be finite and numeric;
- `convention` must be an allowed Pauli-Z convention, initially `ground_plus` for `Z = 1 - 2n`;
- reduced-basis observables must receive the same `BasisContext` used for Hamiltonian and jump-operator construction;
- unsupported solver/backend combinations must fail explicitly before or during solver setup with remediation guidance.

## Verification Checklist

Phase 11 implementation is complete only when tests cover:

- Python shorthand compatibility for `observables={"name": atom_index}`;
- Python typed declarations and invalid declaration errors;
- Julia constructor return values for wavefunction and density-matrix states;
- full-basis versus reduced-basis parity for each first-scope observable;
- shared `BasisContext` use across Hamiltonians, observables, jump operators, and MCWF trajectories;
- Schrodinger, Lindblad, MCWF, and supported CUDA behavior;
- result data, `shared-result/v1`, serialized result artifacts, and run manifests preserving observable names, order, types, and parameters;
- representative Rydberg blockade and MWIS examples.
