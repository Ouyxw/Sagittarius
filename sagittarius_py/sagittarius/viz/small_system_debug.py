"""
Small-system debugging visualization utilities.

Provides diagnostic views for low-dimensional Hilbert spaces, including state probability vectors,
density matrix diagonals, magnitude heatmaps, and phase heatmaps.

All functions are backend-free and operate on pure Python/NumPy data structures.
Charts include "DIAGNOSTIC VIEW" disclaimers and are NOT for hardware calibration.

IMPORTANT: These tools are ONLY applicable to small systems (typically ≤ 10 qubits).
For larger systems, clear error messages are raised when dimensions exceed safe limits.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional, List, Dict, Any, Tuple, Union
import warnings


# Maximum safe Hilbert space dimension for visualization
MAX_SAFE_DIM = 1024  # 2^10 qubits - beyond this, memory and rendering become problematic


def _validate_hilbert_dimension(dim: int, context: str = "visualization") -> None:
    """Validate that Hilbert space dimension is within safe limits."""
    if dim <= 0:
        raise ValueError(f"Hilbert space dimension must be positive, got {dim}.")
    
    if dim > MAX_SAFE_DIM:
        raise ValueError(
            f"Hilbert space dimension {dim} exceeds safe limit ({MAX_SAFE_DIM}). "
            f"This corresponds to more than {int(np.log2(dim))} qubits. "
            f"{context.capitalize()} is only supported for small systems (≤ {int(np.log2(MAX_SAFE_DIM))} qubits). "
            f"Consider using sparse representations or reduced observable sets for larger systems."
        )


def plot_state_probabilities(
    state_vector: Union[List[complex], np.ndarray],
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 6),
    show_labels: bool = True,
    basis: str = 'computational',
) -> Axes:
    """
    Plot state probability vector |ψ_i|^2 for all basis states.
    
    Visualizes the probability distribution across computational basis states.
    Only applicable for small Hilbert spaces (≤ 10 qubits).
    
    Args:
        state_vector: Complex state vector |ψ⟩ of dimension 2^n.
        ax: Matplotlib axes. Creates new if None.
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches.
        show_labels: If True, display binary labels on x-axis.
        basis: Basis type ('computational' for now).
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If state_vector is invalid or dimension too large
        
    Example:
        >>> psi = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])  # Bell state
        >>> ax = plot_state_probabilities(psi)
    """
    # Convert to numpy array
    psi = np.asarray(state_vector, dtype=complex)
    
    # Validate input
    if psi.ndim != 1:
        raise ValueError(f"State vector must be 1D, got {psi.ndim}D array.")
    
    dim = len(psi)
    n_qubits = int(np.log2(dim))
    
    if 2**n_qubits != dim:
        raise ValueError(
            f"State vector dimension {dim} is not a power of 2. "
            f"Expected dimension 2^n for n qubits."
        )
    
    _validate_hilbert_dimension(dim, "State probability visualization")
    
    # Compute probabilities
    probabilities = np.abs(psi)**2
    
    # Normalize to ensure sum = 1 (accounting for numerical errors)
    total_prob = np.sum(probabilities)
    if not np.isclose(total_prob, 1.0, atol=1e-6):
        warnings.warn(
            f"State vector not normalized: Σ|ψ_i|^2 = {total_prob:.6f}. "
            f"Probabilities will be normalized for visualization."
        )
        probabilities = probabilities / total_prob
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Create bar chart
    x_pos = np.arange(dim)
    colors = ['#2E86AB' if p > 0.01 else '#B8C5D6' for p in probabilities]
    
    ax.bar(x_pos, probabilities, color=colors, edgecolor='black', 
          linewidth=0.5, zorder=5)
    
    # Add labels
    if show_labels and dim <= 64:  # Only show labels for manageable sizes
        labels = [format(i, f'0{n_qubits}b') for i in range(dim)]
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=90, fontsize=7)
    else:
        ax.set_xlabel('Basis State Index', fontsize=12)
    
    ax.set_ylabel('Probability |ψ_i|²', fontsize=12)
    
    if title is None:
        title = f'State Probability Distribution ({n_qubits} qubits, dim={dim})'
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.grid(True, axis='y', alpha=0.3, zorder=0)
    
    # Add statistics
    nonzero_count = np.sum(probabilities > 1e-10)
    max_prob_idx = np.argmax(probabilities)
    max_prob = probabilities[max_prob_idx]
    
    stats_text = f'Non-zero states: {nonzero_count}/{dim}\n'
    stats_text += f'Max probability: {max_prob:.4f} (|{format(max_prob_idx, f"0{n_qubits}b")}⟩)'
    
    # Adjust layout first to make room for external elements
    plt.tight_layout()
    
    # Get figure for external text placement
    fig = ax.get_figure()
    
    # Add statistics outside plot area at upper right
    fig.text(0.99, 0.99, stats_text, transform=fig.transFigure, fontsize=9,
            verticalalignment='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # Add disclaimer outside plot area at bottom right (below the axes)
    fig.text(0.99, -0.02, "DIAGNOSTIC VIEW - Not for hardware calibration",
            transform=fig.transFigure, fontsize=7, color='red', ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    return ax


def plot_density_matrix_diagonal(
    density_matrix: Union[List[List[complex]], np.ndarray],
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 6),
    normalize: bool = True,
) -> Axes:
    """
    Plot diagonal elements of density matrix ρ_ii (populations).
    
    Visualizes the population distribution in the computational basis.
    Only applicable for small Hilbert spaces (≤ 10 qubits).
    
    Args:
        density_matrix: Density matrix ρ of shape (dim, dim).
        ax: Matplotlib axes. Creates new if None.
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches.
        normalize: If True, normalize diagonal to sum to 1.
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If density_matrix is invalid or dimension too large
        
    Example:
        >>> rho = np.array([[0.5, 0.1], [0.1, 0.5]])
        >>> ax = plot_density_matrix_diagonal(rho)
    """
    # Convert to numpy array
    rho = np.asarray(density_matrix, dtype=complex)
    
    # Validate input
    if rho.ndim != 2:
        raise ValueError(f"Density matrix must be 2D, got {rho.ndim}D array.")
    
    if rho.shape[0] != rho.shape[1]:
        raise ValueError(
            f"Density matrix must be square, got shape {rho.shape}."
        )
    
    dim = rho.shape[0]
    n_qubits = int(np.log2(dim))
    
    if 2**n_qubits != dim:
        raise ValueError(
            f"Density matrix dimension {dim} is not a power of 2. "
            f"Expected dimension 2^n for n qubits."
        )
    
    _validate_hilbert_dimension(dim, "Density matrix diagonal visualization")
    
    # Extract diagonal
    diagonal = np.real(np.diag(rho))  # Diagonal should be real
    
    # Check for negative populations (unphysical)
    if np.any(diagonal < -1e-10):
        warnings.warn(
            f"Density matrix has negative diagonal elements (min={np.min(diagonal):.2e}). "
            f"This indicates an unphysical state."
        )
    
    # Normalize if requested
    if normalize:
        total_pop = np.sum(diagonal)
        if not np.isclose(total_pop, 1.0, atol=1e-6):
            warnings.warn(
                f"Density matrix trace = {total_pop:.6f} ≠ 1. "
                f"Diagonal will be normalized for visualization."
            )
            diagonal = diagonal / total_pop
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Create bar chart
    x_pos = np.arange(dim)
    colors = ['#A23B72' if p > 0.01 else '#D4A5C3' for p in diagonal]
    
    ax.bar(x_pos, diagonal, color=colors, edgecolor='black', 
          linewidth=0.5, zorder=5)
    
    # Add labels for small systems
    if dim <= 64:
        labels = [format(i, f'0{n_qubits}b') for i in range(dim)]
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=90, fontsize=7)
    else:
        ax.set_xlabel('Basis State Index', fontsize=12)
    
    ax.set_ylabel('Population ρ_ii', fontsize=12)
    
    if title is None:
        title = f'Density Matrix Diagonal (Populations, {n_qubits} qubits)'
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.grid(True, axis='y', alpha=0.3, zorder=0)
    
    # Add statistics
    nonzero_count = np.sum(diagonal > 1e-10)
    max_pop_idx = np.argmax(diagonal)
    max_pop = diagonal[max_pop_idx]
    purity = np.sum(diagonal**2)  # Approximate purity from diagonal
    
    stats_text = f'Non-zero populations: {nonzero_count}/{dim}\n'
    stats_text += f'Max population: {max_pop:.4f} (|{format(max_pop_idx, f"0{n_qubits}b")}⟩)\n'
    stats_text += f'Diagonal purity: {purity:.4f}'
    
    # Adjust layout first to make room for external elements
    plt.tight_layout()
    
    # Get figure for external text placement
    fig = ax.get_figure()
    
    # Add statistics outside plot area at upper right
    fig.text(0.99, 0.99, stats_text, transform=fig.transFigure, fontsize=9,
            verticalalignment='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Add disclaimer outside plot area at bottom right (below the axes)
    fig.text(0.99, -0.02, "DIAGNOSTIC VIEW - Not for hardware calibration",
            transform=fig.transFigure, fontsize=7, color='red', ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    return ax


def plot_density_matrix_magnitude(
    density_matrix: Union[List[List[complex]], np.ndarray],
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 8),
    cmap: str = 'viridis',
    show_values: bool = False,
) -> Axes:
    """
    Plot density matrix magnitude heatmap |ρ_ij|.
    
    Visualizes both populations (diagonal) and coherences (off-diagonal).
    Only applicable for small Hilbert spaces (≤ 10 qubits).
    
    Args:
        density_matrix: Density matrix ρ of shape (dim, dim).
        ax: Matplotlib axes. Creates new if None.
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches.
        cmap: Colormap name for heatmap.
        show_values: If True, annotate cells with numeric values (only for dim ≤ 16).
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If density_matrix is invalid or dimension too large
        
    Example:
        >>> rho = np.array([[0.5, 0.1+0.1j], [0.1-0.1j, 0.5]])
        >>> ax = plot_density_matrix_magnitude(rho)
    """
    # Convert to numpy array
    rho = np.asarray(density_matrix, dtype=complex)
    
    # Validate input
    if rho.ndim != 2:
        raise ValueError(f"Density matrix must be 2D, got {rho.ndim}D array.")
    
    if rho.shape[0] != rho.shape[1]:
        raise ValueError(
            f"Density matrix must be square, got shape {rho.shape}."
        )
    
    dim = rho.shape[0]
    n_qubits = int(np.log2(dim))
    
    if 2**n_qubits != dim:
        raise ValueError(
            f"Density matrix dimension {dim} is not a power of 2. "
            f"Expected dimension 2^n for n qubits."
        )
    
    _validate_hilbert_dimension(dim, "Density matrix magnitude visualization")
    
    # Compute magnitude
    magnitude = np.abs(rho)
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Create heatmap
    im = ax.imshow(magnitude, cmap=cmap, aspect='auto', interpolation='nearest')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('|ρ_ij|', fontsize=11)
    
    # Add labels
    if dim <= 32:
        labels = [format(i, f'0{n_qubits}b') for i in range(dim)]
        ax.set_xticks(range(dim))
        ax.set_yticks(range(dim))
        ax.set_xticklabels(labels, rotation=90, fontsize=6)
        ax.set_yticklabels(labels, fontsize=6)
    else:
        ax.set_xlabel('Column Index (j)', fontsize=12)
        ax.set_ylabel('Row Index (i)', fontsize=12)
    
    if title is None:
        title = f'Density Matrix Magnitude |ρ_ij| ({n_qubits} qubits, {dim}×{dim})'
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Annotate with values for very small systems
    if show_values and dim <= 16:
        for i in range(dim):
            for j in range(dim):
                val = magnitude[i, j]
                if val > 1e-3:  # Only show significant values
                    text_color = 'white' if val > 0.5 * np.max(magnitude) else 'black'
                    ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                           fontsize=7, color=text_color, fontweight='bold')
    
    # Highlight diagonal
    ax.plot([-0.5, dim-0.5], [-0.5, dim-0.5], 'r--', linewidth=2, 
           label='Diagonal (populations)', zorder=10)
    
    # Place legend in upper right with minimal padding
    ax.legend(loc='upper right', fontsize=8, framealpha=0.95, edgecolor='gray',
             borderpad=2, labelspacing=0.3, handletextpad=4)
    
    # Adjust layout first to make room for external elements
    plt.tight_layout()
    
    # Get figure for external text placement
    fig = ax.get_figure()
    
    # Add disclaimer outside plot area at bottom right (below the axes)
    fig.text(0.99, -0.02, "DIAGNOSTIC VIEW - Not for hardware calibration",
            transform=fig.transFigure, fontsize=7, color='red', ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    return ax


def plot_density_matrix_phase(
    density_matrix: Union[List[List[complex]], np.ndarray],
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 8),
    cmap: str = 'twilight',
    threshold: float = 1e-3,
) -> Axes:
    """
    Plot density matrix phase heatmap arg(ρ_ij).
    
    Visualizes the quantum phase structure of coherences.
    Only applicable for small Hilbert spaces (≤ 10 qubits).
    
    Args:
        density_matrix: Density matrix ρ of shape (dim, dim).
        ax: Matplotlib axes. Creates new if None.
        title: Custom plot title. Auto-generated if None.
        figsize: Figure size (width, height) in inches.
        cmap: Colormap name for phase (cyclic colormap recommended).
        threshold: Minimum magnitude to display phase (smaller values masked).
        
    Returns:
        The matplotlib Axes object.
        
    Raises:
        ValueError: If density_matrix is invalid or dimension too large
        
    Example:
        >>> rho = np.array([[0.5, 0.1*np.exp(1j*np.pi/4)], 
        ...                 [0.1*np.exp(-1j*np.pi/4), 0.5]])
        >>> ax = plot_density_matrix_phase(rho)
    """
    # Convert to numpy array
    rho = np.asarray(density_matrix, dtype=complex)
    
    # Validate input
    if rho.ndim != 2:
        raise ValueError(f"Density matrix must be 2D, got {rho.ndim}D array.")
    
    if rho.shape[0] != rho.shape[1]:
        raise ValueError(
            f"Density matrix must be square, got shape {rho.shape}."
        )
    
    dim = rho.shape[0]
    n_qubits = int(np.log2(dim))
    
    if 2**n_qubits != dim:
        raise ValueError(
            f"Density matrix dimension {dim} is not a power of 2. "
            f"Expected dimension 2^n for n qubits."
        )
    
    _validate_hilbert_dimension(dim, "Density matrix phase visualization")
    
    # Compute phase
    magnitude = np.abs(rho)
    phase = np.angle(rho)  # Phase in radians [-π, π]
    
    # Mask elements below threshold
    masked_phase = np.ma.masked_where(magnitude < threshold, phase)
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Create heatmap
    im = ax.imshow(masked_phase, cmap=cmap, aspect='auto', 
                  interpolation='nearest', vmin=-np.pi, vmax=np.pi)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Phase arg(ρ_ij) [rad]', fontsize=11)
    cbar.set_ticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
    cbar.set_ticklabels(['-π', '-π/2', '0', 'π/2', 'π'])
    
    # Add labels
    if dim <= 32:
        labels = [format(i, f'0{n_qubits}b') for i in range(dim)]
        ax.set_xticks(range(dim))
        ax.set_yticks(range(dim))
        ax.set_xticklabels(labels, rotation=90, fontsize=6)
        ax.set_yticklabels(labels, fontsize=6)
    else:
        ax.set_xlabel('Column Index (j)', fontsize=12)
        ax.set_ylabel('Row Index (i)', fontsize=12)
    
    if title is None:
        shown_count = np.sum(magnitude >= threshold)
        total_count = dim * dim
        title = f'Density Matrix Phase arg(ρ_ij) ({shown_count}/{total_count} shown, threshold={threshold:.0e})'
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Highlight diagonal (phase should be 0 or undefined for real populations)
    ax.plot([-0.5, dim-0.5], [-0.5, dim-0.5], 'w--', linewidth=2, 
           label='Diagonal', zorder=10)
    
    # Place legend in upper right with minimal padding
    ax.legend(loc='upper right', fontsize=8, framealpha=0.95, edgecolor='gray',
             borderpad=2, labelspacing=0.3, handletextpad=4)
    
    # Adjust layout first to make room for external elements
    plt.tight_layout()
    
    # Get figure for external text placement
    fig = ax.get_figure()
    
    # Add note about masked elements outside plot area at bottom left
    masked_count = np.sum(magnitude < threshold)
    if masked_count > 0:
        note_text = f'{masked_count} elements masked (|ρ_ij| < {threshold:.0e})'
        fig.text(0.01, -0.02, note_text, transform=fig.transFigure, fontsize=8,
                verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
    
    # Add disclaimer outside plot area at bottom right (below the axes)
    fig.text(0.99, -0.02, "DIAGNOSTIC VIEW - Not for hardware calibration",
            transform=fig.transFigure, fontsize=7, color='red', ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    return ax
