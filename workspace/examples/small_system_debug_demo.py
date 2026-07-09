"""
Small-system debugging visualization examples.

Demonstrates diagnostic views for low-dimensional Hilbert spaces, including:
- State probability vectors
- Density matrix diagonal (populations)
- Density matrix magnitude heatmaps
- Density matrix phase heatmaps

IMPORTANT: These tools are ONLY applicable to small systems (≤ 10 qubits).
For larger systems, clear error messages are raised when dimensions exceed safe limits.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from sagittarius.viz import (
    plot_state_probabilities,
    plot_density_matrix_diagonal,
    plot_density_matrix_magnitude,
    plot_density_matrix_phase,
)

# 输出目录配置
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def example_bell_state():
    """Example 1: Bell state probability distribution."""
    print("=" * 80)
    print("Example 1: Bell State |Φ⁺⟩ = (|00⟩ + |11⟩)/√2")
    print("=" * 80)
    
    # Bell state
    psi = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)], dtype=complex)
    
    # Plot probabilities
    ax = plot_state_probabilities(psi, show_labels=True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'debug_bell_state_probabilities.png'), dpi=150, bbox_inches='tight')
    print("✓ Saved: debug_bell_state_probabilities.png")
    plt.close()
    
    probs = np.abs(psi)**2
    print(f"  • State vector dimension: {len(psi)} (2 qubits)")
    print(f"  • Non-zero probabilities: {np.sum(probs > 1e-10)}")
    print(f"  • Probabilities: |00⟩={probs[0]:.3f}, |11⟩={probs[3]:.3f}\n")


def example_ghz_state():
    """Example 2: GHZ state for 3 qubits."""
    print("=" * 80)
    print("Example 2: GHZ State |GHZ⟩ = (|000⟩ + |111⟩)/√2")
    print("=" * 80)
    
    # GHZ state
    psi = np.zeros(8, dtype=complex)
    psi[0] = 1/np.sqrt(2)  # |000⟩
    psi[7] = 1/np.sqrt(2)  # |111⟩
    
    # Plot probabilities
    ax = plot_state_probabilities(psi, show_labels=True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'debug_ghz_state_probabilities.png'), dpi=150, bbox_inches='tight')
    print("✓ Saved: debug_ghz_state_probabilities.png")
    plt.close()
    
    probs = np.abs(psi)**2
    print(f"  • State vector dimension: {len(psi)} (3 qubits)")
    print(f"  • Non-zero probabilities: {np.sum(probs > 1e-10)}")
    print(f"  • Probabilities: |000⟩={probs[0]:.3f}, |111⟩={probs[7]:.3f}\n")


def example_mixed_state_diagonal():
    """Example 3: Mixed state density matrix diagonal."""
    print("=" * 80)
    print("Example 3: Maximally Mixed State ρ = I/2")
    print("=" * 80)
    
    # Maximally mixed state for 1 qubit
    rho = np.array([[0.5, 0], [0, 0.5]], dtype=complex)
    
    # Plot diagonal
    ax = plot_density_matrix_diagonal(rho, normalize=True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'debug_mixed_state_diagonal.png'), dpi=150, bbox_inches='tight')
    print("✓ Saved: debug_mixed_state_diagonal.png")
    plt.close()
    
    diag = np.real(np.diag(rho))
    print(f"  • Density matrix shape: {rho.shape}")
    print(f"  • Diagonal elements: ρ₀₀={diag[0]:.3f}, ρ₁₁={diag[1]:.3f}")
    print(f"  • Trace: {np.trace(rho):.3f}\n")


def example_pure_state_with_coherence():
    """Example 4: Pure state with coherences - full density matrix."""
    print("=" * 80)
    print("Example 4: Superposition State |+⟩ = (|0⟩ + |1⟩)/√2")
    print("=" * 80)
    
    # |+⟩ state density matrix
    psi = np.array([1/np.sqrt(2), 1/np.sqrt(2)], dtype=complex)
    rho = np.outer(psi, psi.conj())
    
    print(f"  • Density matrix:\n{rho}\n")
    
    # Plot magnitude heatmap
    ax = plot_density_matrix_magnitude(rho, show_values=True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'debug_pure_state_magnitude.png'), dpi=150, bbox_inches='tight')
    print("✓ Saved: debug_pure_state_magnitude.png")
    plt.close()
    
    # Plot phase heatmap
    ax = plot_density_matrix_phase(rho, threshold=1e-10)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'debug_pure_state_phase.png'), dpi=150, bbox_inches='tight')
    print("✓ Saved: debug_pure_state_phase.png")
    plt.close()
    
    magnitude = np.abs(rho)
    phase = np.angle(rho)
    print(f"  • Off-diagonal magnitude: |ρ₀₁|={magnitude[0,1]:.3f}")
    print(f"  • Off-diagonal phase: arg(ρ₀₁)={phase[0,1]:.3f} rad\n")


def example_complex_coherences():
    """Example 5: Density matrix with complex coherences."""
    print("=" * 80)
    print("Example 5: Complex Coherences with Phase Structure")
    print("=" * 80)
    
    # Create a 2-qubit density matrix with complex off-diagonals
    dim = 4
    rho = np.eye(dim, dtype=complex) / dim  # Start with maximally mixed
    
    # Add some complex coherences
    rho[0, 1] = 0.05 * np.exp(1j * np.pi/4)   # Phase = π/4
    rho[1, 0] = 0.05 * np.exp(-1j * np.pi/4)  # Conjugate
    rho[2, 3] = 0.08 * np.exp(1j * np.pi/2)   # Phase = π/2
    rho[3, 2] = 0.08 * np.exp(-1j * np.pi/2)  # Conjugate
    
    # Ensure Hermiticity and trace = 1
    rho = (rho + rho.conj().T) / 2
    rho = rho / np.trace(rho)
    
    # Plot magnitude
    ax = plot_density_matrix_magnitude(rho, show_values=False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'debug_complex_coherences_magnitude.png'), dpi=150, bbox_inches='tight')
    print("✓ Saved: debug_complex_coherences_magnitude.png")
    plt.close()
    
    # Plot phase
    ax = plot_density_matrix_phase(rho, threshold=1e-3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'debug_complex_coherences_phase.png'), dpi=150, bbox_inches='tight')
    print("✓ Saved: debug_complex_coherences_phase.png")
    plt.close()
    
    print(f"  • Density matrix dimension: {dim}×{dim} (2 qubits)")
    print(f"  • Non-zero coherences: {np.sum(np.abs(rho) > 1e-3) - dim}")
    print(f"  • Phase range: [{np.min(np.angle(rho[np.abs(rho) > 1e-3])):.2f}, "
          f"{np.max(np.angle(rho[np.abs(rho) > 1e-3])):.2f}] rad\n")


def example_dimension_limit_error():
    """Example 6: Demonstrate dimension limit error handling."""
    print("=" * 80)
    print("Example 6: Dimension Limit Validation")
    print("=" * 80)
    
    # Try to visualize a state that's too large (> 10 qubits)
    try:
        large_dim = 2**11  # 2048 > MAX_SAFE_DIM (1024)
        psi = np.zeros(large_dim, dtype=complex)
        psi[0] = 1.0
        
        plot_state_probabilities(psi)
        print("  ❌ Should have raised ValueError!")
        
    except ValueError as e:
        print(f"  ✓ Correctly caught dimension limit error:")
        print(f"    {str(e)[:100]}...\n")


def example_unphysical_state_warning():
    """Example 7: Demonstrate unphysical state warning."""
    print("=" * 80)
    print("Example 7: Unphysical State Detection")
    print("=" * 80)
    
    import warnings
    
    # Create an unphysical density matrix with negative population
    rho = np.array([[-0.1, 0], [0, 1.1]], dtype=complex)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ax = plot_density_matrix_diagonal(rho, normalize=False)
        plt.close()
        
        if len(w) > 0:
            print(f"  ✓ Warning raised: {w[0].message}\n")


def main():
    """Run all small-system debugging visualization examples."""
    print("\n" + "=" * 80)
    print("Sagittarius Small-System Debugging Visualization Examples")
    print("=" * 80)
    print("\n⚠️  IMPORTANT: These tools are ONLY for small systems (≤ 10 qubits).")
    print("   All charts include 'DIAGNOSTIC VIEW' disclaimers.\n")
    
    try:
        example_bell_state()
        example_ghz_state()
        example_mixed_state_diagonal()
        example_pure_state_with_coherence()
        example_complex_coherences()
        example_dimension_limit_error()
        example_unphysical_state_warning()
        
        print("=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80)
        print("\nGenerated files:")
        print("  • debug_bell_state_probabilities.png")
        print("  • debug_ghz_state_probabilities.png")
        print("  • debug_mixed_state_diagonal.png")
        print("  • debug_pure_state_magnitude.png")
        print("  • debug_pure_state_phase.png")
        print("  • debug_complex_coherences_magnitude.png")
        print("  • debug_complex_coherences_phase.png")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        raise


if __name__ == '__main__':
    main()
