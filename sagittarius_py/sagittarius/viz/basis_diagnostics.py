"""
Basis space diagnostics visualization for small quantum systems.

Provides diagnostic tools to visualize the structure of Hilbert spaces,
including valid/forbidden bitstrings, basis truncation ratios, and the
relationship between blockade constraints and reduced basis validity.

This module is intended for DEBUGGING PURPOSES ONLY on small systems (N ≤ 10).
It strictly follows Sagittarius unified bitstring sorting rules (ascending integer order).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional, List, Tuple, Dict, Any


def _int_to_bitstring(state: int, n_atoms: int) -> str:
    """Convert integer state to binary string with proper padding."""
    return format(state, f'0{n_atoms}b')


def _check_blockade_violation(state: int, edges: List[Tuple[int, int]]) -> bool:
    """Check if a bitstring violates blockade constraints."""
    for i, j in edges:
        # Check if both atoms are excited (bit = 1)
        if (state & (1 << i)) and (state & (1 << j)):
            return True
    return False


def generate_basis_diagnostics(
    register,
    blockade_radius: float,
    edges: Optional[List[Tuple[int, int]]] = None,
) -> Dict[str, Any]:
    """
    Generate comprehensive basis diagnostics for a quantum register.
    
    Args:
        register: Register object with atom positions
        blockade_radius: Blockade radius for constraint checking
        edges: Optional pre-computed edges. If None, auto-derived from blockade_radius
        
    Returns:
        Dictionary containing:
        - n_atoms: Number of atoms
        - full_dimension: Full Hilbert space dimension (2^N)
        - reduced_dimension: Reduced basis dimension
        - pruning_ratio: Fraction of states pruned (0 to 1)
        - valid_states: List of valid state integers
        - forbidden_states: List of forbidden state integers
        - valid_bitstrings: List of valid bitstrings
        - forbidden_bitstrings: List of forbidden bitstrings
        - edges: List of blockade edges
        - blockade_graph_density: Edge density of blockade graph
    """
    from sagittarius.viz.register import _extract_positions
    
    n_atoms = len(register.atoms)
    
    if n_atoms > 10:
        raise ValueError(
            f"Basis diagnostics limited to N ≤ 10 atoms for tractability. "
            f"Got {n_atoms} atoms (full dimension would be {2**n_atoms})."
        )
    
    # Extract positions and compute edges if not provided
    pos_array = _extract_positions(register)
    
    if edges is None:
        edges = []
        for i in range(n_atoms):
            for j in range(i + 1, n_atoms):
                dist = np.sqrt((pos_array[i, 0] - pos_array[j, 0])**2 + 
                              (pos_array[i, 1] - pos_array[j, 1])**2)
                if dist <= blockade_radius:
                    edges.append((i, j))
    
    # Generate all possible states
    full_dimension = 2 ** n_atoms
    all_states = list(range(full_dimension))
    
    # Classify states as valid or forbidden
    valid_states = []
    forbidden_states = []
    
    for state in all_states:
        if _check_blockade_violation(state, edges):
            forbidden_states.append(state)
        else:
            valid_states.append(state)
    
    # Convert to bitstrings
    valid_bitstrings = [_int_to_bitstring(s, n_atoms) for s in valid_states]
    forbidden_bitstrings = [_int_to_bitstring(s, n_atoms) for s in forbidden_states]
    
    # Compute statistics
    reduced_dimension = len(valid_states)
    pruning_ratio = 1.0 - (reduced_dimension / full_dimension)
    
    # Compute blockade graph density
    max_edges = n_atoms * (n_atoms - 1) // 2
    graph_density = len(edges) / max_edges if max_edges > 0 else 0.0
    
    return {
        'n_atoms': n_atoms,
        'full_dimension': full_dimension,
        'reduced_dimension': reduced_dimension,
        'pruning_ratio': pruning_ratio,
        'valid_states': valid_states,
        'forbidden_states': forbidden_states,
        'valid_bitstrings': valid_bitstrings,
        'forbidden_bitstrings': forbidden_bitstrings,
        'edges': edges,
        'blockade_graph_density': graph_density,
    }


def plot_basis_space_diagram(
    diagnostics: Dict[str, Any],
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    show_bitstrings: bool = True,
    highlight_forbidden: bool = True,
    figsize: Tuple[float, float] = (14, 8),
) -> Axes:
    """
    Create a visual diagram of the basis space showing valid and forbidden states.
    
    This diagnostic view displays:
    - Full Hilbert space dimension vs reduced dimension
    - Valid bitstrings (green) and forbidden bitstrings (red)
    - Blockade constraint edges overlaid on register layout
    - Basis truncation ratio
    
    DIAGNOSTIC USE ONLY: For small systems (N ≤ 10) to understand basis structure.
    
    Args:
        diagnostics: Output from generate_basis_diagnostics()
        ax: Matplotlib axes. If None, creates new figure.
        title: Custom title. Auto-generated if None.
        show_bitstrings: Whether to display bitstring labels
        highlight_forbidden: Whether to color-code forbidden states
        figsize: Figure size for new figures
        
    Returns:
        The matplotlib Axes object
        
    
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    n_atoms = diagnostics['n_atoms']
    full_dim = diagnostics['full_dimension']
    reduced_dim = diagnostics['reduced_dimension']
    pruning_ratio = diagnostics['pruning_ratio']
    valid_bitstrings = diagnostics['valid_bitstrings']
    forbidden_bitstrings = diagnostics['forbidden_bitstrings']
    edges = diagnostics['edges']
    
    # Validate input
    if n_atoms > 10:
        raise ValueError("Basis diagnostics only supported for N ≤ 10")
    
    if len(valid_bitstrings) + len(forbidden_bitstrings) != full_dim:
        raise ValueError(
            f"Inconsistent state counts: {len(valid_bitstrings)} valid + "
            f"{len(forbidden_bitstrings)} forbidden ≠ {full_dim} total"
        )
    
    # Create visualization: bar chart showing dimension breakdown
    categories = ['Full\nHilbert Space', 'Reduced\nBasis', 'Forbidden\nStates']
    dimensions = [full_dim, reduced_dim, len(forbidden_bitstrings)]
    colors = ['steelblue', 'forestgreen', 'crimson']
    
    x_pos = np.arange(len(categories))
    bars = ax.bar(x_pos, dimensions, color=colors, edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for bar, dim in zip(bars, dimensions):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{dim}',
               ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # Formatting
    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylabel('Dimension', fontsize=12, fontweight='bold')
    ax.set_yscale('log')  # Use log scale for better visibility
    
    # Add grid
    ax.grid(axis='y', linestyle=':', alpha=0.5, which='both')
    ax.set_axisbelow(True)
    
    # Add annotation box with key metrics
    info_text = (
        f"N = {n_atoms} atoms\n"
        f"Pruning ratio: {pruning_ratio:.2%}\n"
        f"Blockade edges: {len(edges)}\n"
        f"Graph density: {diagnostics['blockade_graph_density']:.2f}"
    )
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.98, 0.97, info_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='top', horizontalalignment='right',
           bbox=props, family='monospace')
    
    # Title
    if title:
        ax.set_title(title, fontsize=13, fontweight='bold')
    else:
        ax.set_title(
            f"Basis Space Diagnostics (N={n_atoms}, {len(edges)} blockade edges)",
            fontsize=13, fontweight='bold'
        )
    
    # Add subtitle indicating diagnostic purpose
    ax.text(0.5, -0.15, "⚠️  DIAGNOSTIC VIEW — Small Systems Only (N ≤ 10)",
           transform=ax.transAxes, fontsize=9, style='italic',
           ha='center', color='darkred')
    
    plt.tight_layout()
    return ax


def plot_bitstring_space_grid(
    diagnostics: Dict[str, Any],
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    max_display_states: int = 64,
    figsize: Tuple[float, float] = (12, 10),
) -> Axes:
    """
    Visualize bitstring space as a colored grid.
    
    Each row represents a state (sorted by integer value), colored by validity:
    - Green: Valid (in reduced basis)
    - Red: Forbidden (violates blockade constraints)
    
    Strictly follows ascending integer order (Sagittarius unified sorting).
    
    Args:
        diagnostics: Output from generate_basis_diagnostics()
        ax: Matplotlib axes
        title: Custom title
        max_display_states: Maximum states to display (to avoid clutter)
        figsize: Figure size
        
    Returns:
        The matplotlib Axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    n_atoms = diagnostics['n_atoms']
    valid_states = set(diagnostics['valid_states'])
    forbidden_states = set(diagnostics['forbidden_states'])
    
    # Limit display to avoid overwhelming visualization
    all_states = sorted(valid_states | forbidden_states)
    if len(all_states) > max_display_states:
        # Show first max_display_states states
        display_states = all_states[:max_display_states]
        truncated = True
    else:
        display_states = all_states
        truncated = False
    
    # Create color map: green for valid, red for forbidden
    colors = []
    for state in display_states:
        if state in valid_states:
            colors.append('forestgreen')
        elif state in forbidden_states:
            colors.append('crimson')
        else:
            colors.append('gray')  # Should not happen
    
    # Create grid visualization
    y_pos = np.arange(len(display_states))
    ax.barh(y_pos, [1] * len(display_states), color=colors, edgecolor='black', linewidth=0.5)
    
    # Add bitstring labels
    bitstrings = [_int_to_bitstring(s, n_atoms) for s in display_states]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(bitstrings, fontsize=8, family='monospace')
    
    # Formatting
    ax.set_xlabel('State Validity', fontsize=11, fontweight='bold')
    ax.set_ylabel('Bitstring (↑ integer order)', fontsize=11, fontweight='bold')
    ax.set_xlim(0, 1)
    ax.set_xticks([])  # Hide x-axis ticks
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='forestgreen', edgecolor='black', label=f'Valid ({len(valid_states)})'),
        Patch(facecolor='crimson', edgecolor='black', label=f'Forbidden ({len(forbidden_states)})'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    # Title
    if title:
        ax.set_title(title, fontsize=13, fontweight='bold')
    else:
        trunc_note = f" (showing first {max_display_states})" if truncated else ""
        ax.set_title(
            f"Bitstring Space Grid — N={n_atoms}{trunc_note}",
            fontsize=13, fontweight='bold'
        )
    
    # Diagnostic warning
    ax.text(0.5, -0.08, "⚠️  DIAGNOSTIC VIEW — Sorted by Integer Value (Sagittarius Convention)",
           transform=ax.transAxes, fontsize=8, style='italic',
           ha='center', color='darkred')
    
    plt.tight_layout()
    return ax


def plot_blockade_constraint_graph(
    diagnostics: Dict[str, Any],
    register,
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 10),
) -> Axes:
    """
    Visualize blockade constraint graph overlaid on register layout.
    
    Shows:
    - Atom positions
    - Blockade edges (which create forbidden states)
    - Annotation of constraint impact
    
    Args:
        diagnostics: Output from generate_basis_diagnostics()
        register: Register object for atom positions
        ax: Matplotlib axes
        title: Custom title
        figsize: Figure size
        
    Returns:
        The matplotlib Axes object
    """
    from sagittarius.viz.register import plot_register
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Plot register with blockade edges
    plot_register(
        register,
        blockade_radius=None,  # Don't draw disks, just edges
        edges=False,  # We'll draw custom edges
        labels=True,
        ax=ax,
        title=title or f"Blockade Constraint Graph (N={diagnostics['n_atoms']})",
    )
    
    # Draw blockade edges
    pos_array = np.array([[a.x, a.y] for a in register.atoms])
    edges = diagnostics['edges']
    
    for i, j in edges:
        ax.plot([pos_array[i, 0], pos_array[j, 0]],
               [pos_array[i, 1], pos_array[j, 1]],
               'r--', linewidth=2, alpha=0.7, zorder=3, label='Blockade edge' if i == edges[0][0] else '')
    
    # Add statistics text box
    n_atoms = diagnostics['n_atoms']
    n_edges = len(edges)
    pruning_ratio = diagnostics['pruning_ratio']
    graph_density = diagnostics['blockade_graph_density']
    
    stats_text = (
        f"Atoms: {n_atoms}\n"
        f"Blockade edges: {n_edges}\n"
        f"Graph density: {graph_density:.2f}\n"
        f"States pruned: {pruning_ratio:.2%}"
    )
    
    props = dict(boxstyle='round', facecolor='lightyellow', alpha=0.9)
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='top', family='monospace',
           bbox=props)
    
    # Add legend for edges
    ax.plot([], [], 'r--', linewidth=2, alpha=0.7, label='Blockade constraint')
    ax.legend(loc='lower right', fontsize=9)
    
    # Diagnostic warning
    ax.text(0.5, -0.08, "⚠️  DIAGNOSTIC VIEW — Red Dashed Lines = Blockade Constraints",
           transform=ax.transAxes, fontsize=8, style='italic',
           ha='center', color='darkred')
    
    plt.tight_layout()
    return ax


def plot_comprehensive_basis_diagnostics(
    diagnostics: Dict[str, Any],
    register,
    figsize: Tuple[float, float] = (18, 14),
    save_path: Optional[str] = None,
) -> List[Axes]:
    """
    Create a comprehensive multi-panel diagnostic figure.
    
    Combines three views:
    1. Basis space dimension breakdown (bar chart)
    2. Bitstring space grid (colored rows)
    3. Blockade constraint graph (register layout with edges)
    
    All panels follow Sagittarius unified bitstring sorting (ascending integer).
    
    Args:
        diagnostics: Output from generate_basis_diagnostics()
        register: Register object for layout visualization
        figsize: Overall figure size
        save_path: Optional path to save figure
        
    Returns:
        List of three Axes objects
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    
    n_atoms = diagnostics['n_atoms']
    
    # Panel 1: Dimension breakdown
    ax1 = plot_basis_space_diagram(
        diagnostics,
        ax=axes[0],
        title="Basis Dimensions",
        show_bitstrings=False,
    )
    
    # Panel 2: Bitstring grid
    ax2 = plot_bitstring_space_grid(
        diagnostics,
        ax=axes[1],
        title="Bitstring Space",
        max_display_states=64,
    )
    
    # Panel 3: Constraint graph
    ax3 = plot_blockade_constraint_graph(
        diagnostics,
        register,
        ax=axes[2],
        title="Constraint Graph",
    )
    
    # Add overall title
    fig.suptitle(
        f"Basis Space Diagnostics — N={n_atoms} Atoms (DIAGNOSTIC VIEW)",
        fontsize=14, fontweight='bold', y=1.02
    )
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return list(axes)
