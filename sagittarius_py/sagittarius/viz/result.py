"""
Simulation result visualization utilities.

Provides plotting helpers for SimulationResult objects, including observable
trajectories, bitstring distributions, shot histograms, and population heatmaps.
These functions extract data from results without triggering Julia initialization.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional, List, Dict, Any
import pandas as pd


def plot_observables(
    result,
    names: Optional[List[str]] = None,
    ax: Optional[Axes] = None,
    show: bool = False,
    title: Optional[str] = None,
    linewidth: float = 2.0,
    grid_alpha: float = 0.6,
) -> Axes:
    """
    Plot observable trajectories over time.
    
    Extracts time-series data from SimulationResult and plots expectation values
    of observables. Supports selecting specific observables by name.
    
    Args:
        result: SimulationResult object with .to_pandas() method
        names: List of observable names to plot. If None, plots all columns 
              that don't look like metadata (e.g., excludes 'time' if present).
        ax: Matplotlib axes. Creates new figure if None.
        show: If True, calls plt.show() after plotting.
        title: Custom plot title. Auto-generated if None.
        linewidth: Line width for trajectories (default: 2.0)
        grid_alpha: Grid line transparency (default: 0.6)
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If no observable data is found or specified names don't exist.
        
    Example:
        >>> from sagittarius.viz import plot_observables
        >>> result = sim.run()
        >>> ax = plot_observables(result, names=['pop0', 'pop1'])
        >>> ax.set_ylim(-0.1, 1.1)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    
    # Convert result to DataFrame
    try:
        df = result.to_pandas()
    except Exception as e:
        raise ValueError(f"Failed to convert result to pandas DataFrame: {e}")
    
    if df.empty:
        raise ValueError("Result DataFrame is empty. No observable data to plot.")
    
    # Determine which columns to plot
    if names is not None:
        # Validate requested names
        missing = [n for n in names if n not in df.columns]
        if missing:
            raise ValueError(
                f"Observables not found in result: {missing}. "
                f"Available columns: {list(df.columns)}"
            )
        df_plot = df[names]
    else:
        # Auto-detect observable columns (exclude common metadata columns)
        exclude_cols = {'time', 't', 'timestamp', 'index'}
        obs_cols = [col for col in df.columns if col.lower() not in exclude_cols]
        
        if not obs_cols:
            raise ValueError(
                f"No observable columns found. All columns: {list(df.columns)}. "
                "Specify explicit 'names' parameter."
            )
        df_plot = df[obs_cols]
        names = obs_cols
    
    # Get time axis
    # Assume index is time, or look for 'time' column
    if 'time' in df.columns:
        time_vals = df['time'].values
    elif 't' in df.columns:
        time_vals = df['t'].values
    else:
        # Use DataFrame index as time
        time_vals = df.index.values
    
    # Plot each observable
    for col in df_plot.columns:
        ax.plot(time_vals, df_plot[col].values, linewidth=linewidth, label=col)
    
    # Formatting
    ax.set_xlabel("Time (μs)", fontsize=11)
    ax.set_ylabel("Expectation Value", fontsize=11)
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        num_obs = len(df_plot.columns)
        ax.set_title(f"Observable Trajectories ({num_obs} observables)", 
                    fontsize=12, fontweight='bold')
    
    ax.legend(title="Observables", loc='best', fontsize=9)
    ax.grid(True, linestyle=':', alpha=grid_alpha)
    
    # Add horizontal reference line at y=0
    ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
    
    if show:
        plt.tight_layout()
        plt.show()
    
    return ax


def plot_bitstring_distribution(
    result,
    top_k: int = 10,
    ax: Optional[Axes] = None,
    sort_by: str = 'probability',
    title: Optional[str] = None,
    bar_color: str = 'steelblue',
    show_values: bool = True,
    show_basis_info: bool = True,
) -> Axes:
    """
    Plot final-state bitstring probability distribution as a bar chart.
    
    Extracts bitstring probabilities from SimulationResult and displays the
    top-K most probable states. Works with both full and reduced basis results.
    Automatically detects and displays basis mode (full/reduced) and forbidden
    bitstring count when available in result metadata.
    
    Args:
        result: SimulationResult object with .final_bitstring_distribution() method
        top_k: Number of top-probability bitstrings to display (default: 10)
        ax: Matplotlib axes. Creates new if None.
        sort_by: Sorting criterion: 'probability' (desc) or 'bitstring' (asc)
        title: Custom plot title. Auto-generated if None.
        bar_color: Color for bars (default: 'steelblue')
        show_values: If True, display probability values on top of bars
        show_basis_info: If True, display basis mode and forbidden bitstring info
                        in the plot (default: True)
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        AttributeError: If result doesn't support bitstring distribution
        ValueError: If distribution is empty
        
    Example:
        >>> # Direct plotting
        >>> result = sim.run()
        >>> ax = plot_bitstring_distribution(result, top_k=8)
        >>> 
        >>> # From saved file
        >>> from sagittarius import load_result
        >>> result = load_result("result.json")
        >>> ax = plot_bitstring_distribution(result, show_basis_info=True)
        >>> plt.xticks(rotation=45, ha='right')
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 6))
    
    # Extract bitstring distribution
    if not hasattr(result, 'final_bitstring_distribution'):
        raise AttributeError(
            "Result object does not have 'final_bitstring_distribution' method. "
            "This may indicate the simulation didn't compute final state probabilities."
        )
    
    dist_dict = result.final_bitstring_distribution()
    
    if not dist_dict:
        raise ValueError("Bitstring distribution is empty.")
    
    # Convert to Series for easy sorting
    dist_series = pd.Series(dist_dict)
    
    # Sort
    if sort_by == 'probability':
        dist_series = dist_series.sort_values(ascending=False)
    elif sort_by == 'bitstring':
        dist_series = dist_series.sort_index()
    else:
        raise ValueError(f"Invalid sort_by='{sort_by}'. Use 'probability' or 'bitstring'.")
    
    # Take top-k
    if top_k < len(dist_series):
        dist_series = dist_series.head(top_k)
        suffix = f" (top {top_k})"
    else:
        suffix = ""
    
    # Create bar chart
    x_positions = np.arange(len(dist_series))
    bars = ax.bar(x_positions, dist_series.values, color=bar_color, 
                 edgecolor='black', linewidth=0.5)
    
    # Set labels
    ax.set_xticks(x_positions)
    ax.set_xticklabels(dist_series.index, rotation=45, ha='right', fontsize=9)
    
    # Show values on bars
    if show_values:
        for i, (bar, val) in enumerate(zip(bars, dist_series.values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:.3f}',
                   ha='center', va='bottom', fontsize=8, rotation=0)
    
    # Formatting
    ax.set_xlabel("Bitstring", fontsize=11)
    ax.set_ylabel("Probability", fontsize=11)
    
    # Extract basis mode and forbidden bitstring information
    basis_mode = None
    forbidden_count = None
    
    if show_basis_info:
        # Try to get basis mode from metadata
        if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            readout = result.metadata.get('readout', {})
            basis_mode = readout.get('basis_mode')
            forbidden_count = readout.get('forbidden_bitstring_count')
        
        # Also check run_manifest if available
        if basis_mode is None and hasattr(result, 'run_manifest'):
            manifest = result.run_manifest
            solver_config = manifest.get('solver_config', {})
            basis_mode = solver_config.get('basis_mode')
    
    # Build title
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        total_prob = dist_series.sum()
        title_parts = [f"Final Bitstring Distribution{suffix}"]
        
        # Add basis mode info
        if basis_mode:
            mode_label = "Reduced Basis" if basis_mode == "reduced" else "Full Basis"
            title_parts.append(mode_label)
        
        # Add forbidden bitstring info
        if forbidden_count and forbidden_count > 0:
            title_parts.append(f"{forbidden_count} forbidden states excluded")
        
        # Add total probability
        title_parts.append(f"Total probability: {total_prob:.4f}")
        
        ax.set_title('\n'.join(title_parts), fontsize=12, fontweight='bold')
    
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    ax.set_ylim(bottom=0)
    
    # Add basis info text box if enabled and data available
    if show_basis_info and (basis_mode or forbidden_count):
        info_text = ""
        if basis_mode:
            mode_str = "Reduced" if basis_mode == "reduced" else "Full"
            info_text += f"Basis: {mode_str}\n"
        if forbidden_count and forbidden_count > 0:
            info_text += f"Forbidden: {forbidden_count}\n"
        
        if info_text:
            # Position text box in upper right corner
            ax.text(0.98, 0.97, info_text.strip(),
                   transform=ax.transAxes, fontsize=8,
                   verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
    
    plt.tight_layout()
    
    return ax


def plot_shot_histogram(
    result,
    ax: Optional[Axes] = None,
    top_k: int = 20,
    normalize: bool = False,
    title: Optional[str] = None,
    bar_color: str = 'coral',
    show_seed_info: bool = True,
) -> Axes:
    """
    Plot measurement shot counts as a histogram.
    
    Visualizes the results of quantum sampling (result.sample()), showing
    how many times each bitstring was observed. Can display raw counts or
    normalized frequencies. Automatically extracts and displays random seed
    metadata when available in result object.
    
    Supports reading from measurement-samples/v1 format via result.samples
    attribute or result.manifest metadata.
    
    Args:
        result: SimulationResult object with .samples attribute or sample metadata
        ax: Matplotlib axes. Creates new if None.
        top_k: Maximum number of unique bitstrings to display (default: 20)
        normalize: If True, normalize counts to frequencies (sum to 1)
        title: Custom plot title. Auto-generated if None.
        bar_color: Color for bars (default: 'coral')
        show_seed_info: If True, display random seed information in plot
                       (default: True)
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        AttributeError: If result has no samples
        ValueError: If samples array is empty
        
    Example:
        >>> # Direct plotting with samples
        >>> result = sim.run()
        >>> result.sample(shots=1000, seed=42)  # Stores samples internally
        >>> ax = plot_shot_histogram(result, top_k=15, normalize=True)
        >>> 
        >>> # From saved file with measurement-samples/v1
        >>> from sagittarius import load_result
        >>> result = load_result("simulation.json")
        >>> ax = plot_shot_histogram(result, show_seed_info=True)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 6))
    
    # Extract samples
    if not hasattr(result, 'samples') or result.samples is None:
        raise AttributeError(
            "Result object has no 'samples' attribute. "
            "Call result.sample(shots=N, seed=S) before plotting."
        )
    
    samples = result.samples
    
    if len(samples) == 0:
        raise ValueError("Samples array is empty.")
    
    total_shots = len(samples)
    
    # Count occurrences of each unique bitstring
    unique_bitstrings, counts = np.unique(samples, return_counts=True)
    
    # Sort by count (descending) - unified sorting rule
    sorted_indices = np.argsort(counts)[::-1]
    unique_sorted = unique_bitstrings[sorted_indices]
    counts_sorted = counts[sorted_indices]
    
    # Limit to top-k
    if top_k < len(unique_sorted):
        unique_display = unique_sorted[:top_k]
        counts_display = counts_sorted[:top_k]
        remaining_count = counts_sorted[top_k:].sum()
        suffix = f" (top {top_k} of {len(unique_sorted)} unique)"
    else:
        unique_display = unique_sorted
        counts_display = counts_sorted
        remaining_count = 0
        suffix = ""
    
    # Normalize if requested
    if normalize:
        display_values = counts_display / total_shots
        ylabel = "Frequency"
        value_format = '{:.3f}'
    else:
        display_values = counts_display
        ylabel = "Shot Count"
        value_format = '{:d}'
    
    # Create bar chart
    x_positions = np.arange(len(unique_display))
    bars = ax.bar(x_positions, display_values, color=bar_color,
                 edgecolor='black', linewidth=0.5)
    
    # Set labels
    ax.set_xticks(x_positions)
    ax.set_xticklabels(unique_display, rotation=45, ha='right', fontsize=9)
    
    # Show values on bars
    for bar, val in zip(bars, display_values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               value_format.format(val),
               ha='center', va='bottom', fontsize=8)
    
    # Formatting
    ax.set_xlabel("Bitstring", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    
    # Extract random seed metadata
    seed_value = None
    if show_seed_info:
        # Try to get seed from manifest (measurement-samples/v1 format)
        if hasattr(result, 'manifest') and isinstance(result.manifest, dict):
            readout = result.manifest.get('readout', {})
            seed_value = readout.get('seed') or readout.get('effective_seed')
        
        # Also check metadata
        if seed_value is None and hasattr(result, 'metadata'):
            metadata = result.metadata if isinstance(result.metadata, dict) else {}
            readout = metadata.get('readout', {})
            seed_value = readout.get('seed') or readout.get('effective_seed')
    
    # Build title
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        title_parts = [f"Measurement Shot Histogram{suffix}"]
        title_parts.append(f"Total shots: {total_shots}")
        
        # Add seed info if available
        if show_seed_info and seed_value is not None:
            title_parts.append(f"Random seed: {seed_value}")
        
        ax.set_title('\n'.join(title_parts), fontsize=12, fontweight='bold')
    
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    ax.set_ylim(bottom=0)
    
    # Add note about remaining bitstrings if truncated
    if remaining_count > 0:
        remaining_label = value_format.format(remaining_count) if not normalize \
                         else f'{remaining_count/total_shots:.3f}'
        ax.text(0.98, 0.02, f"Remaining: {remaining_label}",
               transform=ax.transAxes, fontsize=8, ha='right', va='bottom',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Add seed info box if enabled and data available
    if show_seed_info and seed_value is not None:
        info_text = f"Seed: {seed_value}\nShots: {total_shots}"
        if normalize:
            info_text += "\nMode: Frequency"
        else:
            info_text += "\nMode: Count"
        
        # Position text box in upper right corner
        ax.text(0.98, 0.97, info_text,
               transform=ax.transAxes, fontsize=8,
               verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    plt.tight_layout()
    
    return ax


def plot_population_heatmap(
    result,
    ax: Optional[Axes] = None,
    cmap: str = 'viridis',
    title: Optional[str] = None,
    show_colorbar: bool = True,
    atom_order: Optional[List[int]] = None,
) -> Axes:
    """
    Plot atom-by-time Rydberg population heatmap.
    
    Creates a 2D heatmap showing how the Rydberg population of each atom
    evolves over time. Requires the result to contain population observables
    (typically named 'pop0', 'pop1', etc.).
    
    Args:
        result: SimulationResult object with population data in .to_pandas()
        ax: Matplotlib axes. Creates new if None.
        cmap: Matplotlib colormap name (default: 'viridis')
        title: Custom plot title. Auto-generated if None.
        show_colorbar: If True, display color scale legend
        atom_order: Optional list of atom indices specifying custom ordering.
                   If None, uses default sorted order from column names.
                   Example: [2, 0, 1] to reorder atoms as pop2, pop0, pop1
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If no population columns found in result or invalid atom_order
        
    Example:
        >>> result = sim.run()
        >>> # Default ordering (pop0, pop1, pop2, ...)
        >>> ax = plot_population_heatmap(result, cmap='plasma')
        >>> 
        >>> # Custom atom ordering
        >>> ax = plot_population_heatmap(result, atom_order=[2, 0, 1])
        >>> plt.colorbar(ax.collections[0], label='Population')
    """
    # Convert to DataFrame
    try:
        df = result.to_pandas()
    except Exception as e:
        raise ValueError(f"Failed to convert result to DataFrame: {e}")
    
    # Find population columns (pop0, pop1, pop2, ...)
    pop_cols = sorted([col for col in df.columns if col.startswith('pop')])
    
    if not pop_cols:
        raise ValueError(
            f"No population columns found in result. "
            f"Available columns: {list(df.columns)}. "
            "Ensure simulation includes Rydberg population observables."
        )
    
    # Extract atom indices from column names
    try:
        available_atom_indices = [int(col.replace('pop', '')) for col in pop_cols]
    except ValueError:
        # If column names don't follow 'popN' pattern, use sequential indices
        available_atom_indices = list(range(len(pop_cols)))
    
    # Apply custom atom ordering if specified - VALIDATE BEFORE CREATING FIGURE
    if atom_order is not None:
        # Validate atom_order
        invalid_atoms = [idx for idx in atom_order if idx not in available_atom_indices]
        if invalid_atoms:
            raise ValueError(
                f"Invalid atom indices in atom_order: {invalid_atoms}. "
                f"Available atom indices: {available_atom_indices}"
            )
        
        # Check for duplicates
        if len(atom_order) != len(set(atom_order)):
            raise ValueError("atom_order contains duplicate indices")
        
        # Reorder population columns according to atom_order
        ordered_cols = []
        for idx in atom_order:
            col_name = f'pop{idx}'
            if col_name in pop_cols:
                ordered_cols.append(col_name)
            else:
                raise ValueError(
                    f"Column '{col_name}' not found for atom index {idx}. "
                    f"Available columns: {pop_cols}"
                )
        pop_cols = ordered_cols
        atom_indices = atom_order
    else:
        # Use default sorted order
        atom_indices = available_atom_indices
    
    # Create figure if needed (after all validation)
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract data matrix: Time x Atoms
    data_matrix = df[pop_cols].values  # Shape: (n_times, n_atoms)
    
    # Get time axis
    if 'time' in df.columns:
        time_vals = df['time'].values
    elif 't' in df.columns:
        time_vals = df['t'].values
    else:
        time_vals = df.index.values
    
    # Create heatmap
    # extent: [left, right, bottom, top]
    extent = [time_vals[0], time_vals[-1], -0.5, len(pop_cols) - 0.5]
    
    im = ax.imshow(data_matrix.T, aspect='auto', extent=extent, 
                  cmap=cmap, origin='lower')
    
    # Set axis labels
    ax.set_yticks(range(len(atom_indices)))
    ax.set_yticklabels([f'Atom {i}' for i in atom_indices], fontsize=9)
    ax.set_xlabel("Time (μs)", fontsize=11)
    ax.set_ylabel("Atom Index", fontsize=11)
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        ax.set_title("Rydberg Population Heatmap", fontsize=12, fontweight='bold')
    
    # Add colorbar
    if show_colorbar:
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Population', fontsize=10)
    
    # Add grid lines between atoms
    ax.set_yticks(np.arange(-0.5, len(pop_cols), 1), minor=True)
    ax.grid(which='minor', axis='y', linestyle='-', linewidth=0.5, color='white', alpha=0.3)
    
    # Add numerical annotations on heatmap cells
    n_times, n_atoms_in_data = data_matrix.shape
    # Only annotate if the matrix is not too large (avoid cluttering)
    if n_times <= 20 and n_atoms_in_data <= 15:
        for i in range(n_times):
            for j in range(n_atoms_in_data):
                value = data_matrix[i, j]
                # Format value based on magnitude
                if value < 0.01:
                    text = f'{value:.3f}'
                elif value < 0.1:
                    text = f'{value:.2f}'
                else:
                    text = f'{value:.2f}'
                
                # Choose text color based on background brightness
                # Normalize colormap to determine if background is dark or light
                norm_value = (value - np.min(data_matrix)) / (np.max(data_matrix) - np.min(data_matrix) + 1e-10)
                text_color = 'white' if norm_value < 0.5 else 'black'
                
                # Calculate center position of the cell
                # For imshow with extent, we need to compute the actual center coordinates
                
                # X-axis: calculate cell boundaries and find center
                if n_times == 1:
                    # Single time point: center at the only time value
                    x_center = time_vals[0]
                else:
                    # Multiple time points: divide the extent into equal cells
                    t_min = time_vals[0]
                    t_max = time_vals[-1]
                    # Each cell width
                    dt = (t_max - t_min) / n_times
                    # Cell center
                    x_center = t_min + (i + 0.5) * dt
                
                # Y-axis: imshow with extent=[..., -0.5, len-0.5], cell centers are at integer positions
                y_center = j
                
                ax.text(x_center, y_center, text,
                       ha='center', va='center',
                       fontsize=7, color=text_color, weight='bold')
    
    return ax


def plot_result_summary(
    result,
    figsize: tuple = (14, 10),
    show: bool = False,
) -> List[Axes]:
    """
    Create a multi-panel summary plot of simulation results.
    
    Convenience function that generates a comprehensive view including:
    - Observable trajectories
    - Final bitstring distribution
    - Population heatmap
    
    Args:
        result: SimulationResult object
        figsize: Figure size (width, height) in inches
        show: If True, display the figure immediately
        
    Returns:
        List of Axes objects [ax_observables, ax_bitstrings, ax_heatmap]
        
    Example:
        >>> result = sim.run()
        >>> axes = plot_result_summary(result, show=True)
    """
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    
    # Flatten axes for easier indexing
    ax_flat = axes.flatten()
    
    try:
        # Panel 1: Observables
        ax_obs = plot_observables(result, ax=ax_flat[0])
    except Exception as e:
        ax_flat[0].text(0.5, 0.5, f"Observable plot failed:\n{str(e)}",
                       ha='center', va='center', transform=ax_flat[0].transAxes)
        ax_obs = ax_flat[0]
    
    try:
        # Panel 2: Bitstring distribution
        ax_bits = plot_bitstring_distribution(result, ax=ax_flat[1], top_k=8)
    except Exception as e:
        ax_flat[1].text(0.5, 0.5, f"Bitstring plot failed:\n{str(e)}",
                       ha='center', va='center', transform=ax_flat[1].transAxes)
        ax_bits = ax_flat[1]
    
    try:
        # Panel 3: Population heatmap
        ax_heat = plot_population_heatmap(result, ax=ax_flat[2])
    except Exception as e:
        ax_flat[2].text(0.5, 0.5, f"Heatmap plot failed:\n{str(e)}",
                       ha='center', va='center', transform=ax_flat[2].transAxes)
        ax_heat = ax_flat[2]
    
    # Panel 4: Metadata summary (text)
    ax_meta = ax_flat[3]
    ax_meta.axis('off')
    
    # Extract metadata
    meta_text = "Simulation Metadata\n" + "="*40 + "\n"
    
    if hasattr(result, 'run_manifest'):
        manifest = result.run_manifest
        if 'register_geometry' in manifest:
            geom = manifest['register_geometry']
            meta_text += f"Atoms: {geom.get('n_atoms', 'N/A')}\n"
            meta_text += f"Geometry type: {geom.get('type', 'N/A')}\n"
        
        if 'solver_config' in manifest:
            solver = manifest['solver_config']
            meta_text += f"Method: {solver.get('method', 'N/A')}\n"
            meta_text += f"Adaptive: {solver.get('adaptive', 'N/A')}\n"
    
    if hasattr(result, 'metadata'):
        meta = result.metadata
        if 'backend' in meta:
            meta_text += f"Backend: {meta['backend']}\n"
        if 'basis_mode' in meta:
            meta_text += f"Basis mode: {meta['basis_mode']}\n"
    
    ax_meta.text(0.1, 0.9, meta_text, transform=ax_meta.transAxes,
                fontsize=9, verticalalignment='top', family='monospace')
    
    plt.tight_layout()
    
    if show:
        plt.show()
    
    return [ax_obs, ax_bits, ax_heat, ax_meta]
