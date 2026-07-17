"""
Spatial snapshot and animation frame extraction demo.

Demonstrates how to extract spatial configuration data at specific time steps,
generate standardized frame data for animations, and visualize atom-by-atom
observable values mapped to colors on the register layout.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig
from sagittarius.viz import (
    extract_spatial_snapshot,
    extract_frame_sequence,
    save_frame_data,
    plot_spatial_snapshot,
    plot_multi_panel_snapshots,
)

# 输出目录配置
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    print("=" * 80)
    print("Spatial Snapshot & Animation Frame Extraction Demo")
    print("=" * 80)
    
    # Create a simple 4-atom chain
    print("\n1. Creating 4-atom chain register...")
    reg = Register.chain(4, spacing=1.0, C6=80.0)
    print(f"   ✓ Created register with {len(reg.atoms)} atoms")
    
    # Define pulse sequence
    print("\n2. Setting up pulse sequence...")
    seq = PulseSequence(omega=2.0 * np.pi, delta=0.0)
    cfg = SolverConfig(reltol=1e-7, abstol=1e-7, saveat=50)
    
    sim = Simulation(reg, seq, cfg)
    psi0 = np.array([1.0] + [0.0] * (2**4 - 1), dtype=complex)
    
    print("   ✓ Running simulation...")
    result = sim.run(psi0, 0.0, 1.0, observables={f'pop{i}': i for i in range(4)})
    print(f"   ✓ Simulation complete: {len(result.to_pandas())} time steps")
    
    # Extract single snapshot
    print("\n3. Extracting single spatial snapshot...")
    snapshot = extract_spatial_snapshot(result, reg, time_index=25)
    print(f"   Time: t={snapshot['time_value']:.3f}")
    print(f"   Atoms: {snapshot['n_atoms']}")
    print(f"   Positions shape: {snapshot['positions'].shape}")
    print(f"   Observable values:")
    for idx, val in sorted(snapshot['observables'].items()):
        print(f"     Atom {idx}: {val:.4f}")
    
    # Plot single snapshot
    print("\n4. Plotting single snapshot...")
    ax = plot_spatial_snapshot(
        snapshot,
        cmap='plasma',
        title=f"Spatial Snapshot at t={snapshot['time_value']:.3f}",
        save_path=os.path.join(OUTPUT_DIR, "spatial_snapshot_single.png")
    )
    plt.close()
    
    # Extract frame sequence
    print("\n5. Extracting frame sequence for animation...")
    frames = extract_frame_sequence(result, reg, stride=5)
    print(f"   ✓ Extracted {len(frames)} frames (stride=5)")
    
    # Save frame data to JSON
    print("\n6. Saving frame data to JSON...")
    save_frame_data(frames, "animation_frames.json")
    print(f"   ✓ Saved to animation_frames.json")
    
    # Load and verify JSON structure
    import json
    with open("animation_frames.json") as f:
        frame_data = json.load(f)
    print(f"   Schema version: {frame_data['schema_version']}")
    print(f"   Frame count: {frame_data['frame_count']}")
    
    # Plot multi-panel snapshots
    print("\n7. Creating multi-panel visualization...")
    panel_indices = [0, 3, 6, 9]  # Show 4 evenly spaced frames (within available 10)
    axes = plot_multi_panel_snapshots(
        frames,
        panel_indices=panel_indices,
        figsize_per_panel=(5, 5),
        cmap='viridis',
        show_colorbar=True,
        suptitle="Quantum State Evolution Over Time",
        save_path=os.path.join(OUTPUT_DIR, "spatial_snapshots_multipanel.png")
    )
    plt.close()
    
    # Diagnostic insights
    print("\n8. Diagnostic Insights:")
    print(f"   - Total simulation time: {result.to_pandas()['t'].iloc[-1]:.3f}s")
    print(f"   - Number of time steps: {len(result.to_pandas())}")
    print(f"   - Frame extraction stride: 5")
    print(f"   - Frames extracted: {len(frames)}")
    print(f"   - JSON file size: {len(json.dumps(frame_data))} bytes")
    
    # Show example of custom observable
    print("\n9. Example with different observable type...")
    print("   (Using 'pop' prefix for Rydberg population)")
    print("   To use other observables, ensure columns follow pattern:")
    print("   - 'energy0', 'energy1', ... for energy")
    print("   - 'phase0', 'phase1', ... for phase")
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  - spatial_snapshot_single.png  (single snapshot)")
    print("  - spatial_snapshots_multipanel.png  (multi-panel comparison)")
    print("  - animation_frames.json  (standardized frame data)")
    print("\nThese files can be used for:")
    print("  - Creating animations with external tools")
    print("  - Comparing state evolution across time")
    print("  - Archiving simulation results as local artifacts")
    print("=" * 80)


if __name__ == "__main__":
    main()
