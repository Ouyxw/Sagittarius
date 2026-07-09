"""
MWIS Visualization Example.

Demonstrates the new MWIS problem visualization tools for experimental
workflow and Phase 16 benchmarking.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from sagittarius import Register
from sagittarius.viz import plot_mwis_problem, plot_mwis_comparison, annotate_solution_quality

# 输出目录配置
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def example_basic_mwis():
    """Basic MWIS problem visualization."""
    print("Example 1: Basic MWIS Problem Visualization")
    
    # Create a simple register
    reg = Register.chain(5, spacing=4.0, C6=1.0)
    
    # Define MWIS problem data
    bitstring = "10101"
    weights = [1.2, 0.8, 1.5, 0.9, 1.1]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
    
    # Visualize
    fig, ax = plt.subplots(figsize=(12, 6))
    plot_mwis_problem(
        reg,
        bitstring=bitstring,
        weights=weights,
        edges=edges,
        blockade_radius=5.0,
        ax=ax,
        title="MWIS Solution: Greedy Algorithm"
    )
    
    # Add quality annotation
    annotate_solution_quality(ax, bitstring, weights, edges)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "mwis_example_basic.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: mwis_example_basic.png")


def example_conflict_detection():
    """Visualize constraint violations."""
    print("\nExample 2: Constraint Violation Detection")
    
    reg = Register.chain(5, spacing=4.0, C6=1.0)
    
    # Invalid solution with conflicts
    invalid_bitstring = "11011"  # Adjacent atoms both excited
    weights = [1.2, 0.8, 1.5, 0.9, 1.1]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    plot_mwis_problem(
        reg,
        bitstring=invalid_bitstring,
        weights=weights,
        edges=edges,
        blockade_radius=5.0,
        highlight_conflicts=True,
        conflict_color='red',
        ax=ax,
        title="Invalid Solution: 2 Constraint Violations"
    )
    
    annotate_solution_quality(ax, invalid_bitstring, weights, edges)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "mwis_example_conflicts.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: mwis_example_conflicts.png")


def example_solution_comparison():
    """Compare multiple solutions side-by-side."""
    print("\nExample 3: Solution Comparison")
    
    reg = Register.chain(5, spacing=4.0, C6=1.0)
    
    # Different candidate solutions
    bitstrings = [
        "10101",  # Greedy solution
        "01010",  # Alternative solution
        "10001",  # Suboptimal solution
    ]
    
    titles = [
        "Greedy Solution (Weight: 3.8)",
        "Alternative (Weight: 2.6)",
        "Suboptimal (Weight: 2.3)"
    ]
    
    weights = [1.2, 0.8, 1.5, 0.9, 1.1]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
    
    axes = plot_mwis_comparison(
        reg,
        bitstrings=bitstrings,
        titles=titles,
        weights=weights,
        edges=edges,
        blockade_radius=5.0,
        figsize=(24, 8)
    )
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "mwis_example_comparison.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: mwis_example_comparison.png")


def example_2d_grid():
    """MWIS on 2D grid layout."""
    print("\nExample 4: 2D Grid Layout")
    
    # Create a 3x3 grid
    coords = []
    for i in range(3):
        for j in range(3):
            coords.append((i * 4.0, j * 4.0))
    
    reg = Register.udg(coords, blockade_radius=5.0)
    
    # Random-like bitstring
    bitstring = "101010101"
    weights = [round(0.5 + np.random.rand() * 1.5, 2) for _ in range(9)]
    
    # Derive edges from blockade radius
    edges = []
    # 从 register.atoms 提取位置信息
    pos_array = np.array([[atom.x, atom.y] for atom in reg.atoms])
    for i in range(9):
        for j in range(i+1, 9):
            dist = np.sqrt((pos_array[i, 0] - pos_array[j, 0])**2 + 
                          (pos_array[i, 1] - pos_array[j, 1])**2)
            if dist <= 5.0:
                edges.append((i, j))
    
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        reg,
        bitstring=bitstring,
        weights=weights,
        edges=edges,
        ax=ax,
        title="3x3 Grid MWIS Problem"
    )
    
    annotate_solution_quality(ax, bitstring, weights, edges)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "mwis_example_2d_grid.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: mwis_example_2d_grid.png")


if __name__ == "__main__":
    print("=" * 60)
    print("MWIS Visualization Examples")
    print("=" * 60)
    
    example_basic_mwis()
    example_conflict_detection()
    example_solution_comparison()
    example_2d_grid()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
