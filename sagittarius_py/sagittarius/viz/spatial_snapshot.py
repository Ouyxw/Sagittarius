"""
Spatial snapshot and animation frame extraction utilities.

Provides tools for extracting spatial configuration data at specific time steps,
generating standardized frame data for animations, and visualizing atom-by-atom
observable values mapped to colors on the register layout.

These functions extract data from SimulationResult objects without triggering
Julia initialization, maintaining strict separation between visualization and
simulation data layers.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from typing import Optional, List, Dict, Any, Tuple, Union
import pandas as pd


def _extract_atom_populations(
    result,
    time_index: int,
    observable_prefix: str = 'pop',
) -> Dict[int, float]:
    """
    Extract per-atom observable values at a specific time step.
    
    Args:
        result: SimulationResult with .to_pandas() method
        time_index: Time step index (0-based)
        observable_prefix: Column prefix for observables (default: 'pop')
        
    Returns:
        Dictionary mapping atom indices to observable values
        
    Raises:
        ValueError: If no matching observable columns found or time_index out of range
    """
    df = result.to_pandas()
    
    if time_index < 0 or time_index >= len(df):
        raise ValueError(
            f"Time index {time_index} out of range [0, {len(df) - 1}]. "
            f"Result has {len(df)} time steps."
        )
    
    # Find observable columns
    obs_cols = [col for col in df.columns if col.startswith(observable_prefix)]
    
    if not obs_cols:
        raise ValueError(
            f"No observable columns with prefix '{observable_prefix}' found. "
            f"Available columns: {list(df.columns)}"
        )
    
    # Extract atom indices from column names
    populations = {}
    for col in obs_cols:
        try:
            atom_idx = int(col.replace(observable_prefix, ''))
            populations[atom_idx] = float(df[col].iloc[time_index])
        except (ValueError, IndexError):
            continue
    
    if not populations:
        raise ValueError(
            f"Could not parse atom indices from columns: {obs_cols}. "
            f"Expected format: '{observable_prefix}0', '{observable_prefix}1', etc."
        )
    
    return populations


def extract_spatial_snapshot(
    result,
    register,
    time_index: int,
    observable_name: str = 'pop',
) -> Dict[str, Any]:
    """
    Extract complete spatial snapshot at a specific time step.
    
    Combines atom positions with observable values to create a complete
    spatial configuration snapshot suitable for visualization or animation frames.
    
    Args:
        result: SimulationResult object
        register: Register object with atom positions
        time_index: Time step index (0-based)
        observable_name: Observable type to extract ('pop' for population, 
                        'energy', 'phase', etc.)
        
    Returns:
        Dictionary containing:
        - n_atoms: int - Number of atoms
        - time_index: int - Time step index
        - time_value: float - Actual time value
        - positions: np.ndarray - Nx2 array of atom coordinates
        - observables: Dict[int, float] - Atom-indexed observable values
        - metadata: Dict - Additional context (register info, observable type)
        
    Raises:
        ValueError: If data extraction fails or parameters invalid
        
    Example:
        >>> snapshot = extract_spatial_snapshot(result, reg, time_index=5)
        >>> print(f"At t={snapshot['time_value']:.3f}:")
        >>> for idx, val in snapshot['observables'].items():
        ...     pos = snapshot['positions'][idx]
        ...     print(f"  Atom {idx} at ({pos[0]:.2f}, {pos[1]:.2f}): {val:.3f}")
    """
    df = result.to_pandas()
    
    # Validate time index
    if time_index < 0 or time_index >= len(df):
        raise ValueError(
            f"Time index {time_index} out of range [0, {len(df) - 1}]"
        )
    
    # Get time value
    if 't' in df.columns:
        time_value = float(df['t'].iloc[time_index])
    elif 'time' in df.columns:
        time_value = float(df['time'].iloc[time_index])
    else:
        time_value = float(time_index)
    
    # Extract atom positions
    positions = np.array([[atom.x, atom.y] for atom in register.atoms])
    n_atoms = len(register.atoms)
    
    # Extract observables
    observable_prefix = observable_name
    populations = _extract_atom_populations(result, time_index, observable_prefix)
    
    # Ensure all atoms have values (fill missing with 0.0)
    for i in range(n_atoms):
        if i not in populations:
            populations[i] = 0.0
    
    return {
        'n_atoms': n_atoms,
        'time_index': time_index,
        'time_value': time_value,
        'positions': positions,
        'observables': populations,
        'metadata': {
            'register': {
                'atom_count': n_atoms,
                'C6': getattr(register, 'C6', None),
            },
            'observable_type': observable_name,
            'total_time_steps': len(df),
        }
    }


def extract_frame_sequence(
    result,
    register,
    time_indices: Optional[List[int]] = None,
    observable_name: str = 'pop',
    stride: int = 1,
) -> List[Dict[str, Any]]:
    """
    Extract sequence of spatial snapshots for animation.
    
    Generates standardized frame data at specified time steps, suitable for
    creating animations or multi-panel visualizations.
    
    Args:
        result: SimulationResult object
        register: Register object
        time_indices: Specific time indices to extract. If None, uses all steps
                     with optional stride
        observable_name: Observable type to map to colors
        stride: Step size when auto-generating time_indices (default: 1)
        
    Returns:
        List of snapshot dictionaries (see extract_spatial_snapshot)
        
    Raises:
        ValueError: If time_indices invalid or extraction fails
        
    Example:
        >>> # Extract every 5th frame
        >>> frames = extract_frame_sequence(result, reg, stride=5)
        >>> print(f"Extracted {len(frames)} frames")
        >>> 
        >>> # Extract specific frames
        >>> frames = extract_frame_sequence(result, reg, time_indices=[0, 10, 20, 30])
    """
    df = result.to_pandas()
    n_steps = len(df)
    
    # Determine time indices
    if time_indices is None:
        time_indices = list(range(0, n_steps, stride))
    else:
        # Validate indices
        invalid = [idx for idx in time_indices if idx < 0 or idx >= n_steps]
        if invalid:
            raise ValueError(
                f"Invalid time indices: {invalid}. "
                f"Valid range: [0, {n_steps - 1}]"
            )
    
    # Extract snapshots
    frames = []
    for idx in time_indices:
        try:
            snapshot = extract_spatial_snapshot(
                result, register, idx, observable_name
            )
            frames.append(snapshot)
        except Exception as e:
            raise ValueError(
                f"Failed to extract frame at time_index={idx}: {e}"
            )
    
    return frames


def save_frame_data(
    frames: List[Dict[str, Any]],
    output_path: str,
    format: str = 'json',
) -> None:
    """
    Save extracted frame data to file for later use.
    
    Supports JSON format for compatibility with external animation tools
    and local artifact storage.
    
    Args:
        frames: List of snapshot dictionaries from extract_frame_sequence
        output_path: Output file path (.json)
        format: Output format (currently only 'json' supported)
        
    Raises:
        ValueError: If format unsupported or serialization fails
        
    Example:
        >>> frames = extract_frame_sequence(result, reg, stride=5)
        >>> save_frame_data(frames, 'animation_frames.json')
    """
    import json
    
    if format != 'json':
        raise ValueError(f"Unsupported format: {format}. Only 'json' is supported.")
    
    # Convert numpy arrays to lists for JSON serialization
    serializable_frames = []
    for frame in frames:
        serializable_frame = {
            'n_atoms': frame['n_atoms'],
            'time_index': frame['time_index'],
            'time_value': frame['time_value'],
            'positions': frame['positions'].tolist(),
            'observables': {str(k): v for k, v in frame['observables'].items()},
            'metadata': frame['metadata'],
        }
        serializable_frames.append(serializable_frame)
    
    # Write to file
    try:
        with open(output_path, 'w') as f:
            json.dump({
                'schema_version': 'spatial-snapshot/v1',
                'frame_count': len(serializable_frames),
                'frames': serializable_frames,
            }, f, indent=2)
    except Exception as e:
        raise ValueError(f"Failed to save frame data to {output_path}: {e}")


def plot_spatial_snapshot(
    snapshot: Dict[str, Any],
    ax: Optional[Axes] = None,
    figsize: Tuple[float, float] = (8, 8),
    cmap: str = 'viridis',
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    show_colorbar: bool = True,
    show_labels: bool = True,
    atom_size: int = 200,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Axes:
    """
    Plot a single spatial snapshot with atoms colored by observable values.
    
    Creates a scatter plot of atom positions where color represents the
    observable value at that time step.
    
    Args:
        snapshot: Snapshot dictionary from extract_spatial_snapshot
        ax: External axes. Creates new if None
        figsize: Figure size (if creating new figure)
        cmap: Colormap for encoding observable values
        vmin: Minimum value for color scale. Auto-calculated if None
        vmax: Maximum value for color scale. Auto-calculated if None
        show_colorbar: Display color scale legend
        show_labels: Show atom index labels
        atom_size: Scatter point size
        title: Custom title. Auto-generated if None
        save_path: Save figure to this path
        
    Returns:
        Matplotlib Axes object
        
    Raises:
        ValueError: If snapshot data invalid
        
    Visual Elements (zorder):
        - zorder=5: Atom scatter points (colored by observable)
        - zorder=10: Atom index labels
        
    Example:
        >>> snapshot = extract_spatial_snapshot(result, reg, time_index=10)
        >>> ax = plot_spatial_snapshot(snapshot, cmap='plasma')
        >>> plt.colorbar(ax.collections[0], label='Population')
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Extract data
    positions = snapshot['positions']
    observables = snapshot['observables']
    n_atoms = snapshot['n_atoms']
    time_value = snapshot['time_value']
    obs_type = snapshot['metadata']['observable_type']
    
    # Prepare color values
    colors = [observables[i] for i in range(n_atoms)]
    
    # Set color scale limits
    if vmin is None:
        vmin = min(colors) if colors else 0.0
    if vmax is None:
        vmax = max(colors) if colors else 1.0
    
    # Plot atoms
    scatter = ax.scatter(
        positions[:, 0], positions[:, 1],
        c=colors, cmap=cmap, s=atom_size,
        vmin=vmin, vmax=vmax, zorder=5,
        edgecolors='black', linewidths=1.5
    )
    
    # Add atom labels
    if show_labels:
        for i in range(n_atoms):
            ax.text(
                positions[i, 0], positions[i, 1], str(i),
                ha='center', va='center', fontsize=9,
                fontweight='bold', color='white',
                zorder=10
            )
    
    # Colorbar
    if show_colorbar:
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(f'{obs_type.capitalize()} Value', fontsize=10)
    
    # Title
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        ax.set_title(
            f"Spatial Snapshot — t={time_value:.3f} ({obs_type})",
            fontsize=12, fontweight='bold'
        )
    
    # Aspect ratio and labels
    ax.set_aspect('equal')
    ax.set_xlabel('x (μm)', fontsize=10)
    ax.set_ylabel('y (μm)', fontsize=10)
    
    # Grid with low alpha to avoid interfering with tick labels
    ax.grid(True, linestyle=':', alpha=0.3, zorder=0)
    
    # Enhance tick label readability with background boxes
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_bbox(dict(
            boxstyle='round,pad=0.2',
            facecolor='white',
            edgecolor='none',
            alpha=0.8
        ))
    
    # Save if requested
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Spatial snapshot saved to: {save_path}")
    
    return ax


def plot_multi_panel_snapshots(
    frames: List[Dict[str, Any]],
    panel_indices: Optional[List[int]] = None,
    figsize_per_panel: Tuple[float, float] = (6, 6),
    cmap: str = 'viridis',
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    show_colorbar: bool = False,
    suptitle: Optional[str] = None,
    save_path: Optional[str] = None,
) -> List[Axes]:
    """
    Create multi-panel visualization of multiple snapshots.
    
    Useful for comparing evolution across time steps in a single figure.
    
    Args:
        frames: List of snapshot dictionaries
        panel_indices: Which frames to display. None = first 4 frames
        figsize_per_panel: Size of each subplot
        cmap: Colormap
        vmin: Global minimum for consistent color scale
        vmax: Global maximum for consistent color scale
        show_colorbar: Show one shared colorbar
        suptitle: Overall figure title
        save_path: Save figure path
        
    Returns:
        List of Axes objects for each panel
        
    Example:
        >>> frames = extract_frame_sequence(result, reg, stride=10)
        >>> axes = plot_multi_panel_snapshots(
        ...     frames, panel_indices=[0, 5, 10, 15],
        ...     suptitle="Evolution Over Time"
        ... )
    """
    if panel_indices is None:
        panel_indices = list(range(min(4, len(frames))))
    
    n_panels = len(panel_indices)
    if n_panels == 0:
        raise ValueError("No panels to display")
    
    # Calculate grid layout
    ncols = min(2, n_panels)
    nrows = (n_panels + ncols - 1) // ncols
    
    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(figsize_per_panel[0] * ncols, figsize_per_panel[1] * nrows)
    )
    
    # Flatten axes array
    if n_panels == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    # Validate panel_indices against available frames
    invalid_indices = [idx for idx in panel_indices if idx >= len(frames)]
    if invalid_indices:
        raise ValueError(
            f"Panel indices {invalid_indices} exceed available frames ({len(frames)}). "
            f"Valid range: [0, {len(frames) - 1}]"
        )
    
    # Calculate global color scale if not provided
    if vmin is None or vmax is None:
        all_values = []
        for idx in panel_indices:
            all_values.extend(frames[idx]['observables'].values())
        if vmin is None:
            vmin = min(all_values) if all_values else 0.0
        if vmax is None:
            vmax = max(all_values) if all_values else 1.0
    
    # Plot each panel
    for panel_idx, frame_idx in enumerate(panel_indices):
        ax = axes[panel_idx]
        frame = frames[frame_idx]
        
        plot_spatial_snapshot(
            frame, ax=ax,
            cmap=cmap, vmin=vmin, vmax=vmax,
            show_colorbar=False,  # Individual colorbars disabled
            show_labels=True
        )
    
    # Hide unused subplots
    for i in range(n_panels, len(axes)):
        axes[i].set_visible(False)
    
    # Shared colorbar
    if show_colorbar:
        # Create dummy scatter for colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap)
        sm.set_clim(vmin, vmax)
        cbar = fig.colorbar(sm, ax=axes[:n_panels], fraction=0.02, pad=0.04)
        cbar.set_label('Observable Value', fontsize=10)
    
    # Super title
    if suptitle:
        fig.suptitle(suptitle, fontsize=14, fontweight='bold', y=1.02)
    
    # Use subplots_adjust instead of tight_layout for complex layouts with colorbar
    fig.subplots_adjust(
        left=0.08, right=0.92, top=0.90, bottom=0.08,
        wspace=0.3, hspace=0.3
    )
    
    # Save if requested
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Multi-panel snapshot saved to: {save_path}")
    
    return axes[:n_panels]
