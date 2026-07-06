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
]
