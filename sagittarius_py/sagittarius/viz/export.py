"""
Chart export utilities with metadata provenance tracking.

Provides functions to export matplotlib figures to PNG/SVG/PDF formats
with accompanying JSON metadata files containing full provenance information.

All exports include:
- Original artifact identifiers
- Mode version and schema information
- Random seeds and backend types
- Basis modes and plotting parameters
- Timestamp and environment details

IMPORTANT: Exported charts are EXPLORATORY VISUALIZATIONS unless bound to
controlled standard artifacts per SPEC-GOV-001.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def _build_provenance_metadata(
    result: Optional[Any] = None,
    artifact_id: Optional[str] = None,
    plot_function: Optional[str] = None,
    plot_params: Optional[Dict[str, Any]] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build comprehensive provenance metadata dictionary.
    
    Args:
        result: SimulationResult or similar object (optional)
        artifact_id: Explicit artifact identifier (optional)
        plot_function: Name of the plotting function used
        plot_params: Parameters passed to the plotting function
        extra_metadata: Additional custom metadata
        
    Returns:
        Dictionary with complete provenance information
    """
    metadata = {
        'schema_version': 'chart-export/v1',
        'export_timestamp': datetime.utcnow().isoformat() + 'Z',
        'provenance': {
            'artifact_id': artifact_id or (result.manifest.get('artifact_id') if hasattr(result, 'manifest') and result.manifest else None),
            'mode_version': getattr(result, 'mode_version', None) if result else None,
            'schema_version_result': getattr(result, 'schema_version', None) if result else None,
            'backend_type': getattr(result, 'backend', None) if result else None,
            'random_seed': getattr(result, 'seed', None) if result else None,
            'basis_mode': None,  # To be filled from result if available
        },
        'plotting': {
            'function': plot_function,
            'parameters': plot_params or {},
        },
        'environment': {
            'python_version': f"{__import__('sys').version}",
            'matplotlib_version': __import__('matplotlib').__version__,
            'platform': __import__('platform').platform(),
        },
        'disclaimer': "EXPLORATORY VISUALIZATION - Not for hardware calibration or performance evidence unless bound to controlled standard artifacts per SPEC-GOV-001",
    }
    
    # Extract basis mode from result if available
    if result and hasattr(result, 'register'):
        try:
            metadata['provenance']['basis_mode'] = str(getattr(result.register, 'basis', 'computational'))
        except:
            pass
    
    # Merge extra metadata
    if extra_metadata:
        metadata.update(extra_metadata)
    
    return metadata


def export_figure(
    fig: Optional[Figure] = None,
    output_path: str = "chart",
    formats: list = None,
    dpi: int = 300,
    metadata: Optional[Dict[str, Any]] = None,
    save_metadata: bool = True,
    **metadata_kwargs,
) -> Dict[str, str]:
    """
    Export matplotlib figure to multiple formats with metadata.
    
    Args:
        fig: Matplotlib figure to export (uses current figure if None)
        output_path: Base output path (without extension)
        formats: List of formats to export ['png', 'svg', 'pdf'] (default: ['png'])
        dpi: Resolution for raster formats (PNG)
        metadata: Pre-built metadata dictionary (optional)
        save_metadata: Whether to save JSON metadata file (default: True)
        **metadata_kwargs: Arguments passed to _build_provenance_metadata()
        
    Returns:
        Dictionary mapping format to exported file path
        
    Example:
        >>> fig, ax = plt.subplots()
        >>> ax.plot([1, 2, 3], [1, 4, 9])
        >>> paths = export_figure(fig, 'my_plot', formats=['png', 'pdf'], 
        ...                      result=simulation_result, plot_function='plot_observables')
        >>> print(paths)
        {'png': 'my_plot.png', 'pdf': 'my_plot.pdf', 'json': 'my_plot.metadata.json'}
    """
    if formats is None:
        formats = ['png']
    
    valid_formats = {'png', 'svg', 'pdf'}
    invalid = set(formats) - valid_formats
    if invalid:
        raise ValueError(f"Invalid formats: {invalid}. Valid formats: {valid_formats}")
    
    # Get current figure if not provided
    if fig is None:
        fig = plt.gcf()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Build metadata
    if metadata is None:
        metadata = _build_provenance_metadata(**metadata_kwargs)
    
    # Export to requested formats
    exported_files = {}
    
    for fmt in formats:
        file_path = f"{output_path}.{fmt}"
        
        if fmt == 'png':
            fig.savefig(file_path, format='png', dpi=dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
        elif fmt == 'svg':
            fig.savefig(file_path, format='svg', bbox_inches='tight')
        elif fmt == 'pdf':
            fig.savefig(file_path, format='pdf', bbox_inches='tight')
        
        exported_files[fmt] = file_path
    
    # Save metadata JSON
    if save_metadata:
        metadata_path = f"{output_path}.metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        exported_files['json'] = metadata_path
    
    return exported_files


def export_from_result(
    result: Any,
    plot_func,
    output_path: str,
    formats: list = None,
    dpi: int = 300,
    plot_args: Optional[Dict[str, Any]] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Convenience function to plot from SimulationResult and export with metadata.
    
    Args:
        result: SimulationResult object
        plot_func: Plotting function that accepts ax parameter and returns Axes
        output_path: Base output path (without extension)
        formats: List of formats to export (default: ['png'])
        dpi: Resolution for PNG
        plot_args: Arguments to pass to plot_func
        extra_metadata: Additional metadata to include
        **kwargs: Additional arguments to export_figure()
        
    Returns:
        Dictionary mapping format to exported file path
        
    Example:
        >>> paths = export_from_result(
        ...     result, 
        ...     plot_observables,
        ...     'observable_trajectories',
        ...     formats=['png', 'pdf'],
        ...     plot_args={'names': ['energy']}
        ... )
    """
    if plot_args is None:
        plot_args = {}
    
    # Create figure and plot
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_func(result=result, ax=ax, **plot_args)
    
    # Export with metadata
    return export_figure(
        fig=fig,
        output_path=output_path,
        formats=formats,
        dpi=dpi,
        result=result,
        plot_function=plot_func.__name__ if hasattr(plot_func, '__name__') else str(plot_func),
        plot_params=plot_args,
        extra_metadata=extra_metadata,
        **kwargs,
    )