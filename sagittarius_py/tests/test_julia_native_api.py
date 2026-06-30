import numpy as np

from sagittarius.runtime import get_julia


def test_julia_native_api_exports_register_basis_hamiltonian_and_solver():
    jl, _ = get_julia()
    report = jl.seval("""
    begin
        using SparseArrays
        reg = Sagittarius.chain_register(3; spacing=0.5, C6=10.0)
        b = Sagittarius.basis(reg; blockade_radius=0.6)
        context = Sagittarius.reduced_basis_context(reg; blockade_radius=0.6)
        rbasis, mapping = Sagittarius.reduced_basis(reg; blockade_radius=0.6)
        H = Sagittarius.hamiltonian(reg, [0.2, 0.3, 0.4], [-0.1, 0.0, 0.2]; basis_context=context)
        Hs = Matrix(sparse(H))
        H_func = Sagittarius.hamiltonian_func(
            reg,
            t -> [0.2, 0.3, 0.4],
            t -> [-0.1, 0.0, 0.2];
            basis_context=context,
        )
        psi0 = ComplexF64[1.0, 0.0, 0.0, 0.0, 0.0]
        obs = Dict("atom1" => Sagittarius.RydbergPopulation(1, 3; basis_context=context))
        sol, saved = Sagittarius.solve_schrodinger(
            psi0,
            H_func,
            (0.0, 0.2);
            observables=obs,
            reltol=1e-9,
            abstol=1e-9,
        )
        jumps = Sagittarius.get_jump_operators(3, 0.1, 0.0; basis_context=context)
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


def test_julia_basis_context_is_shared_by_hamiltonian_observable_and_jumps():
    jl, _ = get_julia()
    report = jl.seval("""
    begin
        reg = Sagittarius.chain_register(3; spacing=0.5, C6=10.0)
        context = Sagittarius.reduced_basis_context(reg; blockade_radius=0.6)
        H = Sagittarius.hamiltonian(reg, [0.2, 0.3, 0.4], [0.0, 0.0, 0.0]; basis_context=context)
        obs = Sagittarius.RydbergPopulation(1, 3; basis_context=context)
        jumps = Sagittarius.get_jump_operators(3, 0.1, 0.0; basis_context=context)
        psi = ComplexF64[0.0, 1.0, 0.0, 0.0, 0.0]
        Dict(
            "same_context" => H.basis_context === context,
            "same_basis" => H.basis === context.basis,
            "same_mapping" => H.mapping === context.mapping,
            "observable_value" => obs(psi, 0.0, nothing),
            "jump_size" => collect(size(jumps[1])),
        )
    end
    """)

    assert report["same_context"] is True
    assert report["same_basis"] is True
    assert report["same_mapping"] is True
    assert report["observable_value"] == 1.0
    assert list(report["jump_size"]) == [5, 5]



def test_julia_native_diagonal_observable_constructors_for_vector_and_density_matrix():
    jl, _ = get_julia()
    report = jl.seval("""
    begin
        psi = zeros(ComplexF64, 8)
        psi[6] = 1.0 # bitstring 5 == atoms 1 and 3 excited
        rho = psi * psi'
        obs = Dict(
            "total" => Sagittarius.TotalRydbergPopulation(3),
            "pair13" => Sagittarius.PairCorrelation([1, 3], 3),
            "connected13" => Sagittarius.ConnectedPairCorrelation([1, 3], 3),
            "violations" => Sagittarius.BlockadeViolation([[1, 3], [2, 3]], 3),
            "target" => Sagittarius.BitstringProbability(5, 3),
            "cost" => Sagittarius.MWISCost([1.0, 2.0, 4.0], [[1, 3]], 10.0, 3),
            "z2" => Sagittarius.PauliZ(2, 3),
            "zz13" => Sagittarius.PauliZZ([1, 3], 3),
            "parity" => Sagittarius.Parity([1, 2, 3], 3),
        )
        Dict(
            "vector" => Dict(k => f(psi, 0.0, nothing) for (k, f) in obs),
            "density" => Dict(k => f(rho, 0.0, nothing) for (k, f) in obs),
        )
    end
    """)

    expected = {
        "total": 2.0,
        "pair13": 1.0,
        "connected13": 0.0,
        "violations": 1.0,
        "target": 1.0,
        "cost": -5.0,
        "z2": 1.0,
        "zz13": 1.0,
        "parity": 1.0,
    }
    assert dict(report["vector"]) == expected
    assert dict(report["density"]) == expected


def test_julia_solver_algorithm_resolver_whitelist():
    jl, _ = get_julia()
    report = jl.seval("""
    begin
        ok_messages = String[]
        for expr in (
            () -> Sagittarius.resolve_solver_algorithm("Bogus"),
            () -> Sagittarius.resolve_solver_algorithm("RK4"; adaptive=true),
            () -> Sagittarius.resolve_solver_algorithm("Tsit5"; adaptive=true, dt=0.01),
        )
            try
                expr()
                push!(ok_messages, "missing error")
            catch err
                push!(ok_messages, sprint(showerror, err))
            end
        end
        Dict(
            "tsit5" => string(typeof(Sagittarius.resolve_solver_algorithm("Tsit5"))),
            "vern9" => string(typeof(Sagittarius.resolve_solver_algorithm("Vern9"))),
            "rk4" => string(typeof(Sagittarius.resolve_solver_algorithm("RK4"; adaptive=false, dt=0.001))),
            "errors" => ok_messages,
        )
    end
    """)

    assert "Tsit5" in report["tsit5"]
    assert "Vern9" in report["vern9"]
    assert "RK4" in report["rk4"]
    assert "unsupported solver method" in report["errors"][0]
    assert "adaptive=false" in report["errors"][1]
    assert "dt=nothing" in report["errors"][2]
