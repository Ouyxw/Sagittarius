"""
Correlation analysis visualization for quantum simulation results.

Backend-free tools to visualize pair correlations, connected correlations,
Pauli-ZZ correlations, and blockade conflict matrices from simulation results.

Provides:
- Pair correlation matrix heatmap
- Connected correlation matrix (C_ij = <n_i n_j> - <n_i><n_j>)
- Pauli-ZZ correlation matrix
- Blockade conflict matrix/edge heatmap

DIAGNOSTIC TOOLS: For data exploration only.
Not for hardware calibration or performance claims.
"""

from typing import Optional, List, Tuple, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import LogNorm


def _extract_atom_pairs_from_columns(columns: List[str], prefix: str) -> List[Tuple[int, int]]:
    """Extract atom pairs from column names with given prefix."""
    pairs = []
    for col in columns:
        if col.startswith(prefix):
            parts = col.split('_')
            if len(parts) >= 4:
                try:
                    i, j = int(parts[-2]), int(parts[-1])
                    pairs.append((i, j))
                except ValueError:
                    continue
    return pairs


def _build_correlation_matrix(
    result_data: Dict[str, List[float]],
    n_atoms: int,
    column_prefix: str,
    default_value: float = 0.0,
) -> np.ndarray:
    """Build NxN correlation matrix from result data columns."""
    matrix = np.full((n_atoms, n_atoms), default_value)
    
    # Extract pairs from column names
    pairs = _extract_atom_pairs_from_columns(list(result_data.keys()), column_prefix)
    
    for i, j in pairs:
        if 0 <= i < n_atoms and 0 <= j < n_atoms:
            col_name = f"{column_prefix}{i}_{j}"
            if col_name in result_data:
                values = result_data[col_name]
                # Use final time point value
                matrix[i, j] = values[-1] if values else default_value
                matrix[j, i] = matrix[i, j]  # Symmetric
    
    return matrix


def _annotate_correlation_heatmap(
    ax: Axes,
    matrix: np.ndarray,
    fmt: str = '.2f',
    fontsize: int = 7,
    threshold: Optional[float] = None,
) -> None:
    """Annotate correlation heatmap cells with numerical values."""
    n_rows, n_cols = matrix.shape
    
    for i in range(n_rows):
        for j in range(n_cols):
            value = matrix[i, j]
            
            # Apply threshold filter if specified
            if threshold is not None and abs(value) < threshold:
                continue
            
            # Calculate cell center (integer indices for imshow)
            x_center = j
            y_center = i
            
            # Choose text color based on background brightness
            norm_value = (value - np.min(matrix)) / (np.max(matrix) - np.min(matrix) + 1e-10)
            text_color = 'white' if norm_value < 0.5 else 'black'
            
            ax.text(x_center, y_center, f'{value:{fmt}}',
                   ha='center', va='center',
                   fontsize=fontsize, color=text_color, weight='bold')


def _validate_result_has_observables(
    result,
    required_prefix: str,
    observable_type: str,
) -> None:
    """Validate that result contains required observables."""
    df = result.to_pandas()
    columns = df.columns.tolist()
    
    # Check for matching columns
    matching_cols = [col for col in columns if col.startswith(required_prefix)]
    
    if not matching_cols:
        available = ', '.join([c for c in columns if c != 't'][:5])
        raise ValueError(
            f"No {observable_type} observables found in result.\n"
            f"Available columns: [{available}].\n"
            f"To enable {observable_type} plots, include {observable_type} in simulation observables.\n"
            f"Example:\n"
            f"    observables = {{\n"
            f'        "{required_prefix}0_1": {observable_type}(atom_i=0, atom_j=1, N_atoms=N),\n'
            f'        "{required_prefix}1_2": {observable_type}(atom_i=1, atom_j=2, N_atoms=N),\n'
            f"    }}"
        )


def plot_pair_correlation_matrix(
    result,
    register=None,
    ax: Optional[Axes] = None,
    figsize: Tuple[float, float] = (8, 8),
    cmap: str = 'viridis',
    show_values: bool = True,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Axes:
    """
    Plot pair correlation matrix heatmap.
    
    Visualizes <n_i n_j> for all atom pairs, showing spatial correlation patterns.
    
    Args:
        result: SimulationResult with pair-correlation observables
        register: Optional Register object for atom positions
        ax: External axes
        figsize: Figure size
        cmap: Colormap name
        show_values: Annotate cells with numerical values
        title: Custom title
        save_path: Save figure path
    
    Returns:
        Axes object
    
    Raises:
        ValueError: If result lacks pair-correlation observables
    
    Example:
        >>> from sagittarius.viz import plot_pair_correlation_matrix
        >>> ax = plot_pair_correlation_matrix(result)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Validate observables
    _validate_result_has_observables(result, 'pair_corr_', 'PairCorrelation')
    
    # Extract data
    df = result.to_pandas()
    n_atoms = result.metadata.get('register', {}).get('atom_count', 0)
    
    if n_atoms == 0:
        raise ValueError("Cannot determine atom count from result metadata.")
    
    # Build correlation matrix
    matrix = _build_correlation_matrix(result.data, n_atoms, 'pair_corr_', default_value=0.0)
    
    # Fill diagonal with single-atom populations if available
    pop_cols = [col for col in df.columns if col.startswith('pop')]
    if pop_cols:
        for i in range(n_atoms):
            pop_col = f'pop{i}'
            if pop_col in df.columns:
                matrix[i, i] = df[pop_col].iloc[-1]
    
    # Plot heatmap
    im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=0, vmax=1)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Pair Correlation <nᵢnⱼ>', fontsize=9)
    
    # Configure axes
    ax.set_xlabel('Atom Index', fontsize=10)
    ax.set_ylabel('Atom Index', fontsize=10)
    ax.set_xticks(range(n_atoms))
    ax.set_yticks(range(n_atoms))
    ax.grid(False)
    
    # Annotate values
    if show_values:
        _annotate_correlation_heatmap(ax, matrix, fmt='.2f', fontsize=7)
    
    # Title
    if title is None:
        n_pairs = sum(1 for i in range(n_atoms) for j in range(i+1, n_atoms) if matrix[i, j] > 0)
        title = f"Pair Correlation Matrix ({n_pairs} pairs)"
    ax.set_title(title, fontsize=11, fontweight='bold')
    
    # Add artifact ID if available
    manifest = getattr(result, 'manifest', {})
    if isinstance(manifest, dict) and 'artifact_id' in manifest:
        ax.set_title(f"{title}\nArtifact: {manifest['artifact_id']}", fontsize=10)
    
    # Save
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Pair correlation matrix saved to: {save_path}")
    
    return ax


def plot_connected_correlation_matrix(
    result,
    register=None,
    ax: Optional[Axes] = None,
    figsize: Tuple[float, float] = (8, 8),
    cmap: str = 'coolwarm',
    show_values: bool = True,
    significance_threshold: float = 0.1,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Axes:
    """
    Plot connected correlation matrix C_ij = <n_i n_j> - <n_i><n_j>.
    
    Shows genuine correlations beyond product of individual populations.
    
    Args:
        result: SimulationResult with connected-correlation observables
        register: Optional Register object
        ax: External axes
        figsize: Figure size
        cmap: Diverging colormap (default: coolwarm)
        show_values: Annotate significant cells
        significance_threshold: Minimum |C_ij| to annotate
        title: Custom title
        save_path: Save figure path
    
    Returns:
        Axes object
    
    Raises:
        ValueError: If result lacks connected-correlation observables
    
    Example:
        >>> from sagittarius.viz import plot_connected_correlation_matrix
        >>> ax = plot_connected_correlation_matrix(result, significance_threshold=0.05)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Validate observables
    _validate_result_has_observables(result, 'connected_corr_', 'ConnectedPairCorrelation')
    
    # Extract data
    n_atoms = result.metadata.get('register', {}).get('atom_count', 0)
    
    if n_atoms == 0:
        raise ValueError("Cannot determine atom count from result metadata.")
    
    # Build correlation matrix
    matrix = _build_correlation_matrix(result.data, n_atoms, 'connected_corr_', default_value=0.0)
    
    # Determine symmetric color range
    max_abs = np.max(np.abs(matrix))
    vmin, vmax = -max_abs, max_abs
    
    # Plot heatmap
    im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=vmin, vmax=vmax)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Connected Correlation Cᵢⱼ', fontsize=9)
    
    # Configure axes
    ax.set_xlabel('Atom Index', fontsize=10)
    ax.set_ylabel('Atom Index', fontsize=10)
    ax.set_xticks(range(n_atoms))
    ax.set_yticks(range(n_atoms))
    ax.grid(False)
    
    # Annotate significant values
    if show_values:
        _annotate_correlation_heatmap(
            ax, matrix, fmt='.2f', fontsize=7,
            threshold=significance_threshold
        )
    
    # Title
    if title is None:
        n_significant = np.sum(np.abs(matrix) > significance_threshold) // 2  # Divide by 2 for symmetry
        title = f"Connected Correlation Matrix ({n_significant} significant)"
    ax.set_title(title, fontsize=11, fontweight='bold')
    
    # Add zero line indicator
    ax.axhline(y=-0.5, color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
    
    # Save
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Connected correlation matrix saved to: {save_path}")
    
    return ax


def plot_pauli_zz_matrix(
    result,
    register=None,
    ax: Optional[Axes] = None,
    figsize: Tuple[float, float] = (8, 8),
    cmap: str = 'RdBu_r',
    show_values: bool = True,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Axes:
    """
    Plot Pauli-ZZ correlation matrix <ZZ>_ij.
    
    Measures spin-spin correlations in computational basis.
    
    Args:
        result: SimulationResult with Pauli-ZZ observables
        register: Optional Register object
        ax: External axes
        figsize: Figure size
        cmap: Diverging colormap (default: RdBu_r)
        show_values: Annotate cells
        title: Custom title
        save_path: Save figure path
    
    Returns:
        Axes object
    
    Raises:
        ValueError: If result lacks Pauli-ZZ observables
    
    Example:
        >>> from sagittarius.viz import plot_pauli_zz_matrix
        >>> ax = plot_pauli_zz_matrix(result)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Validate observables
    _validate_result_has_observables(result, 'pauli_zz_', 'PauliZZ')
    
    # Extract data
    n_atoms = result.metadata.get('register', {}).get('atom_count', 0)
    
    if n_atoms == 0:
        raise ValueError("Cannot determine atom count from result metadata.")
    
    # Build ZZ correlation matrix
    matrix = _build_correlation_matrix(result.data, n_atoms, 'pauli_zz_', default_value=0.0)
    
    # Set diagonal to +1 (self-correlation)
    np.fill_diagonal(matrix, 1.0)
    
    # Plot heatmap
    im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=-1, vmax=1)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Pauli-ZZ Correlation <ZZ>ᵢⱼ', fontsize=9)
    
    # Configure axes
    ax.set_xlabel('Atom Index', fontsize=10)
    ax.set_ylabel('Atom Index', fontsize=10)
    ax.set_xticks(range(n_atoms))
    ax.set_yticks(range(n_atoms))
    ax.grid(False)
    
    # Annotate values
    if show_values:
        _annotate_correlation_heatmap(ax, matrix, fmt='.2f', fontsize=7)
    
    # Title
    if title is None:
        title = "Pauli-ZZ Correlation Matrix"
    ax.set_title(title, fontsize=11, fontweight='bold')
    
    # Save
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Pauli-ZZ matrix saved to: {save_path}")
    
    return ax


def plot_blockade_conflict_heatmap(
    result,
    register=None,
    edges: Optional[List[Tuple[int, int]]] = None,
    blockade_radius: Optional[float] = None,
    ax: Optional[Axes] = None,
    figsize: Tuple[float, float] = (8, 8),
    mode: str = 'matrix',
    cmap: str = 'Reds',
    show_values: bool = True,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Axes:
    """
    Plot blockade conflict matrix or edge heatmap.
    
    Visualizes probability of blockade violations (both atoms excited).
    
    Args:
        result: SimulationResult with blockade violation observables
        register: Optional Register object for spatial layout
        edges: Explicit edge list (optional, auto-derived from R_b if not provided)
        blockade_radius: Blockade radius for edge derivation
        ax: External axes
        figsize: Figure size
        mode: 'matrix' (NxN) or 'edges' (edge-based heatmap)
        cmap: Colormap name
        show_values: Annotate cells/edges
        title: Custom title
        save_path: Save figure path
    
    Returns:
        Axes object
    
    Raises:
        ValueError: If result lacks blockade-violation observables
    
    Example:
        >>> from sagittarius.viz import plot_blockade_conflict_heatmap
        >>> ax = plot_blockade_conflict_heatmap(result, mode='matrix')
        >>> ax = plot_blockade_conflict_heatmap(result, mode='edges', edges=[(0,1), (1,2)])
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Validate observables
    _validate_result_has_observables(result, 'blockade_violation_', 'BlockadeViolation')
    
    # Extract data
    n_atoms = result.metadata.get('register', {}).get('atom_count', 0)
    
    if n_atoms == 0:
        raise ValueError("Cannot determine atom count from result metadata.")
    
    if mode == 'matrix':
        # Build conflict matrix
        matrix = _build_correlation_matrix(
            result.data, n_atoms, 'blockade_violation_', default_value=0.0
        )
        
        # Plot heatmap
        im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=0, vmax=1)
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Conflict Probability', fontsize=9)
        
        # Axes
        ax.set_xlabel('Atom Index', fontsize=10)
        ax.set_ylabel('Atom Index', fontsize=10)
        ax.set_xticks(range(n_atoms))
        ax.set_yticks(range(n_atoms))
        ax.grid(False)
        
        # Annotate
        if show_values:
            _annotate_correlation_heatmap(ax, matrix, fmt='.2f', fontsize=7, threshold=0.01)
        
        # Title
        if title is None:
            n_conflicts = np.sum(matrix > 0.01) // 2
            title = f"Blockade Conflict Matrix ({n_conflicts} conflicting pairs)"
        ax.set_title(title, fontsize=11, fontweight='bold')
    
    elif mode == 'edges':
        # Edge-based visualization
        if edges is None and blockade_radius is not None and register is not None:
            # Auto-derive edges from blockade radius
            from .geometry_diagnostics import extract_geometry_diagnostics
            diag = extract_geometry_diagnostics(register, blockade_radius=blockade_radius)
            edges = diag['edges']
        
        if not edges:
            raise ValueError("No edges provided. Specify 'edges' or provide 'register' + 'blockade_radius'.")
        
        # Extract conflict probabilities for each edge
        conflict_values = []
        edge_labels = []
        
        for i, j in edges:
            col_name = f"blockade_violation_{i}_{j}"
            if col_name in result.data:
                values = result.data[col_name]
                conflict_values.append(values[-1] if values else 0.0)
                edge_labels.append(f"{i}-{j}")
            else:
                conflict_values.append(0.0)
                edge_labels.append(f"{i}-{j}")
        
        # Sort by conflict probability
        sorted_indices = np.argsort(conflict_values)[::-1]
        sorted_values = [conflict_values[i] for i in sorted_indices]
        sorted_labels = [edge_labels[i] for i in sorted_indices]
        
        # Plot horizontal bar chart
        y_pos = np.arange(len(sorted_labels))
        colors = plt.cm.Reds(np.array(sorted_values))
        
        bars = ax.barh(y_pos, sorted_values, color=colors, edgecolor='gray', linewidth=0.5)
        
        # Annotate bars
        if show_values:
            for idx, (val, label) in enumerate(zip(sorted_values, sorted_labels)):
                if val > 0.01:
                    ax.text(val + 0.01, idx, f'{val:.2f}', 
                           va='center', fontsize=7, color='black')
        
        # Configure axes
        ax.set_yticks(y_pos)
        ax.set_yticklabels(sorted_labels, fontsize=8)
        ax.set_xlabel('Conflict Probability', fontsize=10)
        ax.set_xlim(0, 1.05)
        ax.grid(axis='x', alpha=0.3, linestyle=':')
        
        # Title
        if title is None:
            n_high_conflict = sum(1 for v in sorted_values if v > 0.1)
            title = f"Blockade Conflict Edges ({n_high_conflict} high-conflict)"
        ax.set_title(title, fontsize=11, fontweight='bold')
    
    else:
        raise ValueError(f"Invalid mode '{mode}'. Use 'matrix' or 'edges'.")
    
    # Save
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Blockade conflict {mode} saved to: {save_path}")
    
    return ax
