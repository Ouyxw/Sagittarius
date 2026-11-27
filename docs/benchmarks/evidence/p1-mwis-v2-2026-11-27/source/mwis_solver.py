"""Sagittarius AQC adapter for small weighted unit-disk MWIS instances."""

from __future__ import annotations

from typing import List, Tuple

import networkx as nx
import numpy as np

from sagittarius import Pulse, PulseSequence, Register, Simulation, SolverConfig, all_ground_state


class MWIS_AQC:
    """Translate a weighted unit-disk graph into a reduced-basis AQC run.

    This adapter supplies a research verification path. It is not a claim of
    optimization performance or a calibrated hardware schedule.
    """

    def __init__(self, graph: nx.Graph, blockade_radius: float = 1.0):
        self.graph = graph
        self.blockade_radius = float(blockade_radius)
        self.nodes = list(graph.nodes())
        self.register = Register.from_udg_graph(
            graph,
            C6=1.0,
            blockade_radius=self.blockade_radius,
        )

    def create_adiabatic_sequence(
        self,
        *,
        omega_max: float = 2 * np.pi,
        duration: float = 10.0,
    ) -> PulseSequence:
        omega = Pulse.sin_squared(amplitude=float(omega_max), duration=float(duration))
        start_delta = -2.0 * float(omega_max)
        delta = [
            Pulse.ramp(
                start=start_delta,
                end=float(self.graph.nodes[node].get("weight", 1.0)) * 2 * np.pi,
                duration=float(duration),
            )
            for node in self.nodes
        ]
        return PulseSequence(omega=omega, delta=delta)

    def solve(self, config: SolverConfig | None = None, duration: float = 10.0) -> np.ndarray:
        """Run the schedule and return its most-probable final bitstring."""
        bitstring, _, _ = self.solve_full(config=config, duration=duration)
        return bitstring

    def solve_full(
        self,
        config: SolverConfig | None = None,
        duration: float = 10.0,
    ) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """Return the most-probable bitstring, final probabilities, and basis."""
        # Preserve the original raw |psi|^2 tuple semantics. With no
        # observables Simulation.run returns Julia's ODESolution, not the
        # serialized SDK result boundary used by solve_result below.
        simulation, initial = self.prepare_simulation(config=config, duration=duration)
        solution = simulation.run(initial, 0.0, float(duration))
        probabilities = np.abs(np.asarray(list(solution.u)[-1], dtype=np.complex128))**2
        basis = [int(value) for value in simulation._basis] if simulation._basis is not None else list(range(len(probabilities)))
        best = basis[int(np.argmax(probabilities))]
        return np.asarray([(best >> i) & 1 for i in range(len(self.nodes))], dtype=int), probabilities, basis

    def prepare_simulation(self, config: SolverConfig | None = None, duration: float = 10.0):
        """Separate setup from execution, retaining all-ground preparation."""
        config = config or SolverConfig(blockade_radius=self.blockade_radius)
        simulation = Simulation(self.register, self.create_adiabatic_sequence(duration=duration), config)
        return simulation, all_ground_state(simulation)

    def solve_result(self, config: SolverConfig | None = None, duration: float = 10.0, *, observables=None):
        """Return the actual SDK result, collecting pop0 by default.

        Observable execution preserves normalized final readout plus a real
        manifest without retaining the entire wavefunction history.
        """
        simulation, initial_state = self.prepare_simulation(config=config, duration=duration)
        return simulation.run(initial_state, 0.0, float(duration), observables=observables or {"pop0": 0})

    def decode_result(self, result) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """Decode persisted final readout in ascending integer/atom-bit order."""
        distribution = result.final_bitstring_distribution()
        basis = sorted(int(label[::-1], 2) for label in distribution)
        probabilities = np.asarray([distribution[format(value, f"0{len(self.nodes)}b")[::-1]] for value in basis])
        best_value = basis[int(np.argmax(probabilities))]
        bitstring = np.asarray([(best_value >> index) & 1 for index in range(len(self.nodes))], dtype=int)
        return bitstring, probabilities, basis
