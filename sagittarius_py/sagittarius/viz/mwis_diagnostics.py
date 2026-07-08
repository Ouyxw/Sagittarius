"""
MWIS-specific diagnostic visualization utilities.

Provides specialized diagnostic plots for Maximum Weight Independent Set (MWIS)
problem solving via Adiabatic Quantum Computing (AQC).

All functions are backend-free and operate on pure Python/NumPy data structures.
Charts include "DIAGNOSTIC VIEW" disclaimers and are NOT for hardware calibration.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional, List, Dict, Any, Tuple
import warnings


def plot_mwis_convergence(
    result,
    optimal_weight: Optional[float] = None,
    ax: Optional[Axes] = None,
    show_constraint_violations: bool = True,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 6),
) -> Axes:
    """
    Plot MWIS optimization convergence diagnostics.
    
    Visualizes the evolution of solution quality during AQC annealing,
    including weight progression and constraint violations over time.
    
    Args:
        result: SimulationResult object with MWIS observable data
        optimal_weight: Known optimal weight for approximation ratio calculation
        ax: Matplotlib axes. Creates new if None.
        show_constraint_violations: If True, plot constraint violation count
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If required MWIS observables not found in result
        
    Example:
        >>> result = sim_aqc.run()
        >>> ax = plot_mwis_convergence(result, optimal_weight=14.5)
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
    
    # Look for MWIS-specific observables
    weight_col = None
    violation_col = None
    
    for col in df.columns:
        if col.lower() in ['weight', 'solution_weight', 'objective']:
            weight_col = col
        elif col.lower() in ['violations', 'constraint_violations', 'n_conflicts']:
            violation_col = col
    
    if weight_col is None:
        raise ValueError(
            "No weight observable found in result. "
            f"Available columns: {list(df.columns)}. "
            "Expected columns like 'weight', 'solution_weight', or 'objective'."
        )
    
    weight_vals = df[weight_col].values
    
    # Main plot: Weight evolution
    ax.plot(time_vals, weight_vals, 'b-', linewidth=2.5, 
           label=f'Solution weight ({weight_col})', zorder=5)
    
    # Show optimal weight if provided
    if optimal_weight is not None:
        ax.axhline(y=optimal_weight, color='green', linestyle='--', 
                  linewidth=2, label=f'Optimal weight: {optimal_weight:.2f}', zorder=3)
        
        # Calculate and display approximation ratio
        final_weight = weight_vals[-1]
        approx_ratio = final_weight / optimal_weight if optimal_weight > 0 else 0
        ax.text(0.02, 0.95, f"Approx ratio: {approx_ratio:.3f}",
               transform=ax.transAxes, fontsize=9, fontweight='bold',
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
    
    # Secondary y-axis: Constraint violations
    if show_constraint_violations and violation_col is not None:
        ax_violations = ax.twinx()
        violation_vals = df[violation_col].values
        ax_violations.plot(time_vals, violation_vals, 'r-', linewidth=2,
                          label=f'Violations ({violation_col})', zorder=4)
        ax_violations.set_ylabel("Constraint Violations", color='red', fontsize=11)
        ax_violations.tick_params(axis='y', labelcolor='red')
        ax_violations.legend(loc='upper right', fontsize=8)
        
        # Mark feasibility transition
        feasible_idx = np.where(violation_vals == 0)[0]
        if len(feasible_idx) > 0:
            t_feasible = time_vals[feasible_idx[0]]
            ax_violations.axvline(x=t_feasible, color='green', linestyle=':',
                                 linewidth=1.5, alpha=0.6, label='Becomes feasible')
    
    # Formatting
    ax.set_xlabel("Time (μs)", fontsize=11)
    ax.set_ylabel("Solution Weight", fontsize=11)
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        final_weight = weight_vals[-1]
        title_text = f"MWIS Convergence Diagnostics\n"
        title_text += f"Final weight: {final_weight:.2f}"
        if optimal_weight is not None:
            title_text += f" (optimal: {optimal_weight:.2f})"
        ax.set_title(title_text, fontsize=11, fontweight='bold')
    
    ax.legend(fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.4)
    
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
    
    return ax


def plot_mwis_feasibility_diagram(
    register,
    bitstring: str,
    edges: List[Tuple[int, int]],
    blockade_radius: float,
    ax: Optional[Axes] = None,
    show_distance_matrix: bool = True,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 10),
) -> Axes:
    """
    Plot MWIS feasibility diagnostic diagram.
    
    Visualizes constraint satisfaction through distance matrix heatmap,
    highlighting violated blockade constraints.
    
    Args:
        register: Register object with atom positions
        bitstring: Binary string representing the solution
        edges: List of graph edges (i, j) tuples
        blockade_radius: Blockade radius for constraint checking
        ax: Matplotlib axes. Creates new if None.
        show_distance_matrix: If True, show pairwise distance heatmap
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If bitstring length doesn't match atom count
        
    Example:
        >>> reg = Register.chain(5, spacing=4.0)
        >>> edges = [(0,1), (1,2), (2,3), (3,4)]
        >>> ax = plot_mwis_feasibility_diagram(reg, "10101", edges, R=5.0)
    """
    if ax is None:
        fig, ax = plt.subplots(2, 1, figsize=figsize, 
                              gridspec_kw={'height_ratios': [2, 1]})
        ax_spatial, ax_heatmap = ax
    else:
        # If single ax provided, create figure with two panels
        fig = ax.get_figure()
        warnings.warn(
            "Single Axes provided. Creating new figure with two panels.",
            UserWarning
        )
        fig, (ax_spatial, ax_heatmap) = plt.subplots(2, 1, figsize=figsize,
                                                     gridspec_kw={'height_ratios': [2, 1]})
    
    n_atoms = len(register.atoms)
    
    # Validate bitstring
    if len(bitstring) != n_atoms:
        raise ValueError(
            f"Bitstring length ({len(bitstring)}) does not match number of atoms ({n_atoms})."
        )
    
    if not all(c in '01' for c in bitstring):
        raise ValueError("Bitstring must contain only '0' and '1' characters.")
    
    # Extract positions
    positions = np.array([atom.position for atom in register.atoms])
    
    # Panel 1: Spatial layout with conflicts
    selected = [i for i, b in enumerate(bitstring) if b == '1']
    ground = [i for i, b in enumerate(bitstring) if b == '0']
    
    # Plot atoms
    if ground:
        pos_ground = positions[ground]
        ax_spatial.scatter(pos_ground[:, 0], pos_ground[:, 1], 
                          s=200, c='#4682B4', edgecolors='black', 
                          linewidth=1.5, label='Ground state (0)', zorder=5)
    
    if selected:
        pos_selected = positions[selected]
        ax_spatial.scatter(pos_selected[:, 0], pos_selected[:, 1], 
                          s=200, c='#FF8C00', edgecolors='black', 
                          linewidth=1.5, label='Rydberg state (1)', zorder=5)
    
    # Plot edges
    for i, j in edges:
        pos_i, pos_j = positions[i], positions[j]
        # Check if this edge is violated (both endpoints selected)
        is_violated = (bitstring[i] == '1' and bitstring[j] == '1')
        
        if is_violated:
            ax_spatial.plot([pos_i[0], pos_j[0]], [pos_i[1], pos_j[1]], 
                          'r--', linewidth=2.5, alpha=0.8, zorder=3)
            # Mark conflict
            mid_x, mid_y = (pos_i[0] + pos_j[0]) / 2, (pos_i[1] + pos_j[1]) / 2
            ax_spatial.plot(mid_x, mid_y, 'X', markersize=12, 
                          markeredgewidth=2.5, color='red', zorder=6)
        else:
            ax_spatial.plot([pos_i[0], pos_j[0]], [pos_i[1], pos_j[1]], 
                          'gray', linewidth=1, alpha=0.4, zorder=1)
    
    # Draw blockade circles around selected atoms
    for idx in selected:
        circle = plt.Circle(positions[idx], blockade_radius, 
                           fill=False, edgecolor='orange', 
                           linestyle=':', linewidth=1, alpha=0.5, zorder=2)
        ax_spatial.add_patch(circle)
    
    # Count violations
    n_violations = sum(1 for i, j in edges 
                      if bitstring[i] == '1' and bitstring[j] == '1')
    
    ax_spatial.set_xlabel("x (μm)", fontsize=11)
    ax_spatial.set_ylabel("y (μm)", fontsize=11)
    ax_spatial.set_aspect('equal')
    ax_spatial.legend(fontsize=9, loc='upper left')
    ax_spatial.grid(True, linestyle=':', alpha=0.3)
    
    if title:
        ax_spatial.set_title(title, fontsize=12, fontweight='bold')
    else:
        status = "✓ Feasible" if n_violations == 0 else f"✗ {n_violations} violations"
        status_color = 'green' if n_violations == 0 else 'red'
        ax_spatial.set_title(
            f"MWIS Feasibility Diagram\n"
            f"Selected: {len(selected)}/{n_atoms} atoms | {status}",
            fontsize=11, fontweight='bold', color=status_color
        )
    
    # Panel 2: Distance matrix heatmap
    if show_distance_matrix:
        # Compute pairwise distances
        n = len(positions)
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                dist = np.linalg.norm(positions[i] - positions[j])
                dist_matrix[i, j] = dist
                dist_matrix[j, i] = dist
        
        # Create mask for edges that exist
        edge_mask = np.zeros((n, n), dtype=bool)
        for i, j in edges:
            edge_mask[i, j] = True
            edge_mask[j, i] = True
        
        # Highlight violations in heatmap
        im = ax_heatmap.imshow(dist_matrix, cmap='YlOrRd', aspect='auto')
        
        # Overlay blockade radius threshold
        contour_lines = ax_heatmap.contour(dist_matrix, levels=[blockade_radius], 
                                          colors='blue', linewidths=2, linestyles='--')
        
        # Add legend for blockade radius (using manual text annotation instead of label)
        ax_heatmap.text(0.02, 0.98, f"Blockade radius: {blockade_radius:.1f} μm",
                       transform=ax_heatmap.transAxes, fontsize=8,
                       verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
        
        # Mark violated edges
        for i, j in edges:
            if bitstring[i] == '1' and bitstring[j] == '1':
                ax_heatmap.plot(j, i, 'X', markersize=10, 
                              markeredgewidth=2, color='red', zorder=5)
        
        ax_heatmap.set_xlabel("Atom index", fontsize=10)
        ax_heatmap.set_ylabel("Atom index", fontsize=10)
        ax_heatmap.set_title("Pairwise Distance Matrix", fontsize=11, fontweight='bold')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax_heatmap, fraction=0.02, pad=0.02)
        cbar.set_label("Distance (μm)", fontsize=9)
        
        # Add legend for blockade radius
        ax_heatmap.text(0.02, 0.98, f"Blockade radius: {blockade_radius:.1f} μm",
                       transform=ax_heatmap.transAxes, fontsize=8,
                       verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    # Add artifact link if available
    disclaimer_y_pos = 0.01
    if hasattr(register, 'manifest') and getattr(register, 'manifest', None):
        artifact_id = register.manifest.get('artifact_id')
        if artifact_id:
            fig.text(0.5, disclaimer_y_pos + 0.02, f"Artifact: {artifact_id}",
                    ha='center', fontsize=6, style='italic', color='darkblue',
                    transform=fig.transFigure,
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
            disclaimer_y_pos += 0.02
    
    # Add disclaimer
    fig.text(0.5, disclaimer_y_pos, "DIAGNOSTIC VIEW - Not for hardware calibration",
            ha='center', fontsize=7, style='italic', color='gray',
            transform=fig.transFigure)
    
    plt.tight_layout(rect=[0, 0.02, 1, 1])
    return ax


__all__ = [
    "plot_mwis_convergence",
    "plot_mwis_feasibility_diagram",
]
