module Solver

using OrdinaryDiffEq
using LinearAlgebra
using DiffEqCallbacks
using SparseArrays

export solve_schrodinger, solve_lindblad, RydbergPopulation

"""
    RydbergPopulation(atom_idx, N_atoms; basis=nothing)
Returns a function that calculates the population of the Rydberg state for atom `atom_idx`.
Works for both state vectors (Schrodinger) and density matrices (Lindblad).
"""
function RydbergPopulation(atom_idx, N_atoms; basis=nothing)
    mask = 1 << (atom_idx - 1)
    return (state, t, integrator) -> begin
        pop = 0.0
        if state isa Vector
            if isnothing(basis)
                for i in 0:(2^N_atoms - 1)
                    if (i & mask) != 0
                        pop += abs2(state[i + 1])
                    end
                end
            else
                for (idx, bstate) in enumerate(basis)
                    if (bstate & mask) != 0
                        pop += abs2(state[idx])
                    end
                end
            end
        else # Matrix (Density Matrix)
            if isnothing(basis)
                for i in 0:(2^N_atoms - 1)
                    if (i & mask) != 0
                        pop += real(state[i + 1, i + 1])
                    end
                end
            else
                for (idx, bstate) in enumerate(basis)
                    if (bstate & mask) != 0
                        pop += real(state[idx, idx])
                    end
                end
            end
        end
        return pop
    end
end

"""
    solve_schrodinger(ψ0, H_func, tspan; observables=nothing, reltol=1e-8, abstol=1e-8)

Solves the TDSE: i dψ/dt = H(t)ψ. 
"""
function solve_schrodinger(ψ0::Vector{ComplexF64}, H_func, tspan; observables=nothing, reltol=1e-8, abstol=1e-8)
    f(ψ, p, t) = (H_func(t) * ψ) .* (-1im)
    
    saved_values = SavedValues(Float64, Any)
    cb = nothing
    if !isnothing(observables)
        save_func = (ψ, t, integrator) -> [func(ψ, t, integrator) for func in values(observables)]
        cb = SavingCallback(save_func, saved_values)
    end

    prob = ODEProblem(f, ψ0, tspan)
    sol = solve(prob, Tsit5(), reltol=reltol, abstol=abstol, callback=cb)
    
    return isnothing(observables) ? sol : (sol, saved_values)
end

"""
    solve_lindblad(ρ0, H_func, J_ops, tspan; observables=nothing, reltol=1e-8, abstol=1e-8)

Solves the Lindblad Master Equation: dρ/dt = -i[H, ρ] + Σ (JρJ† - 0.5{J†J, ρ}).
"""
function solve_lindblad(ρ0::Matrix{ComplexF64}, H_func, J_ops, tspan; observables=nothing, reltol=1e-8, abstol=1e-8)
    # Pre-calculate J†J terms
    J_dagger_J = [J' * J for J in J_ops]
    J_dagger = [sparse(J') for J in J_ops] # Pre-cache J† as sparse

    f(ρ, p, t) = begin
        H = sparse(H_func(t))
        # -i[H, ρ]
        dρ = -1im * (H * ρ - ρ * H)
        for i in 1:length(J_ops)
            J = J_ops[i]
            J_dag = J_dagger[i]
            J_dag_J = J_dagger_J[i]
            # Lindblad term: JρJ† - 0.5(J†Jρ + ρJ†J)
            dρ += J * ρ * J_dag - 0.5 * (J_dag_J * ρ + ρ * J_dag_J)
        end
        return dρ
    end

    saved_values = SavedValues(Float64, Any)
    cb = nothing
    if !isnothing(observables)
        save_func = (ρ, t, integrator) -> [func(ρ, t, integrator) for func in values(observables)]
        cb = SavingCallback(save_func, saved_values)
    end

    prob = ODEProblem(f, ρ0, tspan)
    sol = solve(prob, Tsit5(), reltol=reltol, abstol=abstol, callback=cb)
    
    return isnothing(observables) ? sol : (sol, saved_values)
end

end # module Solver
