from sagittarius import Atom, Register, Simulation, PulseSequence

reg = Register([Atom(0, 0, 0), Atom(5, 0, 0)])
sim = Simulation(reg, PulseSequence(omega=[1.0]))

try:
    sim.validate_inputs(sample_time=0.0)
except ValueError as exc:
    print(exc)