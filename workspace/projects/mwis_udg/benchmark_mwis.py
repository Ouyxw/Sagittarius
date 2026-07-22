import time
import numpy as np
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from mwis_solver import MWIS_AQC
from solution_verify import get_mwis_classical, calculate_weight, verify_independent_set
from baselines import greedy_mwis, simulated_annealing_mwis, calculate_tts, cplex_mwis, pulp_mwis
from sagittarius import Simulation, SolverConfig

def generate_random_udg(n, density=0.5, R=1.0, weights_mode='random'):
    """Generates a random Unit-Disk Graph with weights."""
    side = np.sqrt(n / density)
    G = nx.Graph()
    for i in range(n):
        pos = (np.random.uniform(0, side), np.random.uniform(0, side))
        if weights_mode == 'uniform':
            weight = 1.0
        else:
            # 1.0 + small random to break ties but keep it close to MIS
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

def run_benchmark(n_range=[14, 16, 18, 20, 22, 24], weights_mode='random', iterations=3):
    densities = [0.4, 0.6]
    
    results = []
    
    print(f"--- Scaling Benchmark (Mode: {weights_mode}) ---")
    print(f"{'N':<3} | {'AvgDeg':<6} | {'H':<6} | {'P_MIS':<6} | {'TTS_AQC':<8} | {'T_CPLEX':<8} | {'GPU':<4}")
    print("-" * 75)

    for n in n_range:
        for d in densities:
            for i in range(iterations):
                G = generate_random_udg(n, density=d, weights_mode=weights_mode)
                
                # 1. Classical Exact
                start_c = time.time()
                bitstring_exact, w_exact, stats = get_mwis_classical(G)
                t_exact = time.time() - start_c
                h_param = stats['h_param']
                
                # 2. CPLEX/PuLP Exact Baseline
                start_cpx = time.time()
                bit_cpx, w_cpx = cplex_mwis(G)
                t_cplex = time.time() - start_cpx
                if w_cpx == 0:
                    start_cpx = time.time()
                    bit_cpx, w_cpx = pulp_mwis(G)
                    t_cplex = time.time() - start_cpx
                
                # 3. Sagittarius AQC
                solver = MWIS_AQC(G)
                # Heuristic duration scaling: longer for larger N
                duration = 2.0 + 0.5 * n 
                
                use_gpu = n > 18
                config = SolverConfig(blockade_radius=solver.R, use_gpu=use_gpu)
                
                start_s = time.time()
                best_bit_aqc, probs, basis = solver.solve_full(config=config, duration=duration)
                t_aqc_run = time.time() - start_s
                
                # Calculate P_MIS
                p_mis = 0.0
                for idx, b_val in enumerate(basis):
                    b_arr = np.array([(b_val >> j) & 1 for j in range(n)])
                    if calculate_weight(G, b_arr) >= w_exact - 1e-6:
                        p_mis += probs[idx]
                
                tts_aqc = calculate_tts(t_aqc_run, p_mis)
                
                # 4. Baselines
                _, w_greedy = greedy_mwis(G)
                ratio_greedy = w_greedy / w_exact if w_exact > 0 else 1.0
                
                sa_runs = 5
                sa_successes = 0
                sa_weights = []
                start_sa_total = time.time()
                for _ in range(sa_runs):
                    bit_sa, w_sa = simulated_annealing_mwis(G, steps=1000)
                    sa_weights.append(w_sa)
                    if w_sa >= w_exact - 1e-6:
                        sa_successes += 1
                t_sa_avg = (time.time() - start_sa_total) / sa_runs
                p_sa = sa_successes / sa_runs
                tts_sa = calculate_tts(t_sa_avg, p_sa)
                
                avg_degree = np.mean([deg for node, deg in G.degree()])
                
                results.append({
                    "N": n,
                    "weights_mode": weights_mode,
                    "density": d,
                    "avg_degree": avg_degree,
                    "h_param": h_param,
                    "w_exact": w_exact,
                    "p_mis_aqc": p_mis,
                    "tts_aqc": tts_aqc,
                    "t_aqc_run": t_aqc_run,
                    "t_cplex": t_cplex,
                    "ratio_greedy": ratio_greedy,
                    "p_sa": p_sa,
                    "tts_sa": tts_sa,
                    "use_gpu": use_gpu
                })
                
                gpu_str = "YES" if use_gpu else "NO"
                print(f"{n:<3} | {avg_degree:<6.1f} | {h_param:<6.2f} | {p_mis:<6.2f} | {tts_aqc:<8.2f} | {t_cplex:<8.3f} | {gpu_str:<4}")
                
    df = pd.DataFrame(results)
    df.to_csv(f"mwis_benchmark_{weights_mode}.csv", index=False)
    return df

def plot_results(df, mode):
    # Set aesthetics
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    summary = df.groupby("N").mean(numeric_only=True)
    
    # 1. TTS Scaling
    ax = axes[0, 0]
    ax.plot(summary.index, summary["tts_aqc"], label="TTS Sagittarius (AQC)", marker='o', linewidth=2.5)
    ax.plot(summary.index, summary["tts_sa"], label="TTS SA", marker='s', linestyle='--', alpha=0.8)
    ax.plot(summary.index, summary["t_cplex"], label="T_Exact (ILP)", marker='^', linestyle=':', color='gray')
    ax.set_yscale('log')
    ax.set_xlabel("N Nodes", fontsize=12)
    ax.set_ylabel("TTS (s)", fontsize=12)
    ax.set_title("Time-to-Solution Scaling", fontweight='bold')
    ax.legend()

    # 2. Hardness Correlation (P_MIS vs H)
    ax = axes[0, 1]
    sns.scatterplot(data=df, x="h_param", y="p_mis_aqc", hue="N", size="avg_degree", ax=ax, palette="viridis", alpha=0.7)
    ax.set_xlabel(r"Hardness Parameter $\mathbb{H}$", fontsize=12)
    ax.set_ylabel(r"$P_{MIS}$ (AQC)", fontsize=12)
    ax.set_title(r"AQC Success Prob vs Instance Hardness $\mathbb{H}$", fontweight='bold')

    # 3. Success Probability Decay
    ax = axes[1, 0]
    sns.lineplot(data=df, x="N", y="p_mis_aqc", marker='o', label="AQC Success Prob", ax=ax)
    sns.lineplot(data=df, x="N", y="p_sa", marker='s', label="SA Success Prob", ax=ax, linestyle='--')
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("Success Probability Scaling", fontweight='bold')

    # 4. Phase Space Heatmap (Avg Degree vs H vs P_MIS)
    ax = axes[1, 1]
    # Binning for heatmap
    df['h_bin'] = pd.cut(df['h_param'], bins=5)
    df['deg_bin'] = pd.cut(df['avg_degree'], bins=5)
    pivot = df.pivot_table(index='deg_bin', columns='h_bin', values='p_mis_aqc', aggfunc='mean')
    sns.heatmap(pivot, annot=True, cmap="RdYlGn", ax=ax)
    ax.set_title("Solvability Heatmap (P_MIS)", fontweight='bold')
    ax.set_xlabel("Hardness Bin")
    ax.set_ylabel("Avg Degree Bin")

    plt.tight_layout()
    plt.savefig(f"mwis_scientific_report_{mode}.png", dpi=300)
    print(f"Report saved: mwis_scientific_report_{mode}.png")

if __name__ == "__main__":
    # Run both modes
    df_rand = run_benchmark(weights_mode='random', iterations=3)
    plot_results(df_rand, 'random')
    
    df_unif = run_benchmark(weights_mode='uniform', iterations=3)
    plot_results(df_unif, 'uniform')
