module Physics

using LinearAlgebra
using SparseArrays
using StaticArrays

export Atom, Register, RydbergHamiltonian, generate_reduced_basis, ReducedRydbergOperator, build_hamiltonian_func, get_jump_operators

struct Atom
    coords::SVector{3, Float64}
end

struct Register
    atoms::Vector{Atom}
    C6::Float64
end

function interaction_matrix(reg::Register)
    N = length(reg.atoms)
    V = zeros(N, N)
    for i in 1:N
        for j in i+1:N
            r = norm(reg.atoms[i].coords - reg.atoms[j].coords)
            V[i, j] = V[j, i] = reg.C6 / r^6
        end
    end
    return V
end

"""
    RydbergOperator

A matrix-free representation of the Rydberg Hamiltonian.
H = Σ (Ω_i/2 σx_i) - Σ (Δ_i n_i) + Σ (V_ij n_i n_j)
"""
mutable struct RydbergOperator
    N::Int
    Ω::Vector{Float64} # Local Rabi frequency
    Δ::Vector{Float64} # Local Detuning
    V::Matrix{Float64} # Interaction matrix
    cached_sparse_cpu::Union{Nothing, SparseMatrixCSC{ComplexF64, Int}}
end

function RydbergOperator(N, Ω, Δ, V)
    return RydbergOperator(N, Ω, Δ, V, nothing)
end

# Define how this operator acts on a vector ψ
function Base.:*(op::RydbergOperator, ψ::Vector{ComplexF64})
    res = zero(ψ)
    N = op.N
    
    for i in 0:(2^N - 1)
        if ψ[i+1] == 0 continue end
        
        # 1. Detuning & Interaction (Diagonal terms)
        diagonal = 0.0
        for j in 1:N
            if (i & (1 << (j-1))) != 0
                diagonal -= op.Δ[j]  # Local Detuning
                
                # Interaction V_jk n_j n_k
                for k in j+1:N
                    if (i & (1 << (k-1))) != 0
                        diagonal += op.V[j, k]
                    end
                end
            end
        end
        res[i+1] += diagonal * ψ[i+1]
        
        # 2. Driving (Off-diagonal terms σx)
        for j in 1:N
            # Flip the j-th bit to find the coupled state
            target = i ⊻ (1 << (j-1))
            res[target+1] += (op.Ω[j] / 2.0) * ψ[i+1]
        end
    end
    return res
end

function _full_diagonal_value(op::RydbergOperator, state::Int)
    diagonal = 0.0
    for j in 1:op.N
        if (state & (1 << (j-1))) != 0
            diagonal -= op.Δ[j]
            for k in j+1:op.N
                if (state & (1 << (k-1))) != 0
                    diagonal += op.V[j, k]
                end
            end
        end
    end
    return diagonal
end

function _full_sparse_value(op::RydbergOperator, row_idx::Int, col_idx::Int)
    col_state = col_idx - 1
    row_state = row_idx - 1
    if row_idx == col_idx
        return ComplexF64(_full_diagonal_value(op, col_state))
    end

    flipped = row_state ⊻ col_state
    if flipped != 0 && (flipped & (flipped - 1)) == 0
        atom_idx = trailing_zeros(flipped) + 1
        return ComplexF64(op.Ω[atom_idx] / 2.0)
    end
    return 0.0 + 0.0im
end

function _build_full_sparse_cache(op::RydbergOperator)
    dim = 2^op.N
    colptr = Vector{Int}(undef, dim + 1)
    rowval = Int[]
    nzval = ComplexF64[]
    colptr[1] = 1

    for col_idx in 1:dim
        state = col_idx - 1
        rows = Int[col_idx]
        for j in 1:op.N
            push!(rows, (state ⊻ (1 << (j-1))) + 1)
        end
        sort!(rows)
        unique!(rows)
        for row_idx in rows
            push!(rowval, row_idx)
            push!(nzval, _full_sparse_value(op, row_idx, col_idx))
        end
        colptr[col_idx + 1] = length(rowval) + 1
    end

    return SparseMatrixCSC(dim, dim, colptr, rowval, nzval)
end

function _update_full_sparse_cache!(op::RydbergOperator)
    H = op.cached_sparse_cpu
    isnothing(H) && return
    for col_idx in 1:size(H, 2)
        for ptr in H.colptr[col_idx]:(H.colptr[col_idx + 1] - 1)
            row_idx = H.rowval[ptr]
            H.nzval[ptr] = _full_sparse_value(op, row_idx, col_idx)
        end
    end
end

function SparseArrays.sparse(op::RydbergOperator)
    if isnothing(op.cached_sparse_cpu)
        op.cached_sparse_cpu = _build_full_sparse_cache(op)
    else
        _update_full_sparse_cache!(op)
    end
    return op.cached_sparse_cpu
end

"""
    ReducedRydbergOperator

A Hamiltonian operator that acts on a truncated Hilbert space.
`basis` is a Vector of bitstrings (Int) representing valid states.
`mapping` is a Dictionary (or lookup table) from bitstring to its index in the reduced basis.
"""
mutable struct ReducedRydbergOperator
    N::Int
    Ω::Vector{Float64}
    Δ::Vector{Float64}
    V::Matrix{Float64}
    basis::Vector{Int}
    mapping::Dict{Int, Int}
    use_gpu::Bool
    cached_sparse_H::Any
    cached_sparse_cpu::Union{Nothing, SparseMatrixCSC{ComplexF64, Int}}
end

# Constructor with default values
function ReducedRydbergOperator(N, Ω, Δ, V, basis, mapping; use_gpu=false)
    return ReducedRydbergOperator(N, Ω, Δ, V, basis, mapping, use_gpu, nothing, nothing)
end

function generate_reduced_basis(reg::Register, blockade_radius::Float64)
    N = length(reg.atoms)
    # 1. Build adjacency list for the blockade graph
    adj = [Int[] for _ in 1:N]
    for i in 1:N, j in i+1:N
        if norm(reg.atoms[i].coords - reg.atoms[j].coords) < blockade_radius
            push!(adj[i], j)
            push!(adj[j], i)
        end
    end

    # 2. Recursive search for all valid independent sets (basis states)
    basis = Int[]
    
    function find_states(current_atom, current_state)
        if current_atom > N
            push!(basis, current_state)
            return
        end
        
        # Option 1: Current atom is in ground state |g> (0)
        find_states(current_atom + 1, current_state)
        
        # Option 2: Current atom is in Rydberg state |r> (1)
        # Only allowed if no neighbors are already in state |r>
        can_be_rydberg = true
        for neighbor in adj[current_atom]
            if neighbor < current_atom && (current_state & (1 << (neighbor - 1))) != 0
                can_be_rydberg = false
                break
            end
        end
        
        if can_be_rydberg
            find_states(current_atom + 1, current_state | (1 << (current_atom - 1)))
        end
    end
    
    find_states(1, 0)
    sort!(basis)
    
    mapping = Dict(state => i for (i, state) in enumerate(basis))
    return basis, mapping
end

function Base.:*(op::ReducedRydbergOperator, ψ::Vector{ComplexF64})
    res = zero(ψ)
    N = op.N

    # We iterate only over the valid basis states
    for (idx, state) in enumerate(op.basis)
        if ψ[idx] == 0 continue end

        # 1. Diagonal terms (Detuning & Interaction)
        # Interaction is only for pairs NOT blockade (which still have some V_ij)
        diagonal = 0.0
        for j in 1:N
            if (state & (1 << (j-1))) != 0
                diagonal -= op.Δ[j]
                for k in j+1:N
                    if (state & (1 << (k-1))) != 0
                        diagonal += op.V[j, k]
                    end
                end
            end
        end
        res[idx] += diagonal * ψ[idx]

        # 2. Off-diagonal terms (Driving σx)
        for j in 1:N
            target_state = state ⊻ (1 << (j-1))
            # Only transition if the target state is in our reduced basis
            if haskey(op.mapping, target_state)
                target_idx = op.mapping[target_state]
                res[target_idx] += (op.Ω[j] / 2.0) * ψ[idx]
            end
        end
    end
    return res
end

function _reduced_diagonal_value(op::ReducedRydbergOperator, state::Int)
    diagonal = 0.0
    for j in 1:op.N
        if (state & (1 << (j-1))) != 0
            diagonal -= op.Δ[j]
            for k in j+1:op.N
                if (state & (1 << (k-1))) != 0
                    diagonal += op.V[j, k]
                end
            end
        end
    end
    return diagonal
end

function _reduced_sparse_value(op::ReducedRydbergOperator, row_idx::Int, col_idx::Int)
    if row_idx == col_idx
        return ComplexF64(_reduced_diagonal_value(op, op.basis[col_idx]))
    end

    flipped = op.basis[row_idx] ⊻ op.basis[col_idx]
    if flipped != 0 && (flipped & (flipped - 1)) == 0
        atom_idx = trailing_zeros(flipped) + 1
        return ComplexF64(op.Ω[atom_idx] / 2.0)
    end
    return 0.0 + 0.0im
end

function _build_reduced_sparse_cache(op::ReducedRydbergOperator)
    dim = length(op.basis)
    colptr = Vector{Int}(undef, dim + 1)
    rowval = Int[]
    nzval = ComplexF64[]
    colptr[1] = 1

    for (col_idx, state) in enumerate(op.basis)
        rows = Int[col_idx]  # keep an explicit diagonal slot even when its value is zero
        for j in 1:op.N
            target_state = state ⊻ (1 << (j-1))
            target_idx = get(op.mapping, target_state, 0)
            if target_idx != 0
                push!(rows, target_idx)
            end
        end
        sort!(rows)
        unique!(rows)
        for row_idx in rows
            push!(rowval, row_idx)
            push!(nzval, _reduced_sparse_value(op, row_idx, col_idx))
        end
        colptr[col_idx + 1] = length(rowval) + 1
    end

    return SparseMatrixCSC(dim, dim, colptr, rowval, nzval)
end

function _update_reduced_sparse_cache!(op::ReducedRydbergOperator)
    H = op.cached_sparse_cpu
    isnothing(H) && return
    for col_idx in 1:size(H, 2)
        for ptr in H.colptr[col_idx]:(H.colptr[col_idx + 1] - 1)
            row_idx = H.rowval[ptr]
            H.nzval[ptr] = _reduced_sparse_value(op, row_idx, col_idx)
        end
    end
end

function SparseArrays.sparse(op::ReducedRydbergOperator)
    if isnothing(op.cached_sparse_cpu)
        op.cached_sparse_cpu = _build_reduced_sparse_cache(op)
    else
        _update_reduced_sparse_cache!(op)
    end
    return op.cached_sparse_cpu
end

"""
    get_jump_operators(N, γ, γ_phi; basis=nothing, mapping=nothing)

Returns a list of sparse jump operators for Lindblad simulation.
γ and γ_phi can be scalars or vectors of length N.
"""
function get_jump_operators(N::Int, γ, γ_phi; basis=nothing, mapping=nothing)
    v_γ = (γ isa AbstractVector) ? convert(Vector{Float64}, γ) : fill(float(γ), N)
    v_γp = (γ_phi isa AbstractVector) ? convert(Vector{Float64}, γ_phi) : fill(float(γ_phi), N)
    
    J_ops = SparseMatrixCSC{ComplexF64, Int}[]
    
    # 1. Decay operators (T1): sqrt(γ) * |g><r|
    for i in 1:N
        if v_γ[i] > 0
            push!(J_ops, jump_sigma_minus(N, i, sqrt(v_γ[i]); basis=basis, mapping=mapping))
        end
    end
    
    # 2. Dephasing operators (T2): sqrt(γ_phi) * |r><r|
    for i in 1:N
        if v_γp[i] > 0
            push!(J_ops, jump_n(N, i, sqrt(v_γp[i]); basis=basis, mapping=mapping))
        end
    end
    
    return J_ops
end

function jump_sigma_minus(N, atom_idx, weight; basis=nothing, mapping=nothing)
    mask = 1 << (atom_idx - 1)
    I = Int[]
    J = Int[]
    V = ComplexF64[]
    
    if isnothing(basis)
        for state in 0:(2^N - 1)
            if (state & mask) != 0
                target = state ⊻ mask
                push!(I, target + 1); push!(J, state + 1); push!(V, weight)
            end
        end
        return sparse(I, J, V, 2^N, 2^N)
    else
        for (idx, state) in enumerate(basis)
            if (state & mask) != 0
                target_state = state ⊻ mask
                if haskey(mapping, target_state)
                    push!(I, mapping[target_state]); push!(J, idx); push!(V, weight)
                end
            end
        end
        dim = length(basis)
        return sparse(I, J, V, dim, dim)
    end
end

function jump_n(N, atom_idx, weight; basis=nothing, mapping=nothing)
    mask = 1 << (atom_idx - 1)
    I = Int[]
    J = Int[]
    V = ComplexF64[]
    
    if isnothing(basis)
        for state in 0:(2^N - 1)
            if (state & mask) != 0
                push!(I, state + 1); push!(J, state + 1); push!(V, weight)
            end
        end
        return sparse(I, J, V, 2^N, 2^N)
    else
        for (idx, state) in enumerate(basis)
            if (state & mask) != 0
                push!(I, idx); push!(J, idx); push!(V, weight)
            end
        end
        dim = length(basis)
        return sparse(I, J, V, dim, dim)
    end
end

"""
    RydbergHamiltonian(reg, Ω, Δ; blockade_radius=0.0)

Returns either a full or reduced Rydberg operator. 
If blockade_radius > 0, the Hilbert space is truncated.
"""
function RydbergHamiltonian(reg::Register, Ω, Δ; blockade_radius=0.0, use_gpu=false)
    V = interaction_matrix(reg)
    N = length(reg.atoms)
    
    # Expand scalars to vectors if necessary
    v_Ω = (Ω isa AbstractVector) ? convert(Vector{Float64}, Ω) : fill(float(Ω), N)
    v_Δ = (Δ isa AbstractVector) ? convert(Vector{Float64}, Δ) : fill(float(Δ), N)
    
    if blockade_radius > 0.0
        basis, mapping = generate_reduced_basis(reg, blockade_radius)
        return ReducedRydbergOperator(N, v_Ω, v_Δ, V, basis, mapping, use_gpu=use_gpu)
    else
        return RydbergOperator(N, v_Ω, v_Δ, V)
    end
end

"""
    build_hamiltonian_func(reg, Ω_func, Δ_func; blockade_radius=0.0)

Returns a highly optimized closure `t -> Operator` for use in ODE solvers,
where `Ω_func` and `Δ_func` are functions of time returning a Vector{Float64}.
"""
function build_hamiltonian_func(reg::Register, Ω_func, Δ_func; blockade_radius=0.0, use_gpu=false)
    V = interaction_matrix(reg)
    N = length(reg.atoms)
    
    if blockade_radius > 0.0
        basis, mapping = generate_reduced_basis(reg, blockade_radius)
        # Create a single operator object to be reused
        op = ReducedRydbergOperator(N, fill(NaN, N), fill(NaN, N), V, basis, mapping, use_gpu=use_gpu)
        
        return t -> begin
            # Get current pulse values
            cur_Ω = convert(Vector{Float64}, Ω_func(t))
            cur_Δ = convert(Vector{Float64}, Δ_func(t))
            
            if op.Ω != cur_Ω || op.Δ != cur_Δ
                copyto!(op.Ω, cur_Ω)
                copyto!(op.Δ, cur_Δ)
            end
            return op
        end
    else
        op = RydbergOperator(N, fill(NaN, N), fill(NaN, N), V)
        return t -> begin
            cur_Ω = convert(Vector{Float64}, Ω_func(t))
            cur_Δ = convert(Vector{Float64}, Δ_func(t))
            if op.Ω != cur_Ω || op.Δ != cur_Δ
                copyto!(op.Ω, cur_Ω)
                copyto!(op.Δ, cur_Δ)
            end
            return op
        end
    end
end

end # module Physics
