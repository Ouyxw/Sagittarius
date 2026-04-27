import time
import numpy as np
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from mwis_solver import MWIS_AQC
from solution_verify import get_mwis_classical, calculate_weight

def generate_random_udg(n, density=0.5, R=1.0):
    """Generates a random Unit-Disk Graph."""
    # Scale box size to control density roughly
    # Area ~ N / density ? 
    side = np.sqrt(n / density)
    G = nx.Graph()
    for i in range(n):
        pos = (np.random.uniform(0, side), np.random.uniform(0, side))
        weight = np.random.uniform(1.0, 2.0)
        G.add_node(i, pos=pos, weight=weight)
    
    nodes = list(G.nodes())
    for i in range(n):
        for j in range(i+1, n):
            u, v = nodes[i], nodes[j]
            du, dv = G.nodes[u]['pos'], G.nodes[v]['pos']
            if np.sqrt((du[0]-dv[0])**2 + (du[1]-dv[1])**2) <= R:
                G.add_edge(u, v)
    return G

def run_benchmark():
    n_range = [4, 6, 8, 10, 12]
    densities = [0.2, 0.5, 0.8]
    iterations = 3
    
    results = []
    
    print("Starting MWIS-UDG Benchmark...")
    for n in n_range:
        for d in densities:
            for i in range(iterations):
                G = generate_random_udg(n, density=d)
                
                # 1. Classical Exact
                start_c = time.time()
                _, w_exact = get_mwis_classical(G)
                t_classical = time.time() - start_c
                
                # 2. Sagittarius AQC
                solver = MWIS_AQC(G)
                start_s = time.time()
                bitstring_aqc = solver.solve()
                t_sagittarius = time.time() - start_s
                
                w_aqc = calculate_weight(G, bitstring_aqc)
                ratio = w_aqc / w_exact if w_exact > 0 else 1.0
                
                # Calculate Hardness: Average Degree & Degeneracy
                avg_degree = np.mean([d for n, d in G.degree()])
                degeneracy = max(nx.core_number(G).values())
                
                results.append({
                    "N": n,
                    "target_density": d,
                    "avg_degree": avg_degree,
                    "degeneracy": degeneracy,
                    "t_classical": t_classical,
                    "t_sagittarius": t_sagittarius,
                    "weight_exact": w_exact,
                    "weight_aqc": w_aqc,
                    "approximation_ratio": ratio
                })
                
                print(f"N={n}, Deg={avg_degree:.1f} | Ratio={ratio:.2f} | Time={t_sagittarius:.3f}s")
                
    df = pd.DataFrame(results)
    df.to_csv("mwis_benchmark_results.csv", index=False)
    
    # Simple summary plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Precision vs N
    summary_n = df.groupby("N")["approximation_ratio"].mean()
    ax1.plot(summary_n.index, summary_n.values, marker='o')
    ax1.set_xlabel("Number of Nodes (N)")
    ax1.set_ylabel("Mean Approximation Ratio")
    ax1.set_title("AQC Precision Scaling")
    ax1.grid(True)
    
    # Plot 2: Time vs N
    summary_t = df.groupby("N")["t_sagittarius"].mean()
    ax2.plot(summary_t.index, summary_t.values, marker='s', color='orange')
    ax2.set_xlabel("Number of Nodes (N)")
    ax2.set_ylabel("Mean Time (s)")
    ax2.set_title("AQC Time-Costing Scaling")
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig("mwis_benchmark_plots.png")
    print("\nBenchmark complete. Data saved to mwis_benchmark_results.csv")

if __name__ == "__main__":
    run_benchmark()
