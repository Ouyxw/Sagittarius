# Pulse Shapes in Neutral-Atom Simulations

Spec ID: `SPEC-PHYS-002`
Status: `Current`
Roadmap: Phase 8, Phase 10
Version: `pulse-shapes/v1`
Last reviewed: 2026-06-30


Pulse shapes define the time dependence of `PulseSequence.omega` and `PulseSequence.delta`. Sagittarius does not attach units to pulse parameters; amplitudes use the same angular-frequency unit as the Hamiltonian coefficients, and durations use the simulation time unit. See [`SPEC-PHYS-001-units.md`](SPEC-PHYS-001-units.md) for the unit convention.

This page explains the physical intent of the built-in pulse nodes and how to choose between global, local, piecewise, and callable pulse definitions. The API-level input contract and indexing rules are documented in [`SPEC-API-001-pulse-and-indexing-contract.md`](../api/SPEC-API-001-pulse-and-indexing-contract.md).

## Supported Pulse Nodes

| Python factory | Parameters | Shape inside `0 <= t <= duration` | Typical use |
| :--- | :--- | :--- | :--- |
| `Pulse.constant(value, duration)` | `value`, `duration` | Constant value. | Baseline Rabi drive, hold segment, idle segment with `value=0.0`. |
| `Pulse.ramp(start, end, duration)` | `start`, `end`, `duration` | Linear interpolation from `start` to `end`. | Detuning sweeps, annealing schedules, amplitude ramps. |
| `Pulse.gaussian(amplitude, sigma, duration, mu=None)` | `amplitude`, `sigma`, `duration`, optional `mu` | Gaussian envelope centered at `mu`; defaults to `duration / 2`. | Smooth local excitation, spectral narrowing, shaped drive pulses. |
| `Pulse.sin_squared(amplitude, duration)` | `amplitude`, `duration` | `amplitude * sin(pi * t / duration)^2`. | Smooth turn-on/turn-off with zero endpoints. |
| `Pulse.blackman(amplitude, duration)` | `amplitude`, `duration` | Blackman window scaled by `amplitude`. | Smooth finite pulse with reduced spectral leakage. |
| `Pulse.sinc(amplitude, width, duration)` | `amplitude`, `width`, `duration` | Sinc centered at `duration / 2`; `width` sets the time scale. | Frequency-selective drive or filter-like test waveform. |
| `Pulse.piecewise([...])` | Ordered list of `PulseNode` segments. | Concatenates segments in order. | Multi-stage protocols on one atom or global channel. |

Each built-in `PulseNode` returns `0.0` outside its own duration. In a `Pulse.piecewise([...])`, each segment uses local segment time: the second segment starts at local `t=0` when the first segment ends.

## Global and Local Addressing

Use a global pulse when every atom receives the same waveform:

```python
from sagittarius import Pulse, PulseSequence

seq = PulseSequence(
    omega=Pulse.global_(Pulse.sin_squared(amplitude=1.0, duration=2.0)),
    delta=0.0,
)
```

Use a local vector when atoms receive different waveforms. List order is exactly `Register.atoms` order:

```python
seq = PulseSequence(
    omega=Pulse.local([
        Pulse.gaussian(amplitude=1.0, sigma=0.1, duration=0.5),
        Pulse.constant(0.0, duration=0.5),
    ]),
    delta=0.0,
)
```

Use a sparse local dictionary when only selected atoms differ. Missing atoms default to `0.0`:

```python
seq = PulseSequence(
    omega=Pulse.local({
        0: Pulse.ramp(start=0.0, end=1.0, duration=1.0),
    }),
)
```

Python atom indices are zero-based. Atom `0` means `Register.atoms[0]`.

## Multiple Pulses on One Atom

Use `Pulse.piecewise` to apply different pulse shapes to the same atom at different times:

```python
atom0_drive = Pulse.piecewise([
    Pulse.constant(0.5, duration=0.2),
    Pulse.gaussian(amplitude=1.5, sigma=0.1, duration=0.4),
    Pulse.ramp(start=1.5, end=0.0, duration=0.3),
])

seq = PulseSequence(
    omega=Pulse.local([
        atom0_drive,
        0.0,
    ]),
)
```

The first atom receives the constant segment for `0.2` time units, then the Gaussian segment for `0.4`, then the ramp for `0.3`. The second atom is undriven.

`duration` is the length of a segment, not an absolute start time. Use `Pulse.piecewise` to express ordering.

## Callable Waveforms

Use `Pulse.callable(f)` when the waveform is easier to compute directly or comes from an external schedule generator. A callable pulse returns a numeric local vector:

```python
seq = PulseSequence(
    omega=Pulse.callable(lambda t: [t, 0.5 * t]),
)
```

For a two-atom register, this means atom `0` receives `omega=t` and atom `1` receives `omega=0.5*t` at simulation time `t`.

Callable pulses must return one numeric value per atom in `Register.atoms` order. They should not return `PulseNode` objects. This is invalid:

```python
Pulse.callable(lambda t: [Pulse.gaussian(1.0, 0.1, 0.5), Pulse.constant(1.0, 0.5)])
```

Use `Pulse.local([...])` or `Pulse.piecewise([...])` when you want to compose built-in pulse nodes.

## Choosing a Shape

| Modeling need | Recommended shape |
| :--- | :--- |
| Isolated Rabi oscillation or constant detuning. | `Pulse.constant` or scalar shorthand. |
| Adiabatic detuning sweep or linear annealing schedule. | `Pulse.ramp`, often assigned to `delta`. |
| Smooth local excitation with a peak near a chosen time. | `Pulse.gaussian`. |
| Smooth pulse with zero endpoints. | `Pulse.sin_squared`. |
| Smooth finite pulse with stronger endpoint suppression. | `Pulse.blackman`. |
| Frequency-selective or filter-like test waveform. | `Pulse.sinc`. |
| Multi-stage drive or detuning protocol. | `Pulse.piecewise`. |
| Optimizer-generated schedule or custom formula. | `Pulse.callable`, returning numeric values. |

For adiabatic or annealing workflows, pair the waveform choice with observable convergence checks. Smooth waveforms reduce abrupt switching artifacts, but they do not by themselves guarantee adiabaticity.

## Parameter Guidance

- `amplitude`, `value`, `start`, and `end` use angular-frequency units, such as `rad/us` under the convention in [`SPEC-PHYS-001-units.md`](SPEC-PHYS-001-units.md).
- `duration`, `sigma`, `mu`, and `width` use the simulation time unit.
- `mu` in `Pulse.gaussian` is the center time within the segment. If omitted, it is `duration / 2`.
- `sigma` controls the Gaussian width; choose a duration long enough that the tails are acceptable for the intended approximation.
- `width` in `Pulse.sinc` controls the sinc time scale around the segment midpoint.
- Ordinary frequencies such as MHz must be converted to angular frequencies before use with `omega`, `delta`, or pulse amplitudes.

## Common Pitfalls

- Returning `PulseNode` objects from `Pulse.callable`; callable pulses must return numbers.
- Returning the wrong vector length from a callable or local list.
- Assuming atoms are sorted by coordinates; local vectors follow `Register.atoms` order.
- Treating `duration` as an absolute start time; use `Pulse.piecewise` for sequential timing.
- Forgetting that built-in pulse nodes evaluate to `0.0` outside their duration.
- Mixing ordinary frequency and angular-frequency units.
- Using a UDG graph radius without also passing the intended `SolverConfig.blockade_radius` when basis reduction is desired.
