"""
MWIS (Maximum Weighted Independent Set) problem visualization utilities.

Provides specialized visualization tools for overlaying MWIS problem metadata
on register layouts, including target bitstrings, node weights, graph edges,
and constraint violation markers. These tools are designed for experimental
workflow demonstration and Phase 16 benchmarking visualization.

NOTE: This module is for display purposes only and does not generate
optimization performance conclusions directly.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import FancyBboxPatch
from typing import Optional, List, Tuple, Dict, Any
import json
import os
from datetime import datetime

# Import helper from register.py
from sagittarius.viz.register import _extract_positions


def plot_mwis_problem(
    register,
    bitstring: str,
    weights: Optional[List[float]] = None,
    edges: Optional[List[Tuple[int, int]]] = None,
    blockade_radius: Optional[float] = None,
    show_weights: bool = True,
    show_edges: bool = True,
    highlight_conflicts: bool = True,
    conflict_color: str = 'red',
    edge_color: str = 'gray',
    weight_fontsize: int = 8,
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    algorithm_name: Optional[str] = None,
    performance_metrics: Optional[Dict[str, float]] = None,
    artifact_id: Optional[str] = None,
) -> Axes:
    """
    Plot MWIS problem on a quantum register layout with overlaid metadata.
    
    Visualizes the Maximum Weighted Independent Set problem by displaying:
    - Atom positions colored by bitstring state (excited/ground)
    - Node weights as numerical labels
    - Graph edges representing Unit-Disk Graph connections
    - Constraint violations (conflicting adjacent excited atoms)
    
    This tool is designed for experimental workflow demonstration and
    Phase 16 benchmarking visualization. It provides clear visual feedback
    on solution quality and constraint satisfaction.
    
    Args:
        register: Register object with atom positions
        bitstring: Binary string representing the independent set solution.
                  '1' = atom in independent set (excited), '0' = not in set (ground)
        weights: List of node weights (one per atom). If None, assumes uniform weights.
        edges: List of graph edges as tuples (i, j). If None, derives from blockade_radius.
        blockade_radius: Blockade radius in μm for deriving edges if not provided.
        show_weights: Whether to display weight values near atoms (default: True)
        show_edges: Whether to draw graph edges (default: True)
        highlight_conflicts: Whether to mark constraint violations (default: True)
        conflict_color: Color for conflict markers (default: 'red')
        edge_color: Color for graph edges (default: 'gray')
        weight_fontsize: Font size for weight labels (default: 8)
        ax: Matplotlib axes to plot on. If None, creates new figure.
        title: Custom plot title. If None, auto-generates based on solution quality.
        algorithm_name: Name of the algorithm used to find the solution.
        performance_metrics: Dictionary of performance metrics to display.
        artifact_id: Unique identifier for the solution artifact.
        
    Returns:
        The matplotlib Axes object
        
    
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 10))
    
    # Extract positions
    pos_array = _extract_positions(register)
    
    if pos_array.size == 0:
        raise ValueError("Register contains no atoms")
    
    x = pos_array[:, 0]
    y = pos_array[:, 1]
    n_atoms = len(x)
    
    # Validate bitstring
    if len(bitstring) != n_atoms:
        raise ValueError(
            f"Bitstring length ({len(bitstring)}) does not match number of atoms ({n_atoms})"
        )
    
    if not all(c in '01' for c in bitstring):
        raise ValueError(f"Bitstring must contain only '0' and '1', got: {bitstring}")
    
    # Validate weights if provided
    if weights is not None:
        if len(weights) != n_atoms:
            raise ValueError(
                f"Weights length ({len(weights)}) does not match number of atoms ({n_atoms})"
            )
    
    # Derive edges from blockade_radius if not provided
    if edges is None and blockade_radius is not None:
        edges = []
        for i in range(n_atoms):
            for j in range(i + 1, n_atoms):
                dist = np.sqrt((x[i] - x[j])**2 + (y[i] - y[j])**2)
                if dist <= blockade_radius:
                    edges.append((i, j))
    
    # Detect conflicts (adjacent atoms both in excited state)
    conflicts = []
    if highlight_conflicts and edges:
        for i, j in edges:
            if bitstring[i] == '1' and bitstring[j] == '1':
                conflicts.append((i, j))
    
    # Determine atom colors based on bitstring
    excited_state_color = '#FF8C00'  # Dark orange for excited
    ground_state_color = '#4682B4'   # Steel blue for ground
    
    colors = []
    for bit in bitstring:
        if bit == '1':
            colors.append(excited_state_color)
        else:
            colors.append(ground_state_color)
    
    # Set axis properties
    ax.set_aspect('equal', adjustable='datalim')
    
    # Plot graph edges (zorder=1)
    if show_edges and edges:
        for i, j in edges:
            # Check if this edge is a conflict
            is_conflict = (i, j) in conflicts
            
            if is_conflict:
                # Draw conflict edges with dashed red lines
                ax.plot([x[i], x[j]], [y[i], y[j]], 
                       color=conflict_color, linestyle='--', 
                       linewidth=2.5, alpha=0.7, zorder=1)
            else:
                # Draw normal edges
                ax.plot([x[i], x[j]], [y[i], y[j]], 
                       color=edge_color, linestyle='-', 
                       linewidth=1.5, alpha=0.4, zorder=1)
    
    # Plot conflict markers (zorder=2)
    if highlight_conflicts and conflicts:
        for i, j in conflicts:
            mid_x = (x[i] + x[j]) / 2
            mid_y = (y[i] + y[j]) / 2
            
            # Draw red X marker
            ax.plot(mid_x, mid_y, 'X', markersize=12, 
                   color=conflict_color, markeredgewidth=2.5, 
                   zorder=2, label='_nolegend_')
    
    # Plot atoms (zorder=5)
    scatter = ax.scatter(x, y, c=colors, s=150, zorder=5, 
                        edgecolors='black', linewidths=2, marker='o')
    
    # Ensure circular markers
    ax.set_aspect('equal', adjustable='datalim')
    
    # Plot atom index labels (zorder=10)
    for i in range(n_atoms):
        offset = 0.15
        ax.text(x[i] + offset, y[i] + offset, str(i), 
               fontsize=9, ha='left', va='bottom', 
               color='white', weight='bold',
               bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.7),
               zorder=10)
    
    # Plot weight labels (zorder=11)
    if show_weights and weights:
        for i in range(n_atoms):
            # Position weights opposite to index labels
            offset_x = -0.35
            offset_y = -0.35
            
            weight_text = f"w={weights[i]:.2f}" if isinstance(weights[i], float) else f"w={weights[i]}"
            
            ax.text(x[i] + offset_x, y[i] + offset_y, weight_text, 
                   fontsize=weight_fontsize, ha='right', va='top', 
                   color='darkgreen', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.25', facecolor='lightyellow', alpha=0.8),
                   zorder=11)
    
    # Calculate solution metrics
    excited_count = bitstring.count('1')
    total_weight = sum(weights) if weights else excited_count
    
    # Generate informative title with Phase 16 enhancements
    if title is None:
        title_parts = []
        
        if algorithm_name:
            title_parts.append(algorithm_name)
        
        if conflicts:
            title_parts.append(f"{excited_count} atoms, {len(conflicts)} conflicts")
        else:
            title_parts.append(f"{excited_count} atoms selected")
        
        if performance_metrics:
            if 'tts' in performance_metrics:
                title_parts.append(f"TTS={performance_metrics['tts']:.2f}s")
            if 'runtime' in performance_metrics:
                title_parts.append(f"T={performance_metrics['runtime']:.2f}s")
        
        title = " | ".join(title_parts) if title_parts else f"MVIS Problem (Weight: {total_weight:.2f})"
        
        # Add artifact ID on new line if provided
        if artifact_id:
            title += f"\nArtifact: {artifact_id}"
    else:
        # Append artifact ID to custom title if provided
        if artifact_id and '\n' not in title:
            title += f"\nArtifact: {artifact_id}"
    
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xlabel("x (μm)", fontsize=11)
    ax.set_ylabel("y (μm)", fontsize=11)
    
    # Add grid
    ax.grid(True, linestyle=':', alpha=0.3, zorder=0)
    
    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=ground_state_color, 
              markersize=12, label=f'Ground state (0)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=excited_state_color, 
              markersize=12, label=f'Excited state (1)'),
    ]
    
    if conflicts:
        legend_elements.append(
            Line2D([0], [0], marker='X', color='w', markerfacecolor=conflict_color, 
                  markersize=10, markeredgewidth=2.5, label=f'Constraint violation ({len(conflicts)})')
        )
    
    if show_edges and edges:
        legend_elements.append(
            Line2D([0], [0], color=edge_color, linestyle='-', linewidth=2, 
                  alpha=0.6, label=f'Graph edges ({len(edges)})')
        )
    
    ax.legend(handles=legend_elements, loc='best', fontsize=9, framealpha=0.9)
    
    return ax


def plot_mwis_comparison(
    register,
    bitstrings: List[str],
    titles: Optional[List[str]] = None,
    weights: Optional[List[float]] = None,
    edges: Optional[List[Tuple[int, int]]] = None,
    blockade_radius: Optional[float] = None,
    figsize: Tuple[int, int] = (16, 6),
    algorithm_names: Optional[List[str]] = None,
    performance_metrics_list: Optional[List[Dict[str, float]]] = None,
    artifact_ids: Optional[List[str]] = None,
) -> List[Axes]:
    """
    Compare multiple MWIS solutions side-by-side.
    
    Creates a multi-panel figure showing different candidate solutions
    for the same MWIS problem, enabling visual comparison of solution quality.
    
    Args:
        register: Register object with atom positions
        bitstrings: List of binary strings representing different solutions
        titles: List of subplot titles. If None, auto-generates.
        weights: Node weights (shared across all subplots)
        edges: Graph edges (shared across all subplots)
        blockade_radius: Blockade radius for edge derivation
        figsize: Figure size (width, height) in inches
        algorithm_names: List of algorithm names for each solution (Phase 16 enhancement)
        performance_metrics_list: List of performance metrics dicts for each solution (Phase 16)
        artifact_ids: List of artifact IDs for each solution (Phase 16)
        
    Returns:
        List of matplotlib Axes objects
        
    Raises:
        ValueError: If algorithm_names, performance_metrics_list, or artifact_ids 
                   length doesn't match bitstrings count
        
    Example:
        >>> # Compare greedy vs optimal solutions
        >>> ax_list = plot_mwis_comparison(
        ...     reg,
        ...     bitstrings=["10101", "01010"],
        ...     titles=["Greedy Solution", "Optimal Solution"],
        ...     weights=[1.2, 0.8, 1.5, 0.9, 1.1],
        ...     edges=[(0,1), (1,2), (2,3), (3,4)],
        ...     blockade_radius=5.0
        ... )
        
        >>> # Phase 16 enhanced usage
        >>> ax_list = plot_mwis_comparison(
        ...     reg,
        ...     bitstrings=[aqc_sol, greedy_sol],
        ...     algorithm_names=["AQC", "Greedy"],
        ...     performance_metrics_list=[
        ...         {"tts": 2.35, "p_success": 0.85},
        ...         {"ratio": 0.92}
        ...     ],
        ...     artifact_ids=["mwis-aqc-n16", "mwis-greedy-n16"]
        ... )
    """
    n_solutions = len(bitstrings)
    
    # Validate metadata lists if provided
    if algorithm_names is not None and len(algorithm_names) != n_solutions:
        raise ValueError(
            f"algorithm_names length ({len(algorithm_names)}) doesn't match bitstrings ({n_solutions})"
        )
    if performance_metrics_list is not None and len(performance_metrics_list) != n_solutions:
        raise ValueError(
            f"performance_metrics_list length ({len(performance_metrics_list)}) doesn't match bitstrings ({n_solutions})"
        )
    if artifact_ids is not None and len(artifact_ids) != n_solutions:
        raise ValueError(
            f"artifact_ids length ({len(artifact_ids)}) doesn't match bitstrings ({n_solutions})"
        )
    
    if titles is None:
        titles = [f"Solution {i+1}" for i in range(n_solutions)]
    elif len(titles) != n_solutions:
        raise ValueError(f"Number of titles ({len(titles)}) doesn't match bitstrings ({n_solutions})")
    
    fig, axes = plt.subplots(1, n_solutions, figsize=figsize)
    
    # Handle single subplot case
    if n_solutions == 1:
        axes = [axes]
    
    for idx, (ax, bitstring, title) in enumerate(zip(axes, bitstrings, titles)):
        # Extract per-solution metadata if available
        algo_name = algorithm_names[idx] if algorithm_names else None
        perf_metrics = performance_metrics_list[idx] if performance_metrics_list else None
        art_id = artifact_ids[idx] if artifact_ids else None
        
        # If algorithm name is provided, use it as the title instead of custom title
        effective_title = algo_name if algo_name else title
        
        plot_mwis_problem(
            register,
            bitstring=bitstring,
            weights=weights,
            edges=edges,
            blockade_radius=blockade_radius,
            ax=ax,
            title=effective_title,
            algorithm_name=None,  # Already used in title
            performance_metrics=perf_metrics,
            artifact_id=art_id
        )
    
    plt.tight_layout()
    return list(axes)


def annotate_solution_quality(
    ax: Axes,
    bitstring: str,
    weights: Optional[List[float]] = None,
    edges: Optional[List[Tuple[int, int]]] = None,
    text_position: Tuple[float, float] = (0.02, 0.98),
    fontsize: int = 10,
    include_approximation_ratio: bool = False,
    optimal_weight: Optional[float] = None,
) -> None:
    """
    Add solution quality metrics as text annotation on an existing plot.
    
    Displays key statistics like total weight, number of selected atoms,
    and constraint violations in a formatted text box.
    
    Args:
        ax: Matplotlib axes to annotate
        bitstring: Binary string representing the solution
        weights: Node weights for calculating total weight
        edges: Graph edges for detecting conflicts
        text_position: (x, y) position in axes coordinates (0-1 range)
        fontsize: Font size for annotation text
        include_approximation_ratio: Whether to show approximation ratio (Phase 16)
        optimal_weight: Optimal solution weight for calculating approximation ratio
        
    Example:
        >>> ax = plot_mwis_problem(reg, bitstring="10101", weights=w, edges=e)
        >>> annotate_solution_quality(ax, "10101", weights=w, edges=e)
        
        >>> # With approximation ratio
        >>> annotate_solution_quality(
        ...     ax, "10101", weights=w, edges=e,
        ...     include_approximation_ratio=True,
        ...     optimal_weight=15.5
        ... )
    """
    n_atoms = len(bitstring)
    selected_count = bitstring.count('1')
    total_weight = sum(weights) if weights else selected_count
    
    # Count conflicts
    conflict_count = 0
    if edges:
        for i, j in edges:
            if i < n_atoms and j < n_atoms:
                if bitstring[i] == '1' and bitstring[j] == '1':
                    conflict_count += 1
    
    # Format metrics
    metrics_lines = [
        f"Atoms selected: {selected_count}/{n_atoms}",
        f"Total weight: {total_weight:.2f}",
    ]
    
    # Add approximation ratio if requested
    if include_approximation_ratio and optimal_weight is not None and optimal_weight > 0:
        approx_ratio = total_weight / optimal_weight
        metrics_lines.append(f"Approx ratio: {approx_ratio:.3f}")
    
    metrics_lines.append(f"Conflicts: {conflict_count}")
    
    if conflict_count == 0:
        status = "✓ Valid IS"
        color = 'green'
    else:
        status = f"✗ {conflict_count} violations"
        color = 'red'
    
    metrics_lines.append(status)
    
    # Create text box
    text_str = '\n'.join(metrics_lines)
    bbox_props = dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.8)
    
    ax.text(text_position[0], text_position[1], text_str,
           transform=ax.transAxes, fontsize=fontsize,
           verticalalignment='top', horizontalalignment='left',
           bbox=bbox_props, family='monospace',
           color=color if conflict_count > 0 else 'black')


def save_mwis_benchmark_figure(
    fig,
    output_path: str,
    metadata: Dict[str, Any],
    dpi: int = 150,
    save_metadata_sidecar: bool = True,
) -> None:
    """
    Save MWIS benchmark figure with optional JSON metadata sidecar.
    
    Saves the matplotlib figure and optionally generates a JSON sidecar file
    containing benchmark metadata for artifact tracking and governance compliance.
    
    Args:
        fig: Matplotlib Figure object to save
        output_path: Output file path (supports .png, .pdf, .svg)
        metadata: Dictionary containing benchmark metadata. Should include:
            - artifact_id: Unique identifier for this benchmark artifact
            - schema_version: Schema version (e.g., "benchmark-artifact/v1")
            - algorithm: Algorithm name used
            - n_atoms: Number of atoms in the problem
            - Other relevant fields...
        dpi: Image resolution for raster formats (default: 150)
        save_metadata_sidecar: Whether to save JSON metadata file (default: True)
        
    Example:
        >>> metadata = {
        ...     "artifact_id": "mwis-bench-n16-d0.5-seed42",
        ...     "schema_version": "benchmark-artifact/v1",
        ...     "algorithm": "AQC",
        ...     "n_atoms": 16,
        ...     "density": 0.5,
        ...     "seed": 42,
        ...     "performance": {"tts": 2.35, "p_success": 0.85},
        ...     "commit_sha": "abc123..."
        ... }
        >>> save_mwis_benchmark_figure(fig, "result.png", metadata)
        # Generates: result.png + result.json
    """
    # Save the figure
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
    print(f"Saved figure: {output_path}")
    
    # Save metadata sidecar if requested
    if save_metadata_sidecar:
        # Generate JSON path
        base_path = os.path.splitext(output_path)[0]
        json_path = base_path + '.json'
        
        # Enhance metadata with timestamp and image info
        enhanced_metadata = metadata.copy()
        enhanced_metadata['visualization_saved_at'] = datetime.utcnow().isoformat() + 'Z'
        enhanced_metadata['image_path'] = output_path
        enhanced_metadata['image_dpi'] = dpi
        
        # Write JSON
        with open(json_path, 'w') as f:
            json.dump(enhanced_metadata, f, indent=2)
        
        print(f"Saved metadata: {json_path}")
