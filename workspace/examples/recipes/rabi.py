"""One-atom Rabi-flip recipe with a saved result artifact."""

from __future__ import annotations

import numpy as np

from sagittarius import Atom, PulseSequence, Register, Simulation, SolverConfig

from common import RecipeRun, output_directory, print_recipe_summary, save_recipe_result


def run_recipe(output_dir) -> RecipeRun:
    """Run a half-period Rabi flip and persist its observable trajectory."""
    simulation = Simulation(
        Register([Atom(0.0, 0.0, 0.0)], C6=0.0),
        PulseSequence(omega=2.0 * np.pi, delta=0.0),
        SolverConfig(reltol=1e-8, abstol=1e-10, saveat=5),
    )
    result = simulation.run(
        np.array([1.0, 0.0], dtype=complex),
        0.0,
        0.5,
        observables={"rydberg_population": 0},
    )
    final_population = float(result.data["rydberg_population"][-1])
    if not np.isclose(final_population, 1.0, atol=1e-3):
        raise RuntimeError(f"Rabi reference check failed: expected final population near 1, got {final_population}.")
    run = save_recipe_result(result, output_dir, "rabi")
    print_recipe_summary("rabi", run, {"final_rydberg_population": round(final_population, 8)})
    return run


if __name__ == "__main__":
    run_recipe(output_directory("rabi"))
