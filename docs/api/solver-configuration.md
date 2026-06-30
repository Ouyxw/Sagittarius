# Solver Configuration Contract

This page defines the planned Phase 12 numerical solver configuration contract. It is an implementation target, not a claim that every option below is already active. The current Python `SolverConfig` exposes `method`, `reltol`, `abstol`, `blockade_radius`, open-system settings, MCWF trajectory count, and GPU settings; the Julia solver paths currently use `Tsit5()` internally.

Phase 12 connects the public solver configuration to the Julia OrdinaryDiffEq algorithm actually used by every supported execution path.

## Current Compatibility

Existing callers that do not configure a method must continue to behave as they do today:

```python
from sagittarius import SolverConfig

cfg = SolverConfig(reltol=1e-8, abstol=1e-8)
```

The backward-compatible default is tolerance-controlled adaptive `Tsit5`.

Until Phase 12 is implemented, changing `SolverConfig.method` should not be treated as evidence that the backend used a different OrdinaryDiffEq algorithm. Phase 12 is complete only when requested and effective solver metadata agree and tests prove dispatch across applicable solver paths.

## Public Method Names

Phase 12 should support only this explicit whitelist:

| Method | Stepping mode | Intended use | Notes |
| :--- | :--- | :--- | :--- |
| `Tsit5` | Adaptive | Default general-purpose nonstiff integration. | Honors `reltol` and `abstol`. |
| `Vern9` | Adaptive | Higher-order accuracy checks and tighter-tolerance studies. | Usually more expensive per step; useful when high precision matters. |
| `RK4` | Fixed step | Reproducible fixed-step comparisons and simple baselines. | Requires `adaptive=False` and finite positive `dt`. |

Method names are stable public strings. Sagittarius must not evaluate arbitrary Julia expressions from user input. Unsupported names must fail with an actionable validation error that lists supported methods.

## Python Configuration Target

Phase 12 extends `SolverConfig` with `adaptive` and `dt`:

```python
from sagittarius import SolverConfig

# Default adaptive Tsit5.
cfg = SolverConfig(method="Tsit5", adaptive=True, reltol=1e-8, abstol=1e-8)

# Higher-order adaptive method.
cfg_high_accuracy = SolverConfig(method="Vern9", adaptive=True, reltol=1e-10, abstol=1e-10)

# Fixed-step RK4.
cfg_fixed = SolverConfig(method="RK4", adaptive=False, dt=1e-3)
```

`adaptive=True` is the default. `dt=None` is the default for adaptive methods.

## Valid Combinations

| Configuration | Valid | Behavior |
| :--- | :---: | :--- |
| `method="Tsit5", adaptive=True, dt=None` | yes | Adaptive Tsit5 controlled by `reltol` and `abstol`. |
| `method="Tsit5", adaptive=True, dt=<positive>` | no | `dt` is not part of the public adaptive contract; reject unless a future schema explicitly defines it. |
| `method="Vern9", adaptive=True, dt=None` | yes | Adaptive Vern9 controlled by `reltol` and `abstol`. |
| `method="Vern9", adaptive=False` | no | Fixed-step Vern9 is not in the Phase 12 public contract. |
| `method="RK4", adaptive=False, dt=<positive>` | yes | Fixed-step RK4. Accuracy is governed by `dt`. |
| `method="RK4", adaptive=True` | no | RK4 must be explicit fixed-step in this contract. |
| `method="RK4", adaptive=False, dt=None` | no | Fixed-step RK4 requires a finite positive `dt`. |
| unsupported `method` | no | Reject before solver execution where possible. |

Invalid combinations must fail explicitly. No execution path may silently substitute `Tsit5` while reporting another method.

## Julia Resolver Contract

The Julia backend should expose an internal whitelist resolver that maps stable public names to OrdinaryDiffEq algorithm instances. The resolver should be the only place where public method strings become Julia algorithm objects.

Conceptual target:

```julia
resolve_solver_algorithm("Tsit5"; adaptive=true, dt=nothing)  # Tsit5()
resolve_solver_algorithm("Vern9"; adaptive=true, dt=nothing)  # Vern9()
resolve_solver_algorithm("RK4"; adaptive=false, dt=1e-3)      # RK4()
```

The resolver must reject unsupported method names and incompatible stepping options with a clear error message. It must not call `eval`, parse user-provided Julia code, or fall back to another algorithm.

## Solver-Path Coverage

Method dispatch applies to every solver path that accepts `SolverConfig` semantics:

| Path | Phase 12 requirement |
| :--- | :--- |
| Schrodinger CPU | Honor selected method and stepping options. |
| Lindblad CPU | Honor selected method and stepping options. |
| MCWF CPU | Honor selected method and stepping options for trajectory evolution, or reject unsupported combinations explicitly. |
| CUDA Schrodinger | Honor selected method where supported by the CUDA path, or reject with a documented diagnostic. |
| AMDGPU / Metal | Planned backend names only; do not report method support before backend parity exists. |

A method must not be documented as supported if any applicable execution path silently ignores it.

## Accuracy and Cost Guidance

`reltol` and `abstol` primarily control adaptive methods. Tightening them usually increases cost but can reduce integration error until other modeling or floating-point limits dominate.

`Tsit5` is the default because it is a practical adaptive method for regular nonstiff workflows. `Vern9` is intended for higher-accuracy comparisons and may cost more per accepted step. `RK4` is useful when a fixed time step is required for reproducibility or comparison against fixed-step references; its accuracy is governed by `dt`, so reducing `dt` is the primary convergence control.

For production or publication-facing runs, compare observables under tighter tolerances or smaller `dt` and record the effective solver metadata with the result artifact.

## Metadata Contract

Diagnostics, run manifests, serialized result artifacts, and relevant `solver_start` events should record both requested and effective configuration. Requested and effective values must agree unless the run failed before execution.

Target shape:

```json
{
  "solver": {
    "method": "RK4",
    "adaptive": false,
    "dt": 0.001,
    "reltol": 1e-8,
    "abstol": 1e-8,
    "effective_method": "RK4",
    "effective_adaptive": false,
    "effective_dt": 0.001
  }
}
```

Metadata must never claim `RK4` or `Vern9` when the backend used `Tsit5`. If a path rejects a method, diagnostics should include an actionable issue code and remediation.

## Validation Rules

Validation should run before Julia backend initialization where possible:

- `method` must be one of `Tsit5`, `Vern9`, or `RK4`;
- `adaptive` must be a boolean;
- `dt` must be `None` for adaptive Phase 12 methods;
- fixed-step `RK4` requires `adaptive=False` and finite positive `dt`;
- `reltol` and `abstol` must be finite positive numbers for adaptive methods;
- unsupported method/backend/solver-path combinations must fail explicitly with remediation guidance;
- result metadata must be generated from the effective backend configuration, not only from the requested Python object.

## Verification Checklist

Phase 12 implementation is complete only when tests prove:

- changing `SolverConfig.method` changes the OrdinaryDiffEq algorithm used by Julia;
- `Tsit5` and `Vern9` run adaptively and honor `reltol`/`abstol`;
- `RK4` runs only as fixed-step with `adaptive=False` and positive `dt`;
- unsupported names and invalid option combinations fail before solver execution where possible;
- Schrodinger, Lindblad, MCWF, CPU, and supported CUDA paths either honor the selected method or reject it explicitly;
- diagnostics, `run-manifest/v1`, result artifacts, and `solver_start` events report effective method, `adaptive`, and `dt` accurately;
- default behavior remains backward-compatible with adaptive `Tsit5`;
- representative numerical sanity checks compare observables across methods at suitable tolerances or step sizes.
