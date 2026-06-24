module Physics

# Core physics models and operators for neutral-atom Rydberg simulations.
#
# This module defines atomic registers and lattice geometries, computes the
# van der Waals interaction V_ij = C6 / r_ij^6, and constructs the driven
# Rydberg Hamiltonian
#
#     H = sum_i (Omega_i / 2) sigma_i^x
#         - sum_i Delta_i n_i
#         + sum_{i<j} V_ij n_i n_j.
#
# Both the full Hilbert space and a Rydberg-blockade-reduced basis are
# supported through matrix-free operators and cached sparse matrices. The
# module also provides reusable basis contexts, time-dependent Hamiltonian
# closures, and Lindblad jump operators for decay and dephasing simulations.

using LinearAlgebra
using SparseArrays
using StaticArrays
using ..StructuredLogging: log_event

export Atom, Register, RydbergHamiltonian, RydbergOperator, ReducedRydbergOperator, DenseBasisMapping, BasisContext, interaction_matrix
export generate_reduced_basis, reduced_basis, reduced_basis_context, basis, hamiltonian, hamiltonian_func, build_hamiltonian_func, get_jump_operators
export chain_register, square_lattice_register

struct DenseBasisMapping
    indices::Vector{Int}
end

const _DENSE_BASIS_LOOKUP_MAX_STATES = 1_048_576
const _BasisMapping = Union{DenseBasisMapping, Dict{Int, Int}}

struct BasisContext
    N::Int
    basis::Vector{Int}
    mapping::_BasisMapping
    blockade_radius::Float64
end

const _ReducedBasisCacheKey = Tuple{Int, Float64, UInt64}
const _REDUCED_BASIS_CACHE = Dict{_ReducedBasisCacheKey, Tuple{Vector{Int}, _BasisMapping}}()
const _REDUCED_BASIS_CACHE_LOCK = ReentrantLock()

function _basis_index(mapping::DenseBasisMapping, state::Integer)
    state < 0 && return 0
    idx = Int(state) + 1
    if idx > length(mapping.indices)
        return 0
    end
    return @inbounds mapping.indices[idx]
end

_basis_index(mapping::Dict{Int, Int}, state::Integer) = get(mapping, Int(state), 0)

Base.get(mapping::DenseBasisMapping, state::Integer, default) = begin
    idx = _basis_index(mapping, state)
    idx == 0 ? default : idx
end
Base.haskey(mapping::DenseBasisMapping, state::Integer) = _basis_index(mapping, state) != 0
Base.getindex(mapping::DenseBasisMapping, state::Integer) = begin
    idx = _basis_index(mapping, state)
    idx == 0 && throw(KeyError(state))
    idx
end

function _build_basis_mapping(basis::Vector{Int})
    if isempty(basis)
        return DenseBasisMapping(Int[])
    end

    max_state = maximum(basis)
    if max_state >= 0 && max_state + 1 <= _DENSE_BASIS_LOOKUP_MAX_STATES
        indices = zeros(Int, max_state + 1)
        for (idx, state) in enumerate(basis)
            @inbounds indices[state + 1] = idx
        end
        return DenseBasisMapping(indices)
    end

    return Dict(state => i for (i, state) in enumerate(basis))
end

struct Atom
    coords::SVector{3, Float64}
end

Atom(x::Real, y::Real, z::Real=0.0) = Atom(SVector(Float64(x), Float64(y), Float64(z)))
Atom(coords::NTuple{2, <:Real}) = Atom(coords[1], coords[2], 0.0)
Atom(coords::NTuple{3, <:Real}) = Atom(coords[1], coords[2], coords[3])
Atom(coords::AbstractVector{<:Real}) = length(coords) == 2 ? Atom(coords[1], coords[2], 0.0) :
    (length(coords) == 3 ? Atom(coords[1], coords[2], coords[3]) : throw(ArgumentError("Atom coordinates must contain 2 or 3 values")))

struct Register
    atoms::Vector{Atom}
    C6::Float64
end

Register(atoms::AbstractVector{Atom}; C6::Real=1.0) = Register(collect(atoms), Float64(C6))
Register(coords::AbstractVector{<:Tuple}; C6::Real=1.0) = Register([Atom(coord) for coord in coords], Float64(C6))
Register(coords::AbstractVector{<:AbstractVector}; C6::Real=1.0) = Register([Atom(coord) for coord in coords], Float64(C6))

function chain_register(n::Integer; spacing::Real=1.0, C6::Real=1.0, origin=(0.0, 0.0, 0.0), axis::Symbol=:x)
    n > 0 || throw(ArgumentError("n must be positive"))
    axis in (:x, :y, :z) || throw(ArgumentError("axis must be one of :x, :y, or :z"))
    o = Atom(origin).coords
    step = axis == :x ? SVector(Float64(spacing), 0.0, 0.0) :
        (axis == :y ? SVector(0.0, Float64(spacing), 0.0) : SVector(0.0, 0.0, Float64(spacing)))
    return Register([Atom(o + (i - 1) * step) for i in 1:n], Float64(C6))
end

function square_lattice_register(rows::Integer, cols::Integer; spacing::Real=1.0, C6::Real=1.0, origin=(0.0, 0.0, 0.0), plane::Symbol=:xy)
    rows > 0 || throw(ArgumentError("rows must be positive"))
    cols > 0 || throw(ArgumentError("cols must be positive"))
    plane in (:xy, :xz, :yz) || throw(ArgumentError("plane must be one of :xy, :xz, or :yz"))
    o = Atom(origin).coords
    s = Float64(spacing)
    row_step, col_step = if plane == :xy
        (SVector(s, 0.0, 0.0), SVector(0.0, s, 0.0))
    elseif plane == :xz
        (SVector(s, 0.0, 0.0), SVector(0.0, 0.0, s))
    else
        (SVector(0.0, s, 0.0), SVector(0.0, 0.0, s))
    end
    atoms = Atom[]
    for r in 0:(rows - 1), c in 0:(cols - 1)
        push!(atoms, Atom(o + r * row_step + c * col_step))
    end
    return Register(atoms, Float64(C6))
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
`mapping` is a lookup table from bitstring to its index in the reduced basis.
"""
mutable struct ReducedRydbergOperator
    N::Int
    Ω::Vector{Float64}
    Δ::Vector{Float64}
    V::Matrix{Float64}
    basis::Vector{Int}
    mapping::_BasisMapping
    basis_context::Union{Nothing, BasisContext}
    use_gpu::Bool
    cached_sparse_H::Any
    cached_sparse_cpu::Union{Nothing, SparseMatrixCSC{ComplexF64, Int}}
end

# Constructor with default values
function ReducedRydbergOperator(N, Ω, Δ, V, basis, mapping; basis_context=nothing, use_gpu=false)
    return ReducedRydbergOperator(N, Ω, Δ, V, basis, mapping, basis_context, use_gpu, nothing, nothing)
end

function _blockade_adjacency(reg::Register, blockade_radius::Float64)
    N = length(reg.atoms)
    adj = [Int[] for _ in 1:N]
    for i in 1:N, j in i+1:N
        if norm(reg.atoms[i].coords - reg.atoms[j].coords) < blockade_radius
            push!(adj[i], j)
            push!(adj[j], i)
        end
    end
    return adj
end

function _adjacency_hash(adj::Vector{Vector{Int}})
    h = UInt(0x9e3779b97f4a7c15)
    for i in eachindex(adj)
        h = hash(i, h)
        for j in adj[i]
            if i < j
                h = hash((i, j), h)
            end
        end
    end
    return UInt64(h)
end

function _reduced_basis_cache_key(reg::Register, blockade_radius::Float64, adj::Vector{Vector{Int}})
    return (length(reg.atoms), blockade_radius, _adjacency_hash(adj))
end

function _clear_reduced_basis_cache!()
    lock(_REDUCED_BASIS_CACHE_LOCK) do
        empty!(_REDUCED_BASIS_CACHE)
    end
    return nothing
end

function _reduced_basis_cache_size()
    lock(_REDUCED_BASIS_CACHE_LOCK) do
        return length(_REDUCED_BASIS_CACHE)
    end
end

function generate_reduced_basis(reg::Register, blockade_radius::Float64)
    N = length(reg.atoms)
    # 1. Build adjacency list for the blockade graph and use it as the cache identity.
    adj = _blockade_adjacency(reg, blockade_radius)
    key = _reduced_basis_cache_key(reg, blockade_radius, adj)

    cached = lock(_REDUCED_BASIS_CACHE_LOCK) do
        get(_REDUCED_BASIS_CACHE, key, nothing)
    end
    if !isnothing(cached)
        return cached
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
    
    mapping = _build_basis_mapping(basis)
    entry = (basis, mapping)
    cached_or_inserted = lock(_REDUCED_BASIS_CACHE_LOCK) do
        get!(_REDUCED_BASIS_CACHE, key, entry)
    end
    if cached_or_inserted === entry
        full_basis_size = 2^N
        log_event(
            "basis_generated";
            atom_count=N,
            basis_size=length(basis),
            full_basis_size=full_basis_size,
            blockade_radius=blockade_radius,
            reduced_basis_pruning_ratio=1.0 - (length(basis) / full_basis_size),
        )
    end
    return cached_or_inserted
end

function reduced_basis(reg::Register; blockade_radius::Real)
    return generate_reduced_basis(reg, Float64(blockade_radius))
end

function reduced_basis_context(reg::Register; blockade_radius::Real)
    radius = Float64(blockade_radius)
    basis, mapping = generate_reduced_basis(reg, radius)
    return BasisContext(length(reg.atoms), basis, mapping, radius)
end

function _basis_context_parts(context::BasisContext)
    return context.basis, context.mapping
end

function basis(reg::Register; blockade_radius::Real=0.0)
    radius = Float64(blockade_radius)
    if radius > 0.0
        return first(generate_reduced_basis(reg, radius))
    end
    return collect(0:(2^length(reg.atoms) - 1))
end

hamiltonian(reg::Register, Ω, Δ; blockade_radius::Real=0.0, basis_context=nothing, use_gpu::Bool=false) =
    RydbergHamiltonian(reg, Ω, Δ; blockade_radius=Float64(blockade_radius), basis_context=basis_context, use_gpu=use_gpu)

hamiltonian_func(reg::Register, Ω_func, Δ_func; blockade_radius::Real=0.0, basis_context=nothing, use_gpu::Bool=false) =
    build_hamiltonian_func(reg, Ω_func, Δ_func; blockade_radius=Float64(blockade_radius), basis_context=basis_context, use_gpu=use_gpu)

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
            target_idx = _basis_index(op.mapping, target_state)
            if target_idx != 0
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
            target_idx = _basis_index(op.mapping, target_state)
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
function get_jump_operators(N::Int, γ, γ_phi; basis=nothing, mapping=nothing, basis_context=nothing)
    if !isnothing(basis_context)
        basis, mapping = _basis_context_parts(basis_context)
        N == basis_context.N || throw(ArgumentError("basis_context atom count $(basis_context.N) does not match N=$N"))
    end
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
                target_idx = _basis_index(mapping, target_state)
                if target_idx != 0
                    push!(I, target_idx); push!(J, idx); push!(V, weight)
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
function RydbergHamiltonian(reg::Register, Ω, Δ; blockade_radius=0.0, basis_context=nothing, use_gpu=false)
    V = interaction_matrix(reg)
    N = length(reg.atoms)
    
    # Expand scalars to vectors if necessary
    v_Ω = (Ω isa AbstractVector) ? convert(Vector{Float64}, Ω) : fill(float(Ω), N)
    v_Δ = (Δ isa AbstractVector) ? convert(Vector{Float64}, Δ) : fill(float(Δ), N)
    
    if blockade_radius > 0.0 || !isnothing(basis_context)
        if isnothing(basis_context)
            basis_context = reduced_basis_context(reg; blockade_radius=blockade_radius)
        else
            basis_context.N == N || throw(ArgumentError("basis_context atom count $(basis_context.N) does not match register atom count $N"))
        end
        basis, mapping = _basis_context_parts(basis_context)
        log_event("hamiltonian_built"; atom_count=N, basis_size=length(basis), use_gpu=use_gpu)
        return ReducedRydbergOperator(N, v_Ω, v_Δ, V, basis, mapping, basis_context=basis_context, use_gpu=use_gpu)
    else
        basis_size = 2^N
        log_event("basis_generated"; atom_count=N, basis_size=basis_size, full_basis_size=basis_size, blockade_radius=0.0)
        log_event("hamiltonian_built"; atom_count=N, basis_size=basis_size, use_gpu=use_gpu)
        return RydbergOperator(N, v_Ω, v_Δ, V)
    end
end

"""
    build_hamiltonian_func(reg, Ω_func, Δ_func; blockade_radius=0.0)

Returns a highly optimized closure `t -> Operator` for use in ODE solvers,
where `Ω_func` and `Δ_func` are functions of time returning a Vector{Float64}.
"""
function build_hamiltonian_func(reg::Register, Ω_func, Δ_func; blockade_radius=0.0, basis_context=nothing, use_gpu=false)
    V = interaction_matrix(reg)
    N = length(reg.atoms)
    
    if blockade_radius > 0.0 || !isnothing(basis_context)
        if isnothing(basis_context)
            basis_context = reduced_basis_context(reg; blockade_radius=blockade_radius)
        else
            basis_context.N == N || throw(ArgumentError("basis_context atom count $(basis_context.N) does not match register atom count $N"))
        end
        basis, mapping = _basis_context_parts(basis_context)
        # Create a single operator object to be reused
        op = ReducedRydbergOperator(N, fill(NaN, N), fill(NaN, N), V, basis, mapping, basis_context=basis_context, use_gpu=use_gpu)
        log_event("hamiltonian_built"; atom_count=N, basis_size=length(basis), use_gpu=use_gpu)
        
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
        basis_size = 2^N
        log_event("basis_generated"; atom_count=N, basis_size=basis_size, full_basis_size=basis_size, blockade_radius=0.0)
        log_event("hamiltonian_built"; atom_count=N, basis_size=basis_size, use_gpu=use_gpu)
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
