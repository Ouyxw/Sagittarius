import networkx as nx
import numpy as np
from typing import List, Tuple

def get_mwis_classical(G: nx.Graph) -> Tuple[List[int], float]:
    """
    Solves the MWIS problem exactly using a classical algorithm.
    For small graphs, we use an exhaustive search or high-quality heuristic.
    """
    # networkx doesn't have a direct MWIS solver for weighted nodes in all versions,
    # but we can use the 'clique' module on the complement graph or 
    # a simple recursive branch-and-bound.
    
    nodes = list(G.nodes())
    weights = {n: G.nodes[n].get('weight', 1.0) for n in nodes}
    
    # 1. Simple branch and bound for small N
    best_weight = 0.0
    best_set = []
    
    def solve_recursive(current_set, remaining_nodes, current_weight):
        nonlocal best_weight, best_set
        
        if not remaining_nodes:
            if current_weight > best_weight:
                best_weight = current_weight
                best_set = list(current_set)
            return

        # Pruning
        potential_future_weight = sum(weights[n] for n in remaining_nodes)
        if current_weight + potential_future_weight <= best_weight:
            return

        v = remaining_nodes[0]
        new_remaining = remaining_nodes[1:]
        
        # Option 1: Include v (if no neighbors are already in set)
        if all(neighbor not in current_set for neighbor in G.neighbors(v)):
            solve_recursive(current_set + [v], 
                            [n for n in new_remaining if n not in G.neighbors(v)], 
                            current_weight + weights[v])
            
        # Option 2: Exclude v
        solve_recursive(current_set, new_remaining, current_weight)

    solve_recursive([], nodes, 0.0)
    
    # Convert best_set to bitstring array
    bitstring = [1 if n in best_set else 0 for n in nodes]
    return bitstring, best_weight

def verify_independent_set(G: nx.Graph, bitstring: np.ndarray) -> bool:
    """Checks if the given bitstring represents a valid Independent Set."""
    nodes = list(G.nodes())
    active_nodes = [nodes[i] for i, val in enumerate(bitstring) if val == 1]
    
    for u in active_nodes:
        for v in active_nodes:
            if u != v and G.has_edge(u, v):
                return False
    return True

def calculate_weight(G: nx.Graph, bitstring: np.ndarray) -> float:
    """Calculates total weight of the selected nodes."""
    nodes = list(G.nodes())
    return sum(G.nodes[n].get('weight', 1.0) for i, n in enumerate(nodes) if bitstring[i] == 1)
