import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from mwis_solver import MWIS_AQC
from solution_verify import get_mwis_classical, verify_independent_set, calculate_weight

def run_example():
    print("--- MWIS-UDG Example using Sagittarius ---")
    
    # 1. Create a Unit-Disk Graph
    # Nodes with positions (x, y) and weights
    # We use a 7-node graph
    G = nx.Graph()
    positions = {
        0: (0.0, 0.0), 1: (0.8, 0.0), 2: (0.4, 0.7),
        3: (1.5, 0.0), 4: (1.2, 0.8), 5: (0.0, 1.5),
        6: (2.0, 1.5)
    }
    weights = {0: 1.0, 1: 1.2, 2: 1.5, 3: 0.8, 4: 1.1, 5: 2.0, 6: 1.0}
    
    for i, pos in positions.items():
        G.add_node(i, pos=pos, weight=weights[i])
        
    # Add edges based on unit-disk radius R=1.0
    R = 1.0
    nodes = list(G.nodes())
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            u, v = nodes[i], nodes[j]
            dist = np.sqrt((positions[u][0] - positions[v][0])**2 + (positions[u][1] - positions[v][1])**2)
            if dist <= R:
                G.add_edge(u, v)
    
    print(f"Graph nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    
    # 2. Solve using Sagittarius (AQC)
    solver = MWIS_AQC(G, blockade_radius=R)
    bitstring_aqc = solver.solve()
    weight_aqc = calculate_weight(G, bitstring_aqc)
    valid_aqc = verify_independent_set(G, bitstring_aqc)
    
    print(f"AQC Solution: {bitstring_aqc}")
    print(f"AQC Weight: {weight_aqc:.2f}, Valid IS: {valid_aqc}")
    
    # 3. Solve Classically (Exact)
    bitstring_exact, weight_exact, stats = get_mwis_classical(G)
    print(f"Exact Weight: {weight_exact:.2f}, Hardness H: {stats['h_param']:.2f}")
    
    # 4. Visualize
    plt.figure(figsize=(8, 6))
    node_colors = ['red' if bitstring_aqc[i] == 1 else 'lightblue' for i in range(len(nodes))]
    nx.draw(G, pos=positions, with_labels=True, node_color=node_colors, node_size=800)
    plt.title(f"MWIS-UDG Solution (AQC)\nApproximation Ratio: {weight_aqc/weight_exact:.2f}")
    plt.savefig("mwis_solution.png")
    print("Visualization saved to mwis_solution.png")
    plt.close()

if __name__ == "__main__":
    run_example()
