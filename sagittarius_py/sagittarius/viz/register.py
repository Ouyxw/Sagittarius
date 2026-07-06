"""
Register and geometry visualization utilities.

Provides backend-free helpers for plotting 2D atom layouts, blockade edges,
and interaction graphs. These functions extract position data from Register
objects and render them using matplotlib without initializing Julia.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional, List, Union

# Helper function to extract positions from Register objects
def _extract_positions(register) -> np.ndarray:

    try:
        if hasattr(register, 'positions'):
            pos_array = np.array(register.positions)
        elif hasattr(register, 'atoms'):
            atoms = register.atoms
            if len(atoms) > 0:
                first_atom = atoms[0]
                # Check if atoms are objects with x, y attributes
                if hasattr(first_atom, 'x') and hasattr(first_atom, 'y'):
                    pos_array = np.array([[a.x, a.y] for a in atoms])
                # Check if atoms are lists/tuples
                elif isinstance(first_atom, (list, tuple)):
                    pos_array = np.array(atoms)
                else:
                    raise ValueError("Atom objects do not have x, y attributes")
            else:
                pos_array = np.array([]).reshape(0, 2)
        else:
            raise ValueError("Register object does not have 'positions' or 'atoms' attribute")
            
        # Validate shape
        if pos_array.ndim != 2 or pos_array.shape[1] != 2:
            raise ValueError(f"Expected positions array of shape (N, 2), got {pos_array.shape}")
            
        return pos_array
        
    except Exception as e:
        raise ValueError(f"Could not extract positions from register: {e}")

# Main plotting function
def plot_register(
    register,
    blockade_radius: Optional[float] = None,
    edges: bool = True,
    labels: bool = True,
    ax: Optional[Axes] = None,
    highlight_atoms: Optional[List[int]] = None,
    highlight_color: str = 'red',
    atom_size: int = 100,
    title: Optional[str] = None,
    show_blockade_disks: bool = False,
    disk_alpha: float = 0.1,
    bitstring: Optional[str] = None,
    excited_state_color: str = 'orange',
    ground_state_color: str = 'steelblue',
) -> Axes:
    """
    Plot the 2D layout of atoms in a quantum register.
    
    Visualizes atom positions, optional blockade radius edges, and interaction graph.
    Supports highlighting specific atoms, rendering blockade disks, and overlaying
    selected bitstrings to show which atoms are in excited/ground states.
    
    Args:
        register: Register object with atom positions (must have .positions or .atoms)
        blockade_radius: Blockade radius in μm for drawing edges/disks
        edges: Whether to draw blockade edges between atoms within R_b
        labels: Whether to show atom index labels
        ax: Matplotlib axes to plot on. If None, creates new figure.
        highlight_atoms: List of atom indices to highlight (deprecated, use bitstring instead)
        highlight_color: Color for highlighted atoms (default: 'red')
        atom_size: Size of atom markers in points (default: 100)
        title: Custom plot title. If None, uses default.
        show_blockade_disks: Whether to render blockade radius circles around each atom
        disk_alpha: Transparency of blockade disks (0.0 to 1.0, default: 0.1)
        bitstring: Binary string representing atomic states (e.g., "0101"). 
                  '1' = excited state (Rydberg), '0' = ground state. Overrides highlight_atoms.
        excited_state_color: Color for atoms in excited state (bit='1', default: 'orange')
        ground_state_color: Color for atoms in ground state (bit='0', default: 'steelblue')
        
    Returns:
        The matplotlib Axes object
        
    Raises:
        ValueError: If register has no atoms, invalid format, or bitstring length mismatch
        
    Example:
        >>> from sagittarius import Register
        >>> from sagittarius.viz import plot_register
        >>> 
        >>> reg = Register.chain(5, spacing=5.0, blockade_radius=8.0)
        >>> # Basic plot with blockade disks
        >>> ax = plot_register(reg, blockade_radius=8.0, show_blockade_disks=True)
        >>> 
        >>> # Overlay a bitstring to show excited/ground states
        >>> ax = plot_register(reg, bitstring="01010", excited_state_color='red')
        >>> 
        >>> # From simulation result
        >>> result = sim.run(...)
        >>> dist = result.final_bitstring_distribution()
        >>> top_bitstring = max(dist, key=dist.get)  # Most probable state
        >>> ax = plot_register(reg, bitstring=top_bitstring)
    """

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    
    # Extract positions
    pos_array = _extract_positions(register)
    
    if pos_array.size == 0:
        raise ValueError("Register contains no atoms")
    
    x = pos_array[:, 0]
    y = pos_array[:, 1]
    n_atoms = len(x)
    
    # Determine colors for atoms based on bitstring or highlight_atoms
    if bitstring is not None:
        # Validate bitstring length
        if len(bitstring) != n_atoms:
            raise ValueError(
                f"Bitstring length ({len(bitstring)}) does not match number of atoms ({n_atoms})"
            )
        
        # Validate bitstring characters
        if not all(c in '01' for c in bitstring):
            raise ValueError(f"Bitstring must contain only '0' and '1', got: {bitstring}")
        
        # Assign colors based on bit values
        colors = []
        for i, bit in enumerate(bitstring):
            if bit == '1':
                colors.append(excited_state_color)
            else:
                colors.append(ground_state_color)
                
        # Add bitstring info to title if not provided
        if title is None:
            excited_count = bitstring.count('1')
            title = f"Register Layout (Bitstring: {bitstring}, {excited_count} excited)"
    elif highlight_atoms:
        # Legacy behavior: use highlight_atoms
        colors = [ground_state_color] * n_atoms
        for idx in highlight_atoms:
            if 0 <= idx < n_atoms:
                colors[idx] = highlight_color
            else:
                raise ValueError(f"highlight_atoms index {idx} out of range [0, {n_atoms-1}]")
    else:
        # Default: all atoms in ground state color
        colors = [ground_state_color] * n_atoms
                
    # Set axis properties BEFORE plotting to ensure circular atoms
    ax.set_aspect('equal', adjustable='datalim')
    
    # Plot Blockade Disks (if enabled)
    if show_blockade_disks and blockade_radius is not None:
        from matplotlib.patches import Circle
        for i in range(n_atoms):
            circle = Circle((x[i], y[i]), blockade_radius, 
                          facecolor=colors[i], alpha=disk_alpha, 
                          edgecolor=colors[i], linewidth=1, zorder=0)
            ax.add_patch(circle)
    
    # Plot atoms as scatter points with circular markers
    # Use transform=ax.transData to ensure circles stay circular
    scatter = ax.scatter(x, y, c=colors, s=atom_size, zorder=5, 
                        edgecolors='black', linewidths=1.5, marker='o')
    
    # Ensure scatter markers are circular by setting aspect ratio after plotting
    ax.set_aspect('equal', adjustable='datalim')
    
    # Plot atomic labels (0-based indices) positioned near atoms without overlap
    if labels:
        for i in range(n_atoms):
            # Calculate minimal offset to position label just outside atom edge
            # Use a very small fixed offset in data coordinates
            offset = 0.1  # Very small offset in μm - label touches atom edge
            
            ax.text(x[i] + offset, y[i] + offset, str(i), 
                   fontsize=9, ha='left', va='bottom', 
                   color='black', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.15', facecolor='white', alpha=0.8),
                   zorder=10)
    # Plot Blockade/UDG Edges
    if edges and blockade_radius is not None:
        edge_count = 0
        for i in range(n_atoms):
            for j in range(i + 1, n_atoms):
                dist = np.sqrt((x[i] - x[j])**2 + (y[i] - y[j])**2)
                if dist <= blockade_radius:
                    ax.plot([x[i], x[j]], [y[i], y[j]], 'k--', alpha=0.3, 
                           zorder=1, linewidth=1)
                    edge_count += 1
        
        # Add edge count to title if edges were drawn
        if edge_count > 0 and title is None:
            title = f"Register Layout ({edge_count} blockade edges)"
    
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        ax.set_title("Register Layout", fontsize=12, fontweight='bold')
    
    ax.set_xlabel("x (μm)", fontsize=10)
    ax.set_ylabel("y (μm)", fontsize=10)
    
    # Add grid for reference
    ax.grid(True, linestyle=':', alpha=0.3, zorder=0)
    
    # Add legend if bitstring or highlighting is used
    if bitstring or highlight_atoms:
        from matplotlib.lines import Line2D
        if bitstring:
            legend_elements = [
                Line2D([0], [0], marker='o', color='w', markerfacecolor=ground_state_color, 
                      markersize=10, label=f'Ground state (0)'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor=excited_state_color, 
                      markersize=10, label=f'Excited state (1)')
            ]
        else:
            legend_elements = [
                Line2D([0], [0], marker='o', color='w', markerfacecolor=ground_state_color, 
                      markersize=10, label='Ground state'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor=highlight_color, 
                      markersize=10, label='Highlighted')
            ]
        ax.legend(handles=legend_elements, loc='best', fontsize=8)
    
    return ax

# Interaction Graph Plotting Function
def plot_interaction_graph(
    register,
    blockade_radius: float,
    ax: Optional[Axes] = None,
    show_distances: bool = False,
) -> Axes:
   
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    
    # Use base plot_register with edges enabled
    ax = plot_register(
        register, 
        blockade_radius=blockade_radius, 
        edges=True, 
        labels=True, 
        ax=ax,
        title=f"Interaction Graph (R_b = {blockade_radius} μm)"
    )
    
    # Optionally add distance labels on edges
    if show_distances:
        pos_array = _extract_positions(register)
        x = pos_array[:, 0]
        y = pos_array[:, 1]
        n_atoms = len(x)
        
        for i in range(n_atoms):
            for j in range(i + 1, n_atoms):
                dist = np.sqrt((x[i] - x[j])**2 + (y[i] - y[j])**2)
                if dist <= blockade_radius:
                    mid_x = (x[i] + x[j]) / 2
                    mid_y = (y[i] + y[j]) / 2
                    ax.text(mid_x, mid_y, f"{dist:.1f}", fontsize=7, 
                           ha='center', va='center', 
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    return ax
