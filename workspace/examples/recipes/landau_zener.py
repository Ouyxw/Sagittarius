"""Single-atom Landau-Zener sweep recipe with explicit pulse metadata."""

from __future__ import annotations

import numpy as np

from sagittarius import Atom, Pulse, PulseSequence, Register, Simulation, SolverConfig

from common import RecipeRun, output_directory, print_recipe_summary, save_recipe_result


def run_recipe(output_dir) -> RecipeRun:
    """Sweep detuning through resonance and persist the population trajectory."""
    duration = 4.0
    simulation = Simulation(
        Register([Atom(0.0, 0.0, 0.0)], C6=0.0),
        PulseSequence(omega=1.0, delta=Pulse.ramp(start=-4.0, end=4.0, duration=duration)),
        SolverConfig(reltol=1e-8, abstol=1e-10, saveat=17),
    )
    result = simulation.run(
        np.array([1.0, 0.0], dtype=complex),
        0.0,
        duration,
        observables={"rydberg_population": 0},
    )
    final_population = float(result.data["rydberg_population"][-1])
    if not 0.0 <= final_population <= 1.0:
        raise RuntimeError(f"Landau-Zener population is outside [0, 1]: {final_population}.")
    run = save_recipe_result(result, output_dir, "landau_zener")
    print_recipe_summary("landau_zener", run, {"final_rydberg_population": round(final_population, 8)})
    return run


if __name__ == "__main__":
    run_recipe(output_directory("landau_zener"))
