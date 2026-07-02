from sagittarius import Atom, Register, Simulation, PulseSequence

reg = Register([Atom(0, 0, 0), Atom(5, 0, 0)])
sim = Simulation(reg, PulseSequence(omega={0: 1.0, 1: 0.0}))
sim.validate_inputs(sample_time=0.0, observables={"atom0": 0, "atom1": 1})
print(sim.validate)