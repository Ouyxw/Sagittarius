import networkx as nx
import numpy as np
from typing import List, Tuple, Dict

def get_mwis_classical(G: nx.Graph) -> Tuple[List[int], float, Dict]:
    """
    Solves the MWIS problem exactly and returns:
    (best_bitstring, best_weight, stats)
    stats contains 'n_mis' and 'n_mis_minus_1' for hardness calculation.
    Note: For hardness parameter H, we usually consider the cardinality MIS.
    """
    nodes = list(G.nodes())
    n = len(nodes)
    weights = {n: G.nodes[n].get('weight', 1.0) for n in nodes}
    
    # We will compute both the weighted MIS and the counts for unweighted MIS 
    # to support the Hardness Parameter H = N_{|MIS|-1} / N_{|MIS|}
    
    # 1. Exact Weighted MIS (Branch and Bound)
    best_w = 0.0
    best_s = []
    
    def solve_weighted(current_set, remaining_nodes, current_weight):
        nonlocal best_w, best_s
        if not remaining_nodes:
            if current_weight > best_w + 1e-9:
                best_w = current_weight
                best_s = list(current_set)
            return
        
        # Pruning
        if current_weight + sum(weights[m] for m in remaining_nodes) <= best_w + 1e-9:
            return

        v = remaining_nodes[0]
        new_rem = remaining_nodes[1:]
        
        # Try Include
        if all(nb not in current_set for nb in G.neighbors(v)):
            solve_weighted(current_set + [v], 
                           [m for m in new_rem if m not in G.neighbors(v)], 
                           current_weight + weights[v])
        
        # Try Exclude
        solve_weighted(current_set, new_rem, current_weight)

    solve_weighted([], nodes, 0.0)
    
    # 2. Count Cardinality MIS and MIS-1 for Hardness Parameter H
    # We use a simple recursive count for small N
    mis_size = 0
    counts = { "n_mis": 0, "n_mis_minus_1": 0 }
    
    # First find MIS size
    def get_max_size(current_set, remaining_nodes):
        nonlocal mis_size
        if not remaining_nodes:
            mis_size = max(mis_size, len(current_set))
            return
        if len(current_set) + len(remaining_nodes) <= mis_size:
            return
        v = remaining_nodes[0]
        new_rem = remaining_nodes[1:]
        if all(nb not in current_set for nb in G.neighbors(v)):
            get_max_size(current_set + [v], [m for m in new_rem if m not in G.neighbors(v)])
        get_max_size(current_set, new_rem)

    get_max_size([], nodes)
    
    # Then count
    def count_sets(current_set, remaining_nodes):
        if not remaining_nodes:
            if len(current_set) == mis_size:
                counts["n_mis"] += 1
            elif len(current_set) == mis_size - 1:
                counts["n_mis_minus_1"] += 1
            return
        
        if len(current_set) + len(remaining_nodes) < mis_size - 1:
            return

        v = remaining_nodes[0]
        new_rem = remaining_nodes[1:]
        
        if all(nb not in current_set for nb in G.neighbors(v)):
            count_sets(current_set + [v], [m for m in new_rem if m not in G.neighbors(v)])
        count_sets(current_set, new_rem)

    count_sets([], nodes)
    
    bitstring = [1 if n in best_s else 0 for n in nodes]
    stats = {
        "mis_size": mis_size,
        "n_mis": counts["n_mis"],
        "n_mis_minus_1": counts["n_mis_minus_1"],
        "h_param": counts["n_mis_minus_1"] / counts["n_mis"] if counts["n_mis"] > 0 else 0
    }
    
    return bitstring, best_w, stats

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
