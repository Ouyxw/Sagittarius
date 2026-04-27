import time
import numpy as np
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from mwis_solver import MWIS_AQC
from solution_verify import get_mwis_classical, calculate_weight, verify_independent_set
from baselines import greedy_mwis, simulated_annealing_mwis, calculate_tts, cplex_mwis, pulp_mwis
from sagittarius import Simulation, SolverConfig

def generate_random_udg(n, density=0.5, R=1.0):
    """Generates a random Unit-Disk Graph with weights."""
    side = np.sqrt(n / density)
    G = nx.Graph()
    for i in range(n):
        pos = (np.random.uniform(0, side), np.random.uniform(0, side))
        # Use weights as suggested in some benchmarks: 1.0 + small random
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

def run_benchmark():
    n_range = [6, 8, 10, 12, 14] # Small range for quick verification
    densities = [0.4, 0.6]
    iterations = 2
    
    results = []
    
    print(f"{'N':<3} | {'AvgDeg':<6} | {'P_MIS':<6} | {'TTS_AQC':<8} | {'T_CPLEX':<8} | {'Ratio_G':<7}")
    print("-" * 65)

    for n in n_range:
        for d in densities:
            for i in range(iterations):
                G = generate_random_udg(n, density=d)
                
                # 1. Classical Exact (Baseline for MIS weight)
                start_c = time.time()
                bitstring_exact, w_exact, stats = get_mwis_classical(G)
                t_exact = time.time() - start_c
                h_param = stats['h_param']
                
                # 2. CPLEX Exact Baseline
                start_cpx = time.time()
                bit_cpx, w_cpx = cplex_mwis(G)
                t_cplex = time.time() - start_cpx
                # If CPLEX failed (no license/install), try PuLP-CBC
                if w_cpx == 0:
                    start_cpx = time.time()
                    bit_cpx, w_cpx = pulp_mwis(G)
                    t_cplex = time.time() - start_cpx
                
                # 3. Sagittarius AQC
                solver = MWIS_AQC(G)
                duration = 5.0 # Fixed duration for benchmarking
                start_s = time.time()
                best_bit_aqc, probs, basis = solver.solve_full(duration=duration)
                t_aqc_run = time.time() - start_s
                
                w_aqc = calculate_weight(G, best_bit_aqc)
                
                # Calculate P_MIS (probability of finding any MIS)
                p_mis = 0.0
                for idx, b_val in enumerate(basis):
                    # Convert b_val to bitstring array
                    b_arr = np.array([(b_val >> j) & 1 for j in range(n)])
                    if calculate_weight(G, b_arr) >= w_exact - 1e-6:
                        p_mis += probs[idx]
                
                tts_aqc = calculate_tts(t_aqc_run, p_mis)
                
                # 3. Greedy Baseline
                start_g = time.time()
                bit_greedy, w_greedy = greedy_mwis(G)
                t_greedy = time.time() - start_g
                ratio_greedy = w_greedy / w_exact if w_exact > 0 else 1.0
                
                # 4. Simulated Annealing Baseline
                # We'll run it once and check ratio, or estimate its success prob
                # For simplicity, let's run it 10 times to estimate P_SA
                sa_runs = 10
                sa_successes = 0
                sa_weights = []
                start_sa_total = time.time()
                for _ in range(sa_runs):
                    bit_sa, w_sa = simulated_annealing_mwis(G, steps=500)
                    sa_weights.append(w_sa)
                    if w_sa >= w_exact - 1e-6:
                        sa_successes += 1
                t_sa_avg = (time.time() - start_sa_total) / sa_runs
                p_sa = sa_successes / sa_runs
                tts_sa = calculate_tts(t_sa_avg, p_sa)
                ratio_sa = np.mean(sa_weights) / w_exact if w_exact > 0 else 1.0
                
                avg_degree = np.mean([deg for node, deg in G.degree()])
                
                results.append({
                    "N": n,
                    "density": d,
                    "avg_degree": avg_degree,
                    "h_param": h_param,
                    "w_exact": w_exact,
                    "p_mis_aqc": p_mis,
                    "tts_aqc": tts_aqc,
                    "t_aqc_run": t_aqc_run,
                    "t_cplex": t_cplex,
                    "ratio_greedy": ratio_greedy,
                    "ratio_sa": ratio_sa,
                    "p_sa": p_sa,
                    "tts_sa": tts_sa
                })
                
                print(f"{n:<3} | {avg_degree:<6.1f} | {p_mis:<6.2f} | {tts_aqc:<8.2f} | {t_cplex:<8.3f} | {ratio_greedy:<7.2f}")
                
    df = pd.DataFrame(results)
    df.to_csv("mwis_improved_benchmark.csv", index=False)
    
    # Plotting: Multi-panel visualization matching paper style
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    summary = df.groupby("N").mean()
    
    # 1. TTS Scaling (Top-Left)
    ax = axes[0, 0]
    ax.plot(summary.index, summary["tts_aqc"], label="TTS Sagittarius (AQC)", marker='o', color='tab:blue', linewidth=2)
    ax.plot(summary.index, summary["tts_sa"], label="TTS Simulated Annealing", marker='s', color='tab:orange', linewidth=2)
    if "t_cplex" in summary.columns:
        ax.plot(summary.index, summary["t_cplex"], label="Time Exact (CPLEX/ILP)", marker='^', color='tab:green', linestyle='--', linewidth=2)
    
    ax.set_yscale('log')
    ax.set_xlabel("Number of Nodes (N)", fontsize=12)
    ax.set_ylabel("Time-to-Solution (s)", fontsize=12)
    ax.set_title("TTS Scaling Comparison", fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, which="both", ls="-", alpha=0.5)

    # 2. TTS vs Hardness Parameter H (Top-Right)
    ax = axes[0, 1]
    # Use scatter for raw data points to show correlation
    scatter = ax.scatter(df["h_param"], df["tts_aqc"], c=df["N"], cmap='viridis', alpha=0.7, label='AQC Runs')
    # Add a trendline if enough points
    if len(df) > 1:
        z = np.polyfit(df["h_param"], np.log10(df["tts_aqc"]), 1)
        p = np.poly1d(z)
        h_range = np.linspace(df["h_param"].min(), df["h_param"].max(), 100)
        ax.plot(h_range, 10**p(h_range), "r--", alpha=0.5, label="Log-linear fit")
    
    ax.set_yscale('log')
    ax.set_xlabel(r"Hardness Parameter $\mathbb{H}$ ($N_{|MIS|-1}/N_{|MIS|}$)", fontsize=12)
    ax.set_ylabel("TTS Sagittarius (s)", fontsize=12)
    ax.set_title(r"TTS vs Instance Hardness ($\mathbb{H}$)", fontsize=14, fontweight='bold')
    plt.colorbar(scatter, ax=ax, label='Node Count (N)')
    ax.legend()
    ax.grid(True, which="both", ls="-", alpha=0.5)

    # 3. Success Probability P_MIS (Bottom-Left)
    ax = axes[1, 0]
    ax.plot(summary.index, summary["p_mis_aqc"], label="P_MIS (AQC)", marker='o', color='tab:blue', linewidth=2)
    ax.plot(summary.index, df.groupby("N")["p_sa"].mean(), label="P_MIS (SA)", marker='s', color='tab:orange', linewidth=2)
    
    ax.set_xlabel("Number of Nodes (N)", fontsize=12)
    ax.set_ylabel("Success Probability $P_{MIS}$", fontsize=12)
    ax.set_title("Success Probability Scaling", fontsize=14, fontweight='bold')
    ax.set_ylim(-0.05, 1.05)
    ax.legend()
    ax.grid(True, alpha=0.5)

    # 4. Approximation Ratio (Bottom-Right)
    ax = axes[1, 1]
    ax.plot(summary.index, summary["ratio_greedy"], label="Greedy", marker='d', color='tab:red', linewidth=2)
    ax.plot(summary.index, summary["ratio_sa"], label="Simulated Annealing", marker='s', color='tab:orange', linewidth=2)
    
    ax.set_xlabel("Number of Nodes (N)", fontsize=12)
    ax.set_ylabel("Approximation Ratio ($W/W_{MIS}$)", fontsize=12)
    ax.set_title("Heuristic Quality Comparison", fontsize=14, fontweight='bold')
    ax.set_ylim(0.5, 1.05)
    ax.legend()
    ax.grid(True, alpha=0.5)

    plt.tight_layout()
    plt.savefig("mwis_benchmark_scientific.png", dpi=300)
    print("\nScientific visualization saved to mwis_benchmark_scientific.png")
    
    print("\nBenchmark complete. Results saved to mwis_improved_benchmark.csv")

if __name__ == "__main__":
    run_benchmark()
