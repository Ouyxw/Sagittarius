"""
Minimal examples for sweep visualization.

Demonstrates:
- Sweep heatmaps (2D parameter scans)
- Line slices (1D parameter sweeps)
- Final observable maps
- Failed run masks
- Summary statistics extraction

All examples use synthetic data since user-facing sweep artifacts are not yet implemented.
"""

import numpy as np
import matplotlib.pyplot as plt
from sagittarius.viz import (
    plot_sweep_heatmap,
    plot_sweep_line_slice,
    plot_final_observable_map,
    plot_observables_comparison,
    plot_failed_run_mask,
    extract_sweep_summary,
    generate_synthetic_sweep_data,
)


def example_1_sweep_heatmap():
    """Example 1: 2D parameter sweep heatmap with failed runs overlay."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Sweep Heatmap")
    print("="*80)
    
    # Generate synthetic sweep data
    sweep_data = generate_synthetic_sweep_data(
        omega_range=(0.5, 5.0),
        delta_range=(-3.0, 3.0),
        n_omega=25,
        n_delta=20,
        seed=42,
        failure_rate=0.08,
    )
    
    print(f"Generated sweep data:")
    print(f"  • Omega range: {sweep_data['parameters']['omega'][0]:.2f} to {sweep_data['parameters']['omega'][-1]:.2f}")
    print(f"  • Delta range: {sweep_data['parameters']['delta'][0]:.2f} to {sweep_data['parameters']['delta'][-1]:.2f}")
    print(f"  • Grid size: {len(sweep_data['parameters']['omega'])} x {len(sweep_data['parameters']['delta'])}")
    print(f"  • Failed runs: {len(sweep_data['failed_runs'])}")
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 9))
    plot_sweep_heatmap(
        sweep_data,
        x_param='omega',
        y_param='delta',
        metric='pop0',
        ax=ax,
        show_colorbar=True,
        show_failed_mask=True,
        title="Rabi Frequency vs Detuning Sweep",
        cmap='viridis',
    )
    
    plt.savefig('example_sweep_heatmap.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: example_sweep_heatmap.png")
    print("  • Features:")
    print("    - 2D colormap showing pop0 values")
    print("    - Red X markers indicate failed runs")
    print("    - Colorbar with metric label")
    print("    - Disclaimer: EXPLORATORY VISUALIZATION")
    print("  • Backend: NONE (synthetic data)")
    print("  • Classification: EXPLORATORY")
    
    plt.close()


def example_2_line_slice():
    """Example 2: 1D line slice through sweep data."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Line Slice")
    print("="*80)
    
    # Generate synthetic sweep data
    sweep_data = generate_synthetic_sweep_data(
        omega_range=(0.5, 5.0),
        delta_range=(-3.0, 3.0),
        n_omega=30,
        n_delta=15,
        seed=123,
        failure_rate=0.05,
    )
    
    print(f"Generated sweep data with {len(sweep_data['parameters']['omega'])} omega values")
    
    # Create line slice at delta = 0
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_sweep_line_slice(
        sweep_data,
        fixed_param='delta',
        fixed_value=0.0,
        varying_param='omega',
        metric='pop0',
        ax=ax,
        show_error_bars=True,
        title="Population vs Rabi Frequency (δ=0)",
        color='steelblue',
        marker='o',
    )
    
    plt.savefig('example_line_slice.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: example_line_slice.png")
    print("  • Features:")
    print("    - 1D slice at fixed detuning (δ=0)")
    print("    - Error bars showing ±std")
    print("    - Smooth curve with markers")
    print("    - Disclaimer: EXPLORATORY VISUALIZATION")
    print("  • Backend: NONE (synthetic data)")
    print("  • Classification: EXPLORATORY")
    
    plt.close()


def example_3_final_observable_map():
    """Example 3: Final observable values across parameter sweep."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Final Observable Map")
    print("="*80)
    
    # Generate 1D sweep data
    omega_vals = np.linspace(0.5, 5.0, 40)
    # Simulate time evolution for each omega
    time_points = np.linspace(0, 2, 100)
    pop0_time = np.array([
        np.sin(omega * time_points)**2 * np.exp(-0.1 * time_points)
        for omega in omega_vals
    ])
    
    sweep_data = {
        'parameters': {
            'omega': omega_vals,
        },
        'results': {
            'pop0': pop0_time,  # Shape: (40, 100) - params x time
        },
    }
    
    print(f"Generated time-series data:")
    print(f"  • Omega values: {len(omega_vals)}")
    print(f"  • Time points: {pop0_time.shape[1]}")
    print(f"  • Data shape: {pop0_time.shape}")
    
    # Create final observable map
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_final_observable_map(
        sweep_data,
        observable_name='pop0',
        param_name='omega',
        ax=ax,
        show_markers=True,
        title="Final Population vs Rabi Frequency",
        color='darkgreen',
    )
    
    plt.savefig('example_final_observable.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: example_final_observable.png")
    print("  • Features:")
    print("    - Extracts final time point from time series")
    print("    - Shows population as function of omega")
    print("    - Markers at each data point")
    print("    - Disclaimer: EXPLORATORY VISUALIZATION")
    print("  • Backend: NONE (synthetic data)")
    print("  • Classification: EXPLORATORY")
    
    plt.close()


def example_4_failed_run_mask():
    """Example 4: Binary mask showing failed vs successful runs."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Failed Run Mask")
    print("="*80)
    
    # Generate sweep data with higher failure rate
    sweep_data = generate_synthetic_sweep_data(
        omega_range=(0.5, 5.0),
        delta_range=(-3.0, 3.0),
        n_omega=20,
        n_delta=15,
        seed=456,
        failure_rate=0.15,  # 15% failure rate
    )
    
    n_total = len(sweep_data['parameters']['omega']) * len(sweep_data['parameters']['delta'])
    n_failed = len(sweep_data['failed_runs'])
    success_rate = (1 - n_failed / n_total) * 100
    
    print(f"Generated sweep data:")
    print(f"  • Total runs: {n_total}")
    print(f"  • Failed runs: {n_failed}")
    print(f"  • Success rate: {success_rate:.1f}%")
    
    # Create failed run mask
    fig, ax = plt.subplots(figsize=(10, 8))
    plot_failed_run_mask(
        sweep_data,
        x_param='omega',
        y_param='delta',
        ax=ax,
        title="Run Success/Failure Map",
    )
    
    plt.savefig('example_failed_mask.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: example_failed_mask.png")
    print("  • Features:")
    print("    - Green cells: successful runs")
    print("    - Red cells: failed runs")
    print("    - Success rate in title")
    print("    - Manifest link count if available")
    print("    - Disclaimer: EXPLORATORY VISUALIZATION")
    print("  • Backend: NONE (synthetic data)")
    print("  • Classification: EXPLORATORY")
    
    plt.close()


def example_5_sweep_summary():
    """Example 5: Extract and display sweep summary statistics."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Sweep Summary Statistics")
    print("="*80)
    
    # Generate sweep data
    sweep_data = generate_synthetic_sweep_data(
        omega_range=(0.5, 5.0),
        delta_range=(-3.0, 3.0),
        n_omega=20,
        n_delta=15,
        seed=789,
        failure_rate=0.1,
    )
    
    # Extract summary
    summary = extract_sweep_summary(sweep_data, metrics=['pop0', 'energy'])
    
    print("\nSummary Statistics:")
    print("-" * 80)
    
    for metric, stats in summary.items():
        if metric == 'run_statistics':
            print(f"\n{metric.upper().replace('_', ' ')}:")
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"  • {key}: {value:.2f}")
                else:
                    print(f"  • {key}: {value}")
        else:
            print(f"\n{metric.upper()}:")
            print(f"  • Min:    {stats['min']:.4f}")
            print(f"  • Max:    {stats['max']:.4f}")
            print(f"  • Mean:   {stats['mean']:.4f}")
            print(f"  • Std:    {stats['std']:.4f}")
            print(f"  • Median: {stats['median']:.4f}")
            print(f"  • Q25:    {stats['q25']:.4f}")
            print(f"  • Q75:    {stats['q75']:.4f}")
    
    print("\n✓ Summary extracted successfully")
    print("  • Includes statistical measures for each metric")
    print("  • Includes run success/failure statistics")
    print("  • Backend: NONE (pure Python/NumPy)")


def example_6_complete_workflow():
    """Example 6: Complete sweep analysis workflow."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Complete Sweep Analysis Workflow")
    print("="*80)
    
    # Step 1: Generate sweep data
    print("\n[Step 1] Generating synthetic sweep data...")
    sweep_data = generate_synthetic_sweep_data(
        omega_range=(1.0, 4.0),
        delta_range=(-2.0, 2.0),
        n_omega=20,
        n_delta=15,
        seed=2026,
        failure_rate=0.07,
    )
    print(f"  ✓ Generated {len(sweep_data['parameters']['omega'])} x {len(sweep_data['parameters']['delta'])} grid")
    
    # Step 2: Extract summary statistics
    print("\n[Step 2] Extracting summary statistics...")
    summary = extract_sweep_summary(sweep_data)
    print(f"  ✓ pop0 range: [{summary['pop0']['min']:.3f}, {summary['pop0']['max']:.3f}]")
    print(f"  ✓ Success rate: {summary['run_statistics']['success_rate']:.1f}%")
    
    # Step 3: Create comprehensive visualization
    print("\n[Step 3] Creating visualizations...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Heatmap
    plot_sweep_heatmap(sweep_data, ax=axes[0, 0], title="Sweep Heatmap")
    
    # Line slice
    plot_sweep_line_slice(
        sweep_data,
        fixed_param='delta',
        fixed_value=0.0,
        varying_param='omega',
        ax=axes[0, 1],
        title="Line Slice (δ=0)"
    )
    
    # Failed run mask
    plot_failed_run_mask(sweep_data, ax=axes[1, 0], title="Failed Run Mask")
    
    # Final observable map
    plot_final_observable_map(
        sweep_data,
        observable_name='pop0',
        param_name='omega',
        ax=axes[1, 1],
        title="Final Observable Map"
    )
    
    plt.tight_layout()
    plt.savefig('example_complete_workflow.png', dpi=150, bbox_inches='tight')
    print(f"  ✓ Saved: example_complete_workflow.png")
    print("  • 4-panel figure showing complete analysis")
    print("  • All plots include disclaimers")
    print("  • All plots preserve parameter values")
    print("  • Backend: NONE (synthetic data)")
    print("  • Classification: EXPLORATORY")
    
    plt.close()


def example_7_observables_comparison():
    """Example 7: Multiple observables comparison on single plot."""
    print("\n" + "="*80)
    print("EXAMPLE 7: Observables Comparison")
    print("="*80)
    
    # Generate sweep data with multiple observables
    omega_vals = np.linspace(0.5, 5.0, 30)
    
    # Create multiple observables with different behaviors
    pop0 = np.sin(omega_vals)**2 * np.exp(-0.1 * omega_vals)
    pop1 = np.cos(omega_vals)**2 * np.exp(-0.1 * omega_vals)
    energy = omega_vals**2 / (1 + omega_vals)
    coherence = np.sin(2 * omega_vals) * np.exp(-0.05 * omega_vals)
    
    sweep_data = {
        'parameters': {
            'omega': omega_vals,
        },
        'results': {
            'pop0': pop0,
            'pop1': pop1,
            'energy': energy,
            'coherence': coherence,
        },
    }
    
    print(f"Generated sweep data with {len(omega_vals)} omega values")
    print(f"Observables: pop0, pop1, energy, coherence")
    
    # Create comparison plot
    fig, ax = plt.subplots(figsize=(12, 7))
    plot_observables_comparison(
        sweep_data,
        observables=['pop0', 'pop1', 'energy', 'coherence'],
        param_name='omega',
        ax=ax,
        show_markers=True,
        title="Multiple Observables vs Rabi Frequency",
    )
    
    plt.savefig('example_observables_comparison.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: example_observables_comparison.png")
    print("  • Features:")
    print("    - Multiple observables on same axes")
    print("    - Auto-assigned colors from tab10 colormap")
    print("    - Markers at each data point")
    print("    - Legend with all observable names")
    print("    - Disclaimer: EXPLORATORY VISUALIZATION")
    print("  • Backend: NONE (synthetic data)")
    print("  • Classification: EXPLORATORY")
    
    plt.close()
    
    # Example with normalization
    print("\n--- Normalized Comparison ---")
    fig, ax = plt.subplots(figsize=(12, 7))
    plot_observables_comparison(
        sweep_data,
        observables=['pop0', 'pop1', 'energy'],
        normalize=True,
        ax=ax,
        title="Normalized Observables Comparison",
    )
    
    plt.savefig('example_observables_normalized.png', dpi=150, bbox_inches='tight')
    print(f"✓ Saved: example_observables_normalized.png")
    print("  • All values normalized to [0, 1] range")
    print("  • Easier visual comparison of trends")
    
    plt.close()


# ============================================================================
# Main execution
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SWEEP VISUALIZATION EXAMPLES")
    print("="*80)
    print("\nThis script demonstrates sweep visualization capabilities:")
    print("  1. Sweep Heatmap (2D parameter scan)")
    print("  2. Line Slice (1D parameter sweep)")
    print("  3. Final Observable Map")
    print("  4. Failed Run Mask")
    print("  5. Summary Statistics")
    print("  6. Complete Workflow")
    print("\nNote: All examples use SYNTHETIC DATA")
    print("      User-facing sweep artifacts are not yet implemented.")
    
    example_1_sweep_heatmap()
    example_2_line_slice()
    example_3_final_observable_map()
    example_4_failed_run_mask()
    example_5_sweep_summary()
    example_6_complete_workflow()
    example_7_observables_comparison()
    
    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
    print("="*80)
    print("\nKey features demonstrated:")
    print("  ✓ 2D heatmaps with failed run overlay")
    print("  ✓ 1D line slices with error bars")
    print("  ✓ Final observable extraction from time series")
    print("  ✓ Binary success/failure masks")
    print("  ✓ Statistical summary extraction")
    print("  ✓ Multiple observables comparison (NEW)")
    print("  ✓ Artifact link preservation")
    print("  ✓ Mandatory disclaimers on all plots")
    print("  ✓ No backend dependency (pure Python/NumPy/Matplotlib)")
    print("\nCompliance with requirements:")
    print("  ✓ Preserves parameter values")
    print("  ✓ Preserves result locations")
    print("  ✓ Marks failed runs clearly")
    print("  ✓ Links to run manifests when available")
    print("  ✓ Clearly marked as EXPLORATORY (not for calibration)")
