"""
Sagittarius Visualization Module.

Provides backend-free visualization helpers for quantum simulation results,
register geometries, and pulse sequences.

This module implements Phase 19 P0 (Priority 0) visualization features:
- Register layout plotting with blockade edges
- Pulse waveform sampling and plotting
- Observable trajectory plotting
- Bitstring distribution histograms
- Shot count histograms
- Population heatmaps

All functions are backend-free and do not trigger Julia initialization.
They operate on pure Python/NumPy data structures extracted from
SimulationResult, Register, or PulseSequence objects.
"""

from sagittarius.viz.register import plot_register, plot_interaction_graph
from sagittarius.viz.pulse import (
    plot_pulse_waveform, 
    plot_pulse_both_fields,
    sample_pulse_waveform,
)
from sagittarius.viz.result import (
    plot_observables,
    plot_bitstring_distribution,
    plot_shot_histogram,
    plot_population_heatmap,
)
from sagittarius.viz.mwis_viz import (
    plot_mwis_problem,
    plot_mwis_comparison,
    annotate_solution_quality,
    save_mwis_benchmark_figure,
)
from sagittarius.viz.basis_diagnostics import (
    generate_basis_diagnostics,
    plot_basis_space_diagram,
    plot_bitstring_space_grid,
    plot_blockade_constraint_graph,
    plot_comprehensive_basis_diagnostics,
)
from sagittarius.viz.geometry_diagnostics import (
    extract_geometry_diagnostics,
    plot_geometry_diagnostics,
    plot_unit_disk_graph,
)

__all__ = [
    "plot_register",
    "plot_interaction_graph",
    "plot_pulse_waveform",
    "plot_pulse_both_fields",
    "sample_pulse_waveform",
    "plot_observables",
    "plot_bitstring_distribution",
    "plot_shot_histogram",
    "plot_population_heatmap",
    "plot_mwis_problem",
    "plot_mwis_comparison",
    "annotate_solution_quality",
    "save_mwis_benchmark_figure",
    "generate_basis_diagnostics",
    "plot_basis_space_diagram",
    "plot_bitstring_space_grid",
    "plot_blockade_constraint_graph",
    "plot_comprehensive_basis_diagnostics",
    "extract_geometry_diagnostics",
    "plot_geometry_diagnostics",
    "plot_unit_disk_graph",
]
