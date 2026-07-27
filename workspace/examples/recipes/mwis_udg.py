"""Small UDG/MWIS AQC workflow using only public Sagittarius APIs."""

from __future__ import annotations

from itertools import product

import numpy as np

from sagittarius import Pulse, PulseSequence, Register, Simulation, SolverConfig

from common import RecipeRun, output_directory, print_recipe_summary, save_recipe_result


POINTS = [(0.0, 0.0), (0.8, 0.0), (2.0, 0.0)]
EDGES = [(0, 1)]
WEIGHTS = [1.0, 2.0, 1.5]
BLOCKADE_RADIUS = 1.0


def _is_independent(bitstring: str) -> bool:
    return all(not (bitstring[left] == "1" and bitstring[right] == "1") for left, right in EDGES)


def _exact_weight() -> float:
    return max(
        sum(weight for bit, weight in zip(candidate, WEIGHTS) if bit == "1")
        for candidate in product("01", repeat=len(WEIGHTS))
        if _is_independent("".join(candidate))
    )


def run_recipe(output_dir) -> RecipeRun:
    """Run a small weighted UDG schedule and save observables plus readout data.

    This is an exploratory AQC workflow. The exact enumeration is a small
    instance reference, not a claim that the schedule is an optimizer.
    """
    duration = 3.0
    register = Register.udg(POINTS, C6=1.0, blockade_radius=BLOCKADE_RADIUS)
    sequence = PulseSequence(
        omega=Pulse.sin_squared(amplitude=2.0, duration=duration),
        delta=[Pulse.ramp(start=-4.0, end=weight * 2.0, duration=duration) for weight in WEIGHTS],
    )
    simulation = Simulation(
        register,
        sequence,
        SolverConfig(blockade_radius=BLOCKADE_RADIUS, reltol=1e-8, abstol=1e-10, saveat=13),
    )
    basis_size = simulation.validate()
    psi0 = np.zeros(basis_size, dtype=complex)
    psi0[0] = 1.0
    result = simulation.run(
        psi0,
        0.0,
        duration,
        observables={
            "mwis_cost": {"type": "mwis_cost", "weights": WEIGHTS, "edges": EDGES, "penalty": 10.0},
            "blockade_violation": {"type": "blockade_violation", "edges": EDGES},
            "total_population": {"type": "total_rydberg_population"},
        },
    )
    distribution = result.final_bitstring_distribution()
    candidate = max(distribution, key=distribution.get)
    if not _is_independent(candidate):
        raise RuntimeError(f"Reduced-basis readout produced a non-independent candidate: {candidate}.")
    run = save_recipe_result(result, output_dir, "mwis_udg")
    print_recipe_summary(
        "mwis_udg",
        run,
        {
            "reduced_basis_size": basis_size,
            "most_likely_bitstring": candidate,
            "most_likely_probability": round(float(distribution[candidate]), 8),
            "exact_small_instance_weight": _exact_weight(),
        },
    )
    return run


if __name__ == "__main__":
    run_recipe(output_directory("mwis_udg"))
