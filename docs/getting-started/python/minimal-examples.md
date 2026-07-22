# Python Minimal Examples with Expected Output

These Python examples are intended for quick user verification. Examples marked **backend-free** should run without initializing Julia. Examples marked **Julia-backed** require a working Julia/PythonCall environment. For Julia-native examples, see [Julia minimal examples](../julia/minimal-examples.md).

## 1. Runtime Diagnostics Shape (backend-free)

```python
from sagittarius import doctor

report = doctor()
print(report["schema_version"])
print(report["requested_backend"])
print(report["available"])
print(report["backend_probe"])
```

Expected output shape:

```text
doctor/v2.1
CPU
True
None
```

`doctor()` does not initialize Julia unless `initialize_backend=True` is passed.

## 2. Local Addressing Validation (backend-free)

```python
from sagittarius import Atom, Register, Simulation, PulseSequence

reg = Register([Atom(0, 0, 0), Atom(5, 0, 0)])
sim = Simulation(reg, PulseSequence(omega=[1.0]))

try:
    sim.validate_inputs(sample_time=0.0)
except ValueError as exc:
    print(exc)
```

Expected output:

```text
PulseSequence.omega list length 1 does not match 2 atoms
```

Local pulse lists must have one entry per atom in `Register.atoms` order.

## 3. Local Indexing Semantics (backend-free)

```python
from sagittarius import Atom, Register, Simulation, PulseSequence

reg = Register([Atom(0, 0, 0), Atom(5, 0, 0)])
sim = Simulation(reg, PulseSequence(omega={0: 1.0, 1: 0.0}))
sim.validate_inputs(sample_time=0.0, observables={"atom0": 0, "atom1": 1})
print("valid")
```

Expected output:

```text
valid
```

Python atom indices are zero-based and follow `Register.atoms` order. Julia boundary calls convert to one-based indices internally.

## 4. One-Atom Rabi Flip (Julia-backed)

```python
import numpy as np
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

reg = Register([Atom(0.0, 0.0, 0.0)], C6=0.0)
seq = PulseSequence(omega=2.0 * np.pi, delta=0.0)
cfg = SolverConfig(reltol=1e-7, abstol=1e-7)

sim = Simulation(reg, seq, cfg)
psi0 = np.array([1.0, 0.0], dtype=complex)
result = sim.run(psi0, 0.0, 0.5, observables={"pop_atom_0": 0})

print(round(result.data["pop_atom_0"][-1], 3))
```

Expected output:

```text
1.0
```

This is a half-period Rabi flip for a single atom with `omega = 2π`. Small numerical variation is expected if solver tolerances change.

## 5. Three-Atom Blockade Basis Size (Julia-backed)

```python
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

reg = Register([
    Atom(0.0, 0.0, 0.0),
    Atom(0.5, 0.0, 0.0),
    Atom(1.0, 0.0, 0.0),
], C6=100.0)

sim = Simulation(
    reg,
    PulseSequence(omega=1.0, delta=0.0),
    SolverConfig(blockade_radius=0.6),
)

print(sim.validate())
```

Expected output:

```text
5
```

The nearest-neighbor blockade removes states where adjacent atoms are simultaneously excited.

## 6. Serialization Envelope (backend-free)

```python
import json
import tempfile
from sagittarius import SimulationResult, load_result

result = SimulationResult(
    {"t": [0.0, 1.0], "pop": [0.0, 1.0]},
    metadata={"example": "minimal"},
    diagnostics={"backend": "CPU"},
)

with tempfile.NamedTemporaryFile(suffix=".json") as f:
    result.save(f.name)
    with open(f.name) as saved:
        envelope = json.load(saved)
    loaded = load_result(f.name)
    print(envelope["schema_version"])
    print(loaded.data["pop"][-1])
    print(loaded.metadata["example"])
    print(loaded.diagnostics["backend"])
```

Expected output:

```text
result-artifact/v1
1.0
minimal
CPU
```

## 7. Specialized Register Constructors (backend-free)

```python
from sagittarius import Register

chain = Register.chain(3, spacing=0.5, C6=100.0)
lattice = Register.square_lattice(2, 2, spacing=1.0)
udg = Register.udg([(0.0, 0.0), (0.5, 0.0), (2.0, 0.0)], blockade_radius=1.0)

print(chain.topology["kind"])
print(len(lattice.atoms))
print(udg.geometry_summary(blockade_radius=1.0)["blockade_edge_count"])
```

Expected output:

```text
chain
4
1
```

## 8. Dense-vs-Reduced Validation (backend-free)

```python
from sagittarius import Register, PulseSequence, dense_vs_reduced_validation

report = dense_vs_reduced_validation(
    Register.chain(3, spacing=0.5, C6=10.0),
    PulseSequence(omega=[0.2, 0.3, 0.4], delta=[-0.1, 0.0, 0.2]),
    blockade_radius=0.6,
    duration=0.7,
)

print(report["ok"])
print(report["basis"])
print(report["reduced_basis_pruning_ratio"])
```

Expected output:

```text
True
[0, 1, 2, 4, 5]
0.375
```


## 9. Visualization-Ready Observable Series (Julia-backed)

The current Python SDK exposes `SimulationResult.plot()` and `SimulationResult.to_pandas()` plus the public `sagittarius.viz` register, pulse, result, diagnostic, export, and report helpers. The example below uses the lightweight result API and avoids opening a GUI window.

```python
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

reg = Register([Atom(0.0, 0.0, 0.0)], C6=0.0)
seq = PulseSequence(omega=2.0 * np.pi, delta=0.0)
cfg = SolverConfig(reltol=1e-7, abstol=1e-7, saveat=[0.0, 0.25, 0.5])

sim = Simulation(reg, seq, cfg)
psi0 = np.array([1.0, 0.0], dtype=complex)
result = sim.run(psi0, 0.0, 0.5, observables={"pop_atom_0": 0})

# Current lightweight plotting helper. Use show=False for scripts and tests.
result.plot(show=False)
artifact_dir = Path(__file__).with_name("artifacts")
artifact_dir.mkdir(parents=True, exist_ok=True)
figure_path = artifact_dir / "observable_trajectory.png"
plt.gcf().savefig(figure_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"saved figure: {figure_path}")

df = result.to_pandas()
print(list(df.columns))
print([round(value, 2) for value in df["pop_atom_0"].tolist()])
```

Example output shape; the figure path depends on the script location:

```text
saved figure: <script-dir>/artifacts/observable_trajectory.png
['pop_atom_0', 't']
[0.0, 0.5, 1.0]
```

Small numerical variation is expected if solver tolerances, output times, or matplotlib/pandas versions change. The public visualization API also provides register layouts, pulse waveforms, population heatmaps, bitstring distributions, correlations, spatial snapshots, figure export, and lightweight reports; the examples below cover a compact subset.

## 10. Final-State Sampling with a Seed (backend-free)

`SimulationResult.sample()` draws final bitstrings from readout metadata. A seed
makes the sampling sequence reproducible; the returned mapping is
`measurement-samples/v1` data and records the requested/effective seed.

```python
from sagittarius import SimulationResult

result = SimulationResult(
    {"t": [0.0, 1.0], "pop0": [0.0, 0.5]},
    metadata={
        "readout": {
            "schema_version": "readout-metadata/v1",
            "final_bitstring_probabilities": {"0": 0.25, "1": 0.75},
        }
    },
    manifest={"schema_version": "run-manifest/v1", "readout": {"basis_mode": "full"}},
)

samples = result.sample(shots=12, seed=1234)
print(samples["schema_version"])
print(samples["seed"])
print(sum(samples["counts"].values()))
```

Expected output:

```text
measurement-samples/v1
1234
12
```

Sampling requires a result with final-state readout metadata. Reduced-basis
results record whether forbidden bitstrings were excluded; inspect the returned
`basis_mode` and `forbidden_bitstrings_excluded` fields before interpreting
counts.

## 11. MCWF Seed, Output Grid, and Individual Trajectories (Julia-backed)

`saveat` accepts an output sample count or an explicit time array. Sagittarius
records the requested value and normalized `effective_saveat` in the run
manifest. Set `store_trajectories=True` with MCWF to retain individual samples
as `trajectory-data/v1`, whose axes are `(trajectory, time)`.

```python
import numpy as np
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

config = SolverConfig(
    gamma=0.4,
    use_mc=True,
    n_trajectories=8,
    seed=20260716,
    saveat=5,
    store_trajectories=True,
)
result = Simulation(
    Register([Atom(0.0, 0.0, 0.0)], C6=0.0),
    PulseSequence(omega=0.0, delta=0.0),
    config,
).run(
    np.array([0.0, 1.0], dtype=complex),
    0.0,
    1.0,
    observables={"pop": 0},
)

storage = result.manifest["solver"]["trajectory_storage"]
print(len(result.manifest["solver"]["effective_saveat"]))
print(result.trajectories["pop"].shape)
print(storage["schema_version"])
print(np.allclose(result.data["pop"], result.trajectories["pop"].mean(axis=0)))
```

Expected output:

```text
5
(8, 5)
trajectory-data/v1
True
```

Trajectory storage can be large. Leave `store_trajectories=False` unless
individual trajectories are needed; aggregate observables remain available in
`result.data` either way.

## 12. Register, Pulse, Observable, and Figure Export (backend-free)

The public `sagittarius.viz` module provides backend-free register geometry,
pulse waveform, observable, population, bitstring, correlation, diagnostic,
and export helpers. This compact example uses register, pulse, and observable
plots, then writes a PNG plus provenance sidecar.

```python
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sagittarius import PulseSequence, Register, SimulationResult
from sagittarius.viz import export_figure, plot_observables, plot_pulse_waveform, plot_register

register = Register.chain(3, spacing=0.5, C6=10.0)
result = SimulationResult({"t": [0.0, 0.5, 1.0], "pop0": [0.0, 0.5, 1.0]})

fig, axes = plt.subplots(1, 3, figsize=(12, 3))
plot_register(register, blockade_radius=0.6, ax=axes[0])
plot_pulse_waveform(
    PulseSequence(omega=1.0, delta=0.0),
    time_grid=np.linspace(0.0, 1.0, 5),
    field="omega",
    ax=axes[1],
)
plot_observables(result, names=["pop0"], ax=axes[2])

paths = export_figure(fig, str(Path("artifacts") / "minimal-viz"), formats=["png"])
plt.close(fig)
print(sorted(paths))
```

Expected output:

```text
['json', 'png']
```

`export_figure()` writes `chart-export/v1` provenance metadata beside the
figure. These are exploratory visualizations, not benchmark or hardware
performance evidence. See the visualization API reference for the complete
public catalog and result-specific helpers.
