import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

# __file__ = 当前脚本 visualization.py 的绝对路径
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True, parents=True)

reg = Register([Atom(0.0, 0.0, 0.0)], C6=0.0)
seq = PulseSequence(omega=2.0 * np.pi, delta=0.0)
cfg = SolverConfig(reltol=1e-7, abstol=1e-7, saveat=[0.0, 0.25, 0.5])

sim = Simulation(reg, seq, cfg)
psi0 = np.array([1.0, 0.0], dtype=complex)
result = sim.run(psi0, 0.0, 0.5, observables={"pop_atom_0": 0})

result.plot(show=False)
plt.savefig(output_dir / "rabi_population.png", dpi=300, bbox_inches="tight")
plt.close()

df = result.to_pandas()
print(list(df.columns))
print([round(v, 2) for v in df["pop_atom_0"].tolist()])