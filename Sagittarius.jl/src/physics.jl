module Physics

using LinearAlgebra
using SparseArrays
using StaticArrays

export Atom, Register, RydbergHamiltonian, generate_reduced_basis, ReducedRydbergOperator, build_hamiltonian_func

struct Atom{N}
    coords::SVector{N, Float64}
end

struct Register{N}
    atoms::Vector{Atom{N}}
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
H = Σ (Ω/2 σx_i) - Σ (Δ n_i) + Σ (V_ij n_i n_j)
"""
struct RydbergOperator
    N::Int
    Ω::Float64
    Δ::Float64
    V::Matrix{Float64} # Interaction matrix
end

# Define how this operator acts on a vector ψ
function Base.:*(op::RydbergOperator, ψ::Vector{ComplexF64})
    res = zero(ψ)
    N = op.N
    half_Ω = op.Ω / 2.0
    
    for i in 0:(2^N - 1)
        if ψ[i+1] == 0 continue end
        
        # 1. Detuning & Interaction (Diagonal terms)
        diagonal = 0.0
        for j in 1:N
            if (i & (1 << (j-1))) != 0
                diagonal -= op.Δ  # Detuning
                
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
            res[target+1] += half_Ω * ψ[i+1]
        end
    end
    return res
end

"""
    ReducedRydbergOperator

A Hamiltonian operator that acts on a truncated Hilbert space.
`basis` is a Vector of bitstrings (Int) representing valid states.
`mapping` is a Dictionary (or lookup table) from bitstring to its index in the reduced basis.
"""
struct ReducedRydbergOperator
    N::Int
    Ω::Float64
    Δ::Float64
    V::Matrix{Float64}
    basis::Vector{Int}
    mapping::Dict{Int, Int}
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
    half_Ω = op.Ω / 2.0
    N = op.N

    # We iterate only over the valid basis states
    for (idx, state) in enumerate(op.basis)
        if ψ[idx] == 0 continue end

        # 1. Diagonal terms (Detuning & Interaction)
        # Interaction is only for pairs NOT blockaded (which still have some V_ij)
        diagonal = 0.0
        for j in 1:N
            if (state & (1 << (j-1))) != 0
                diagonal -= op.Δ
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
                res[target_idx] += half_Ω * ψ[idx]
            end
        end
    end
    return res
end

"""
    RydbergHamiltonian(reg, Ω, Δ; blockade_radius=0.0)

Returns either a full or reduced Rydberg operator. 
If blockade_radius > 0, the Hilbert space is truncated.
"""
function RydbergHamiltonian(reg::Register, Ω, Δ; blockade_radius=0.0)
    V = interaction_matrix(reg)
    N = length(reg.atoms)
    
    if blockade_radius > 0.0
        basis, mapping = generate_reduced_basis(reg, blockade_radius)
        return ReducedRydbergOperator(N, float(Ω), float(Δ), V, basis, mapping)
    else
        return RydbergOperator(N, float(Ω), float(Δ), V)
    end
end

"""
    build_hamiltonian_func(reg, Ω_func, Δ_func; blockade_radius=0.0)

Returns a highly optimized closure `t -> Operator` for use in ODE solvers,
where `Ω_func` and `Δ_func` are functions of time.
"""
function build_hamiltonian_func(reg::Register, Ω_func, Δ_func; blockade_radius=0.0)
    V = interaction_matrix(reg)
    N = length(reg.atoms)
    
    if blockade_radius > 0.0
        basis, mapping = generate_reduced_basis(reg, blockade_radius)
        return t -> ReducedRydbergOperator(N, float(Ω_func(t)), float(Δ_func(t)), V, basis, mapping)
    else
        return t -> RydbergOperator(N, float(Ω_func(t)), float(Δ_func(t)), V)
    end
end

end # module Physics
