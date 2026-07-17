"""
Basis diagnostics demonstration for small quantum systems.

This example shows how to use the basis space diagnostics tools to understand
Hilbert space structure, valid/forbidden bitstrings, and blockade constraints.

DIAGNOSTIC TOOLS: For small systems only (N ≤ 10).
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sagittarius import Register
from sagittarius.viz import (
    generate_basis_diagnostics,
    plot_comprehensive_basis_diagnostics,
)

# 输出目录配置 - example同目录下的output文件夹
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    """Demonstrate basis diagnostics on a 4-atom chain."""
    
    print("=" * 70)
    print("BASIS SPACE DIAGNOSTICS DEMONSTRATION")
    print("=" * 70)
    
    # Create a 4-atom chain register
    reg = Register.chain(4, spacing=0.6, C6=10.0)
    blockade_radius = 1.0
    
    print(f"\nRegister: {len(reg.atoms)}-atom chain")
    print(f"Blockade radius: {blockade_radius} μm")
    
    # Generate diagnostics
    print("\nGenerating basis diagnostics...")
    diagnostics = generate_basis_diagnostics(reg, blockade_radius)
    
    # Print summary
    print(f"\n{'='*70}")
    print("DIAGNOSTICS SUMMARY")
    print(f"{'='*70}")
    print(f"Atoms: {diagnostics['n_atoms']}")
    print(f"Full Hilbert space dimension: {diagnostics['full_dimension']}")
    print(f"Reduced basis dimension: {diagnostics['reduced_dimension']}")
    print(f"Forbidden states: {len(diagnostics['forbidden_states'])}")
    print(f"Pruning ratio: {diagnostics['pruning_ratio']:.2%}")
    print(f"Blockade edges: {len(diagnostics['edges'])}")
    print(f"Graph density: {diagnostics['blockade_graph_density']:.2f}")
    
    print(f"\n{'='*70}")
    print("VALID BITSTRINGS (in reduced basis)")
    print(f"{'='*70}")
    for i, bs in enumerate(diagnostics['valid_bitstrings']):
        state_int = diagnostics['valid_states'][i]
        print(f"  State {state_int:2d}: {bs}")
    
    if diagnostics['forbidden_bitstrings']:
        print(f"\n{'='*70}")
        print("FORBIDDEN BITSTRINGS (violate blockade constraints)")
        print(f"{'='*70}")
        for i, bs in enumerate(diagnostics['forbidden_bitstrings'][:10]):  # Show first 10
            state_int = diagnostics['forbidden_states'][i]
            print(f"  State {state_int:2d}: {bs}")
        if len(diagnostics['forbidden_bitstrings']) > 10:
            print(f"  ... and {len(diagnostics['forbidden_bitstrings']) - 10} more")
    
    # Create comprehensive visualization
    print(f"\n{'='*70}")
    print("GENERATING VISUALIZATION")
    print(f"{'='*70}")
    
    axes = plot_comprehensive_basis_diagnostics(
        diagnostics,
        reg,
        figsize=(18, 14),
        save_path=os.path.join(OUTPUT_DIR, "basis_diagnostics_demo.png"),
    )
    
    print(f"\n✓ Comprehensive diagnostic figure saved to:")
    print(f"  {os.path.join(OUTPUT_DIR, 'basis_diagnostics_demo.png')}")
    print(f"\nFigure contains 3 panels:")
    print(f"  1. Basis space dimensions (bar chart)")
    print(f"  2. Bitstring space grid (colored by validity)")
    print(f"  3. Blockade constraint graph (register layout)")
    
    plt.close()
    
    print(f"\n{'='*70}")
    print("⚠️  IMPORTANT NOTES")
    print(f"{'='*70}")
    print("• These are DIAGNOSTIC tools for understanding basis structure")
    print("• Limited to small systems (N ≤ 10) for tractability")
    print("• All bitstrings sorted by ascending integer value")
    print("• Follows Sagittarius unified sorting convention")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
