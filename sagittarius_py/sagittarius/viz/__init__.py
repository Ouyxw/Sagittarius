"""
Visualization module for Sagittarius quantum simulation framework.

Provides backend-free plotting utilities for:
- Register geometry and pulse sequences
- Observable trajectories and expectation values
- MWIS problem visualization and solution quality
- Diagnostic views for numerical validation (Phase 14/16)
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
from sagittarius.viz.correlation_viz import (
    plot_pair_correlation_matrix,
    plot_connected_correlation_matrix,
    plot_pauli_zz_matrix,
    plot_blockade_conflict_heatmap,
)
from sagittarius.viz.spatial_snapshot import (
    extract_spatial_snapshot,
    extract_frame_sequence,
    save_frame_data,
    plot_spatial_snapshot,
    plot_multi_panel_snapshots,
)
from sagittarius.viz.diagnostics import (
    plot_time_grid_diagnostics,
    plot_lindblad_validation,
    plot_mcwf_vs_lindblad,
    plot_trajectory_statistics,
)
from sagittarius.viz.mwis_diagnostics import (
    plot_mwis_convergence,
    plot_mwis_feasibility_diagram,
)
from sagittarius.viz.benchmark_perf import (
    plot_runtime_scaling,
    plot_memory_scaling,
    plot_solver_comparison,
    plot_success_failure_summary,
    plot_cpu_gpu_error_comparison,
)
from sagittarius.viz.small_system_debug import (
    plot_state_probabilities,
    plot_density_matrix_diagonal,
    plot_density_matrix_magnitude,
    plot_density_matrix_phase,
)
from sagittarius.viz.export import (
    export_figure,
    export_from_result,
)
from sagittarius.viz.report import (
    ReportGenerator,
    generate_quick_report,
)
from sagittarius.viz.sweep import (
    plot_sweep_heatmap,
    plot_sweep_line_slice,
    plot_final_observable_map,
    plot_observables_comparison,
    plot_failed_run_mask,
    extract_sweep_summary,
    generate_synthetic_sweep_data,
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
    "plot_pair_correlation_matrix",
    "plot_connected_correlation_matrix",
    "plot_pauli_zz_matrix",
    "plot_blockade_conflict_heatmap",
    "extract_spatial_snapshot",
    "extract_frame_sequence",
    "save_frame_data",
    "plot_spatial_snapshot",
    "plot_multi_panel_snapshots",
    "plot_time_grid_diagnostics",
    "plot_lindblad_validation",
    "plot_mcwf_vs_lindblad",
    "plot_trajectory_statistics",
    # MWIS diagnostic visualization (Phase 16)
    "plot_mwis_convergence",
    "plot_mwis_feasibility_diagram",
    # Benchmark performance analysis
    "plot_runtime_scaling",
    "plot_memory_scaling",
    "plot_solver_comparison",
    "plot_success_failure_summary",
    "plot_cpu_gpu_error_comparison",
    # Small-system debugging views
    "plot_state_probabilities",
    "plot_density_matrix_diagonal",
    "plot_density_matrix_magnitude",
    "plot_density_matrix_phase",
    # Chart export with metadata provenance
    "export_figure",
    "export_from_result",
    # Lightweight report generation
    "ReportGenerator",
    "generate_quick_report",
    # Parameter sweep visualization (Phase 19)
    "plot_sweep_heatmap",
    "plot_sweep_line_slice",
    "plot_final_observable_map",
    "plot_observables_comparison",
    "plot_failed_run_mask",
    "extract_sweep_summary",
    "generate_synthetic_sweep_data",
]
