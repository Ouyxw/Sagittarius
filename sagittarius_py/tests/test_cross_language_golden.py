import numpy as np

from sagittarius import Atom, PulseSequence, Register, Simulation, SolverConfig, validate_run_manifest
from sagittarius.api import (
    _constant_vector,
    _dense_hamiltonian_matrix,
    _reduced_basis_python,
    _reduced_hamiltonian_matrix,
)
from sagittarius.runtime import get_julia


def test_full_hamiltonian_matches_julia_native_api():
    reg = Register([Atom(0.0, 0.0), Atom(1.3, 0.0)], C6=2.5)
    omega = [0.2, 0.35]
    delta = [-0.1, 0.05]

    python_h = _dense_hamiltonian_matrix(reg, omega, delta)
    jl, _ = get_julia()
    julia_h = jl.seval("""
    begin
        using SparseArrays
        using StaticArrays
        reg = Sagittarius.Physics.Register([
            Sagittarius.Physics.Atom(SVector(0.0, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(1.3, 0.0, 0.0)),
        ], 2.5)
        Matrix(sparse(Sagittarius.Physics.RydbergHamiltonian(reg, [0.2, 0.35], [-0.1, 0.05])))
    end
    """)

    assert np.allclose(python_h, np.asarray(julia_h), atol=1e-12)


def test_reduced_basis_and_hamiltonian_match_julia_native_api():
    reg = Register.chain(3, spacing=0.5, C6=10.0)
    omega = [0.2, 0.3, 0.4]
    delta = [-0.1, 0.0, 0.2]
    blockade_radius = 0.6

    python_basis = _reduced_basis_python(reg, blockade_radius)
    python_h = _reduced_hamiltonian_matrix(reg, omega, delta, python_basis)

    jl, _ = get_julia()
    report = jl.seval("""
    begin
        using SparseArrays
        reg = Sagittarius.Physics.Register([
            Sagittarius.Physics.Atom(SVector(0.0, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(0.5, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(1.0, 0.0, 0.0)),
        ], 10.0)
        basis, mapping = Sagittarius.Physics.generate_reduced_basis(reg, 0.6)
        H = Matrix(sparse(Sagittarius.Physics.RydbergHamiltonian(
            reg, [0.2, 0.3, 0.4], [-0.1, 0.0, 0.2]; blockade_radius=0.6
        )))
        Dict("basis" => basis, "hamiltonian" => H)
    end
    """)

    assert list(report["basis"]) == python_basis == [0, 1, 2, 4, 5]
    assert np.allclose(python_h, np.asarray(report["hamiltonian"]), atol=1e-12)


def test_python_zero_based_local_addressing_matches_julia_one_based_order():
    reg = Register.chain(3, spacing=1.0)
    seq = PulseSequence(omega={0: 0.5, 2: 0.25}, delta={1: -0.2})

    assert _constant_vector(seq.omega, 3, field_name="omega") == [0.5, 0.0, 0.25]
    assert _constant_vector(seq.delta, 3, field_name="delta") == [0.0, -0.2, 0.0]

    python_h = _dense_hamiltonian_matrix(
        reg,
        _constant_vector(seq.omega, 3, field_name="omega"),
        _constant_vector(seq.delta, 3, field_name="delta"),
    )
    jl, _ = get_julia()
    julia_h = jl.seval("""
    begin
        using SparseArrays
        reg = Sagittarius.Physics.Register([
            Sagittarius.Physics.Atom(SVector(0.0, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(1.0, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(2.0, 0.0, 0.0)),
        ], 1.0)
        Matrix(sparse(Sagittarius.Physics.RydbergHamiltonian(
            reg, [0.5, 0.0, 0.25], [0.0, -0.2, 0.0]
        )))
    end
    """)

    assert np.allclose(python_h, np.asarray(julia_h), atol=1e-12)


def test_python_solver_observable_matches_direct_julia_solver_and_manifest_contract():
    reg = Register([Atom(0.0, 0.0), Atom(1.4, 0.0)], C6=1.5)
    seq = PulseSequence(omega=[0.15, 0.22], delta=[-0.03, 0.04])
    config = SolverConfig(reltol=1e-9, abstol=1e-9)
    psi0 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)

    result = Simulation(reg, seq, config).run(psi0, 0.0, 0.4, observables={"atom0": 0})
    validate_run_manifest(result.manifest)

    jl, _ = get_julia()
    direct = jl.seval("""
    begin
        using StaticArrays
        reg = Sagittarius.Physics.Register([
            Sagittarius.Physics.Atom(SVector(0.0, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(1.4, 0.0, 0.0)),
        ], 1.5)
        H_func = Sagittarius.Physics.build_hamiltonian_func(
            reg,
            t -> [0.15, 0.22],
            t -> [-0.03, 0.04],
        )
        psi0 = ComplexF64[1.0, 0.0, 0.0, 0.0]
        obs = Dict("atom0" => Sagittarius.Solver.RydbergPopulation(1, 2))
        sol, saved = Sagittarius.Solver.solve_schrodinger(
            psi0, H_func, SVector(0.0, 0.4); observables=obs, reltol=1e-9, abstol=1e-9
        )
        Dict("t" => collect(saved.t), "atom0" => [v[1] for v in saved.saveval])
    end
    """)

    assert np.allclose(result.data["t"], np.asarray(direct["t"]), atol=1e-12)
    assert np.allclose(result.data["atom0"], np.asarray(direct["atom0"]), atol=1e-10)
    assert result.manifest["register"]["atom_count"] == 2
    assert result.manifest["solver"]["blockade_radius"] == 0.0
    assert result.manifest["solver"]["observables"] == {"atom0": 0}
    assert result.manifest["initial_state"]["basis_size"] == 4
