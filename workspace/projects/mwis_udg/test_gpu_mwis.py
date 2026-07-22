import numpy as np
import networkx as nx
from mwis_solver import MWIS_AQC
from sagittarius import SolverConfig
import time

def test_gpu():
    # Small graph but force GPU
    n = 10
    G = nx.Graph()
    for i in range(n):
        G.add_node(i, pos=(i*0.5, 0), weight=1.0)
    for i in range(n-1):
        G.add_edge(i, i+1)
        
    solver = MWIS_AQC(G, blockade_radius=1.0)
    config = SolverConfig(blockade_radius=1.0, use_gpu=True)
    
    print("Running with GPU...")
    start = time.time()
    bitstring, probs, basis = solver.solve_full(config=config, duration=2.0)
    print(f"GPU time: {time.time() - start:.4f}s")
    print(f"Best bitstring: {bitstring}")

    config_cpu = SolverConfig(blockade_radius=1.0, use_gpu=False)
    print("Running with CPU...")
    start = time.time()
    bitstring_cpu, probs_cpu, basis_cpu = solver.solve_full(config=config_cpu, duration=2.0)
    print(f"CPU time: {time.time() - start:.4f}s")
    
    assert np.allclose(probs, probs_cpu, atol=1e-5)
    print("GPU and CPU results match!")

if __name__ == "__main__":
    test_gpu()
