#!/usr/bin/env python3
"""
Phase 19 Visualization Module - Complete Usage Examples

This script demonstrates all P0 visualization features implemented in
sagittarius.viz module. It can be run standalone to generate sample plots.

Usage:
    python examples_phase19_viz.py [--show] [--output-dir OUTPUT_DIR]

Options:
    --show          Display plots interactively (requires GUI backend)
    --output-dir    Directory to save plots (default: ./viz_examples)
"""

import argparse
import os
import sys
from pathlib import Path

# Use non-interactive backend for batch generation
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np

# Add sagittarius to path if running from docs/ directory
sys.path.insert(0, str(Path(__file__).parent.parent / 'sagittarius_py'))

from sagittarius import Simulation, Register, Pulse
from sagittarius.viz import (
    plot_register,
    plot_interaction_graph,
    plot_pulse_waveform,
    plot_observables,
    plot_bitstring_distribution,
    plot_shot_histogram,
    plot_population_heatmap,
    plot_result_summary,
)
from sagittarius.viz.pulse import plot_pulse_both_fields


def example_1_register_layout(output_dir):
    """Example 1: Register layout with blockade edges"""
    print("\n📊 Example 1: Register Layout Visualization")
    print("=" * 60)
    
    # Create different register geometries
    chain_reg = Register.chain(5, spacing=5.0)
    
    # Plot basic register
    ax = plot_register(chain_reg, blockade_radius=6.0, title="Chain Register (5 atoms)")
    ax.figure.savefig(output_dir / "register_chain.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: register_chain.png")
    
    # Highlight specific atoms (e.g., MWIS solution)
    ax = plot_register(
        chain_reg, 
        blockade_radius=6.0,
        highlight_atoms=[0, 2, 4],
        highlight_color='gold',
        title="MWIS Solution (atoms 0, 2, 4 selected)"
    )
    ax.figure.savefig(output_dir / "register_mwis.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: register_mwis.png")
    
    # Interaction graph with distances
    ax = plot_interaction_graph(chain_reg, blockade_radius=6.0, show_distances=True)
    ax.figure.savefig(output_dir / "interaction_graph.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: interaction_graph.png")


def example_2_pulse_waveforms(output_dir):
    """Example 2: Pulse waveform sampling and plotting"""
    print("\n📊 Example 2: Pulse Waveform Visualization")
    print("=" * 60)
    
    # Constant pulse
    pulse_const = Pulse.global_(omega=2.0, delta=0.5, duration=10.0)
    
    ax = plot_pulse_waveform(pulse_const, field='omega', title="Constant Rabi Frequency")
    ax.figure.savefig(output_dir / "pulse_constant_omega.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: pulse_constant_omega.png")
    
    # Time-dependent pulse
    pulse_var = Pulse.global_(
        omega=lambda t: 2.0 * np.exp(-((t - 5)**2) / 8),  # Gaussian envelope
        delta=lambda t: 1.0 - 0.2 * t,  # Linear sweep
        duration=10.0
    )
    
    # Plot omega
    ax = plot_pulse_waveform(pulse_var, field='omega', title="Gaussian Rabi Pulse")
    ax.figure.savefig(output_dir / "pulse_gaussian_omega.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: pulse_gaussian_omega.png")
    
    # Plot delta
    ax = plot_pulse_waveform(pulse_var, field='delta', title="Linear Detuning Sweep")
    ax.figure.savefig(output_dir / "pulse_linear_delta.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: pulse_linear_delta.png")
    
    # Both fields together
    ax = plot_pulse_both_fields(pulse_var, title="Pulse Sequence: Ω and Δ")
    ax.figure.savefig(output_dir / "pulse_both_fields.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: pulse_both_fields.png")
    
    # Custom time grid
    custom_times = np.linspace(0, 10, 500)
    ax = plot_pulse_waveform(
        pulse_var, 
        time_grid=custom_times, 
        field='omega',
        title="High-Resolution Sampling (500 points)"
    )
    ax.figure.savefig(output_dir / "pulse_high_res.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: pulse_high_res.png")


def example_3_simulation_results(output_dir):
    """Example 3: Full simulation result visualization"""
    print("\n📊 Example 3: Simulation Result Visualization")
    print("=" * 60)
    
    # Create a small simulation
    reg = Register.chain(3, spacing=5.0)
    pulse = Pulse.global_(
        omega=lambda t: 2.0 * np.sin(np.pi * t / 5),
        delta=0.0,
        duration=5.0
    )
    
    sim = Simulation(
        register=reg,
        pulse=pulse,
        observables={'pop0': 0, 'pop1': 1, 'pop2': 2}
    )
    
    print("  Running simulation...")
    result = sim.run()
    print(f"  ✅ Simulation complete. Basis size: {result.metadata.get('basis_size', 'N/A')}")
    
    # Sample measurements
    print("  Sampling measurements (500 shots)...")
    result.sample(shots=500, seed=42)
    print(f"  ✅ Sampling complete.")
    
    # Observable trajectories
    ax = plot_observables(result, title="Rydberg Population Dynamics")
    ax.figure.savefig(output_dir / "result_observables.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: result_observables.png")
    
    # Select specific observables
    ax = plot_observables(result, names=['pop0', 'pop2'], title="Selected Atoms (0, 2)")
    ax.figure.savefig(output_dir / "result_selected_obs.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: result_selected_obs.png")
    
    # Bitstring distribution
    ax = plot_bitstring_distribution(result, top_k=8, title="Final State Probabilities")
    ax.figure.savefig(output_dir / "result_bitstrings.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: result_bitstrings.png")
    
    # Shot histogram
    ax = plot_shot_histogram(result, top_k=12, title="Measurement Shot Distribution")
    ax.figure.savefig(output_dir / "result_shots.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: result_shots.png")
    
    # Normalized shot frequencies
    ax = plot_shot_histogram(result, normalize=True, bar_color='lightgreen',
                            title="Normalized Shot Frequencies")
    ax.figure.savefig(output_dir / "result_shots_normalized.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: result_shots_normalized.png")
    
    # Population heatmap
    ax = plot_population_heatmap(result, cmap='plasma', title="Population Heatmap")
    ax.figure.savefig(output_dir / "result_heatmap.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: result_heatmap.png")
    
    # Alternative colormap
    ax = plot_population_heatmap(result, cmap='coolwarm', title="Population (coolwarm)")
    ax.figure.savefig(output_dir / "result_heatmap_coolwarm.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: result_heatmap_coolwarm.png")


def example_4_summary_report(output_dir):
    """Example 4: Comprehensive summary report"""
    print("\n📊 Example 4: Summary Report Generation")
    print("=" * 60)
    
    # Reuse simulation from Example 3
    reg = Register.chain(3, spacing=5.0)
    pulse = Pulse.global_(omega=2.0, delta=0.0, duration=5.0)
    sim = Simulation(
        register=reg,
        pulse=pulse,
        observables={'pop0': 0, 'pop1': 1, 'pop2': 2}
    )
    result = sim.run()
    result.sample(shots=300, seed=99)
    
    # Generate summary
    print("  Generating comprehensive summary...")
    axes = plot_result_summary(result, figsize=(16, 12))
    
    # Customize individual panels
    axes[0].set_ylim(-0.1, 1.1)  # Observables
    axes[1].tick_params(axis='x', rotation=30)  # Bitstrings
    
    axes[2].figure.savefig(output_dir / "summary_report.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: summary_report.png")


def example_5_custom_combinations(output_dir):
    """Example 5: Custom multi-panel figures"""
    print("\n📊 Example 5: Custom Multi-Panel Combinations")
    print("=" * 60)
    
    # Setup simulation
    reg = Register.chain(4, spacing=5.0)
    pulse = Pulse.global_(
        omega=lambda t: 1.5 + 0.5 * np.cos(2 * np.pi * t / 10),
        delta=lambda t: 0.5 * np.sin(2 * np.pi * t / 10),
        duration=10.0
    )
    sim = Simulation(
        register=reg,
        pulse=pulse,
        observables={f'pop{i}': i for i in range(4)}
    )
    result = sim.run()
    result.sample(shots=400, seed=77)
    
    # Create custom 2x3 layout
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    
    # Panel 1: Register
    plot_register(reg, blockade_radius=6.0, ax=axes[0, 0])
    axes[0, 0].set_title("Register Geometry")
    
    # Panel 2: Pulse omega
    plot_pulse_waveform(pulse, field='omega', ax=axes[0, 1])
    axes[0, 1].set_title("Rabi Frequency Ω(t)")
    
    # Panel 3: Pulse delta
    plot_pulse_waveform(pulse, field='delta', ax=axes[0, 2])
    axes[0, 2].set_title("Detuning Δ(t)")
    
    # Panel 4: Observables
    plot_observables(result, ax=axes[1, 0])
    axes[1, 0].set_title("Population Dynamics")
    axes[1, 0].set_ylim(-0.1, 1.1)
    
    # Panel 5: Bitstring dist
    plot_bitstring_distribution(result, top_k=6, ax=axes[1, 1])
    axes[1, 1].set_title("Top-6 Bitstrings")
    axes[1, 1].tick_params(axis='x', rotation=25)
    
    # Panel 6: Heatmap
    plot_population_heatmap(result, ax=axes[1, 2], cmap='viridis')
    axes[1, 2].set_title("Population Heatmap")
    
    plt.tight_layout()
    fig.savefig(output_dir / "custom_multipanel.png", dpi=150, bbox_inches='tight')
    plt.close('all')
    print(f"  ✅ Saved: custom_multipanel.png")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 19 Visualization Examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all examples to default directory
  python examples_phase19_viz.py
  
  # Save to custom directory
  python examples_phase19_viz.py --output-dir ./my_plots
  
  # Show plots interactively (requires GUI)
  python examples_phase19_viz.py --show
        """
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help='Display plots interactively instead of saving to files'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./viz_examples',
        help='Directory to save plot files (default: ./viz_examples)'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Output directory: {output_dir.absolute()}")
    
    if args.show:
        # Switch to interactive backend
        matplotlib.use('TkAgg')
        print("⚠️  Interactive mode enabled. Close each plot window to continue.\n")
    
    try:
        # Run all examples
        example_1_register_layout(output_dir)
        example_2_pulse_waveforms(output_dir)
        example_3_simulation_results(output_dir)
        example_4_summary_report(output_dir)
        example_5_custom_combinations(output_dir)
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print(f"📁 Generated {len(list(output_dir.glob('*.png')))} plots in {output_dir}")
        print("=" * 60)
        
        if not args.show:
            print("\n💡 Tip: Use --show flag to display plots interactively")
            print(f"💡 View plots: ls -lh {output_dir}/*.png")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
