module Solver

using OrdinaryDiffEq
using LinearAlgebra
using DiffEqCallbacks

export solve_schrodinger, RydbergPopulation

"""
    RydbergPopulation(atom_idx)
Returns a function that calculates the population of the Rydberg state for atom `atom_idx`.
"""
function RydbergPopulation(atom_idx, N_atoms)
    mask = 1 << (atom_idx - 1)
    return (ψ, t, integrator) -> begin
        pop = 0.0
        for i in 0:(2^N_atoms - 1)
            if (i & mask) != 0
                pop += abs2(ψ[i + 1])
            end
        end
        return pop
    end
end

"""
    solve_schrodinger(ψ0, H_func, tspan; observables=nothing)

Solves the TDSE: i dψ/dt = H(t)ψ. 
`observables` can be a Dict of label => function(ψ, t, integrator).
"""
function solve_schrodinger(ψ0::Vector{ComplexF64}, H_func, tspan; observables=nothing)
    # Corrected order: (H * ψ) * -1im
    f(ψ, p, t) = (H_func(t) * ψ) .* (-1im)
    
    # Setup callback for saving observables if provided
    saved_values = SavedValues(Float64, Any)
    cb = nothing
    if !isnothing(observables)
        # Create a function that evaluates all observables at once
        save_func = (ψ, t, integrator) -> [func(ψ, t, integrator) for func in values(observables)]
        cb = SavingCallback(save_func, saved_values)
    end

    prob = ODEProblem(f, ψ0, tspan)
    sol = solve(prob, Tsit5(), reltol=1e-8, abstol=1e-8, callback=cb)
    
    return isnothing(observables) ? sol : (sol, saved_values)
end

end # module Solver
