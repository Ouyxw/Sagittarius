"""
Sweep visualization module for parameter sweep analysis.

Provides backend-free plotting utilities for:
- Sweep heatmaps (2D parameter scans)
- Line slices (1D parameter sweeps)
- Final-observable maps
- Failed-run masks
- Run manifest links and parameter preservation

All visualizations are marked as EXPLORATORY unless bound to controlled artifacts.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from typing import List, Dict, Optional, Tuple, Union, Any
import warnings


def plot_sweep_heatmap(
    sweep_data: Dict[str, Any],
    x_param: str = "omega",
    y_param: str = "delta",
    metric: str = "pop0",
    ax=None,
    show_colorbar: bool = True,
    show_failed_mask: bool = True,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 8),
    cmap: str = "viridis",
) -> plt.Axes:
    """
    Plot a 2D parameter sweep heatmap.
    
    Parameters
    ----------
    sweep_data : dict
        Dictionary containing sweep results with structure:
        {
            'parameters': {
                'omega': array-like,  # x-axis values
                'delta': array-like,  # y-axis values
            },
            'results': {
                'metric_name': 2D array,  # shape (len(delta), len(omega))
                ...
            },
            'failed_runs': set of (omega_idx, delta_idx) tuples or boolean mask array
        }
    x_param : str
        Parameter name for x-axis (default: 'omega')
    y_param : str
        Parameter name for y-axis (default: 'delta')
    metric : str
        Metric name to visualize from results (default: 'final_population')
    ax : matplotlib.axes.Axes, optional
        Existing axes to plot on
    show_colorbar : bool
        Whether to show colorbar (default: True)
    show_failed_mask : bool
        Whether to overlay failed runs as red X markers (default: True)
    title : str, optional
        Custom title for the plot
    figsize : tuple
        Figure size in inches (default: (10, 8))
    cmap : str
        Colormap name (default: 'viridis')
    
    Returns
    -------
    matplotlib.axes.Axes
        The axes object with the heatmap
    
    Raises
    ------
    ValueError
        If required data is missing or shapes don't match
    """
    # Validate input data
    if 'parameters' not in sweep_data:
        raise ValueError("Missing 'parameters' key in sweep_data")
    if 'results' not in sweep_data:
        raise ValueError("Missing 'results' key in sweep_data")
    
    params = sweep_data['parameters']
    results = sweep_data['results']
    
    if x_param not in params:
        raise ValueError(f"Parameter '{x_param}' not found in sweep_data['parameters']")
    if y_param not in params:
        raise ValueError(f"Parameter '{y_param}' not found in sweep_data['parameters']")
    if metric not in results:
        raise ValueError(f"Metric '{metric}' not found in sweep_data['results']")
    
    x_vals = np.asarray(params[x_param])
    y_vals = np.asarray(params[y_param])
    z_data = np.asarray(results[metric])
    
    # Validate shapes
    expected_shape = (len(y_vals), len(x_vals))
    if z_data.shape != expected_shape:
        raise ValueError(
            f"Result metric '{metric}' has shape {z_data.shape}, "
            f"expected {expected_shape} based on parameter lengths"
        )
    
    # Create figure/axes if needed
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    
    # Create meshgrid for plotting
    X, Y = np.meshgrid(x_vals, y_vals)
    
    # Plot heatmap
    im = ax.pcolormesh(X, Y, z_data, cmap=cmap, shading='auto')
    
    # Overlay failed runs if requested
    if show_failed_mask and 'failed_runs' in sweep_data:
        failed = sweep_data['failed_runs']
        
        if isinstance(failed, np.ndarray) and failed.shape == z_data.shape:
            # Boolean mask array
            fail_y, fail_x = np.where(failed)
        elif isinstance(failed, (set, list)):
            # Set/list of (x_idx, y_idx) tuples
            fail_indices = np.array(list(failed))
            if len(fail_indices) > 0:
                fail_x = fail_indices[:, 0]
                fail_y = fail_indices[:, 1]
            else:
                fail_x, fail_y = [], []
        else:
            fail_x, fail_y = [], []
        
        if len(fail_x) > 0:
            # Get center coordinates of failed cells
            fail_x_centers = x_vals[fail_x]
            fail_y_centers = y_vals[fail_y]
            
            # Mark with red X
            ax.scatter(fail_x_centers, fail_y_centers, 
                      marker='x', color='red', s=100, linewidths=2,
                      label='Failed runs', zorder=5)
            ax.legend(loc='upper right', fontsize=8)
    
    # Add colorbar
    if show_colorbar:
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(metric, fontsize=10)
    
    # Labels and title
    ax.set_xlabel(x_param, fontsize=11)
    ax.set_ylabel(y_param, fontsize=11)
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        ax.set_title(
            f"Sweep Heatmap: {metric}\n{x_param} vs {y_param}",
            fontsize=12, fontweight='bold'
        )
    
    # Disclaimer
    disclaimer_parts = ["⚠️ EXPLORATORY VISUALIZATION - Not for hardware calibration"]
    
    # Check for artifact link
    if 'manifest_links' in sweep_data:
        manifest_links = sweep_data['manifest_links']
        if isinstance(manifest_links, dict) and len(manifest_links) > 0:
            sample_id = list(manifest_links.keys())[0]
            disclaimer_parts.insert(0, f"Sample Artifact: {sample_id}")
    
    fig.text(0.5, 0.01, "\n".join(disclaimer_parts),
            ha='center', fontsize=7, style='italic', color='gray',
            transform=fig.transFigure)
    
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    return ax


def plot_sweep_line_slice(
    sweep_data: Dict[str, Any],
    fixed_param: str,
    fixed_value: float,
    varying_param: str,
    metric: str = "pop0",
    ax=None,
    show_error_bars: bool = False,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 6),
    color: str = 'steelblue',
    marker: str = 'o',
) -> plt.Axes:
    """
    Plot a 1D slice through a parameter sweep (line slice).
    
    Parameters
    ----------
    sweep_data : dict
        Dictionary containing sweep results (same structure as plot_sweep_heatmap)
    fixed_param : str
        Parameter that is held constant
    fixed_value : float
        Value of the fixed parameter
    varying_param : str
        Parameter that varies along the x-axis
    metric : str
        Metric name to visualize
    ax : matplotlib.axes.Axes, optional
        Existing axes to plot on
    show_error_bars : bool
        Whether to show error bars if std data available (default: False)
    title : str, optional
        Custom title
    figsize : tuple
        Figure size in inches (default: (10, 6))
    color : str
        Line color (default: 'steelblue')
    marker : str
        Marker style (default: 'o')
    
    Returns
    -------
    matplotlib.axes.Axes
        The axes object with the line plot
    """
    params = sweep_data['parameters']
    results = sweep_data['results']
    
    if varying_param not in params:
        raise ValueError(f"Varying parameter '{varying_param}' not found")
    if fixed_param not in params:
        raise ValueError(f"Fixed parameter '{fixed_param}' not found")
    if metric not in results:
        raise ValueError(f"Metric '{metric}' not found")
    
    x_vals = np.asarray(params[varying_param])
    fixed_vals = np.asarray(params[fixed_param])
    
    # Find index of fixed value
    try:
        fixed_idx = np.argmin(np.abs(fixed_vals - fixed_value))
    except Exception:
        raise ValueError(f"Could not find fixed value {fixed_value} for parameter {fixed_param}")
    
    # Extract 1D slice
    if varying_param == list(params.keys())[0]:
        # varying_param is first dimension (columns)
        y_vals = results[metric][fixed_idx, :]
    else:
        # varying_param is second dimension (rows)
        y_vals = results[metric][:, fixed_idx]
    
    # Create figure/axes if needed
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    
    # Plot line
    if show_error_bars and f"{metric}_std" in results:
        if varying_param == list(params.keys())[0]:
            y_std = results[f"{metric}_std"][fixed_idx, :]
        else:
            y_std = results[f"{metric}_std"][:, fixed_idx]
        
        ax.errorbar(x_vals, y_vals, yerr=y_std, fmt=f'{marker}-', 
                   color=color, capsize=3, label=f'{metric} ± std')
    else:
        ax.plot(x_vals, y_vals, f'{marker}-', color=color, linewidth=2, 
               markersize=6, label=metric)
    
    # Labels and title
    ax.set_xlabel(varying_param, fontsize=11)
    ax.set_ylabel(metric, fontsize=11)
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        ax.set_title(
            f"Line Slice: {fixed_param}={fixed_value:.3f}\n{metric} vs {varying_param}",
            fontsize=12, fontweight='bold'
        )
    
    ax.legend(fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.4)
    
    # Disclaimer
    disclaimer = "⚠️ EXPLORATORY VISUALIZATION - Not for hardware calibration"
    fig.text(0.5, 0.01, disclaimer,
            ha='center', fontsize=7, style='italic', color='gray',
            transform=fig.transFigure)
    
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    return ax


def plot_final_observable_map(
    sweep_data: Dict[str, Any],
    observable_name: str = "pop0",
    param_name: str = "omega",
    ax=None,
    show_markers: bool = True,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 6),
    color: str = 'steelblue',
) -> plt.Axes:
    """
    Plot final observable values across a 1D parameter sweep.
    
    Parameters
    ----------
    sweep_data : dict
        Dictionary containing sweep results
    observable_name : str
        Name of the observable to plot (default: 'pop0')
    param_name : str
        Parameter name for x-axis (default: 'omega')
    ax : matplotlib.axes.Axes, optional
        Existing axes to plot on
    show_markers : bool
        Whether to show data point markers (default: True)
    title : str, optional
        Custom title
    figsize : tuple
        Figure size in inches (default: (10, 6))
    color : str
        Line/marker color (default: 'steelblue')
    
    Returns
    -------
    matplotlib.axes.Axes
        The axes object with the plot
    """
    params = sweep_data['parameters']
    results = sweep_data['results']
    
    if param_name not in params:
        raise ValueError(f"Parameter '{param_name}' not found")
    
    # Try to find the observable in results
    obs_key = observable_name
    if obs_key not in results:
        # Try common variations
        for key in results.keys():
            if observable_name in key.lower():
                obs_key = key
                break
        else:
            raise ValueError(
                f"Observable '{observable_name}' not found in results. "
                f"Available: {list(results.keys())}"
            )
    
    x_vals = np.asarray(params[param_name])
    y_vals = np.asarray(results[obs_key])
    
    # Handle 2D data by taking last time point or appropriate slice
    if y_vals.ndim == 2:
        # Assume first dimension is the parameter dimension
        if y_vals.shape[0] == len(x_vals):
            y_vals = y_vals[:, -1]  # Take final time point for each parameter
        elif y_vals.shape[1] == len(x_vals):
            y_vals = y_vals[-1, :]  # Take last row if second dim matches
        else:
            raise ValueError(
                f"Cannot extract 1D slice from 2D array with shape {y_vals.shape} "
                f"for parameter with {len(x_vals)} values"
            )
    
    # Create figure/axes if needed
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    
    # Plot
    marker_style = 'o' if show_markers else ''
    ax.plot(x_vals, y_vals, f'{marker_style}-', color=color, linewidth=2, 
           markersize=6, label=obs_key)
    
    # Labels and title
    ax.set_xlabel(param_name, fontsize=11)
    ax.set_ylabel(f"Final {observable_name}", fontsize=11)
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        ax.set_title(
            f"Final Observable Map: {observable_name}\nvs {param_name}",
            fontsize=12, fontweight='bold'
        )
    
    ax.legend(fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.4)
    
    # Disclaimer
    disclaimer = "⚠️ EXPLORATORY VISUALIZATION - Not for hardware calibration"
    fig.text(0.5, 0.01, disclaimer,
            ha='center', fontsize=7, style='italic', color='gray',
            transform=fig.transFigure)
    
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    return ax


def plot_observables_comparison(
    sweep_data: Dict[str, Any],
    observables: List[str] = None,
    param_name: str = "omega",
    ax=None,
    show_markers: bool = True,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 7),
    colors: List[str] = None,
    normalize: bool = False,
) -> plt.Axes:
    """
    Plot multiple observables on the same axes for comparison.
    
    Parameters
    ----------
    sweep_data : dict
        Dictionary containing sweep results
    observables : list of str, optional
        List of observable names to plot (default: auto-detect all numeric observables)
    param_name : str
        Parameter name for x-axis (default: 'omega')
    ax : matplotlib.axes.Axes, optional
        Existing axes to plot on
    show_markers : bool
        Whether to show data point markers (default: True)
    title : str, optional
        Custom title
    figsize : tuple
        Figure size in inches (default: (12, 7))
    colors : list of str, optional
        Colors for each observable line (auto-assigned if None)
    normalize : bool
        Whether to normalize all observables to [0, 1] range (default: False)
    
    Returns
    -------
    matplotlib.axes.Axes
        The axes object with the comparison plot
    
    Raises
    ------
    ValueError
        If required data is missing or observables not found
    """
    params = sweep_data['parameters']
    results = sweep_data['results']
    
    if param_name not in params:
        raise ValueError(f"Parameter '{param_name}' not found")
    
    # Auto-detect observables if not specified
    if observables is None:
        observables = [k for k in results.keys() 
                      if isinstance(results[k], np.ndarray)]
    
    if not observables:
        raise ValueError("No observables found in results")
    
    # Prepare colors
    if colors is None:
        # Use matplotlib's default color cycle
        import matplotlib.cm as cm
        try:
            # Matplotlib 3.7+ preferred method
            cmap = plt.get_cmap('tab10')
        except (AttributeError, TypeError):
            # Fallback for older versions
            cmap = cm.get_cmap('tab10')
        colors = [cmap(i % 10) for i in range(len(observables))]
    
    x_vals = np.asarray(params[param_name])
    
    # Create figure/axes if needed
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    
    # Plot each observable
    for idx, obs_name in enumerate(observables):
        if obs_name not in results:
            print(f"Warning: Observable '{obs_name}' not found, skipping")
            continue
        
        y_vals = np.asarray(results[obs_name])
        
        # Handle 2D data
        if y_vals.ndim == 2:
            if y_vals.shape[0] == len(x_vals):
                y_vals = y_vals[:, -1]
            elif y_vals.shape[1] == len(x_vals):
                y_vals = y_vals[-1, :]
            else:
                print(f"Warning: Cannot extract 1D slice for '{obs_name}', skipping")
                continue
        
        # Normalize if requested
        if normalize:
            y_min, y_max = np.min(y_vals), np.max(y_vals)
            if y_max > y_min:
                y_vals = (y_vals - y_min) / (y_max - y_min)
        
        # Plot
        marker_style = 'o' if show_markers else ''
        color = colors[idx % len(colors)]
        ax.plot(x_vals, y_vals, f'{marker_style}-', color=color, 
               linewidth=2, markersize=5, label=obs_name, alpha=0.8)
    
    # Labels and title
    ax.set_xlabel(param_name, fontsize=11)
    ax.set_ylabel("Observable Value" if not normalize else "Normalized Value", 
                 fontsize=11)
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        obs_list = ', '.join(observables[:3])
        if len(observables) > 3:
            obs_list += f" (+{len(observables)-3} more)"
        ax.set_title(
            f"Observables Comparison\n{obs_list} vs {param_name}",
            fontsize=12, fontweight='bold'
        )
    
    ax.legend(fontsize=9, loc='best')
    ax.grid(True, linestyle=':', alpha=0.4)
    
    # Add normalization note if applicable
    if normalize:
        ax.text(0.02, 0.98, "Note: Values normalized to [0, 1]",
               transform=ax.transAxes, fontsize=7, verticalalignment='top',
               style='italic', color='gray')
    
    # Disclaimer
    disclaimer = "⚠️ EXPLORATORY VISUALIZATION - Not for hardware calibration"
    fig.text(0.5, 0.01, disclaimer,
            ha='center', fontsize=7, style='italic', color='gray',
            transform=fig.transFigure)
    
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    return ax


def plot_failed_run_mask(
    sweep_data: Dict[str, Any],
    x_param: str = "omega",
    y_param: str = "delta",
    ax=None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 8),
) -> plt.Axes:
    """
    Plot a binary mask showing failed vs successful runs in a 2D sweep.
    
    Parameters
    ----------
    sweep_data : dict
        Dictionary containing sweep results with 'failed_runs' key
    x_param : str
        Parameter name for x-axis (default: 'omega')
    y_param : str
        Parameter name for y-axis (default: 'delta')
    ax : matplotlib.axes.Axes, optional
        Existing axes to plot on
    title : str, optional
        Custom title
    figsize : tuple
        Figure size in inches (default: (10, 8))
    
    Returns
    -------
    matplotlib.axes.Axes
        The axes object with the failure mask
    """
    if 'failed_runs' not in sweep_data:
        raise ValueError("Missing 'failed_runs' in sweep_data")
    
    params = sweep_data['parameters']
    
    if x_param not in params:
        raise ValueError(f"Parameter '{x_param}' not found")
    if y_param not in params:
        raise ValueError(f"Parameter '{y_param}' not found")
    
    x_vals = np.asarray(params[x_param])
    y_vals = np.asarray(params[y_param])
    
    failed = sweep_data['failed_runs']
    
    # Convert to boolean mask
    if isinstance(failed, np.ndarray):
        if failed.dtype == bool:
            mask = failed
        else:
            # Assume it's indices or some other format
            mask = np.zeros((len(y_vals), len(x_vals)), dtype=bool)
    elif isinstance(failed, (set, list)):
        mask = np.zeros((len(y_vals), len(x_vals)), dtype=bool)
        for item in failed:
            if isinstance(item, (tuple, list)) and len(item) == 2:
                x_idx, y_idx = int(item[0]), int(item[1])
                if 0 <= x_idx < len(x_vals) and 0 <= y_idx < len(y_vals):
                    mask[y_idx, x_idx] = True
    else:
        raise ValueError("Unsupported format for 'failed_runs'")
    
    # Create figure/axes if needed
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    
    # Create meshgrid
    X, Y = np.meshgrid(x_vals, y_vals)
    
    # Plot mask (0=success/green, 1=failure/red)
    cmap = plt.cm.RdYlGn_r  # Red-Yellow-Green reversed (green=0, red=1)
    im = ax.pcolormesh(X, Y, mask.astype(float), cmap=cmap, vmin=0, vmax=1, shading='auto')
    
    # Add colorbar with custom labels
    cbar = plt.colorbar(im, ax=ax, ticks=[0, 1])
    cbar.set_ticklabels(['Success', 'Failed'])
    cbar.set_label('Run Status', fontsize=10)
    
    # Labels and title
    ax.set_xlabel(x_param, fontsize=11)
    ax.set_ylabel(y_param, fontsize=11)
    
    n_failed = int(mask.sum())
    n_total = mask.size
    success_rate = (1 - n_failed / n_total) * 100 if n_total > 0 else 0
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        ax.set_title(
            f"Failed Run Mask\n{n_failed}/{n_total} failed ({success_rate:.1f}% success)",
            fontsize=12, fontweight='bold'
        )
    
    # Disclaimer with manifest link if available
    disclaimer_parts = ["⚠️ EXPLORATORY VISUALIZATION - Not for hardware calibration"]
    
    if 'manifest_links' in sweep_data:
        manifest_links = sweep_data['manifest_links']
        if isinstance(manifest_links, dict) and len(manifest_links) > 0:
            n_linked = len([v for v in manifest_links.values() if v is not None])
            disclaimer_parts.insert(0, f"Manifest Links: {n_linked}/{n_total} runs linked")
    
    fig.text(0.5, 0.01, "\n".join(disclaimer_parts),
            ha='center', fontsize=7, style='italic', color='gray',
            transform=fig.transFigure)
    
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    return ax


def extract_sweep_summary(
    sweep_data: Dict[str, Any],
    metrics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Extract summary statistics from sweep data.
    
    Parameters
    ----------
    sweep_data : dict
        Dictionary containing sweep results
    metrics : list of str, optional
        Specific metrics to summarize (default: all numeric metrics)
    
    Returns
    -------
    dict
        Summary statistics including min, max, mean, std for each metric
    """
    results = sweep_data['results']
    
    if metrics is None:
        # Auto-detect numeric metrics
        metrics = [k for k in results.keys() 
                  if isinstance(results[k], np.ndarray) and results[k].dtype in [np.float32, np.float64]]
    
    summary = {}
    for metric in metrics:
        data = np.asarray(results[metric])
        summary[metric] = {
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'mean': float(np.mean(data)),
            'std': float(np.std(data)),
            'median': float(np.median(data)),
            'q25': float(np.percentile(data, 25)),
            'q75': float(np.percentile(data, 75)),
        }
    
    # Add run statistics
    if 'failed_runs' in sweep_data:
        failed = sweep_data['failed_runs']
        if isinstance(failed, np.ndarray):
            n_failed = int(failed.sum())
        elif isinstance(failed, (set, list)):
            n_failed = len(failed)
        else:
            n_failed = 0
        
        # Calculate total runs as product of all parameter dimensions
        param_lengths = [len(v) for v in sweep_data['parameters'].values()]
        total = int(np.prod(param_lengths))
        
        summary['run_statistics'] = {
            'total_runs': total,
            'failed_runs': n_failed,
            'successful_runs': total - n_failed,
            'success_rate': float((total - n_failed) / total * 100) if total > 0 else 0,
        }
    
    return summary


# Synthetic data generator for demonstration
def generate_synthetic_sweep_data(
    omega_range: Tuple[float, float] = (0.1, 5.0),
    delta_range: Tuple[float, float] = (-2.0, 2.0),
    n_omega: int = 20,
    n_delta: int = 15,
    seed: int = 42,
    failure_rate: float = 0.05,
) -> Dict[str, Any]:
    """
    Generate synthetic sweep data for demonstration purposes.
    
    Parameters
    ----------
    omega_range : tuple
        (min, max) range for omega parameter
    delta_range : tuple
        (min, max) range for delta parameter
    n_omega : int
        Number of omega values to sample
    n_delta : int
        Number of delta values to sample
    seed : int
        Random seed for reproducibility
    failure_rate : float
        Fraction of runs that should fail (0-1)
    
    Returns
    -------
    dict
        Synthetic sweep data suitable for visualization functions
    """
    rng = np.random.RandomState(seed)
    
    # Generate parameter grids
    omega_vals = np.linspace(omega_range[0], omega_range[1], n_omega)
    delta_vals = np.linspace(delta_range[0], delta_range[1], n_delta)
    
    # Create 2D grid
    Omega, Delta = np.meshgrid(omega_vals, delta_vals)
    
    # Generate synthetic observables (Rabi oscillation pattern)
    # Population follows sin^2 pattern with damping
    pop0 = np.sin(Omega * 2)**2 * np.exp(-0.1 * Delta**2)
    pop0 += rng.normal(0, 0.02, pop0.shape)  # Add noise
    pop0 = np.clip(pop0, 0, 1)
    
    pop1 = 1 - pop0
    
    # Generate standard deviations
    pop0_std = rng.uniform(0.01, 0.05, pop0.shape)
    
    # Generate failed runs (random positions)
    n_failed = int(n_omega * n_delta * failure_rate)
    failed_indices = set()
    while len(failed_indices) < n_failed:
        i = rng.randint(0, n_omega)
        j = rng.randint(0, n_delta)
        failed_indices.add((i, j))
    
    # Generate mock manifest links
    manifest_links = {}
    for i in range(n_omega):
        for j in range(n_delta):
            if (i, j) not in failed_indices:
                manifest_links[f"omega_{i}_delta_{j}"] = f"artifact_{i}_{j}"
    
    sweep_data = {
        'parameters': {
            'omega': omega_vals,
            'delta': delta_vals,
        },
        'results': {
            'pop0': pop0,
            'pop1': pop1,
            'pop0_std': pop0_std,
            'energy': Omega**2 + Delta**2,  # Fake energy metric
        },
        'failed_runs': failed_indices,
        'manifest_links': manifest_links,
        'metadata': {
            'schema_version': 'sweep-data/v0-experimental',
            'description': 'Synthetic sweep data for demonstration',
            'seed': seed,
            'timestamp': '2026-07-09T00:00:00Z',
        },
    }
    
    return sweep_data


__all__ = [
    "plot_sweep_heatmap",
    "plot_sweep_line_slice",
    "plot_final_observable_map",
    "plot_failed_run_mask",
    "extract_sweep_summary",
    "generate_synthetic_sweep_data",
]
