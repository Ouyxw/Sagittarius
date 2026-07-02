from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

reg = Register([
    Atom(0.0, 0.0, 0.0),
    Atom(0.5, 0.0, 0.0),
    Atom(1.0, 0.0, 0.0),
], C6=100.0)

sim = Simulation(
    reg,
    PulseSequence(omega=1.0, delta=0.0),
    SolverConfig(blockade_radius=0.6),
)

print(sim.validate())