"""
Example demonstrating trajectory storage and diagnostic visualization.

Shows how to:
1. Enable trajectory storage in SolverConfig
2. Access individual trajectory data from SimulationResult
3. Use plot_trajectory_statistics for convergence analysis
4. Save and load results with trajectory data

This example is designed for Phase 16 benchmark workflows.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 输出目录配置
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

from sagittarius import Register, Atom, PulseSequence, SolverConfig, Simulation
from sagittarius.viz import plot_trajectory_statistics


def main():
    """Demonstrate trajectory storage and diagnostics."""
    
    print("\n" + "="*70)
    print("Trajectory Storage & Diagnostics Example")
    print("="*70)
    
    # Step 1: Configure simulation with trajectory storage enabled
    print("\n[Step 1] Configuring MCWF simulation with trajectory storage...")
    reg = Register([Atom(0, 0), Atom(4, 0)], C6=1.0)
    pulse_seq = PulseSequence(omega=1.0, delta=0.0)
    
    config = SolverConfig(
        gamma=0.1,              # T1 decay rate
        use_mc=True,            # Enable Monte Carlo method
        n_trajectories=50,      # Number of trajectories
        seed=42,                # For reproducibility
        store_trajectories=True,  # ← Enable trajectory storage (Phase 16)
        reltol=1e-8,
        abstol=1e-8,
    )
    
    print(f"  ✓ Method: MCWF")
    print(f"  ✓ Trajectories: {config.n_trajectories}")
    print(f"  ✓ Store trajectories: {config.store_trajectories}")
    print(f"  ✓ Seed: {config.seed}")
    
    # Step 2: Run simulation
    print("\n[Step 2] Running MCWF simulation...")
    sim = Simulation(reg, pulse_seq, config)
    
    # Define observables
    observables = {"pop0": 0}  # Population of atom 0
    
    result = sim.run(
        psi0=np.array([1.0, 0.0, 0.0, 0.0], dtype=complex),
        t_start=0.0,
        t_end=2.0,
        observables=observables,
    )
    
    print(f"  ✓ Simulation completed")
    print(f"  ✓ Time points: {len(result.t)}")
    
    # Step 3: Check if trajectories were stored
    print("\n[Step 3] Checking trajectory data...")
    if hasattr(result, 'trajectories') and result.trajectories is not None:
        print(f"  ✓ Trajectories stored successfully")
        for obs_name, traj_data in result.trajectories.items():
            n_traj, n_time = traj_data.shape
            print(f"    - {obs_name}: shape={traj_data.shape}")
            print(f"      Final mean: {np.mean(traj_data[:, -1]):.3f}")
            print(f"      Final std: {np.std(traj_data[:, -1]):.3f}")
    else:
        print("  ⚠ Warning: No trajectory data found")
        print("     Ensure store_trajectories=True in SolverConfig")
        return
    
    # Step 4: Attach benchmark artifact metadata
    print("\n[Step 4] Attaching benchmark artifact metadata...")
    result.manifest = {
        'artifact_id': 'mcwf-trajectory-demo-n2-traj50',
        'schema_version': 'benchmark-artifact/v1',
        'algorithm': 'MCWF',
        'n_atoms': 2,
        'n_trajectories': config.n_trajectories,
        'gamma': config.gamma,
        'seed': config.seed,
        'commit_sha': 'demo-sha-123...',
        'timestamp': '2026-07-08T08:00:00Z'
    }
    print(f"  ✓ Artifact ID: {result.manifest['artifact_id']}")
    
    # Step 5: Generate trajectory statistics visualization
    print("\n[Step 5] Generating trajectory statistics visualization...")
    axes = plot_trajectory_statistics(
        result,
        observable_name='pop0',
        confidence_level=0.95,
        show_individual=False,  # Too many trajectories to show individually
        figsize=(12, 6)
    )
    
    print(f"  ✓ Visualization generated")
    print(f"  ✓ Includes artifact link: {result.manifest['artifact_id']}")
    print(f"  ✓ Includes disclaimer: DIAGNOSTIC VIEW")
    
    # Save figure
    output_path = os.path.join(OUTPUT_DIR, 'trajectory_diagnostics_demo.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  ✓ Saved: {output_path}")
    plt.close()
    
    # Step 6: Demonstrate save/load with trajectories
    print("\n[Step 6] Testing save/load with trajectory data...")
    save_path = os.path.join(OUTPUT_DIR, 'mcwf_result_with_trajectories.json')
    result.save(save_path)
    print(f"  ✓ Saved result to: {save_path}")
    
    # Load the result back
    from sagittarius.api import SimulationResult
    loaded_result = SimulationResult.load(save_path)
    print(f"  ✓ Loaded result from: {save_path}")
    
    # Verify trajectories were preserved
    if loaded_result.trajectories is not None:
        print(f"  ✓ Trajectories preserved after save/load")
        for obs_name, traj_data in loaded_result.trajectories.items():
            print(f"    - {obs_name}: shape={traj_data.shape}")
    else:
        print("  ⚠ Warning: Trajectories lost during save/load")
    
    # Step 7: Show convergence analysis with different sample sizes
    print("\n[Step 7] Demonstrating convergence analysis...")
    
    # Subsample trajectories to show effect on confidence intervals
    for n_sample in [10, 25, 50]:
        if n_sample > config.n_trajectories:
            continue
        
        # Create subsampled result
        subsampled_traj = {
            'pop0': result.trajectories['pop0'][:n_sample, :]
        }
        
        # Calculate statistics
        mean_final = np.mean(subsampled_traj['pop0'][:, -1])
        std_final = np.std(subsampled_traj['pop0'][:, -1])
        ci_half_width = 1.96 * std_final / np.sqrt(n_sample)  # 95% CI
        
        print(f"  • n={n_sample:2d}: mean={mean_final:.3f}, "
              f"std={std_final:.3f}, CI_95=±{ci_half_width:.3f}")
    
    print("\n✅ Example completed successfully!")
    print("\nKey takeaways:")
    print("  1. Set store_trajectories=True in SolverConfig to enable storage")
    print("  2. Access trajectories via result.trajectories dict")
    print("  3. Use plot_trajectory_statistics for diagnostic visualization")
    print("  4. Trajectories are preserved in save/load operations")
    print("  5. More trajectories → narrower confidence intervals")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
