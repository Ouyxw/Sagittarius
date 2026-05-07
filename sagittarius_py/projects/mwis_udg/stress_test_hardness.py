import time
import numpy as np
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from mwis_solver import MWIS_AQC
from solution_verify import get_mwis_classical, calculate_weight

def generate_random_udg(n, density=0.5, R=1.0):
    """Generates a random Unit-Disk Graph with random weights."""
    side = np.sqrt(n / density)
    G = nx.Graph()
    for i in range(n):
        pos = (np.random.uniform(0, side), np.random.uniform(0, side))
        weight = 1.0 + np.random.uniform(0, 0.5)
        G.add_node(i, pos=pos, weight=weight)
    
    nodes = list(G.nodes())
    for i in range(n):
        for j in range(i+1, n):
            u, v = nodes[i], nodes[j]
            du, dv = G.nodes[u]['pos'], G.nodes[v]['pos']
            if np.sqrt((du[0]-dv[0])**2 + (du[1]-dv[1])**2) <= R:
                G.add_edge(u, v)
    return G

def run_stress_test():
    # N from 10 to 22, with multiple densities to catch various H values
    n_range = range(10, 23, 2)
    densities = [0.3, 0.4, 0.5, 0.6, 0.7]
    samples_per_config = 5
    
    results = []
    threshold = 0.10
    
    print(f"Starting Stress Test: N={list(n_range)}, Densities={densities}")
    print(f"{'N':<3} | {'H':<6} | {'P_MIS':<6} | {'Solved':<8} | {'GPU':<4}")
    print("-" * 45)

    for n in n_range:
        for d in densities:
            for _ in range(samples_per_config):
                G = generate_random_udg(n, density=d)
                
                # 1. Exact Analysis
                bit_exact, w_exact, stats = get_mwis_classical(G)
                h_param = stats['h_param']
                
                # 2. Sagittarius AQC
                solver = MWIS_AQC(G)
                duration = 5.0 + 0.2 * n
                
                from sagittarius import SolverConfig
                use_gpu = n > 18
                config = SolverConfig(blockade_radius=solver.R, use_gpu=use_gpu)
                
                _, probs, basis = solver.solve_full(config=config, duration=duration)
                
                # Calculate P_MIS
                p_mis = 0.0
                for idx, b_val in enumerate(basis):
                    b_arr = np.array([(b_val >> j) & 1 for j in range(n)])
                    if calculate_weight(G, b_arr) >= w_exact - 1e-6:
                        p_mis += probs[idx]
                
                solved = p_mis >= threshold
                
                results.append({
                    "N": n,
                    "density": d,
                    "h_param": h_param,
                    "p_mis": p_mis,
                    "solved": solved,
                    "use_gpu": use_gpu
                })
                
                gpu_str = "YES" if use_gpu else "NO"
                print(f"{n:<3} | {h_param:<6.2f} | {p_mis:<6.2f} | {str(solved):<8} | {gpu_str:<4}")
                
    df = pd.DataFrame(results)
    df.to_csv("mwis_hardness_stress_test.csv", index=False)
    
    # Visualization: Solvability Boundary Map
    plt.figure(figsize=(12, 8))
    
    # Plot all points
    solved_df = df[df['solved'] == True]
    unsolved_df = df[df['solved'] == False]
    
    plt.scatter(solved_df['N'], solved_df['h_param'], c='tab:blue', label=f'Solved ($P_{{MIS}} \geq {threshold}$)', alpha=0.6, edgecolors='none')
    plt.scatter(unsolved_df['N'], unsolved_df['h_param'], c='tab:red', label=f'Unsolved ($P_{{MIS}} < {threshold}$)', alpha=0.4, edgecolors='none')
    
    # Calculate and plot the solvability frontier (max H for each N)
    frontier_n = []
    frontier_h = []
    for n in sorted(df['N'].unique()):
        solved_n = df[(df['N'] == n) & (df['solved'] == True)]
        if not solved_n.empty:
            frontier_n.append(n)
            frontier_h.append(solved_n['h_param'].max())
            
    if frontier_n:
        plt.plot(frontier_n, frontier_h, 'k--', linewidth=2, label='Solvability Frontier')
        plt.fill_between(frontier_n, frontier_h, 0, color='tab:blue', alpha=0.1)

    plt.xlabel("Number of Nodes (N)", fontsize=12)
    plt.ylabel("Hardness Parameter $\mathbb{H}$ ($N_{|MIS|-1}/N_{|MIS|}$)", fontsize=12)
    plt.title(f"Sagittarius MWIS-UDG Solvability Boundary ($T={duration}$, $P_{{MIS}} \geq {threshold}$)", fontsize=14, fontweight='bold')
    plt.xticks(sorted(df['N'].unique()))
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig("mwis_solvability_boundary.png", dpi=300)
    print("\nSolvability boundary map saved to mwis_solvability_boundary.png")

if __name__ == "__main__":
    run_stress_test()
