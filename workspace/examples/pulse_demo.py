"""
Minimum test for pulse sampling and visualization.

This script demonstrates:
1. Global pulse
2. Local pulse (list)
3. Local pulse (dict)
4. Dictionary pulse
5. Callable pulse
6. Pulse AST
7. External Axes
8. Omega / Detuning plotting

All figures are saved to ./output/.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from sagittarius import PulseSequence
from sagittarius.pulse import Pulse
from sagittarius.viz import plot_pulse_waveform

# --------------------------------------------------------------------
# Output directory
# --------------------------------------------------------------------

OUTPUT = Path(__file__).parent / "output"
OUTPUT.mkdir(exist_ok=True)

times = np.linspace(0.0, 5.0, 500)


def save_plot(name, omega=None, delta=None, field="omega", atom=None):
    """Sample and save one waveform."""

    # Create a minimal PulseSequence with the given pulse
    if omega is None and delta is None:
        raise ValueError("Either omega or delta must be provided")
    
    seq = PulseSequence(omega=omega if omega is not None else 0.0, 
                        delta=delta if delta is not None else 0.0)

    fig, ax = plt.subplots(figsize=(6, 3))

    ax, values = plot_pulse_waveform(
        pulse_sequence=seq,
        time_grid=times,
        field=field,
        atom_index=atom,
        ax=ax,
    )

    fig.savefig(
        OUTPUT / f"{name}.png",
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"✓ {name}.png")


# --------------------------------------------------------------------
# 1 Global pulse
# --------------------------------------------------------------------

save_plot(
    "global",
    omega=Pulse.global_(2.0),
)

# --------------------------------------------------------------------
# 2 Local pulse (list)
# --------------------------------------------------------------------

save_plot(
    "local_list",
    omega=Pulse.local([1.0, 2.0, 3.0]),
    atom=1,
)

# --------------------------------------------------------------------
# 3 Local pulse (dict)
# --------------------------------------------------------------------

save_plot(
    "local_dict",
    omega=Pulse.local({
        0: 1.0,
        3: 5.0,
    }),
    atom=3,
)

# --------------------------------------------------------------------
# 4 Dictionary pulse (AST format)
# --------------------------------------------------------------------

save_plot(
    "dictionary",
    omega={
        "type": "ramp",
        "start_val": 0,
        "end_val": 3,
        "duration": 5,
    },
)

# --------------------------------------------------------------------
# 5 Callable pulse
# --------------------------------------------------------------------

save_plot(
    "callable",
    omega=Pulse.callable(
        lambda t: [
            np.sin(t),
            np.cos(t),
        ]
    ),
    atom=0,
)

# --------------------------------------------------------------------
# 6 Pulse AST
# --------------------------------------------------------------------

save_plot(
    "pulse_ast",
    omega=Pulse.piecewise([
        Pulse.constant(2.0, 2.0),
        Pulse.ramp(2.0, 0.0, 3.0),
    ]),
)

# --------------------------------------------------------------------
# 7 Detuning
# --------------------------------------------------------------------

save_plot(
    "detuning",
    delta=Pulse.global_(1.0),
    field="delta",
)

print()
print("===================================")
print("All pulse examples completed.")
print(f"Figures saved to: {OUTPUT.resolve()}")
print("===================================")
