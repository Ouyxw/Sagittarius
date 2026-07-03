import numpy as np
import matplotlib
matplotlib.use("Agg")

from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

reg = Register([Atom(0.0, 0.0, 0.0)], C6=0.0)
seq = PulseSequence(omega=2.0 * np.pi, delta=0.0)
cfg = SolverConfig(reltol=1e-7, abstol=1e-7, saveat=[0.0, 0.25, 0.5])

sim = Simulation(reg, seq, cfg)
psi0 = np.array([1.0, 0.0], dtype=complex)
result = sim.run(psi0, 0.0, 0.5, observables={"pop_atom_0": 0})

# Current lightweight plotting helper. Use show=False for scripts and tests.
result.plot(show=True)

df = result.to_pandas()
print(list(df.columns))
print([round(value, 2) for value in df["pop_atom_0"].tolist()])