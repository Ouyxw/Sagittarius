import numpy as np
import networkx as nx
import random
import time
from typing import List, Tuple

def greedy_mwis(G: nx.Graph) -> Tuple[List[int], float]:
    """
    Standard greedy algorithm for MWIS: 
    Iteratively pick the node with the highest weight/(degree+1).
    """
    remaining_nodes = set(G.nodes())
    mwis = []
    total_weight = 0.0
    
    while remaining_nodes:
        # Heuristic: max(weight / (degree + 1))
        best_node = max(remaining_nodes, key=lambda n: G.nodes[n].get('weight', 1.0) / (G.degree(n) + 1))
        mwis.append(best_node)
        total_weight += G.nodes[best_node].get('weight', 1.0)
        
        # Remove best_node and its neighbors
        to_remove = {best_node} | set(G.neighbors(best_node))
        remaining_nodes -= to_remove
        
    nodes = list(G.nodes())
    bitstring = [1 if n in mwis else 0 for n in nodes]
    return bitstring, total_weight

def simulated_annealing_mwis(G: nx.Graph, 
                             steps: int = 1000, 
                             t_start: float = 10.0, 
                             t_end: float = 0.01) -> Tuple[List[int], float]:
    """
    Simulated Annealing for MWIS.
    State: A valid independent set.
    Transitions: Add a node, remove a node, or swap a node with its neighbors.
    """
    nodes = list(G.nodes())
    n = len(nodes)
    weights = {node: G.nodes[node].get('weight', 1.0) for node in nodes}
    
    # Initial state: empty set
    current_set = set()
    current_weight = 0.0
    
    best_set = set()
    best_weight = 0.0
    
    t = t_start
    alpha = (t_end / t_start) ** (1.0 / steps)
    
    for i in range(steps):
        # Propose a move
        node = random.choice(nodes)
        
        if node in current_set:
            # Try to remove
            delta = -weights[node]
            if random.random() < np.exp(delta / t):
                current_set.remove(node)
                current_weight += delta
        else:
            # Try to add
            neighbors_in_set = [nb for nb in G.neighbors(node) if nb in current_set]
            if not neighbors_in_set:
                # Direct add
                delta = weights[node]
                if random.random() < np.exp(delta / t) or delta > 0:
                    current_set.add(node)
                    current_weight += delta
            else:
                # Try a swap? (Standard in some MWIS SA implementations)
                # If we remove all neighbors, can we add this node?
                swap_weight = sum(weights[nb] for nb in neighbors_in_set)
                delta = weights[node] - swap_weight
                if random.random() < np.exp(delta / t):
                    for nb in neighbors_in_set:
                        current_set.remove(nb)
                    current_set.add(node)
                    current_weight += delta
        
        if current_weight > best_weight:
            best_weight = current_weight
            best_set = set(current_set)
            
        t *= alpha
        
    bitstring = [1 if n in best_set else 0 for n in nodes]
    return bitstring, best_weight

def cplex_mwis(G: nx.Graph) -> Tuple[List[int], float]:
    """
    Solves MWIS using IBM CPLEX (via docplex).
    Requires a local CPLEX installation.
    """
    try:
        from docplex.mp.model import Model
    except ImportError:
        print("Warning: docplex not installed. Skipping CPLEX baseline.")
        return [], 0.0

    nodes = list(G.nodes())
    weights = {node: G.nodes[node].get('weight', 1.0) for node in nodes}
    
    mdl = Model(name='MWIS')
    # Decision variables
    x = mdl.binary_var_dict(nodes, name='x')
    
    # Objective: Maximize sum of weights
    mdl.maximize(mdl.sum(weights[i] * x[i] for i in nodes))
    
    # Constraint: No two adjacent nodes can be in the set
    for u, v in G.edges():
        mdl.add_constraint(x[u] + x[v] <= 1)
    
    try:
        solution = mdl.solve()
    except Exception as e:
        print(f"Warning: CPLEX solve failed: {e}")
        return [], 0.0
    
    if solution:
        bitstring = [1 if solution.get_value(x[i]) > 0.5 else 0 for i in nodes]
        return bitstring, solution.objective_value
    else:
        return [0] * len(nodes), 0.0

def pulp_mwis(G: nx.Graph, solver_name: str = 'PULP_CBC_CMD') -> Tuple[List[int], float]:
    """
    Solves MWIS using PuLP, which can interface with various solvers (CBC, GLPK, CPLEX, etc.).
    """
    try:
        import pulp
    except ImportError:
        return [], 0.0

    nodes = list(G.nodes())
    weights = {node: G.nodes[node].get('weight', 1.0) for node in nodes}
    
    prob = pulp.LpProblem("MWIS", pulp.LpMaximize)
    
    # Decision variables
    x = pulp.LpVariable.dicts("x", nodes, cat='Binary')
    
    # Objective
    prob += pulp.lpSum([weights[i] * x[i] for i in nodes])
    
    # Constraints
    for u, v in G.edges():
        prob += x[u] + x[v] <= 1
        
    # Try to use CPLEX if available, otherwise default
    if solver_name == 'CPLEX_CMD':
        solver = pulp.CPLEX_CMD(msg=False)
    else:
        solver = pulp.PULP_CBC_CMD(msg=False)
        
    prob.solve(solver)
    
    if pulp.LpStatus[prob.status] == 'Optimal':
        bitstring = [1 if pulp.value(x[i]) > 0.5 else 0 for i in nodes]
        return bitstring, pulp.value(prob.objective)
    else:
        return [0] * len(nodes), 0.0

def calculate_tts(t_run: float, p_success: float, target_prob: float = 0.99) -> float:
    """Calculates Time-to-Solution (TTS)."""
    if p_success >= 1.0:
        return t_run
    if p_success <= 0.0:
        return float('inf')
    return t_run * (np.log(1 - target_prob) / np.log(1 - p_success))
