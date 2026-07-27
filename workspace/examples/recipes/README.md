# Sagittarius Executable Experiment Recipes

These Phase 15 recipes are short, CPU-first, Julia-backed workflows. Each
creates a `result-artifact/v1` JSON result and an adjacent copy of its embedded
`run-manifest/v1` manifest. They are reproducible experiment examples, not
benchmark artifacts or hardware-calibration workflows.

From a source checkout after resolving the Python/Julia environment:

```bash
cd sagittarius_py
uv run python ../workspace/examples/recipes/rabi.py --output-dir ../artifacts/rabi
```

- `rabi.py`: one-atom half-period Rabi flip with an analytic final-population check.
- `two_atom_blockade.py`: blockade-reduced two-atom dynamics and forbidden-double-excitation check.
- `landau_zener.py`: a detuning sweep through resonance using a `Pulse.ramp` schedule.
- `open_system_decay.py`: local Markovian Rydberg decay and pure dephasing with an analytic population reference.
- `mwis_udg.py`: a small weighted UDG/MWIS AQC workflow with readout distribution and exact small-instance reference.

- `wheel_installed_mwis_udg.py`: self-contained template for an external project using an installed wheel.
See the [Python experiment recipes guide](../../../docs/getting-started/python/experiment-recipes.md)
for expected output shapes and interpretation boundaries.
