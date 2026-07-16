"""
Benchmark performance analysis visualization utilities.

Provides diagnostic chart primitives for caller-supplied rows. Governed public entry points live in `benchmark_governed.py` and validate `benchmark-artifact/v1` before delegating here.
including runtime scaling, memory usage, solver comparisons, and success/failure summaries.

All functions in this module are explicitly diagnostic-only and operate on pure Python/NumPy data structures. They must not be used for hardware calibration or performance claims.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional, List, Dict, Any, Tuple, Union
import warnings
import json
from pathlib import Path


def _load_benchmark_artifact(artifact_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a governed benchmark artifact from JSON file."""
    path = Path(artifact_path)
    if not path.exists():
        raise FileNotFoundError(f"Benchmark artifact not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Validate schema version
    if 'schema_version' not in data:
        raise ValueError("Artifact missing 'schema_version' field. Not a valid governed artifact.")
    
    return data


def plot_diagnostic_runtime_scaling(
    artifacts: List[Dict[str, Any]],
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 6),
    show_fit: bool = True,
) -> Axes:
    """
    Plot runtime vs atom count scaling curve from benchmark artifacts.
    
    Visualizes how simulation runtime scales with system size (number of atoms).
    Only reads from governed benchmark artifacts or validated experimental data.
    
    Args:
        artifacts: List of benchmark artifact dicts, each containing:
            - 'n_atoms': int - number of atoms
            - 'runtime_seconds': float - wall-clock time
            - 'artifact_id': str - unique identifier
        ax: Matplotlib axes. Creates new if None.
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches.
        show_fit: If True, fit and display power-law scaling curve.
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If artifacts lack required fields
        
    Example:
        >>> artifacts = [load_artifact(f"bench_{n}.json") for n in [5, 10, 15, 20]]
        >>> ax = plot_runtime_scaling(artifacts, show_fit=True)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Extract data
    n_atoms_list = []
    runtime_list = []
    
    for i, artifact in enumerate(artifacts):
        if 'n_atoms' not in artifact:
            raise ValueError(f"Artifact {i} missing 'n_atoms' field.")
        if 'runtime_seconds' not in artifact:
            raise ValueError(f"Artifact {i} missing 'runtime_seconds' field.")
        
        n_atoms_list.append(artifact['n_atoms'])
        runtime_list.append(artifact['runtime_seconds'])
    
    n_atoms_arr = np.array(n_atoms_list)
    runtime_arr = np.array(runtime_list)
    
    # Sort by atom count
    sort_idx = np.argsort(n_atoms_arr)
    n_atoms_arr = n_atoms_arr[sort_idx]
    runtime_arr = runtime_arr[sort_idx]
    
    # Plot data points
    ax.scatter(n_atoms_arr, runtime_arr, s=100, c='#2E86AB', 
              edgecolors='black', linewidth=1.5, zorder=5, label='Benchmark data')
    
    # Fit power-law: T = a * N^b
    if show_fit and len(n_atoms_arr) >= 3:
        log_n = np.log(n_atoms_arr)
        log_t = np.log(runtime_arr)
        
        # Linear fit in log-log space
        coeffs = np.polyfit(log_n, log_t, 1)
        b = coeffs[0]  # exponent
        log_a = coeffs[1]
        a = np.exp(log_a)
        
        # Generate smooth curve
        n_smooth = np.linspace(n_atoms_arr.min(), n_atoms_arr.max(), 100)
        t_smooth = a * n_smooth ** b
        
        ax.plot(n_smooth, t_smooth, 'r--', linewidth=2, alpha=0.7, 
               label=f'Fit: T ∝ N^{b:.2f}', zorder=4)
        
        # Display fit parameters
        textstr = f'Scaling exponent: {b:.2f}\nPrefactor: {a:.2e}'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', bbox=props, zorder=10)
    
    ax.set_xlabel('Number of Atoms (N)', fontsize=12)
    ax.set_ylabel('Runtime (seconds)', fontsize=12)
    
    if title is None:
        title = f'Runtime Scaling Analysis ({len(artifacts)} benchmarks)'
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Adjust layout first to make room for external elements
    plt.tight_layout()
    
    # Get figure for external text placement
    fig = ax.get_figure()
    
    # Place legend outside plot area at upper right
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), fontsize=8, 
             framealpha=0.95, edgecolor='gray', borderpad=2,
             labelspacing=0.3, handletextpad=4)
    
    # Add disclaimer outside plot area at bottom right (below the axes)
    fig.text(0.99, -0.02, "DIAGNOSTIC VIEW - Not for hardware calibration",
            transform=fig.transFigure, fontsize=7, color='red', ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    return ax


def plot_diagnostic_memory_scaling(
    artifacts: List[Dict[str, Any]],
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 6),
    y_unit: str = 'MB',
) -> Axes:
    """
    Plot memory usage vs Hilbert space dimension from benchmark artifacts.
    
    Visualizes how memory consumption scales with system dimension.
    Memory values should be in bytes; converted to specified unit for display.
    
    Args:
        artifacts: List of benchmark artifact dicts, each containing:
            - 'hilbert_dim': int - Hilbert space dimension (2^n for n qubits)
            - 'memory_bytes': int - peak memory usage in bytes
            - 'artifact_id': str - unique identifier
        ax: Matplotlib axes. Creates new if None.
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches.
        y_unit: Memory unit for display ('B', 'KB', 'MB', 'GB').
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If artifacts lack required fields
        
    Example:
        >>> artifacts = [load_artifact(f"bench_{d}.json") for d in [16, 32, 64, 128]]
        >>> ax = plot_memory_scaling(artifacts, y_unit='MB')
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Unit conversion factors
    unit_factors = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
    if y_unit not in unit_factors:
        raise ValueError(f"Invalid y_unit '{y_unit}'. Choose from {list(unit_factors.keys())}.")
    
    factor = unit_factors[y_unit]
    
    # Extract data
    hilbert_dims = []
    memory_values = []
    
    for i, artifact in enumerate(artifacts):
        if 'hilbert_dim' not in artifact:
            raise ValueError(f"Artifact {i} missing 'hilbert_dim' field.")
        if 'memory_bytes' not in artifact:
            raise ValueError(f"Artifact {i} missing 'memory_bytes' field.")
        
        hilbert_dims.append(artifact['hilbert_dim'])
        memory_values.append(artifact['memory_bytes'] / factor)
    
    hilbert_dims_arr = np.array(hilbert_dims)
    memory_arr = np.array(memory_values)
    
    # Sort by dimension
    sort_idx = np.argsort(hilbert_dims_arr)
    hilbert_dims_arr = hilbert_dims_arr[sort_idx]
    memory_arr = memory_arr[sort_idx]
    
    # Plot with log scale on x-axis (Hilbert space grows exponentially)
    ax.semilogy(hilbert_dims_arr, memory_arr, 'o-', linewidth=2, markersize=8,
               c='#A23B72', markeredgecolor='black', markeredgewidth=1.5,
               label='Memory usage', zorder=5)
    
    ax.set_xlabel('Hilbert Space Dimension (log scale)', fontsize=12)
    ax.set_ylabel(f'Memory Usage ({y_unit})', fontsize=12)
    
    if title is None:
        title = f'Memory Scaling Analysis ({len(artifacts)} benchmarks)'
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Adjust layout first to make room for external elements
    plt.tight_layout()
    
    # Get figure for external text placement
    fig = ax.get_figure()
    
    # Place legend outside plot area at upper right
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), fontsize=8, 
             framealpha=0.95, edgecolor='gray', borderpad=2,
             labelspacing=0.3, handletextpad=4)
    
    # Add disclaimer outside plot area at bottom right (below the axes)
    fig.text(0.99, -0.02, "DIAGNOSTIC VIEW - Not for hardware calibration",
            transform=fig.transFigure, fontsize=7, color='red', ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    return ax


def plot_diagnostic_solver_comparison(
    results: List[Dict[str, Any]],
    metric: str = 'runtime',
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 6),
    show_error_bars: bool = True,
) -> Axes:
    """
    Plot horizontal comparison of different solvers on same problem instance.
    
    Compares solver performance across metrics like runtime, accuracy, or memory.
    
    Args:
        results: List of result dicts, each containing:
            - 'solver_name': str - solver identifier (e.g., 'Tsit5', 'EM', 'MCWF')
            - 'metric_value': float - performance metric value
            - 'metric_std': float - standard deviation (optional, for error bars)
            - 'artifact_id': str - unique identifier
        metric: Metric to compare ('runtime', 'accuracy', 'memory', 'error').
        ax: Matplotlib axes. Creates new if None.
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches.
        show_error_bars: If True, display error bars when std available.
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If results lack required fields
        
    Example:
        >>> results = [
        ...     {'solver_name': 'Tsit5', 'metric_value': 1.23, 'metric_std': 0.05},
        ...     {'solver_name': 'EM', 'metric_value': 2.45, 'metric_std': 0.12},
        ... ]
        >>> ax = plot_solver_comparison(results, metric='runtime')
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Extract data
    solver_names = []
    metric_values = []
    metric_stds = []
    
    for i, result in enumerate(results):
        if 'solver_name' not in result:
            raise ValueError(f"Result {i} missing 'solver_name' field.")
        if 'metric_value' not in result:
            raise ValueError(f"Result {i} missing 'metric_value' field.")
        
        solver_names.append(result['solver_name'])
        metric_values.append(result['metric_value'])
        metric_stds.append(result.get('metric_std', 0.0))
    
    # Sort by metric value (ascending for runtime/error, descending for accuracy)
    reverse_sort = metric in ['accuracy']
    sorted_indices = np.argsort(metric_values)[::-1 if reverse_sort else 1]
    
    solver_names_sorted = [solver_names[i] for i in sorted_indices]
    metric_values_sorted = [metric_values[i] for i in sorted_indices]
    metric_stds_sorted = [metric_stds[i] for i in sorted_indices]
    
    # Create horizontal bar chart
    y_pos = np.arange(len(solver_names_sorted))
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']
    bar_colors = [colors[i % len(colors)] for i in range(len(solver_names_sorted))]
    
    if show_error_bars and any(std > 0 for std in metric_stds_sorted):
        ax.barh(y_pos, metric_values_sorted, xerr=metric_stds_sorted,
               color=bar_colors, edgecolor='black', linewidth=1.5,
               capsize=5, zorder=5)
    else:
        ax.barh(y_pos, metric_values_sorted, color=bar_colors,
               edgecolor='black', linewidth=1.5, zorder=5)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(solver_names_sorted, fontsize=11)
    ax.set_xlabel(f'{metric.capitalize()} Value', fontsize=12)
    
    if title is None:
        title = f'Solver Comparison: {metric.capitalize()} ({len(results)} solvers)'
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Legend not needed for horizontal bar chart (solver names on y-axis)
    # But add it in lower right if desired
    ax.grid(True, axis='x', alpha=0.3, zorder=0)
    
    # Highlight best performer
    best_idx = 0  # Already sorted
    ax.text(metric_values_sorted[best_idx] + max(metric_values_sorted) * 0.02,
           best_idx, '★ Best', fontsize=10, color='green',
           fontweight='bold', va='center', zorder=10)
    
    # Add disclaimer
    disclaimer = "DIAGNOSTIC VIEW - Not for hardware calibration"
    ax.text(0.99, 0.01, disclaimer, transform=ax.transAxes,
           fontsize=7, color='red', ha='right', va='bottom',
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    return ax


def plot_diagnostic_success_failure_summary(
    benchmark_runs: List[Dict[str, Any]],
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 8),
    group_by: str = 'solver',
) -> Axes:
    """
    Plot summary of successful vs failed benchmark runs.
    
    Visualizes success/failure rates across different dimensions (solver, problem size, etc.).
    
    Args:
        benchmark_runs: List of benchmark run records, each containing:
            - 'status': str - 'success' or 'failure'
            - 'solver': str - solver name
            - 'n_atoms': int - problem size
            - 'error_message': str - failure reason (if failed)
            - 'artifact_id': str - unique identifier
        ax: Matplotlib axes. Creates new if None.
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches.
        group_by: Grouping dimension ('solver', 'n_atoms', 'problem_type').
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If benchmark_runs lack required fields
        
    Example:
        >>> runs = load_benchmark_log('benchmark_log.json')
        >>> ax = plot_success_failure_summary(runs, group_by='solver')
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Extract and validate data
    statuses = []
    groups = []
    
    for i, run in enumerate(benchmark_runs):
        if 'status' not in run:
            raise ValueError(f"Benchmark run {i} missing 'status' field.")
        if group_by not in run:
            raise ValueError(f"Benchmark run {i} missing '{group_by}' field.")
        
        statuses.append(run['status'].lower())
        groups.append(str(run[group_by]))
    
    # Count successes and failures per group
    unique_groups = sorted(set(groups))
    success_counts = []
    failure_counts = []
    
    for group in unique_groups:
        indices = [i for i, g in enumerate(groups) if g == group]
        success_count = sum(1 for i in indices if statuses[i] == 'success')
        failure_count = sum(1 for i in indices if statuses[i] == 'failure')
        success_counts.append(success_count)
        failure_counts.append(failure_count)
    
    # Create stacked bar chart
    x_pos = np.arange(len(unique_groups))
    width = 0.6
    
    p1 = ax.bar(x_pos, success_counts, width, label='Success',
               color='#6A994E', edgecolor='black', linewidth=1.5, zorder=5)
    p2 = ax.bar(x_pos, failure_counts, width, bottom=success_counts,
               label='Failure', color='#C73E1D', edgecolor='black',
               linewidth=1.5, zorder=5)
    
    # Add count labels on bars
    for i, (s, f) in enumerate(zip(success_counts, failure_counts)):
        total = s + f
        if total > 0:
            success_rate = s / total * 100
            ax.text(i, s + f / 2, f'{success_rate:.0f}%',
                   ha='center', va='center', fontsize=9,
                   fontweight='bold', color='white', zorder=10)
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(unique_groups, rotation=45, ha='right', fontsize=10)
    ax.set_ylabel('Number of Runs', fontsize=12)
    ax.set_xlabel(group_by.replace('_', ' ').title(), fontsize=12)
    
    if title is None:
        total_runs = len(benchmark_runs)
        title = f'Benchmark Success/Failure Summary ({total_runs} runs)'
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, axis='y', alpha=0.3, zorder=0)
    
    # Adjust layout first to make room for external elements
    plt.tight_layout()
    
    # Get figure for external text placement
    fig = ax.get_figure()
    
    # Add overall statistics outside plot area at upper right (above legend)
    total_success = sum(success_counts)
    total_failure = sum(failure_counts)
    total = total_success + total_failure
    if total > 0:
        overall_rate = total_success / total * 100
        stats_text = f'Total: {total}\nSuccess Rate: {overall_rate:.1f}%'
        fig.text(0.99, 0.99, stats_text, transform=fig.transFigure, fontsize=9,
                verticalalignment='top', ha='right',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # Place legend outside plot area at upper right (below stats)
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 0.85), fontsize=8, 
             framealpha=0.95, edgecolor='gray', borderpad=2,
             labelspacing=0.3, handletextpad=4)
    
    # Add disclaimer outside plot area at bottom right (below the axes)
    fig.text(0.99, -0.02, "DIAGNOSTIC VIEW - Not for hardware calibration",
            transform=fig.transFigure, fontsize=7, color='red', ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    return ax


def plot_diagnostic_cpu_gpu_error_comparison(
    cpu_results: List[Dict[str, Any]],
    gpu_results: List[Dict[str, Any]],
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 6),
    error_metric: str = 'relative_error',
) -> Axes:
    """
    Plot CPU vs GPU computation error comparison.
    
    Compares numerical accuracy between CPU and GPU implementations.
    
    Args:
        cpu_results: List of CPU result dicts, each containing:
            - 'observable': str - observable name
            - 'value': float - computed value
            - 'reference_value': float - ground truth or high-precision reference
        gpu_results: List of GPU result dicts (same structure as cpu_results).
        ax: Matplotlib axes. Creates new if None.
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches.
        error_metric: Error metric type ('relative_error', 'absolute_error').
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If results lack required fields
        
    Example:
        >>> cpu_res = [{'observable': 'pop_0', 'value': 0.498, 'reference_value': 0.5}]
        >>> gpu_res = [{'observable': 'pop_0', 'value': 0.497, 'reference_value': 0.5}]
        >>> ax = plot_cpu_gpu_error_comparison(cpu_res, gpu_res)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    def compute_errors(results):
        errors = {}
        for r in results:
            if 'observable' not in r:
                raise ValueError("Result missing 'observable' field.")
            if 'value' not in r:
                raise ValueError("Result missing 'value' field.")
            if 'reference_value' not in r:
                raise ValueError("Result missing 'reference_value' field.")
            
            obs = r['observable']
            val = r['value']
            ref = r['reference_value']
            
            if error_metric == 'relative_error':
                if ref == 0:
                    err = abs(val) if val != 0 else 0
                else:
                    err = abs(val - ref) / abs(ref)
            elif error_metric == 'absolute_error':
                err = abs(val - ref)
            else:
                raise ValueError(f"Unknown error_metric: {error_metric}")
            
            errors[obs] = err
        return errors
    
    cpu_errors = compute_errors(cpu_results)
    gpu_errors = compute_errors(gpu_results)
    
    # Find common observables
    common_obs = sorted(set(cpu_errors.keys()) & set(gpu_errors.keys()))
    
    if not common_obs:
        raise ValueError("No common observables found between CPU and GPU results.")
    
    cpu_err_vals = [cpu_errors[obs] for obs in common_obs]
    gpu_err_vals = [gpu_errors[obs] for obs in common_obs]
    
    # Plot grouped bar chart
    x = np.arange(len(common_obs))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, cpu_err_vals, width, label='CPU',
                  color='#2E86AB', edgecolor='black', linewidth=1.5, zorder=5)
    bars2 = ax.bar(x + width/2, gpu_err_vals, width, label='GPU',
                  color='#A23B72', edgecolor='black', linewidth=1.5, zorder=5)
    
    ax.set_xticks(x)
    ax.set_xticklabels(common_obs, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel(f'{error_metric.replace("_", " ").title()}', fontsize=12)
    ax.set_xlabel('Observable', fontsize=12)
    
    if title is None:
        title = f'CPU vs GPU Error Comparison ({error_metric.replace("_", " ").title()})'
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Adjust layout first to make room for external elements
    plt.tight_layout()
    
    # Get figure for external text placement
    fig = ax.get_figure()
    
    # Add ratio annotation outside plot area at upper right (above legend)
    ratios = [gpu/cpu if cpu > 0 else float('inf') for cpu, gpu in zip(cpu_err_vals, gpu_err_vals)]
    avg_ratio = np.mean([r for r in ratios if r != float('inf')])
    
    if avg_ratio != float('inf'):
        ratio_text = f'Avg GPU/CPU ratio: {avg_ratio:.2f}x'
        fig.text(0.99, 0.99, ratio_text, transform=fig.transFigure, fontsize=9,
                verticalalignment='top', ha='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Place legend outside plot area at upper right (below ratio text)
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 0.85), fontsize=8, 
             framealpha=0.95, edgecolor='gray', borderpad=2,
             labelspacing=0.3, handletextpad=4)
    ax.grid(True, axis='y', alpha=0.3, zorder=0)
    ax.set_yscale('log')  # Log scale for error visualization
    
    # Add disclaimer outside plot area at bottom right (below the axes)
    fig.text(0.99, -0.02, "DIAGNOSTIC VIEW - Not for hardware calibration",
            transform=fig.transFigure, fontsize=7, color='red', ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    return ax
