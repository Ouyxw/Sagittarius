import pytest
import numpy as np
import pandas as pd
from sagittarius import Atom, Register, RUN_MANIFEST_SCHEMA_VERSION, Simulation, PulseSequence, SolverConfig, Constant, validate_run_manifest

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
    validate_run_manifest(results.manifest)
    assert results.manifest["schema_version"] == RUN_MANIFEST_SCHEMA_VERSION
    assert results.manifest["result_type"] == "observables"
    assert results.manifest["register"]["atom_count"] == 1
    assert results.manifest["solver"]["observables"] == {"pop": 0}

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


def test_simulation_forwards_blockade_radius_to_julia_solver(monkeypatch):
    import sagittarius.api as api

    calls = {}

    class FakeRegister:
        atoms = [object(), object()]

        @property
        def jl_obj(self):
            return self

        def geometry_summary(self, **kwargs):
            calls["geometry"] = kwargs
            return {"atom_count": 2}

    class FakeContext:
        basis = [0, 1]
        mapping = {0: 0, 1: 1}

    class FakePhys:
        def reduced_basis_context(self, reg, *, blockade_radius):
            calls["basis_radius"] = blockade_radius
            return FakeContext()

        def build_hamiltonian_func(self, reg, omega_func, delta_func, **kwargs):
            calls["hamiltonian"] = kwargs
            return lambda t: None

    class FakeSolver:
        def solve_schrodinger(self, psi0, h_func, tspan, **kwargs):
            calls["solver"] = kwargs
            return "raw-result"

    class FakeVectorFactory:
        def __getitem__(self, dtype):
            return lambda values: list(values)

    class FakeJL:
        ComplexF64 = complex
        Vector = FakeVectorFactory()

        def SVector(self, *values):
            return tuple(values)

    monkeypatch.setattr(api, "doctor", lambda backend: {"requested_backend": backend})
    monkeypatch.setattr(api, "get_modules", lambda: (FakeJL(), None, FakePhys(), FakeSolver()))
    monkeypatch.setattr(api.Simulation, "_get_compiled_func", lambda self, pulse, n: (lambda t: [0.0] * n))

    sim = api.Simulation(FakeRegister(), api.PulseSequence(), api.SolverConfig(blockade_radius=0.6))
    result = sim.run(np.array([1.0, 0.0], dtype=complex), 0.0, 0.1)

    assert result == "raw-result"
    assert calls["basis_radius"] == 0.6
    assert calls["hamiltonian"]["blockade_radius"] == 0.6
    assert calls["solver"]["blockade_radius"] == 0.6
