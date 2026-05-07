import pytest
import numpy as np
import pandas as pd
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig, Constant

def test_simulation_object_api():
    """Verify the new Simulation/SimulationResult API works as expected."""
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    psi0 = np.array([1.0, 0.0], dtype=complex)
    
    # Setup using new classes
    seq = PulseSequence(omega=2.0 * np.pi * 1.0)
    cfg = SolverConfig(reltol=1e-7)
    
    sim = Simulation(reg, seq, cfg)
    
    # Run simulation
    results = sim.run(psi0, 0.0, 0.5, observables={"pop": 0})
    
    # Check Result object
    assert hasattr(results, 'to_pandas')
    assert hasattr(results, 'plot')
    
    # Check data accuracy (Rabi flip at t=0.5)
    df = results.to_pandas()
    assert isinstance(df, pd.DataFrame)
    assert "pop" in df.columns
    assert "t" in df.columns
    assert np.isclose(df["pop"].iloc[-1], 1.0, atol=1e-2)

def test_simulation_validation():
    """Verify that validation correctly calculates basis size."""
    # 3 atoms with blockade
    reg = Register([Atom(0, 0, 0), Atom(0.5, 0, 0), Atom(1.0, 0, 0)], C6=100.0)
    seq = PulseSequence(omega=1.0)
    
    # No blockade: 2^3 = 8 states
    sim_full = Simulation(reg, seq, SolverConfig(blockade_radius=0.0))
    assert sim_full.validate() == 8
    
    # With blockade (radius 0.6): [|ggg>, |rgr>, |rgg>, |grg>, |ggr>] -> 5 states
    sim_reduced = Simulation(reg, seq, SolverConfig(blockade_radius=0.6))
    assert sim_reduced.validate() == 5

def test_simulation_plot_no_error():
    """Ensure the plot method doesn't crash (mocking plt.show)."""
    import matplotlib.pyplot as plt
    from unittest.mock import patch
    
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    psi0 = np.array([1, 0], dtype=complex)
    sim = Simulation(reg, PulseSequence(omega=1.0))
    results = sim.run(psi0, 0.0, 0.1, observables={"pop": 0})
    
    with patch("matplotlib.pyplot.show"):
        results.plot(show=True)
