import pytest
import numpy as np
from sagittarius import Atom, Register, solve, PulseSequence, SolverConfig, Constant, Ramp, Piecewise

def test_single_atom_rabi():
    """Verify single atom oscillates correctly under a constant Omega."""
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    psi0 = np.array([1.0, 0.0], dtype=complex) # |g>
    
    # Omega = 2pi * 1.0 (Rabi freq of 1.0 Hz)
    # At t = 0.5s, we expect full inversion to |r>
    omega = 2.0 * np.pi * 1.0
    seq = PulseSequence(omega=omega, delta=0.0)
    results = solve(reg, seq, psi0=psi0, t_start=0.0, t_end=0.5, observables={"pop": 0})
    
    final_pop_rydberg = results["pop"][-1]
    # At t=0.5, Rydberg population should be 1.0
    assert np.isclose(final_pop_rydberg, 1.0, atol=1e-2)

def test_two_atom_blockade():
    """Verify Rydberg blockade prevents simultaneous excitation."""
    # Atoms very close (dist=0.5) with strong C6=100
    reg = Register([Atom(0, 0, 0), Atom(0.5, 0, 0)], C6=100.0)
    
    # Pruned Basis with radius 1.0: [|gg>, |rg>, |gr>] (3 states)
    # |rr> is removed.
    psi0 = np.array([1, 0, 0], dtype=complex)
    
    omega = 2.0 * np.pi * 1.0
    seq = PulseSequence(omega=omega, delta=0.0)
    config = SolverConfig(blockade_radius=1.0)
    results = solve(reg, seq, config=config, psi0=psi0, t_start=0.0, t_end=1.0, observables={"a1": 0, "a2": 1})
    
    p1 = np.array(results["a1"])
    p2 = np.array(results["a2"])
    total_pop = p1 + p2
    
    # Total population should not exceed 1.0 (since |rr> is gone)
    assert np.max(total_pop) <= 1.0001

def test_piecewise_pulse_transition():
    """Verify AST Piecewise pulse correctly transitions from zero to driving."""
    reg = Register([Atom(0, 0, 0)], C6=0.0)
    psi0 = np.array([1, 0], dtype=complex)
    
    # Pulse sequence: Zero for 1.0s, then Constant for 0.5s
    # Total time 1.5s
    pulse = Piecewise([
        Constant(0.0, duration=1.0),
        Constant(2.0 * np.pi * 1.0, duration=0.5)
    ])
    
    seq = PulseSequence(omega=pulse, delta=0.0)
    results = solve(reg, seq, psi0=psi0, t_start=0.0, t_end=1.5, observables={"pop": 0})
    
    # Check that at t=1.0, Rydberg population is still 0.0 (no excitation during zero pulse)
    t = np.array(results["t"])
    idx_1s = np.argmin(np.abs(t - 1.0))
    assert np.isclose(results["pop"][idx_1s], 0.0, atol=1e-3)
    
    # Check that at t=1.5 (after 0.5s of driving), Rydberg population is high (~1.0)
    assert results["pop"][-1] > 0.95


def test_full_sparse_pattern_reuses_structure_when_pulses_change():
    from sagittarius.runtime import get_julia

    jl, _ = get_julia()
    report = jl.seval("""
    begin
        using SparseArrays
        using StaticArrays
        reg = Sagittarius.Physics.Register([
            Sagittarius.Physics.Atom(SVector(0.0, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(1.5, 0.0, 0.0)),
        ], 2.0)
        H_func = Sagittarius.Physics.build_hamiltonian_func(
            reg,
            t -> [1.0 + t, 2.0],
            t -> [0.0, t];
            blockade_radius=0.0,
        )

        op = H_func(0.0)
        H1 = sparse(op)
        matrix_id = objectid(H1)
        colptr_id = objectid(H1.colptr)
        rowval_id = objectid(H1.rowval)
        old_values = copy(H1.nzval)

        H_func(0.5)
        H2 = sparse(op)
        fresh = sparse(Sagittarius.Physics.RydbergHamiltonian(reg, [1.5, 2.0], [0.0, 0.5]))

        Dict(
            "same_matrix" => objectid(H2) == matrix_id,
            "same_colptr" => objectid(H2.colptr) == colptr_id,
            "same_rowval" => objectid(H2.rowval) == rowval_id,
            "values_changed" => old_values != H2.nzval,
            "matches_fresh" => Matrix(H2) ≈ Matrix(fresh),
        )
    end
    """)

    assert report["same_matrix"] is True
    assert report["same_colptr"] is True
    assert report["same_rowval"] is True
    assert report["values_changed"] is True
    assert report["matches_fresh"] is True


def test_reduced_basis_cache_reuses_basis_by_adjacency_radius_and_atom_count():
    from sagittarius.runtime import get_julia

    jl, _ = get_julia()
    report = jl.seval("""
    begin
        using StaticArrays
        Sagittarius.Physics._clear_reduced_basis_cache!()

        reg1 = Sagittarius.Physics.Register([
            Sagittarius.Physics.Atom(SVector(0.0, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(0.5, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(1.5, 0.0, 0.0)),
        ], 10.0)
        reg_same_graph = Sagittarius.Physics.Register([
            Sagittarius.Physics.Atom(SVector(10.0, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(10.5, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(11.5, 0.0, 0.0)),
        ], 20.0)

        basis1, mapping1 = Sagittarius.Physics.generate_reduced_basis(reg1, 0.75)
        cache_after_first = Sagittarius.Physics._reduced_basis_cache_size()
        basis2, mapping2 = Sagittarius.Physics.generate_reduced_basis(reg1, 0.75)
        cache_after_second = Sagittarius.Physics._reduced_basis_cache_size()
        basis3, mapping3 = Sagittarius.Physics.generate_reduced_basis(reg_same_graph, 0.75)
        cache_after_same_graph = Sagittarius.Physics._reduced_basis_cache_size()
        basis4, mapping4 = Sagittarius.Physics.generate_reduced_basis(reg1, 1.25)
        cache_after_new_radius = Sagittarius.Physics._reduced_basis_cache_size()

        Dict(
            "same_register_basis_reused" => basis1 === basis2,
            "same_register_mapping_reused" => mapping1 === mapping2,
            "same_graph_basis_reused" => basis1 === basis3,
            "same_graph_mapping_reused" => mapping1 === mapping3,
            "new_radius_basis_separated" => basis1 !== basis4,
            "cache_after_first" => cache_after_first,
            "cache_after_second" => cache_after_second,
            "cache_after_same_graph" => cache_after_same_graph,
            "cache_after_new_radius" => cache_after_new_radius,
            "basis_values" => basis1,
        )
    end
    """)

    assert report["same_register_basis_reused"] is True
    assert report["same_register_mapping_reused"] is True
    assert report["same_graph_basis_reused"] is True
    assert report["same_graph_mapping_reused"] is True
    assert report["new_radius_basis_separated"] is True
    assert report["cache_after_first"] == 1
    assert report["cache_after_second"] == 1
    assert report["cache_after_same_graph"] == 1
    assert report["cache_after_new_radius"] == 2
    assert list(report["basis_values"]) == [0, 1, 2, 4, 5, 6]


def test_reduced_sparse_pattern_reuses_structure_when_pulses_change():
    from sagittarius.runtime import get_julia

    jl, _ = get_julia()
    report = jl.seval("""
    begin
        using SparseArrays
        using StaticArrays
        reg = Sagittarius.Physics.Register([
            Sagittarius.Physics.Atom(SVector(0.0, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(0.5, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(1.0, 0.0, 0.0)),
        ], 10.0)
        H_func = Sagittarius.Physics.build_hamiltonian_func(
            reg,
            t -> [1.0 + t, 2.0, 3.0],
            t -> [0.0, t, 0.2];
            blockade_radius=0.75,
        )

        op = H_func(0.0)
        H1 = sparse(op)
        matrix_id = objectid(H1)
        colptr_id = objectid(H1.colptr)
        rowval_id = objectid(H1.rowval)
        old_values = copy(H1.nzval)

        H_func(0.5)
        H2 = sparse(op)
        fresh = sparse(Sagittarius.Physics.RydbergHamiltonian(
            reg, [1.5, 2.0, 3.0], [0.0, 0.5, 0.2]; blockade_radius=0.75
        ))

        Dict(
            "same_matrix" => objectid(H2) == matrix_id,
            "same_colptr" => objectid(H2.colptr) == colptr_id,
            "same_rowval" => objectid(H2.rowval) == rowval_id,
            "values_changed" => old_values != H2.nzval,
            "matches_fresh" => Matrix(H2) ≈ Matrix(fresh),
        )
    end
    """)

    assert report["same_matrix"] is True
    assert report["same_colptr"] is True
    assert report["same_rowval"] is True
    assert report["values_changed"] is True
    assert report["matches_fresh"] is True


def test_gpu_sparse_value_copy_reuses_existing_value_buffer():
    from sagittarius.runtime import get_julia

    jl, _ = get_julia()
    report = jl.seval("""
    begin
        using SparseArrays
        mutable struct FakeGpuSparseForReuseTest
            nzVal::Vector{ComplexF64}
        end

        cpu_sparse = sparse(ComplexF64[1 0; 2 3])
        fake = FakeGpuSparseForReuseTest(zeros(ComplexF64, length(cpu_sparse.nzval)))
        value_buffer_id = objectid(fake.nzVal)
        updated = Sagittarius.Solver._copy_sparse_values_to_gpu!(fake, cpu_sparse)

        Dict(
            "same_object" => updated === fake,
            "same_value_buffer" => objectid(fake.nzVal) == value_buffer_id,
            "values_match" => fake.nzVal == cpu_sparse.nzval,
        )
    end
    """)

    assert report["same_object"] is True
    assert report["same_value_buffer"] is True
    assert report["values_match"] is True


def test_reduced_gpu_sparse_cache_survives_value_only_pulse_updates():
    from sagittarius.runtime import get_julia

    jl, _ = get_julia()
    report = jl.seval("""
    begin
        using StaticArrays
        sentinel = Ref("gpu-buffer-sentinel")
        reg = Sagittarius.Physics.Register([
            Sagittarius.Physics.Atom(SVector(0.0, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(0.5, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(1.0, 0.0, 0.0)),
        ], 10.0)
        H_func = Sagittarius.Physics.build_hamiltonian_func(
            reg,
            t -> [1.0 + t, 2.0, 3.0],
            t -> [0.0, t, 0.2];
            blockade_radius=0.75,
            use_gpu=true,
        )

        op = H_func(0.0)
        op.cached_sparse_H = sentinel
        H_func(0.5)

        Dict(
            "same_gpu_cache" => op.cached_sparse_H === sentinel,
            "omega_updated" => op.Ω == [1.5, 2.0, 3.0],
            "delta_updated" => op.Δ == [0.0, 0.5, 0.2],
        )
    end
    """)

    assert report["same_gpu_cache"] is True
    assert report["omega_updated"] is True
    assert report["delta_updated"] is True

if __name__ == "__main__":
    test_single_atom_rabi()
    test_two_atom_blockade()
    test_piecewise_pulse_transition()
    print("All physics tests passed!")
