import numpy as np
import networkx as nx
from typing import Dict, List, Tuple
from sagittarius import Atom, Register, Simulation, PulseSequence, Pulse, SolverConfig

class MWIS_AQC:
    """
    Translates an MWIS problem on a Unit-Disk Graph into a 
    Neutral Atom Adiabatic Simulation.
    """
    
    def __init__(self, G: nx.Graph, blockade_radius: float = 1.0):
        """
        G: A networkx Graph where nodes have 'pos' (x, y) and 'weight' attributes.
        blockade_radius: The distance within which atoms blockade each other.
        """
        self.G = G
        self.R = blockade_radius
        self.nodes = list(G.nodes())
        self.N = len(self.nodes)
        
        # 1. Create Register
        atoms = []
        for node in self.nodes:
            pos = G.nodes[node].get('pos', (0.0, 0.0))
            # Atom expects SVector{3} now
            atoms.append(Atom(pos[0], pos[1], 0.0))
        
        self.register = Register(atoms, C6=1.0)
        
    def create_adiabatic_sequence(self, 
                                  omega_max: float = 2*np.pi * 1.0, 
                                  duration: float = 10.0) -> PulseSequence:
        """
        Constructs an adiabatic ramp using native Julia pulse shapes.
        """
        # Optimized: Use native SinSquared pulse
        omega = Pulse.sin_squared(amplitude=omega_max, duration=duration)
            
        # Optimized: Use native Ramp pulses for each atom
        weights = np.array([self.G.nodes[n].get('weight', 1.0) for n in self.nodes])
        start_delta = -2.0 * omega_max
        
        delta = []
        for i in range(self.N):
            end_delta = weights[i] * (2*np.pi)
            delta.append(Pulse.ramp(start=start_delta, end=float(end_delta), duration=duration))
            
        return PulseSequence(omega=omega, delta=delta)

    def solve(self, config: SolverConfig = None, duration: float = 10.0) -> np.ndarray:
        """
        Runs the simulation and returns the final bitstring (Independent Set).
        """
        bitstring, _, _ = self.solve_full(config, duration)
        return bitstring

    def solve_full(self, config: SolverConfig = None, duration: float = 10.0) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """
        Runs the simulation and returns (best_bitstring, probabilities, basis).
        probabilities is an array of size 2^N (or basis size).
        basis is a list of bitstrings as integers.
        """
        if config is None:
            config = SolverConfig(blockade_radius=self.R)
        
        seq = self.create_adiabatic_sequence(duration=duration)
        sim = Simulation(self.register, seq, config)
        
        basis_size = sim.validate()
        psi0 = np.zeros(basis_size, dtype=complex)
        psi0[0] = 1.0
        
        sol = sim.run(psi0, 0.0, duration)
        
        psi_final = np.array(sol.u[-1])
        probs = np.abs(psi_final)**2
        best_idx = np.argmax(probs)
        
        basis = list(sim._basis)
        best_bitstring_val = basis[best_idx]
        best_bitstring = np.array([(best_bitstring_val >> i) & 1 for i in range(self.N)])
        
        return best_bitstring, probs, basis
