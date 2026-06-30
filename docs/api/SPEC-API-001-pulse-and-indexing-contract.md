# Pulse and Indexing Contract

Spec ID: `SPEC-API-001`
Status: `Current`
Roadmap: Phase 8
Version: `pulse-contract/v1`
Last reviewed: 2026-06-30


This document defines the current Python SDK pulse input contract and atom indexing semantics. For physical waveform selection and parameter guidance, see [`SPEC-PHYS-002-pulse-shapes.md`](../physics/SPEC-PHYS-002-pulse-shapes.md).

## Atom Indexing

Python-facing Sagittarius APIs use zero-based atom indices in the order supplied to `Register(atoms=[...])`.

- `Register.atoms[0]` is Python atom index `0`.
- Local pulse dictionaries use these same zero-based indices.
- Observable dictionaries use these same zero-based indices.
- Julia internals use one-based indices, and the Python SDK converts observable indices with `idx + 1` at the boundary.
- Local pulse vectors are passed to Julia in `Register.atoms` order; they are not reversed.

For a two-atom register `[a0, a1]`, a local Rabi pulse `{0: 1.0, 1: 0.0}` drives `a0` and leaves `a1` undriven. A list pulse `[1.0, 0.0]` has the same meaning.

## Pulse Inputs

`PulseSequence.omega` and `PulseSequence.delta` accept explicit addressing wrappers and legacy shorthand forms:

| Input form | Meaning | Validation |
| :--- | :--- | :--- |
| `GlobalPulse(value)` / `Pulse.global_(value)` | Explicit global value or `PulseNode` applied to every atom. | Value must be numeric or a `PulseNode`. |
| `LocalPulseVector(values)` / `Pulse.local(values)` | Explicit local vector/list or sparse dict in `Register.atoms` order. | List length must equal atom count; dict keys are zero-based atom indices; values must be numeric or `PulseNode`. |
| `CallablePulse(f)` / `Pulse.callable(f)` | Explicit time-dependent local vector callback. | Called as `f(t)` and must return exactly one numeric value per atom. |
| Numeric scalar | Legacy shorthand for global value applied to every atom. | Must be numeric and not boolean. |
| `PulseNode` | Global time-dependent pulse applied to every atom. | Must be one of the SDK pulse node types. |
| `list` | Local values in `Register.atoms` order. | Length must equal atom count; each value must be numeric or a `PulseNode`. |
| `dict` | Sparse local values keyed by zero-based atom index. | Keys must be integer atom indices in range; missing atoms default to `0.0`; values must be numeric or a `PulseNode`. |
| callable | Time-dependent local vector callback. | Called as `f(t)` and must return exactly one numeric value per atom in `Register.atoms` order. |

Callable pulses are validated before backend initialization using the simulation start time. The Julia bridge also checks vector length at runtime for callback evaluations during integration.

## Examples

```python
from sagittarius import Atom, Register, PulseSequence, Pulse, GlobalPulse

reg = Register([Atom(0, 0, 0), Atom(5, 0, 0)])

# Explicit global scalar drive.
PulseSequence(omega=Pulse.global_(1.0), delta=GlobalPulse(0.0))

# Legacy global scalar shorthand.
PulseSequence(omega=1.0, delta=0.0)

# Explicit local list drive: atom 0 driven, atom 1 off.
PulseSequence(omega=Pulse.local([1.0, 0.0]))

# Legacy local list shorthand.
PulseSequence(omega=[1.0, 0.0])

# Sparse local dictionary drive with the same meaning.
PulseSequence(omega={0: Pulse.constant(1.0, duration=1.0)})

# Explicit callable local vector in Register.atoms order.
PulseSequence(omega=Pulse.callable(lambda t: [1.0, 0.0]))

# Legacy callable shorthand.
PulseSequence(omega=lambda t: [1.0, 0.0])
```
