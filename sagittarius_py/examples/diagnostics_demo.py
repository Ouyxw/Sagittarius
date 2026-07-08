"""
Diagnostic visualization examples for quantum simulation validation.

Demonstrates time grid analysis, Lindblad validation, MCWF comparison,
and trajectory statistics plotting.

Usage:
    python examples/diagnostics_demo.py
"""

import numpy as np
import matplotlib.pyplot as plt

from sagittarius import (
    Atom,
    PulseSequence,
    Register,
    SolverConfig,
    Simulation,
    open_system_sanity_checks,
)
from sagittarius.viz import (
    plot_time_grid_diagnostics,
    plot_lindblad_validation,
    plot_mcwf_vs_lindblad,
    plot_trajectory_statistics,
)


def example_time_grid_diagnostics():
    """Example 1: Time grid sampling analysis."""
    print("=" * 60)
    print("Example 1: Time Grid Diagnostics")
    print("=" * 60)
    
    # Create simple simulation
    reg = Register([Atom(0, 0), Atom(1, 0)], C6=1.0)
    seq = PulseSequence(omega=2.0, delta=0.0)
    config = SolverConfig(reltol=1e-8, abstol=1e-10)
    
    sim = Simulation(reg, seq, config)
    result = sim.run()
    
    print(f"Time points: {len(result.t)}")
    print(f"Time range: [{result.t[0]:.3f}, {result.t[-1]:.3f}] μs")
    
    # Plot time grid diagnostics
    ax = plot_time_grid_diagnostics(result, show_adaptive=True)
    ax.set_title("Time Grid Sampling Pattern", fontsize=12)
    plt.tight_layout()
    plt.savefig("time_grid_diagnostics.png", dpi=150, bbox_inches='tight')
    print("Saved: time_grid_diagnostics.png")
    plt.show()


def example_lindblad_validation():
    """Example 2: Lindblad equation numerical validation."""
    print("\n" + "=" * 60)
    print("Example 2: Lindblad Validation")
    print("=" * 60)
    
    # Create small system for validation
    reg = Register([Atom(0, 0)], C6=0.0)
    seq = PulseSequence(omega=1.0, delta=0.0)
    config = SolverConfig(gamma=0.1, reltol=1e-7, abstol=1e-9)
    
    psi0 = np.array([0.0, 1.0], dtype=complex)  # Start in excited state
    
    # Run sanity checks
    metrics = open_system_sanity_checks(
        reg, seq,
        config=config,
        psi0=psi0,
        t_end=2.0,
        observables={"pop": 0},
        n_trajectories=100,
    )
    
    print(f"Trace validation: {'PASS' if metrics['lindblad_trace']['ok'] else 'FAIL'}")
    print(f"  Max error: {metrics['lindblad_trace']['max_error']:.2e}")
    print(f"Positivity validation: {'PASS' if metrics['lindblad_positivity']['ok'] else 'FAIL'}")
    print(f"  Min eigenvalue: {metrics['lindblad_positivity']['min_eigenvalue']:.2e}")
    
    # Run actual Lindblad simulation for time axis
    sim = Simulation(reg, seq, config)
    result = sim.run(psi0)
    
    # Plot validation results
    ax = plot_lindblad_validation(result, metrics)
    plt.suptitle("Lindblad Equation Numerical Validation", fontsize=12, y=1.02)
    plt.tight_layout()
    plt.savefig("lindblad_validation.png", dpi=150, bbox_inches='tight')
    print("Saved: lindblad_validation.png")
    plt.show()


def example_mcwf_vs_lindblad():
    """Example 3: MCWF vs Lindblad comparison."""
    print("\n" + "=" * 60)
    print("Example 3: MCWF vs Lindblad Comparison")
    print("=" * 60)
    
    # Create two-atom system
    reg = Register([Atom(0, 0), Atom(1, 2)], C6=1.0)
    seq = PulseSequence(omega=1.5, delta=0.0)
    
    # Lindblad simulation
    config_lind = SolverConfig(gamma=0.05, use_mc=False)
    sim_lind = Simulation(reg, seq, config_lind)
    result_lind = sim_lind.run(observables={'pop0': 0, 'pop1': 1})
    
    print(f"Lindblad time points: {len(result_lind.t)}")
    
    # MCWF simulation
    config_mcwf = SolverConfig(gamma=0.05, use_mc=True, n_trajectories=50)
    sim_mcwf = Simulation(reg, seq, config_mcwf)
    result_mcwf = sim_mcwf.run(observables={'pop0': 0, 'pop1': 1})
    
    print(f"MCWF trajectories: {config_mcwf.n_trajectories}")
    
    # Plot comparison
    axes = plot_mcwf_vs_lindblad(
        result_lind, result_mcwf,
        observables=['pop0', 'pop1'],
        show_error_bands=True
    )
    plt.tight_layout()
    plt.savefig("mcwf_vs_lindblad.png", dpi=150, bbox_inches='tight')
    print("Saved: mcwf_vs_lindblad.png")
    plt.show()


def example_trajectory_statistics():
    """Example 4: Monte Carlo trajectory statistics."""
    print("\n" + "=" * 60)
    print("Example 4: Trajectory Statistics")
    print("=" * 60)
    
    # Create system with many trajectories
    reg = Register([Atom(0, 0)], C6=0.0)
    seq = PulseSequence(omega=2.0, delta=0.0)
    
    n_trajectories = 100
    config = SolverConfig(gamma=0.1, use_mc=True, n_trajectories=n_trajectories)
    
    sim = Simulation(reg, seq, config)
    
    # Note: Current API may not store individual trajectories
    # This is a placeholder for when trajectory-level data is available
    print(f"Running MCWF with {n_trajectories} trajectories...")
    print("(Trajectory storage feature pending implementation)")
    
    # For now, create synthetic trajectory data for demonstration
    class MockResultWithTrajectories:
        def __init__(self):
            self.data = {'t': np.linspace(0, 1.0, 50)}
            self.metadata = {}
            self.diagnostics = {}
            self.manifest = {}
            self.t = self.data['t']
            
            # Synthetic trajectories
            n_traj, n_time = 100, 50
            t = self.data['t']
            traj_pop = np.zeros((n_traj, n_time))
            for i in range(n_traj):
                noise = np.random.normal(0, 0.05, n_time)
                traj_pop[i] = 0.5 + 0.3 * np.sin(2 * np.pi * t) + noise
            
            self.trajectories = {'pop0': traj_pop}
        
        def to_pandas(self):
            import pandas as pd
            return pd.DataFrame(self.data)
    
    mock_result = MockResultWithTrajectories()
    
    print(f"Synthetic trajectories: {mock_result.trajectories['pop0'].shape}")
    
    # Plot trajectory statistics
    axes = plot_trajectory_statistics(
        mock_result, 'pop0',
        confidence_level=0.95,
        show_individual=True,
        n_sample_trajectories=10
    )
    plt.tight_layout()
    plt.savefig("trajectory_statistics.png", dpi=150, bbox_inches='tight')
    print("Saved: trajectory_statistics.png")
    plt.show()


def main():
    """Run all diagnostic visualization examples."""
    print("\n" + "=" * 60)
    print("Sagittarius Diagnostic Visualization Examples")
    print("=" * 60)
    print("\nThese examples demonstrate diagnostic tools for:")
    print("1. Time grid sampling analysis")
    print("2. Lindblad equation validation")
    print("3. MCWF vs Lindblad comparison")
    print("4. Trajectory statistics")
    print("\nNote: All plots include 'DIAGNOSTIC VIEW' disclaimers")
    print("      and are NOT for hardware calibration.\n")
    
    try:
        example_time_grid_diagnostics()
    except Exception as e:
        print(f"Example 1 failed: {e}")
    
    try:
        example_lindblad_validation()
    except Exception as e:
        print(f"Example 2 failed: {e}")
    
    try:
        example_mcwf_vs_lindblad()
    except Exception as e:
        print(f"Example 3 failed: {e}")
    
    try:
        example_trajectory_statistics()
    except Exception as e:
        print(f"Example 4 failed: {e}")
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
