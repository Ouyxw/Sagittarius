"""
Geometry diagnostics for Rydberg atom registers.

Backend-free tools to validate geometric parameters, units, and blockade radius
configuration before running expensive quantum simulations.

Provides:
- Distance matrix extraction
- Van der Waals interaction matrix (V_ij = C6/r^6)
- Blockade adjacency matrix (binary connectivity)
- Unit disk graph visualization with blockade overlays

DIAGNOSTIC TOOLS: For pre-simulation validation only.
Not for hardware calibration or performance claims.
"""

from typing import Optional, List, Tuple, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from .register import _extract_positions


def extract_geometry_diagnostics(
    register,
    blockade_radius: Optional[float] = None,
    C6: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Extract geometric diagnostics from a register configuration.
    
    Computes distance matrix, optional van der Waals interaction matrix,
    and blockade adjacency structure for pre-simulation validation.
    
    Args:
        register: Register object with atom positions
        blockade_radius: Blockade radius (μm) for adjacency computation
        C6: Van der Waals coefficient for interaction strength calculation
    
    Returns:
        Dictionary containing:
        - n_atoms: Number of atoms
        - positions: Nx2 array of atom coordinates (x, y)
        - distance_matrix: NxN symmetric distance matrix (μm)
        - vdw_matrix: NxN VDW interaction matrix (if C6 provided), V_ij = C6/r^6
        - adjacency_matrix: NxN binary adjacency matrix (if R_b provided)
        - edges: List of (i, j) tuples representing blockade constraints
        - graph_density: Edge density = |E| / (N*(N-1)/2)
        - min_distance: Minimum inter-atom distance
        - max_distance: Maximum inter-atom distance
        - mean_distance: Mean inter-atom distance (excluding diagonal)
    """
    # Extract positions
    pos_array = _extract_positions(register)
    n_atoms = len(pos_array)
    
    if n_atoms == 0:
        raise ValueError("Register contains no atoms")
    
    # Compute pairwise distance matrix
    diff = pos_array[:, np.newaxis, :] - pos_array[np.newaxis, :, :]
    distance_matrix = np.sqrt(np.sum(diff**2, axis=2))
    
    # Initialize result dict
    diagnostics = {
        'n_atoms': n_atoms,
        'positions': pos_array.copy(),
        'distance_matrix': distance_matrix.copy(),
        'vdw_matrix': None,
        'adjacency_matrix': None,
        'edges': [],
        'graph_density': 0.0,
        'min_distance': 0.0,
        'max_distance': 0.0,
        'mean_distance': 0.0,
    }
    
    # Compute statistics (excluding diagonal)
    off_diag_mask = ~np.eye(n_atoms, dtype=bool)
    off_diag_distances = distance_matrix[off_diag_mask]
    
    if len(off_diag_distances) > 0:
        diagnostics['min_distance'] = float(np.min(off_diag_distances))
        diagnostics['max_distance'] = float(np.max(off_diag_distances))
        diagnostics['mean_distance'] = float(np.mean(off_diag_distances))
    
    # Compute van der Waals interaction matrix if C6 provided
    if C6 is not None:
        if C6 <= 0:
            raise ValueError(f"C6 coefficient must be positive, got {C6}")
        
        # V_ij = C6 / r^6, with diagonal set to 0
        vdw_matrix = np.zeros_like(distance_matrix)
        nonzero_dist = distance_matrix > 0
        vdw_matrix[nonzero_dist] = C6 / (distance_matrix[nonzero_dist]**6)
        np.fill_diagonal(vdw_matrix, 0.0)
        
        diagnostics['vdw_matrix'] = vdw_matrix
    
    # Compute blockade adjacency matrix if R_b provided
    if blockade_radius is not None:
        if blockade_radius <= 0:
            raise ValueError(f"Blockade radius must be positive, got {blockade_radius}")
        
        # Adjacency: 1 if distance < R_b (excluding self)
        adjacency_matrix = (distance_matrix < blockade_radius).astype(int)
        np.fill_diagonal(adjacency_matrix, 0)
        
        diagnostics['adjacency_matrix'] = adjacency_matrix
        
        # Extract edge list (upper triangle to avoid duplicates)
        edges = []
        for i in range(n_atoms):
            for j in range(i+1, n_atoms):
                if adjacency_matrix[i, j] == 1:
                    edges.append((i, j))
        
        diagnostics['edges'] = edges
        
        # Compute graph density
        max_edges = n_atoms * (n_atoms - 1) / 2
        if max_edges > 0:
            diagnostics['graph_density'] = len(edges) / max_edges
    
    return diagnostics


def _annotate_heatmap(ax, matrix, fmt='.2f', fontsize=8, threshold=None):
    """
    Helper function to annotate heatmap cells with numerical values.
    
    Args:
        ax: Matplotlib axes
        matrix: 2D numpy array
        fmt: Format string for values
        fontsize: Font size for annotations
        threshold: If provided, only annotate values above this threshold
    """
    rows, cols = matrix.shape
    
    for i in range(rows):
        for j in range(cols):
            value = matrix[i, j]
            
            # Skip if below threshold
            if threshold is not None and value < threshold:
                continue
            
            # Determine text color based on normalized value
            vmin, vmax = np.min(matrix), np.max(matrix)
            if vmax > vmin:
                norm_value = (value - vmin) / (vmax - vmin)
            else:
                norm_value = 0.5
            
            text_color = 'white' if norm_value < 0.5 else 'black'
            
            # Format the value
            if isinstance(value, (int, np.integer)):
                text = str(value)
            else:
                text = f'{value:{fmt}}'
            
            ax.text(j, i, text,
                   ha='center', va='center',
                   fontsize=fontsize, color=text_color, weight='bold')


def plot_geometry_diagnostics(
    register,
    blockade_radius: Optional[float] = None,
    C6: Optional[float] = None,
    show_distances: bool = False,
    show_vdw_matrix: bool = True,
    show_adjacency: bool = True,
    figsize: Tuple[float, float] = (16, 12),
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> List[Axes]:
    """
    Create comprehensive geometry diagnostic visualization.
    
    Generates multi-panel figure showing:
    1. Register layout with blockade disks and edges
    2. Distance matrix heatmap (with numerical annotations)
    3. VDW interaction matrix heatmap (if C6 provided, with annotations)
    4. Adjacency matrix heatmap (if R_b provided, with annotations)
    
    Args:
        register: Register object
        blockade_radius: Blockade radius (μm)
        C6: Van der Waals coefficient
        show_distances: Annotate distances on register layout
        show_vdw_matrix: Display VDW matrix panel
        show_adjacency: Display adjacency matrix panel
        figsize: Figure size (width, height)
        ax: External axes (unused, kept for API consistency)
        title: Custom title
        save_path: Save figure to file path
    
    Returns:
        List of Axes objects for each panel
    """
    # Extract diagnostics
    diag = extract_geometry_diagnostics(register, blockade_radius, C6)
    n_atoms = diag['n_atoms']
    distance_matrix = diag['distance_matrix']
    
    # Determine number of panels
    n_panels = 2  # Always: register layout + distance matrix
    if C6 is not None and show_vdw_matrix:
        n_panels += 1
    if blockade_radius is not None and show_adjacency:
        n_panels += 1
    
    # Create figure
    fig, axes = plt.subplots(1, n_panels, figsize=figsize)
    if n_panels == 1:
        axes = [axes]
    
    panel_idx = 0
    
    # ===== Panel 1: Register Layout with Blockade Disks =====
    ax_register = axes[panel_idx]
    positions = diag['positions']
    x, y = positions[:, 0], positions[:, 1]
    
    # Plot atoms
    ax_register.scatter(x, y, s=150, c='steelblue', edgecolors='black', 
                       linewidths=1.5, zorder=5)
    
    # Plot blockade disks if R_b provided
    if blockade_radius is not None:
        from matplotlib.patches import Circle
        for i in range(n_atoms):
            circle = Circle((x[i], y[i]), blockade_radius, 
                          alpha=0.1, facecolor='red', edgecolor='red',
                          linestyle='--', linewidth=1, zorder=0)
            ax_register.add_patch(circle)
        
        # Plot blockade edges
        for i, j in diag['edges']:
            ax_register.plot([x[i], x[j]], [y[i], y[j]], 
                           'r--', linewidth=1.5, alpha=0.7, zorder=1)
    
    # Plot atom labels (offset to upper-right to avoid covering atoms)
    for i in range(n_atoms):
        offset = 0.15  # μm offset
        ax_register.text(x[i] + offset, y[i] + offset, str(i), 
                        fontsize=9, ha='center', va='center',
                        color='white', weight='bold',
                        bbox=dict(boxstyle='round,pad=0.2', 
                                 facecolor='black', alpha=0.7),
                        zorder=10)
    
    # Annotate distances if requested
    if show_distances and n_atoms <= 8:
        for i in range(n_atoms):
            for j in range(i+1, n_atoms):
                mid_x, mid_y = (x[i] + x[j]) / 2, (y[i] + y[j]) / 2
                dist = distance_matrix[i, j]
                ax_register.text(mid_x, mid_y, f'{dist:.2f}',
                               fontsize=7, ha='center', va='center',
                               color='darkgreen', weight='bold',
                               bbox=dict(boxstyle='round,pad=0.15',
                                        facecolor='lightyellow', alpha=0.8),
                               zorder=11)
    
    ax_register.set_aspect('equal', adjustable='datalim')
    ax_register.set_xlabel('X (μm)', fontsize=10)
    ax_register.set_ylabel('Y (μm)', fontsize=10)
    
    reg_title = f"Register Layout (N={n_atoms})"
    if blockade_radius is not None:
        reg_title += f"\nR_b = {blockade_radius} μm"
    ax_register.set_title(reg_title, fontsize=11, fontweight='bold')
    ax_register.grid(True, alpha=0.3, linestyle=':')
    
    panel_idx += 1
    
    # ===== Panel 2: Distance Matrix Heatmap (WITH NUMERICAL ANNOTATIONS) =====
    ax_dist = axes[panel_idx]
    im_dist = ax_dist.imshow(distance_matrix, cmap='viridis', aspect='auto')
    ax_dist.set_xlabel('Atom Index', fontsize=10)
    ax_dist.set_ylabel('Atom Index', fontsize=10)
    ax_dist.set_title(f"Distance Matrix (μm)\nMin: {diag['min_distance']:.2f}, Max: {diag['max_distance']:.2f}",
                     fontsize=11, fontweight='bold')
    
    # Add colorbar
    cbar_dist = plt.colorbar(im_dist, ax=ax_dist, fraction=0.046, pad=0.04)
    cbar_dist.set_label('Distance (μm)', fontsize=9)
    
    # Add grid
    ax_dist.set_xticks(range(n_atoms))
    ax_dist.set_yticks(range(n_atoms))
    ax_dist.grid(False)
    
    # Annotate all distance values
    _annotate_heatmap(ax_dist, distance_matrix, fmt='.2f', fontsize=8)
    
    panel_idx += 1
    
    # ===== Panel 3: VDW Interaction Matrix (WITH NUMERICAL ANNOTATIONS) =====
    if C6 is not None and show_vdw_matrix and diag['vdw_matrix'] is not None:
        ax_vdw = axes[panel_idx]
        vdw_matrix = diag['vdw_matrix']
        
        # Use log scale for better visualization
        vdw_log = np.log1p(vdw_matrix)
        
        im_vdw = ax_vdw.imshow(vdw_log, cmap='hot', aspect='auto')
        ax_vdw.set_xlabel('Atom Index', fontsize=10)
        ax_vdw.set_ylabel('Atom Index', fontsize=10)
        ax_vdw.set_title(f"VDW Interaction Matrix\nV_ij = C6/r^6 (log scale)",
                        fontsize=11, fontweight='bold')
        
        cbar_vdw = plt.colorbar(im_vdw, ax=ax_vdw, fraction=0.046, pad=0.04)
        cbar_vdw.set_label('log(1 + V_ij)', fontsize=9)
        
        ax_vdw.set_xticks(range(n_atoms))
        ax_vdw.set_yticks(range(n_atoms))
        ax_vdw.grid(False)
        
        # Annotate VDW values (use original values, not log)
        _annotate_heatmap(ax_vdw, vdw_matrix, fmt='.2e', fontsize=7)
        
        panel_idx += 1
    
    # ===== Panel 4: Adjacency Matrix (WITH NUMERICAL ANNOTATIONS) =====
    if blockade_radius is not None and show_adjacency and diag['adjacency_matrix'] is not None:
        ax_adj = axes[panel_idx]
        adj_matrix = diag['adjacency_matrix']
        
        im_adj = ax_adj.imshow(adj_matrix, cmap='Reds', aspect='auto', vmin=0, vmax=1)
        ax_adj.set_xlabel('Atom Index', fontsize=10)
        ax_adj.set_ylabel('Atom Index', fontsize=10)
        
        adj_title = f"Blockade Adjacency Matrix\nDensity: {diag['graph_density']:.2%}"
        if len(diag['edges']) > 0:
            adj_title += f" ({len(diag['edges'])} edges)"
        ax_adj.set_title(adj_title, fontsize=11, fontweight='bold')
        
        cbar_adj = plt.colorbar(im_adj, ax=ax_adj, fraction=0.046, pad=0.04)
        cbar_adj.set_label('Connected', fontsize=9)
        cbar_adj.set_ticks([0, 1])
        cbar_adj.set_ticklabels(['No', 'Yes'])
        
        ax_adj.set_xticks(range(n_atoms))
        ax_adj.set_yticks(range(n_atoms))
        ax_adj.grid(False)
        
        # Annotate adjacency values (only non-zero)
        _annotate_heatmap(ax_adj, adj_matrix, fmt='d', fontsize=9, threshold=0.5)
        
        panel_idx += 1
    
    # Add overall title with diagnostic warning
    if title is None:
        title = "GEOMETRY DIAGNOSTICS — Pre-Simulation Validation"
    
    fig.suptitle(title + "\n⚠️ FOR PARAMETER VALIDATION ONLY — Not for calibration",
                fontsize=13, fontweight='bold', y=0.98)
    
    # Adjust layout
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save if requested
    if save_path is not None:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Geometry diagnostics saved to: {save_path}")
    
    return axes


def plot_unit_disk_graph(
    register,
    blockade_radius: float,
    ax: Optional[Axes] = None,
    figsize: Tuple[float, float] = (10, 10),
    show_labels: bool = True,
    show_distances: bool = False,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Axes:
    """
    Simplified unit disk graph visualization.
    
    Shows register layout with blockade disks and constraint edges only.
    Useful for quick visual inspection of blockade structure.
    
    Args:
        register: Register object
        blockade_radius: Blockade radius (μm)
        ax: External axes
        figsize: Figure size
        show_labels: Show atom indices
        show_distances: Annotate edge distances
        title: Custom title
    
    Returns:
        Axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Extract diagnostics
    diag = extract_geometry_diagnostics(register, blockade_radius=blockade_radius)
    positions = diag['positions']
    x, y = positions[:, 0], positions[:, 1]
    
    # Plot blockade disks
    from matplotlib.patches import Circle
    for i in range(diag['n_atoms']):
        circle = Circle((x[i], y[i]), blockade_radius,
                       alpha=0.15, facecolor='orange', edgecolor='red',
                       linestyle='--', linewidth=1.5, zorder=0)
        ax.add_patch(circle)
    
    # Plot atoms
    ax.scatter(x, y, s=200, c='steelblue', edgecolors='black',
              linewidths=2, zorder=5)
    
    # Plot blockade edges
    for i, j in diag['edges']:
        ax.plot([x[i], x[j]], [y[i], y[j]],
               'r--', linewidth=2, alpha=0.8, zorder=1)
        
        # Annotate distance if requested
        if show_distances:
            mid_x = (x[i] + x[j]) / 2
            mid_y = (y[i] + y[j]) / 2
            dist = diag['distance_matrix'][i, j]
            ax.text(mid_x, mid_y, f'{dist:.2f}',
                   fontsize=8, ha='center', va='center',
                   color='darkred', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.2',
                            facecolor='white', alpha=0.9),
                   zorder=11)
    
    # Plot labels
    if show_labels:
        for i in range(diag['n_atoms']):
            ax.text(x[i], y[i], str(i),
                   fontsize=11, ha='center', va='center',
                   color='white', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.3',
                            facecolor='black', alpha=0.8),
                   zorder=10)
    
    ax.set_aspect('equal', adjustable='datalim')
    ax.set_xlabel('X (μm)', fontsize=12)
    ax.set_ylabel('Y (μm)', fontsize=12)
    
    if title is None:
        title = f"Unit Disk Graph (R_b = {blockade_radius} μm)\n{diag['n_atoms']} atoms, {len(diag['edges'])} edges"
    ax.set_title(title, fontsize=13, fontweight='bold')
    
    ax.grid(True, alpha=0.3, linestyle=':')
    
    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='steelblue',
              markersize=10, label='Atoms'),
        Line2D([0], [0], linestyle='--', color='red', linewidth=2,
              label=f'Blockade edges (R_b={blockade_radius}μm)'),
    ]
    ax.legend(handles=legend_elements, loc='best', fontsize=9)
    
    if save_path is not None:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Unit disk graph saved to: {save_path}")
    
    return ax
