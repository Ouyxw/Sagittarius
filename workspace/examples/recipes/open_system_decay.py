"""One-atom local Markovian decay recipe using the Lindblad solver path."""

from __future__ import annotations

import math

import numpy as np

from sagittarius import Atom, PulseSequence, Register, Simulation, SolverConfig

from common import RecipeRun, output_directory, print_recipe_summary, save_recipe_result


def run_recipe(output_dir) -> RecipeRun:
    """Evolve an initially excited atom under local Rydberg decay and dephasing."""
    gamma = 0.5
    duration = 2.0
    gamma_phi = 0.25
    simulation = Simulation(
        Register([Atom(0.0, 0.0, 0.0)], C6=0.0),
        PulseSequence(omega=0.0, delta=0.0),
        SolverConfig(gamma=gamma, gamma_phi=gamma_phi, reltol=1e-8, abstol=1e-10, saveat=9),
    )
    result = simulation.run(
        np.array([0.0, 1.0], dtype=complex),
        0.0,
        duration,
        observables={"rydberg_population": 0},
    )
    final_population = float(result.data["rydberg_population"][-1])
    expected_population = math.exp(-gamma * duration)
    if not np.isclose(final_population, expected_population, atol=2e-3):
        raise RuntimeError(
            "Decay reference check failed: expected exp(-gamma * duration) = "
            f"{expected_population}, got {final_population}."
        )
    run = save_recipe_result(result, output_dir, "open_system_decay")
    print_recipe_summary(
        "open_system_decay",
        run,
        {
            "final_rydberg_population": round(final_population, 8),
            "analytic_population": round(expected_population, 8),
            "gamma_phi": gamma_phi,
        },
    )
    return run


if __name__ == "__main__":
    run_recipe(output_directory("open_system_decay"))
