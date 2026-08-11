"""Sagittarius AQC adapter for small weighted unit-disk MWIS instances."""

from __future__ import annotations

from typing import List, Tuple

import networkx as nx
import numpy as np

from sagittarius import Pulse, PulseSequence, Register, Simulation, SolverConfig


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
        config = config or SolverConfig(blockade_radius=self.blockade_radius)
        simulation = Simulation(self.register, self.create_adiabatic_sequence(duration=duration), config)
        basis_size = simulation.validate()
        initial_state = np.zeros(basis_size, dtype=np.complex128)
        initial_state[0] = 1.0
        solution = simulation.run(initial_state, 0.0, float(duration))
        final_state = np.asarray(list(solution.u)[-1], dtype=np.complex128)
        probabilities = np.abs(final_state) ** 2
        basis = [int(value) for value in simulation._basis]
        best_value = basis[int(np.argmax(probabilities))]
        bitstring = np.asarray([(best_value >> index) & 1 for index in range(len(self.nodes))], dtype=int)
        return bitstring, probabilities, basis
