"""
Geometry diagnostics demonstration.

Shows how to use geometry diagnostic tools for pre-simulation validation
of Rydberg atom register configurations.

This example demonstrates:
1. Distance matrix extraction
2. Van der Waals interaction computation
3. Blockade adjacency analysis
4. Comprehensive visualization with numerical annotations
"""

import matplotlib.pyplot as plt
from sagittarius import Register, Atom
from sagittarius.viz import (
    extract_geometry_diagnostics,
    plot_geometry_diagnostics,
    plot_unit_disk_graph,
)


def main():
    """Run geometry diagnostics demonstration."""
    
    print("=" * 70)
    print("GEOMETRY DIAGNOSTICS DEMONSTRATION")
    print("=" * 70)
    
    # Create a 4-atom chain register
    print("\n[1] Creating 4-atom chain register...")
    atoms = [Atom(i * 0.6, 0.0, 0.0) for i in range(4)]
    reg = Register(atoms=atoms)
    
    print(f"    ✓ Created register with {len(atoms)} atoms")
    print(f"    ✓ Spacing: 0.6 μm")
    
    # Set parameters
    blockade_radius = 1.0  # μm
    C6 = 80.0  # Typical Rydberg C6 coefficient
    
    print(f"\n[2] Configuration:")
    print(f"    Blockade radius (R_b): {blockade_radius} μm")
    print(f"    C6 coefficient: {C6}")
    
    # Extract diagnostics
    print("\n[3] Extracting geometric diagnostics...")
    diag = extract_geometry_diagnostics(reg, blockade_radius, C6)
    
    print(f"\n    === Distance Statistics ===")
    print(f"    Min distance: {diag['min_distance']:.3f} μm")
    print(f"    Max distance: {diag['max_distance']:.3f} μm")
    print(f"    Mean distance: {diag['mean_distance']:.3f} μm")
    
    print(f"\n    === Blockade Structure ===")
    print(f"    Number of edges: {len(diag['edges'])}")
    print(f"    Graph density: {diag['graph_density']:.2%}")
    print(f"    Edges: {diag['edges']}")
    
    print(f"\n    === Distance Matrix ===")
    print("    ", "  ".join([f"{i:>6}" for i in range(diag['n_atoms'])]))
    for i in range(diag['n_atoms']):
        row_str = "  ".join([f"{diag['distance_matrix'][i, j]:6.2f}" 
                            for j in range(diag['n_atoms'])])
        print(f"    {i}: {row_str}")
    
    print(f"\n    === VDW Interaction Matrix (V_ij = C6/r^6) ===")
    print("    ", "  ".join([f"{i:>10}" for i in range(diag['n_atoms'])]))
    for i in range(diag['n_atoms']):
        row_str = "  ".join([f"{diag['vdw_matrix'][i, j]:10.2e}" 
                            for j in range(diag['n_atoms'])])
        print(f"    {i}: {row_str}")
    
    print(f"\n    === Adjacency Matrix (R_b = {blockade_radius} μm) ===")
    print("    ", "  ".join([f"{i:>6}" for i in range(diag['n_atoms'])]))
    for i in range(diag['n_atoms']):
        row_str = "  ".join([f"{int(diag['adjacency_matrix'][i, j]):6d}" 
                            for j in range(diag['n_atoms'])])
        print(f"    {i}: {row_str}")
    
    # Create comprehensive visualization
    print("\n[4] Creating comprehensive visualization...")
    save_path = "geometry_diagnostics_demo.png"
    
    axes = plot_geometry_diagnostics(
        reg,
        blockade_radius=blockade_radius,
        C6=C6,
        show_distances=True,
        show_vdw_matrix=True,
        show_adjacency=True,
        figsize=(18, 14),
        title="4-Atom Chain - Geometry Diagnostics",
        save_path=save_path
    )
    
    print(f"    ✓ Saved to: {save_path}")
    print(f"    ✓ Generated {len(axes)} panels:")
    print(f"       - Panel 1: Register layout with blockade disks")
    print(f"       - Panel 2: Distance matrix (with numerical annotations)")
    print(f"       - Panel 3: VDW interaction matrix (with numerical annotations)")
    print(f"       - Panel 4: Adjacency matrix (with numerical annotations)")
    
    # Create simplified unit disk graph
    print("\n[5] Creating simplified unit disk graph...")
    udg_path = "unit_disk_graph_demo.png"
    
    ax_udg = plot_unit_disk_graph(
        reg,
        blockade_radius=blockade_radius,
        show_distances=True,
        show_labels=True,
        title=f"Unit Disk Graph (R_b = {blockade_radius} μm)",
    )
    
    plt.savefig(udg_path, dpi=150, bbox_inches='tight')
    print(f"    ✓ Saved to: {udg_path}")
    
    # Validation insights
    print("\n[6] Validation Insights:")
    print(f"    • All adjacent atoms are within blockade radius (d=0.6 < R_b=1.0)")
    print(f"    • Non-adjacent pairs are outside blockade (d≥1.2 > R_b=1.0)")
    print(f"    • Graph is a linear chain with 3 edges")
    print(f"    • VDW interactions decay rapidly with distance (r^-6)")
    print(f"    • This configuration is suitable for MWIS problems")
    
    print("\n" + "=" * 70)
    print("✓ GEOMETRY DIAGNOSTICS COMPLETE")
    print("=" * 70)
    print("\n⚠️  REMINDER: These diagnostics are for parameter validation only.")
    print("    They do NOT constitute hardware calibration or performance claims.")
    print("=" * 70)


if __name__ == "__main__":
    main()
