"""Self-contained UDG/MWIS recipe for a project using an installed wheel.

Copy this file into an external Python project.  It intentionally imports only
the public Sagittarius package, NumPy, and the Python standard library; it does
not import any repository ``workspace`` module or private Sagittarius API.
"""

from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path

import numpy as np

from sagittarius import Pulse, PulseSequence, Register, Simulation, SolverConfig


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


def run_recipe(output_dir: Path) -> dict[str, object]:
    """Run the public-API workflow and persist reproducible result files."""
    duration = 3.0
    output_dir.mkdir(parents=True, exist_ok=True)
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

    artifact_path = output_dir / "mwis_udg_wheel.result.json"
    manifest_path = output_dir / "mwis_udg_wheel.run-manifest.json"
    samples_path = output_dir / "mwis_udg_wheel.measurement-samples.json"
    result.save(str(artifact_path))
    manifest_path.write_text(json.dumps(result.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    samples = result.sample(shots=64, seed=20260727)
    samples_path.write_text(json.dumps(samples, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "result_artifact": str(artifact_path),
        "manifest_copy": str(manifest_path),
        "measurement_samples": str(samples_path),
        "reduced_basis_size": basis_size,
        "most_likely_bitstring": candidate,
        "most_likely_probability": float(distribution[candidate]),
        "exact_small_instance_weight": _exact_weight(),
    }
    print(json.dumps(summary, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a wheel-installed Sagittarius UDG/MWIS recipe.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts") / "mwis_udg_wheel",
        help="Directory for the result artifact, manifest copy, and seeded samples.",
    )
    args = parser.parse_args()
    run_recipe(args.output_dir)


if __name__ == "__main__":
    main()
