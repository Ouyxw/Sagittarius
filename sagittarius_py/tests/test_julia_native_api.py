import numpy as np

from sagittarius.runtime import get_julia


def test_julia_native_api_exports_register_basis_hamiltonian_and_solver():
    jl, _ = get_julia()
    report = jl.seval("""
    begin
        using SparseArrays
        reg = Sagittarius.chain_register(3; spacing=0.5, C6=10.0)
        b = Sagittarius.basis(reg; blockade_radius=0.6)
        rbasis, mapping = Sagittarius.reduced_basis(reg; blockade_radius=0.6)
        H = Sagittarius.hamiltonian(reg, [0.2, 0.3, 0.4], [-0.1, 0.0, 0.2]; blockade_radius=0.6)
        Hs = Matrix(sparse(H))
        H_func = Sagittarius.hamiltonian_func(
            reg,
            t -> [0.2, 0.3, 0.4],
            t -> [-0.1, 0.0, 0.2];
            blockade_radius=0.6,
        )
        psi0 = ComplexF64[1.0, 0.0, 0.0, 0.0, 0.0]
        obs = Dict("atom1" => Sagittarius.RydbergPopulation(1, 3; basis=rbasis))
        sol, saved = Sagittarius.solve_schrodinger(
            psi0,
            H_func,
            (0.0, 0.2);
            observables=obs,
            reltol=1e-9,
            abstol=1e-9,
        )
        jumps = Sagittarius.get_jump_operators(3, 0.1, 0.0; basis=rbasis, mapping=mapping)
        Dict(
            "basis" => b,
            "reduced_basis" => rbasis,
            "hamiltonian_type" => string(typeof(H)),
            "hamiltonian_size" => collect(size(Hs)),
            "saved_count" => length(saved.t),
            "jump_count" => length(jumps),
        )
    end
    """)

    assert list(report["basis"]) == [0, 1, 2, 4, 5]
    assert list(report["reduced_basis"]) == [0, 1, 2, 4, 5]
    assert "ReducedRydbergOperator" in report["hamiltonian_type"]
    assert list(report["hamiltonian_size"]) == [5, 5]
    assert report["saved_count"] > 0
    assert report["jump_count"] == 3


def test_julia_native_api_coordinate_constructors_and_lattice_helpers():
    jl, _ = get_julia()
    report = jl.seval("""
    begin
        atom = Sagittarius.Atom(1.0, 2.0)
        reg_from_tuples = Sagittarius.Register([(0.0, 0.0), (1.0, 0.0)]; C6=2.0)
        reg_from_vectors = Sagittarius.Register([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]; C6=3.0)
        lattice = Sagittarius.square_lattice_register(2, 2; spacing=1.5, C6=4.0, plane=:xy)
        Dict(
            "atom_coords" => collect(atom.coords),
            "tuple_atom_count" => length(reg_from_tuples.atoms),
            "tuple_c6" => reg_from_tuples.C6,
            "vector_atom_count" => length(reg_from_vectors.atoms),
            "vector_c6" => reg_from_vectors.C6,
            "lattice_atom_count" => length(lattice.atoms),
            "lattice_last" => collect(lattice.atoms[end].coords),
        )
    end
    """)

    assert np.allclose(report["atom_coords"], [1.0, 2.0, 0.0])
    assert report["tuple_atom_count"] == 2
    assert report["tuple_c6"] == 2.0
    assert report["vector_atom_count"] == 2
    assert report["vector_c6"] == 3.0
    assert report["lattice_atom_count"] == 4
    assert np.allclose(report["lattice_last"], [1.5, 1.5, 0.0])


def test_julia_native_api_validates_constructor_inputs():
    jl, _ = get_julia()
    message = jl.seval("""
    begin
        try
            Sagittarius.chain_register(0)
            "missing validation"
        catch err
            sprint(showerror, err)
        end
    end
    """)

    assert "n must be positive" in message
