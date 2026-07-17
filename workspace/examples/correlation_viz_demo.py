"""
Example: Correlation Analysis Visualization

Demonstrates how to visualize pair correlations, connected correlations,
Pauli-ZZ correlations, and blockade conflict matrices from simulation results.

This example shows:
1. Pair correlation matrix heatmap
2. Connected correlation matrix (genuine correlations)
3. Pauli-ZZ correlation matrix
4. Blockade conflict matrix and edge heatmap

Note: These are diagnostic tools for data exploration only.
They do NOT constitute hardware calibration or performance claims.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from sagittarius import Register, PulseSequence, Simulation, SolverConfig

# 输出目录配置
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_mock_result_with_correlations():
    """
    Create a mock result with correlation observables for demonstration.
    
    In real usage, you would run a simulation with proper observables:
        observables = {
            "pair_corr_0_1": PairCorrelation([0, 1], N_atoms),
            "connected_corr_0_1": ConnectedPairCorrelation([0, 1], N_atoms),
            "pauli_zz_0_1": PauliZZ([0, 1], N_atoms),
            "blockade_violation_0_1": BlockadeViolation(edges=[(0, 1)], N_atoms),
        }
    """
    # For demo purposes, we'll create synthetic data
    class MockResult:
        def __init__(self):
            n_atoms = 4
            times = np.linspace(0, 2.0, 50)
            
            # Generate synthetic correlation data
            self.data = {'t': times.tolist()}
            
            # Pair correlations <n_i n_j>
            for i in range(n_atoms):
                for j in range(i+1, n_atoms):
                    # Decay with distance
                    dist = abs(i - j) * 0.6  # Assume 0.6 μm spacing
                    amplitude = 0.5 * np.exp(-dist / 2.0)
                    self.data[f'pair_corr_{i}_{j}'] = (
                        amplitude * (1 - np.exp(-times / 0.5))
                    ).tolist()
            
            # Connected correlations C_ij = <n_i n_j> - <n_i><n_j>
            for i in range(n_atoms):
                for j in range(i+1, n_atoms):
                    dist = abs(i - j) * 0.6
                    amplitude = 0.2 * np.exp(-dist / 1.5)
                    self.data[f'connected_corr_{i}_{j}'] = (
                        amplitude * np.sin(times * np.pi) * np.exp(-times / 1.0)
                    ).tolist()
            
            # Pauli-ZZ correlations
            for i in range(n_atoms):
                for j in range(i+1, n_atoms):
                    dist = abs(i - j) * 0.6
                    self.data[f'pauli_zz_{i}_{j}'] = (
                        np.exp(-dist / 1.0) * np.cos(times * 0.5)
                    ).tolist()
            
            # Blockade violations
            edges = [(0, 1), (1, 2), (2, 3)]
            for i, j in edges:
                self.data[f'blockade_violation_{i}_{j}'] = (
                    0.3 * (1 - np.exp(-times / 0.8))
                ).tolist()
            
            # Single-atom populations
            for i in range(n_atoms):
                self.data[f'pop{i}'] = (
                    0.7 * (1 - np.exp(-times / 0.6))
                ).tolist()
            
            self.metadata = {
                'register': {'atom_count': n_atoms}
            }
            self.manifest = {}
        
        def to_pandas(self):
            import pandas as pd
            return pd.DataFrame(self.data)
    
    return MockResult()


def main():
    print("=" * 70)
    print("CORRELATION ANALYSIS VISUALIZATION EXAMPLE")
    print("=" * 70)
    
    # Create mock result with correlation data
    print("\n[1] Creating mock simulation result with correlation observables...")
    result = create_mock_result_with_correlations()
    print(f"    ✓ Result contains {len(result.data)} time series")
    
    # Extract atom count
    n_atoms = result.metadata['register']['atom_count']
    print(f"    ✓ Atom count: {n_atoms}")
    
    # Example 1: Pair Correlation Matrix
    print("\n[2] Plotting pair correlation matrix...")
    from sagittarius.viz import plot_pair_correlation_matrix
    
    ax1 = plot_pair_correlation_matrix(
        result,
        title="Pair Correlation Matrix <nᵢnⱼ>",
        save_path=os.path.join(OUTPUT_DIR, "correlation_pair.png")
    )
    print("    ✓ Saved to: correlation_pair.png")
    
    # Example 2: Connected Correlation Matrix
    print("\n[3] Plotting connected correlation matrix...")
    from sagittarius.viz import plot_connected_correlation_matrix
    
    ax2 = plot_connected_correlation_matrix(
        result,
        significance_threshold=0.05,
        title="Connected Correlation Matrix Cᵢⱼ",
        save_path=os.path.join(OUTPUT_DIR, "correlation_connected.png")
    )
    print("    ✓ Saved to: correlation_connected.png")
    
    # Example 3: Pauli-ZZ Correlation Matrix
    print("\n[4] Plotting Pauli-ZZ correlation matrix...")
    from sagittarius.viz import plot_pauli_zz_matrix
    
    ax3 = plot_pauli_zz_matrix(
        result,
        title="Pauli-ZZ Correlation Matrix <ZZ>ᵢⱼ",
        save_path=os.path.join(OUTPUT_DIR, "correlation_pauli_zz.png")
    )
    print("    ✓ Saved to: correlation_pauli_zz.png")
    
    # Example 4: Blockade Conflict Matrix
    print("\n[5] Plotting blockade conflict matrix...")
    from sagittarius.viz import plot_blockade_conflict_heatmap
    
    ax4 = plot_blockade_conflict_heatmap(
        result,
        mode='matrix',
        title="Blockade Conflict Matrix",
        save_path=os.path.join(OUTPUT_DIR, "conflict_matrix.png")
    )
    print("    ✓ Saved to: conflict_matrix.png")
    
    # Example 5: Blockade Conflict Edge Heatmap
    print("\n[6] Plotting blockade conflict edge heatmap...")
    edges = [(0, 1), (1, 2), (2, 3)]
    
    ax5 = plot_blockade_conflict_heatmap(
        result,
        mode='edges',
        edges=edges,
        title="Blockade Conflict Edges",
        save_path=os.path.join(OUTPUT_DIR, "conflict_edges.png")
    )
    print("    ✓ Saved to: conflict_edges.png")
    
    # Example 6: Combined figure
    print("\n[7] Creating combined correlation analysis figure...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 16))
    
    plot_pair_correlation_matrix(result, ax=axes[0, 0], show_values=False)
    plot_connected_correlation_matrix(result, ax=axes[0, 1], show_values=False)
    plot_pauli_zz_matrix(result, ax=axes[1, 0], show_values=False)
    plot_blockade_conflict_heatmap(result, mode='matrix', ax=axes[1, 1], show_values=False)
    
    plt.suptitle("Correlation Analysis Dashboard", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "correlation_dashboard.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("    ✓ Saved to: correlation_dashboard.png")
    
    # Diagnostic insights
    print("\n[8] Diagnostic Insights:")
    df = result.to_pandas()
    
    # Analyze pair correlations
    pair_cols = [c for c in df.columns if c.startswith('pair_corr_')]
    if pair_cols:
        final_values = [df[c].iloc[-1] for c in pair_cols]
        print(f"    • Pair correlations: {len(pair_cols)} pairs")
        print(f"      Max: {max(final_values):.3f}, Min: {min(final_values):.3f}")
    
    # Analyze connected correlations
    conn_cols = [c for c in df.columns if c.startswith('connected_corr_')]
    if conn_cols:
        final_values = [df[c].iloc[-1] for c in conn_cols]
        significant = sum(1 for v in final_values if abs(v) > 0.05)
        print(f"    • Connected correlations: {len(conn_cols)} pairs")
        print(f"      Significant (|C_ij| > 0.05): {significant}")
    
    # Analyze blockade violations
    viol_cols = [c for c in df.columns if c.startswith('blockade_violation_')]
    if viol_cols:
        final_values = [df[c].iloc[-1] for c in viol_cols]
        high_conflict = sum(1 for v in final_values if v > 0.1)
        print(f"    • Blockade violations: {len(viol_cols)} edges")
        print(f"      High-conflict (> 0.1): {high_conflict}")
    
    print("\n" + "=" * 70)
    print("✓ CORRELATION ANALYSIS COMPLETE")
    print("=" * 70)
    print("\n⚠️  REMINDER: These visualizations are for data exploration only.")
    print("    They do NOT constitute hardware calibration or performance claims.")
    print("=" * 70)


if __name__ == "__main__":
    main()
