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



def test_saveat_count_sets_stable_observable_grid():
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    psi0 = np.array([1.0, 0.0], dtype=complex)
    cfg = SolverConfig(saveat=5)
    sim = Simulation(reg, PulseSequence(omega=1.0), cfg)

    result = sim.run(psi0, 0.0, 1.0, observables={"pop": 0})

    assert np.allclose(result.data["t"], np.linspace(0.0, 1.0, 5))
    assert result.manifest["solver"]["saveat"] == 5
    assert np.allclose(result.manifest["solver"]["effective_saveat"], np.linspace(0.0, 1.0, 5))
    assert result.diagnostics["simulation"]["saveat"] == 5
    assert np.allclose(result.diagnostics["simulation"]["effective_saveat"], np.linspace(0.0, 1.0, 5))


def test_saveat_explicit_grid_sets_stable_observable_grid():
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    psi0 = np.array([1.0, 0.0], dtype=complex)
    grid = [0.0, 0.25, 0.75, 1.0]
    cfg = SolverConfig(saveat=grid)
    sim = Simulation(reg, PulseSequence(omega=1.0), cfg)

    result = sim.run(psi0, 0.0, 1.0, observables={"pop": 0})

    assert np.allclose(result.data["t"], grid)
    assert result.manifest["solver"]["saveat"] == grid
    assert result.manifest["solver"]["effective_saveat"] == grid


def test_invalid_seed_and_saveat_fail_validation():
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    psi0 = np.array([1.0, 0.0], dtype=complex)

    with pytest.raises(Exception) as seed_exc:
        Simulation(reg, PulseSequence(), SolverConfig(seed=-1)).run(psi0, 0.0, 1.0, observables={"pop": 0})
    assert seed_exc.value.issue.code == "VALIDATION_RANDOM_SEED_VALUE"

    with pytest.raises(Exception) as saveat_exc:
        Simulation(reg, PulseSequence(), SolverConfig(saveat=[0.0, 0.5, 0.5])).run(psi0, 0.0, 1.0, observables={"pop": 0})
    assert saveat_exc.value.issue.code == "VALIDATION_SAVEAT_GRID_ORDER"


def test_seed_and_saveat_forwarded_to_mcwf_solver(monkeypatch):
    import sagittarius.api as api

    calls = {}

    class FakeAtom:
        x = 0.0
        y = 0.0
        z = 0.0

    class FakeRegister:
        atoms = [FakeAtom()]
        C6 = 0.0

        @property
        def jl_obj(self):
            return self

        def geometry_summary(self, **kwargs):
            return {"atom_count": 1}

    class FakePhys:
        def build_hamiltonian_func(self, reg, omega_func, delta_func, **kwargs):
            return lambda t: None

        def get_jump_operators(self, n, gamma, gamma_phi):
            return ["jump"]

    class FakeSolver:
        def RydbergPopulation(self, atom_idx, n, **kwargs):
            return lambda state, t, integrator: 0.0

        def solve_mc_trajectories(self, psi0, h_func, j_ops, tspan, **kwargs):
            calls.update(kwargs)
            return ([0.0, 0.5, 1.0], [[0.0], [0.1], [0.2]])

    class FakeVectorFactory:
        def __getitem__(self, dtype):
            return lambda values: list(values)

    class FakeJL:
        Any = object
        ComplexF64 = complex
        Float64 = float
        Vector = FakeVectorFactory()

        def SVector(self, *values):
            return tuple(values)

    monkeypatch.setattr(api, "doctor", lambda backend: {"requested_backend": backend})
    monkeypatch.setattr(api, "version_info", lambda: {"schema_version": "version-info/v1"})
    monkeypatch.setattr(api, "get_modules", lambda: (FakeJL(), None, FakePhys(), FakeSolver()))
    monkeypatch.setattr(api.Simulation, "_get_compiled_func", lambda self, pulse, n: (lambda t: [0.0] * n))

    cfg = api.SolverConfig(gamma=0.1, use_mc=True, seed=123, saveat=3)
    sim = api.Simulation(FakeRegister(), api.PulseSequence(), cfg)
    result = sim.run(np.array([1.0, 0.0], dtype=complex), 0.0, 1.0, observables={"pop": 0})

    assert calls["seed"] == 123
    assert np.allclose(calls["saveat"], [0.0, 0.5, 1.0])
    assert result.manifest["random"] == {"seed": 123, "effective_seed": 123, "n_trajectories": 100}
    assert result.manifest["solver"]["saveat"] == 3
    assert np.allclose(result.manifest["solver"]["effective_saveat"], [0.0, 0.5, 1.0])
