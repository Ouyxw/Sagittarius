"""Two-atom blockade recipe with reduced-basis observables and an artifact."""

from __future__ import annotations

import numpy as np

from sagittarius import Atom, PulseSequence, Register, Simulation, SolverConfig

from common import RecipeRun, output_directory, print_recipe_summary, save_recipe_result


def run_recipe(output_dir) -> RecipeRun:
    """Run blockade-reduced two-atom dynamics and verify excluded double excitation."""
    blockade_radius = 0.6
    simulation = Simulation(
        Register([Atom(0.0, 0.0, 0.0), Atom(0.5, 0.0, 0.0)], C6=100.0),
        PulseSequence(omega=2.0 * np.pi, delta=0.0),
        SolverConfig(blockade_radius=blockade_radius, reltol=1e-8, abstol=1e-10, saveat=7),
    )
    basis_size = simulation.validate()
    result = simulation.run(
        np.array([1.0, 0.0, 0.0], dtype=complex),
        0.0,
        0.25,
        observables={
            "population_atom_0": 0,
            "population_atom_1": 1,
            "total_population": {"type": "total_rydberg_population"},
            "blockade_violation": {"type": "blockade_violation", "edges": [[0, 1]]},
        },
    )
    max_violation = float(max(result.data["blockade_violation"]))
    if basis_size != 3 or max_violation > 1e-12:
        raise RuntimeError(
            "Blockade reference check failed: expected a three-state basis and zero double excitation."
        )
    run = save_recipe_result(result, output_dir, "two_atom_blockade")
    print_recipe_summary(
        "two_atom_blockade",
        run,
        {"reduced_basis_size": basis_size, "max_blockade_violation": max_violation},
    )
    return run


if __name__ == "__main__":
    run_recipe(output_directory("two_atom_blockade"))
