# Python Executable Experiment Recipes

The recipes in [`workspace/examples/recipes/`](../../../workspace/examples/recipes/) are short,
Julia-backed Phase 15 workflows for users who want a reproducible result
artifact rather than an isolated API snippet. They run on the CPU-default
backend, use only the public Python SDK, and write both a `result-artifact/v1`
file and a convenient copy of its embedded `run-manifest/v1`.

They are not Phase 16 benchmarks: their outputs do not establish performance,
scalability, hardware-calibration, or optimization-quality claims.

## Prerequisites

Use either the source-install path or an equivalent independent Python project
with Sagittarius installed and Julia dependencies resolved. From a source
checkout:

```bash
cd Sagittarius/sagittarius_py
uv sync
uv run python -m juliapkg resolve
```

Each command below uses an explicit output directory so reruns do not overwrite
another recipe's evidence.

## Rabi Flip

```bash
uv run python ../workspace/examples/recipes/rabi.py --output-dir ../artifacts/rabi
```

The recipe drives one atom for half a Rabi period. It checks that the final
Rydberg population is near one and writes a five-sample population trajectory.

## Two-Atom Blockade

```bash
uv run python ../workspace/examples/recipes/two_atom_blockade.py --output-dir ../artifacts/two-atom-blockade
```

Two atoms separated by `0.5` use `blockade_radius=0.6`. The recipe checks the
three-state reduced basis and records atom populations, total population, and
the forbidden double-excitation observable, which remains zero.

## Landau-Zener Sweep

```bash
uv run python ../workspace/examples/recipes/landau_zener.py --output-dir ../artifacts/landau-zener
```

This single-atom example uses a `Pulse.ramp` detuning sweep from `-4` to `4`
with a constant drive. Its output is a 17-sample population trajectory. The
final transfer probability depends on the stated schedule and is not presented
as a universal Landau-Zener accuracy claim.

## Open-System Decay and Dephasing

```bash
uv run python ../workspace/examples/recipes/open_system_decay.py --output-dir ../artifacts/open-system-decay
```

An initially excited atom evolves under local Markovian decay (`gamma=0.5`) and
pure dephasing (`gamma_phi=0.25`). With zero drive and a diagonal initial
state, pure dephasing does not alter the population, so the recipe can compare
the final population with `exp(-gamma * duration)` while its manifest records
both noise rates. This covers the currently supported local Markovian channels;
custom and correlated channels are
not available yet.

## Small UDG/MWIS Workflow

```bash
uv run python ../workspace/examples/recipes/mwis_udg.py --output-dir ../artifacts/mwis-udg
```

The recipe creates a three-node weighted unit-disk graph, uses local detuning
ramps in register order, runs a blockade-reduced schedule, and writes typed
MWIS-cost, blockade-violation, and total-population observables. It also prints
the most likely final bitstring from the saved readout distribution and the
exact weight of this tiny enumerated reference instance. The comparison is for
interpretation of this example only, not an optimization-performance claim.

## State Preparation

Recipes can use a named preparation directly:

```python
from sagittarius import all_ground_state, single_excitation_state

prepared = all_ground_state(simulation)
result = simulation.run(prepared, 0.0, 1.0, observables={"population": 0})
# single_excitation_state(simulation, 0) prepares atom 0 instead.
```

The saved artifact retains `state-preparation/v1` metadata in its result metadata, diagnostics, and `manifest["initial_state"]["preparation"]`. A requested bitstring that is excluded by a blockade-reduced basis fails with an actionable validation error.

## Inspecting Output

Every recipe prints paths such as:

```text
recipe: rabi
result artifact: ../artifacts/rabi/rabi.result.json
manifest copy: ../artifacts/rabi/rabi.run-manifest.json
final_rydberg_population: 1.0
```

The result file is the authoritative envelope. Load it through the public API:

```python
from sagittarius import load_result

result = load_result("../artifacts/rabi/rabi.result.json")
print(result.manifest["schema_version"])
print(result.data["rydberg_population"][-1])
```

The manifest records the actual register, pulse, solver, backend diagnostics,
versions, output grid, and readout metadata. Keep the result artifact whenever
the numerical output is used in a report or subsequent analysis.


## Visualization Tasks

### Inspect a saved readout artifact

```python
from sagittarius import load_result
from sagittarius.viz import plot_bitstring_distribution

result = load_result("../artifacts/rabi/rabi.result.json")
ax = plot_bitstring_distribution(result, top_k=8, sort_by="probability")
ax.figure.savefig("../artifacts/rabi/final-bitstrings.png", dpi=150)
```

This reads the existing result-artifact/v1 envelope and plots its stored final-state distribution; it does not rerun a solver or initialize Julia.

### Check geometry and a pulse before solving

```python
import numpy as np
from sagittarius import Register, PulseSequence
from sagittarius.viz import plot_pulse_waveform, plot_register

register = Register.chain(3, spacing=1.0)
plot_register(register, blockade_radius=1.2, labels=True)
ax, omega = plot_pulse_waveform(
    PulseSequence(omega=1.0), time_grid=np.linspace(0.0, 1.0, 101)
)
ax.figure.savefig("preflight-pulse.png", dpi=150)
```

These pre-solver checks consume Python-side geometry and pulse declarations only. They help inspect intended inputs, but they are not numerical verification or benchmark evidence.
