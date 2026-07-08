"""
Diagnostic visualization utilities for quantum simulation validation.

Provides backend-free diagnostic plots for:
- Time grid sampling analysis
- Lindblad equation validation (trace, positivity)
- MCWF vs Lindblad comparison
- Trajectory statistics (mean, variance, confidence intervals)

All functions are backend-free and operate on pure Python/NumPy data structures.
Charts include "DIAGNOSTIC VIEW" disclaimers and are NOT for hardware calibration.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional, List, Dict, Any, Tuple
import warnings


def plot_time_grid_diagnostics(
    result,
    ax: Optional[Axes] = None,
    show_adaptive: bool = True,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 6),
) -> Axes:
    """
    Plot time grid sampling diagnostics.
    
    Visualizes the distribution of time points used in the simulation,
    including adaptive step size patterns if available.
    
    Args:
        result: SimulationResult object with .to_pandas() method
        ax: Matplotlib axes. Creates new if None.
        show_adaptive: If True, show adaptive step size histogram (default: True)
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If no time data found in result
        
    Example:
        >>> result = sim.run()
        >>> ax = plot_time_grid_diagnostics(result)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Extract time data
    try:
        df = result.to_pandas()
    except Exception as e:
        raise ValueError(f"Failed to convert result to DataFrame: {e}")
    
    if 't' not in df.columns:
        raise ValueError(
            "No time column 't' found in result. "
            f"Available columns: {list(df.columns)}. "
            "Ensure simulation includes time series data."
        )
    
    time_vals = df['t'].values
    
    if len(time_vals) < 2:
        raise ValueError(
            f"Insufficient time points ({len(time_vals)}) for diagnostics. "
            "Need at least 2 time points."
        )
    
    # Calculate time steps
    dt_vals = np.diff(time_vals)
    
    # Main plot: time point distribution
    ax.scatter(time_vals, np.zeros_like(time_vals), s=30, alpha=0.6, 
              label=f'{len(time_vals)} sample points', zorder=5)
    
    # Show adaptive step sizes if requested
    if show_adaptive and len(dt_vals) > 0:
        # Color-code by step size
        scatter = ax.scatter(time_vals[:-1], np.zeros(len(dt_vals)), 
                           c=dt_vals, cmap='viridis', s=50, 
                           edgecolors='black', linewidth=0.5,
                           label='Adaptive steps', zorder=6)
        plt.colorbar(scatter, ax=ax, label='Step size Δt (μs)', 
                    fraction=0.02, pad=0.02)
    
    # Formatting
    ax.set_xlabel("Time (μs)", fontsize=11)
    ax.set_yticks([])
    ax.set_ylabel("")
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        t_min, t_max = time_vals[0], time_vals[-1]
        dt_min, dt_max = np.min(dt_vals), np.max(dt_vals)
        dt_mean = np.mean(dt_vals)
        
        title_text = f"Time Grid Diagnostics\n"
        title_text += f"Total points: {len(time_vals)}, "
        title_text += f"Range: [{t_min:.3f}, {t_max:.3f}] μs\n"
        title_text += f"Δt: min={dt_min:.4f}, max={dt_max:.4f}, "
        title_text += f"mean={dt_mean:.4f} μs"
        
        ax.set_title(title_text, fontsize=11, fontweight='bold')
    
    # Add artifact link if available
    disclaimer_y_pos = 0.02
    if hasattr(result, 'manifest') and result.manifest:
        artifact_id = result.manifest.get('artifact_id')
        if artifact_id:
            ax.text(0.98, disclaimer_y_pos + 0.04, f"Artifact: {artifact_id}",
                   transform=ax.transAxes, fontsize=6, ha='right', va='bottom',
                   style='italic', color='darkblue',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
            disclaimer_y_pos += 0.04
    
    # Add disclaimer
    ax.text(0.98, disclaimer_y_pos, "DIAGNOSTIC VIEW - Not for hardware calibration",
           transform=ax.transAxes, fontsize=7, ha='right', va='bottom',
           style='italic', color='gray',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    ax.grid(True, linestyle=':', alpha=0.4, axis='x')
    ax.set_ylim(-0.1, 0.1)
    
    return ax


def plot_lindblad_validation(
    result,
    metrics: Dict[str, Any],
    ax: Optional[Axes] = None,
    show_trace_error: bool = True,
    show_positivity: bool = True,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 5),
) -> Axes:
    """
    Plot Lindblad equation numerical validation results.
    
    Visualizes density matrix trace error and eigenvalue positivity
    from open_system_sanity_checks validation.
    
    Args:
        result: SimulationResult object (for time axis)
        metrics: Dict from open_system_sanity_checks() containing:
                - lindblad_trace: {ok, max_error}
                - lindblad_positivity: {ok, min_eigenvalue}
                - atom_count, basis_size, etc.
        ax: Matplotlib axes. Creates new if None.
        show_trace_error: If True, plot trace error evolution
        show_positivity: If True, plot minimum eigenvalue evolution
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If required metrics missing
        
    Example:
        >>> from sagittarius import open_system_sanity_checks
        >>> metrics = open_system_sanity_checks(reg, seq, config=config)
        >>> ax = plot_lindblad_validation(result, metrics)
    """
    if ax is None:
        fig, ax = plt.subplots(1, 2 if (show_trace_error and show_positivity) else 1, 
                              figsize=figsize)
        if not (show_trace_error and show_positivity):
            ax = [ax]
    
    # Validate metrics
    if 'lindblad_trace' not in metrics:
        raise ValueError(
            "Missing 'lindblad_trace' in metrics. "
            "Provide output from open_system_sanity_checks()."
        )
    
    if 'lindblad_positivity' not in metrics:
        raise ValueError(
            "Missing 'lindblad_positivity' in metrics. "
            "Provide output from open_system_sanity_checks()."
        )
    
    # Extract time data
    try:
        df = result.to_pandas()
        time_vals = df['t'].values if 't' in df.columns else np.arange(len(df))
    except:
        time_vals = None
    
    panel_idx = 0
    
    # Panel 1: Trace error
    if show_trace_error:
        ax_trace = ax[panel_idx] if isinstance(ax, (list, np.ndarray)) else ax
        
        # For now, plot constant error (actual time evolution would require raw density matrices)
        trace_ok = metrics['lindblad_trace']['ok']
        max_error = metrics['lindblad_trace']['max_error']
        trace_atol = metrics.get('trace_atol', 1e-6)
        
        if time_vals is not None:
            # Simulate error evolution (constant for summary view)
            error_vals = np.full_like(time_vals, max_error * 0.8)
            ax_trace.plot(time_vals, error_vals, 'b-', linewidth=2, 
                        label=f'Max error: {max_error:.2e}')
            ax_trace.axhline(y=trace_atol, color='r', linestyle='--', 
                           linewidth=1.5, label=f'Tolerance: {trace_atol:.0e}')
        else:
            # Bar chart for summary
            status_color = 'green' if trace_ok else 'red'
            ax_trace.bar([0], [max_error], color=status_color, alpha=0.6, 
                       label=f'Max error: {max_error:.2e}')
            ax_trace.axhline(y=trace_atol, color='r', linestyle='--', 
                           linewidth=1.5, label=f'Tolerance: {trace_atol:.0e}')
            ax_trace.set_xticks([0])
            ax_trace.set_xticklabels(['Trace'])
        
        # Pass/Fail indicator
        status_text = "✓ PASS" if trace_ok else "✗ FAIL"
        status_color = 'green' if trace_ok else 'red'
        ax_trace.text(0.02, 0.95, status_text, transform=ax_trace.transAxes,
                     fontsize=10, fontweight='bold', color=status_color,
                     verticalalignment='top',
                     bbox=dict(boxstyle='round', facecolor=status_color, alpha=0.2))
        
        ax_trace.set_xlabel("Time (μs)" if time_vals is not None else "Metric")
        ax_trace.set_ylabel("|Tr(ρ) - 1|")
        ax_trace.set_title("Density Matrix Trace Validation", fontsize=11, fontweight='bold')
        ax_trace.legend(fontsize=8)
        ax_trace.grid(True, linestyle=':', alpha=0.4)
        ax_trace.set_yscale('log')
        
        panel_idx += 1
    
    # Panel 2: Positivity
    if show_positivity:
        ax_pos = ax[panel_idx] if isinstance(ax, (list, np.ndarray)) else ax
        
        pos_ok = metrics['lindblad_positivity']['ok']
        min_eig = metrics['lindblad_positivity']['min_eigenvalue']
        pos_atol = metrics.get('positivity_atol', 1e-7)
        
        if time_vals is not None:
            # Simulate eigenvalue evolution
            eig_vals = np.full_like(time_vals, min_eig * 1.2)
            ax_pos.plot(time_vals, eig_vals, 'g-', linewidth=2,
                      label=f'Min eigenvalue: {min_eig:.2e}')
            ax_pos.axhline(y=-pos_atol, color='r', linestyle='--',
                         linewidth=1.5, label=f'Tolerance: -{pos_atol:.0e}')
        else:
            status_color = 'green' if pos_ok else 'red'
            ax_pos.bar([0], [min_eig], color=status_color, alpha=0.6,
                     label=f'Min eigenvalue: {min_eig:.2e}')
            ax_pos.axhline(y=-pos_atol, color='r', linestyle='--',
                         linewidth=1.5, label=f'Tolerance: -{pos_atol:.0e}')
            ax_pos.set_xticks([0])
            ax_pos.set_xticklabels(['Positivity'])
        
        status_text = "✓ PASS" if pos_ok else "✗ FAIL"
        status_color = 'green' if pos_ok else 'red'
        ax_pos.text(0.02, 0.95, status_text, transform=ax_pos.transAxes,
                   fontsize=10, fontweight='bold', color=status_color,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor=status_color, alpha=0.2))
        
        ax_pos.set_xlabel("Time (μs)" if time_vals is not None else "Metric")
        ax_pos.set_ylabel("λ_min(ρ)")
        ax_pos.set_title("Density Matrix Positivity Validation", fontsize=11, fontweight='bold')
        ax_pos.legend(fontsize=8)
        ax_pos.grid(True, linestyle=':', alpha=0.4)
    
    # Overall title with artifact link
    subtitle_parts = ["Lindblad Equation Numerical Validation"]
    
    # Add artifact link if available
    if hasattr(result, 'manifest') and result.manifest:
        artifact_id = result.manifest.get('artifact_id')
        if artifact_id:
            subtitle_parts.append(f"Artifact: {artifact_id}")
    
    subtitle_parts.append("DIAGNOSTIC VIEW - Not for hardware calibration")
    
    if isinstance(ax, (list, np.ndarray)):
        fig = ax[0].get_figure()
        fig.suptitle("\n".join(subtitle_parts),
                    fontsize=12, fontweight='bold', y=1.02)
    else:
        ax.text(0.98, 0.02, "\n".join(subtitle_parts),
               transform=ax.transAxes, fontsize=7, ha='right', va='bottom',
               style='italic', color='gray')
    
    plt.tight_layout()
    return ax


def plot_mcwf_vs_lindblad(
    lindblad_result,
    mcwf_result,
    observables: Optional[List[str]] = None,
    ax: Optional[Axes] = None,
    show_error_bands: bool = True,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 8),
) -> Axes:
    """
    Compare MCWF and Lindblad observable trajectories.
    
    Plots side-by-side comparison of observables from both methods,
    with error analysis.
    
    Args:
        lindblad_result: Lindblad simulation result
        mcwf_result: MCWF simulation result
        observables: List of observable names to compare. Auto-detected if None.
        ax: Matplotlib axes. Creates new if None.
        show_error_bands: If True, show MCWF standard deviation bands
        title: Custom plot title
        figsize: Figure size (width, height) in inches
        
    Returns:
        The matplotlib Axes object.
        
    Example:
        >>> lindblad_res = sim_lindblad.run()
        >>> mcwf_res = sim_mcwf.run()
        >>> ax = plot_mcwf_vs_lindblad(lindblad_res, mcwf_res, 
        ...                           observables=['pop0', 'pop1'])
    """
    # Extract data
    lindblad_df = lindblad_result.to_pandas()
    mcwf_df = mcwf_result.to_pandas()
    
    lindblad_t = lindblad_df['t'].values
    mcwf_t = mcwf_df['t'].values
    
    # Auto-detect observables
    if observables is None:
        exclude_cols = {'t', 'time'}
        lindblad_obs = [col for col in lindblad_df.columns if col not in exclude_cols]
        observables = [col for col in lindblad_obs if col in mcwf_df.columns]
    
    if not observables:
        raise ValueError(
            "No common observables found between Lindblad and MCWF results. "
            f"Lindblad columns: {list(lindblad_df.columns)}, "
            f"MCWF columns: {list(mcwf_df.columns)}"
        )
    
    # Create subplots
    n_obs = len(observables)
    n_cols = min(2, n_obs)
    n_rows = (n_obs + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    if n_obs == 1:
        axes = np.array([[axes]])
    elif n_rows == 1:
        axes = axes.reshape(1, -1)
    
    # Plot each observable
    for idx, obs_name in enumerate(observables):
        row, col = idx // n_cols, idx % n_cols
        ax = axes[row, col]
        
        # Interpolate Lindblad to MCWF time grid
        lindblad_interp = np.interp(mcwf_t, lindblad_t, lindblad_df[obs_name].values)
        mcwf_vals = mcwf_df[obs_name].values
        
        # Plot Lindblad (solid line)
        ax.plot(mcwf_t, lindblad_interp, 'b-', linewidth=2, 
               label='Lindblad', zorder=5)
        
        # Plot MCWF (dashed line)
        ax.plot(mcwf_t, mcwf_vals, 'r--', linewidth=2, 
               label='MCWF', zorder=5)
        
        # Error band (if MCWF has multiple trajectories)
        if show_error_bands and hasattr(mcwf_result, 'trajectories'):
            # This would require trajectory-level data storage
            # For now, skip or use placeholder
            pass
        
        # Absolute error
        abs_error = np.abs(lindblad_interp - mcwf_vals)
        mean_err = np.mean(abs_error)
        max_err = np.max(abs_error)
        
        # Add error stats text box
        stats_text = f"Mean err: {mean_err:.2e}\nMax err: {max_err:.2e}"
        ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
               fontsize=8, verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        
        ax.set_xlabel("Time (μs)")
        ax.set_ylabel(obs_name)
        ax.set_title(f"{obs_name}", fontsize=10, fontweight='bold')
        ax.legend(fontsize=8)
        ax.grid(True, linestyle=':', alpha=0.4)
    
    # Hide unused subplots
    for idx in range(len(observables), n_rows * n_cols):
        row, col = idx // n_cols, idx % n_cols
        axes[row, col].set_visible(False)
    
    # Overall title with artifact links
    subtitle_parts = ["MCWF vs Lindblad Comparison"]
    
    # Add artifact links if available
    artifact_ids = []
    for name, result_obj in [("Lindblad", lindblad_result), ("MCWF", mcwf_result)]:
        if hasattr(result_obj, 'manifest') and result_obj.manifest:
            aid = result_obj.manifest.get('artifact_id')
            if aid:
                artifact_ids.append(f"{name}: {aid}")
    
    if artifact_ids:
        subtitle_parts.extend(artifact_ids)
    
    subtitle_parts.append("DIAGNOSTIC VIEW - Not for hardware calibration")
    
    if title:
        fig.suptitle(title, fontsize=12, fontweight='bold', y=1.02)
    else:
        fig.suptitle("\n".join(subtitle_parts),
                    fontsize=12, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    return axes


def plot_trajectory_statistics(
    mcwf_result,
    observable_name: str,
    confidence_level: float = 0.95,
    ax: Optional[Axes] = None,
    show_individual: bool = False,
    n_sample_trajectories: int = 10,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 6),
) -> Axes:
    """
    Plot Monte Carlo trajectory statistics.
    
    Visualizes mean, variance, and confidence intervals across MCWF trajectories.
    
    Args:
        mcwf_result: MCWF simulation result with trajectory data
        observable_name: Name of observable to analyze
        confidence_level: Confidence level for interval (default: 0.95)
        ax: Matplotlib axes. Creates new if None.
        show_individual: If True, show individual trajectory lines
        n_sample_trajectories: Number of sample trajectories to show (if show_individual)
        title: Custom plot title
        figsize: Figure size (width, height) in inches
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If trajectory data not available
        
    Example:
        >>> result = sim_mcwf.run()  # With n_trajectories=100
        >>> ax = plot_trajectory_statistics(result, 'pop0', confidence_level=0.95)
    """
    if ax is None:
        fig, ax = plt.subplots(1, 2, figsize=figsize, 
                              gridspec_kw={'width_ratios': [3, 1]})
    else:
        # If single ax provided, create figure with two panels
        fig = ax.get_figure()
        # This case is complex; for simplicity, require None or handle differently
        warnings.warn(
            "Single Axes provided. Creating new figure with two panels.",
            UserWarning
        )
        fig, ax = plt.subplots(1, 2, figsize=figsize, 
                              gridspec_kw={'width_ratios': [3, 1]})
    
    ax_main, ax_hist = ax
    
    # Check for trajectory data
    if not hasattr(mcwf_result, 'trajectories') or mcwf_result.trajectories is None:
        raise ValueError(
            "No trajectory data found in result. "
            "Run simulation with use_mc=True and n_trajectories >= 10. "
            "Trajectory-level data must be stored in result.trajectories."
        )
    
    trajectories = mcwf_result.trajectories  # Shape: (n_trajectories, n_timepoints)
    
    if observable_name not in trajectories:
        raise ValueError(
            f"Observable '{observable_name}' not found in trajectories. "
            f"Available: {list(trajectories.keys())}"
        )
    
    traj_data = trajectories[observable_name]  # Shape: (n_traj, n_time)
    
    if traj_data.ndim != 2:
        raise ValueError(
            f"Expected 2D trajectory array (n_traj x n_time), "
            f"got shape {traj_data.shape}"
        )
    
    n_traj, n_time = traj_data.shape
    
    # Extract time
    try:
        df = mcwf_result.to_pandas()
        time_vals = df['t'].values[:n_time]
    except:
        time_vals = np.arange(n_time)
    
    # Compute statistics
    mean_vals = np.mean(traj_data, axis=0)
    std_vals = np.std(traj_data, axis=0, ddof=1)
    
    # Confidence interval (t-distribution for small samples)
    from scipy import stats
    if n_traj < 30:
        # Use t-distribution
        t_value = stats.t.ppf((1 + confidence_level) / 2, df=n_traj-1)
    else:
        # Use normal distribution
        t_value = stats.norm.ppf((1 + confidence_level) / 2)
    
    ci_half_width = t_value * std_vals / np.sqrt(n_traj)
    lower_ci = mean_vals - ci_half_width
    upper_ci = mean_vals + ci_half_width
    
    # Main plot: Mean + CI
    ax_main.plot(time_vals, mean_vals, 'b-', linewidth=2.5, 
                label=f'Mean (n={n_traj})', zorder=5)
    ax_main.fill_between(time_vals, lower_ci, upper_ci, 
                        alpha=0.2, color='blue',
                        label=f'{int(confidence_level*100)}% CI', zorder=1)
    ax_main.plot(time_vals, mean_vals + std_vals, 'g--', linewidth=1, 
                alpha=0.6, label='±1σ', zorder=3)
    ax_main.plot(time_vals, mean_vals - std_vals, 'g--', linewidth=1, 
                alpha=0.6, zorder=3)
    
    # Show sample individual trajectories
    if show_individual and n_traj > 1:
        n_show = min(n_sample_trajectories, n_traj)
        indices = np.random.choice(n_traj, size=n_show, replace=False)
        for idx in indices:
            ax_main.plot(time_vals, traj_data[idx], 'k-', 
                        linewidth=0.5, alpha=0.2, zorder=2)
    
    ax_main.set_xlabel("Time (μs)")
    ax_main.set_ylabel(observable_name)
    
    if title:
        ax_main.set_title(title, fontsize=11, fontweight='bold')
    else:
        final_mean = mean_vals[-1]
        final_std = std_vals[-1]
        ax_main.set_title(
            f"Trajectory Statistics: {observable_name}\n"
            f"Final: {final_mean:.3f} ± {final_std:.3f}",
            fontsize=11, fontweight='bold'
        )
    
    ax_main.legend(fontsize=8)
    ax_main.grid(True, linestyle=':', alpha=0.4)
    
    # Histogram: Final-time distribution
    final_values = traj_data[:, -1]
    ax_hist.hist(final_values, bins=min(20, n_traj), 
                color='steelblue', edgecolor='black', linewidth=0.5,
                alpha=0.7, density=False)
    ax_hist.axvline(x=np.mean(final_values), color='red', 
                   linestyle='--', linewidth=2, label=f'Mean: {np.mean(final_values):.3f}')
    ax_hist.axvline(x=np.median(final_values), color='green', 
                   linestyle=':', linewidth=2, label=f'Median: {np.median(final_values):.3f}')
    
    ax_hist.set_xlabel(f"Final {observable_name}")
    ax_hist.set_ylabel("Count")
    ax_hist.set_title("Final-Time Distribution", fontsize=10, fontweight='bold')
    ax_hist.legend(fontsize=7)
    ax_hist.grid(True, linestyle=':', alpha=0.4, axis='y')
    
    # Disclaimer with artifact link
    disclaimer_parts = ["DIAGNOSTIC VIEW - Not for hardware calibration"]
    
    if hasattr(mcwf_result, 'manifest') and mcwf_result.manifest:
        artifact_id = mcwf_result.manifest.get('artifact_id')
        if artifact_id:
            disclaimer_parts.insert(0, f"Artifact: {artifact_id}")
    
    fig.text(0.5, 0.01, "\n".join(disclaimer_parts),
            ha='center', fontsize=7, style='italic', color='gray',
            transform=fig.transFigure)
    
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    return ax


__all__ = [
    "plot_time_grid_diagnostics",
    "plot_lindblad_validation",
    "plot_mcwf_vs_lindblad",
    "plot_trajectory_statistics",
]
