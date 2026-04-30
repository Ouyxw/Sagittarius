module Solver

using OrdinaryDiffEq
using LinearAlgebra
using DiffEqCallbacks
using SparseArrays
using Random
using SciMLBase
using CUDA
using CUDA.CUSPARSE

# Optional dependencies handled via requires or dynamic checks in real packages,
# but for this prototype we'll assume they are available if selected.
# using AMDGPU
# using Metal

export solve_schrodinger, solve_lindblad, solve_mc_trajectories, RydbergPopulation
export solve_schrodinger_gpu

"""
    RydbergPopulation(atom_idx, N_atoms; basis=nothing)
Returns a function that calculates the population of the Rydberg state for atom \`atom_idx\`.
"""
function RydbergPopulation(atom_idx, N_atoms; basis=nothing)
    mask = 1 << (atom_idx - 1)
    return (state, t, integrator) -> begin
        if state isa Vector
            pop = 0.0
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
            return pop
        elseif state isa Matrix
            # Lindblad density matrix: sum diagonal elements
            pop = 0.0
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
            return pop
        elseif state isa CuVector
            # Optimized GPU implementation using broadcasting and reduction
            if isnothing(basis)
                # Correcting for 1-based indexing: (i-1) is the bitstring
                indices = findall(i -> ((i-1) & mask) != 0, 1:length(state))
                if isempty(indices) return 0.0 end
                return Float64(sum(abs2, state[indices]))
            else
                indices = findall(bstate -> (bstate & mask) != 0, basis)
                if isempty(indices) return 0.0 end
                return Float64(sum(abs2, state[indices]))
            end
        else 
            return 0.0
        end
    end
end

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

function solve_schrodinger_gpu(ψ0, H_func, tspan; observables=nothing, reltol=1e-8, abstol=1e-8)
    function f(ψ, p, t)
        op = H_func(t)
        # Check for our cached sparse matrix
        if hasproperty(op, :use_gpu) && op.use_gpu
            if isnothing(op.cached_sparse_H)
                # Determine which GPU array type to use
                if ψ isa CuVector
                    op.cached_sparse_H = CuSparseMatrixCSC(sparse(op))
                else
                    # Fallback or other backends
                    return (sparse(op) * ψ) .* (-1im)
                end
            end
            return (op.cached_sparse_H * ψ) .* (-1im)
        else
            # Dynamic conversion (slow)
            H_sparse = sparse(op)
            if ψ isa CuVector
                return (CuSparseMatrixCSC(H_sparse) * ψ) .* (-1im)
            else
                return (H_sparse * ψ) .* (-1im)
            end
        end
    end
    
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

function solve_lindblad(ρ0::Matrix{ComplexF64}, H_func, J_ops, tspan; observables=nothing, reltol=1e-8, abstol=1e-8)
    J_dagger_J = [J' * J for J in J_ops]
    J_dagger = [sparse(J') for J in J_ops]
    f(ρ, p, t) = begin
        H = sparse(H_func(t))
        dρ = -1im * (H * ρ - ρ * H)
        for i in 1:length(J_ops)
            J = J_ops[i]
            J_dag = J_dagger[i]
            J_dag_J = J_dagger_J[i]
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

function solve_mc_trajectories(ψ0::Vector{ComplexF64}, H_func, J_ops, tspan; 
                               n_trajectories=100, observables=nothing, 
                               reltol=1e-8, abstol=1e-8)
    J_dagger_J = [J' * J for J in J_ops]
    sum_J_dagger_J = isempty(J_ops) ? spzeros(ComplexF64, length(ψ0), length(ψ0)) : sum(J_dagger_J)
    f(ψ, p, t) = begin
        H = sparse(H_func(t))
        return (-1im * H - 0.5 * sum_J_dagger_J) * ψ
    end
    condition(u, t, integrator) = norm(u)^2 - integrator.p[1] + 1e-15
    function affect!(integrator)
        ψ = integrator.u
        weights = [real(ψ' * J_dag_J * ψ) for J_dag_J in J_dagger_J]
        w_sum = sum(weights)
        if w_sum > 0
            r = rand() * w_sum
            c = 0.0
            jump_idx = 1
            for (i, w) in enumerate(weights)
                c += w
                if r <= c
                    jump_idx = i
                    break
                end
            end
            J = J_ops[jump_idx]
            new_ψ = J * ψ
            integrator.u = new_ψ / norm(new_ψ)
        end
        integrator.p[1] = rand()
    end
    cb_jump = ContinuousCallback(condition, affect!, save_positions=(false, false))
    prob = ODEProblem(f, ψ0, tspan, [rand()])
    function prob_func(prob, i, args...)
        remake(prob, p=[rand()])
    end
    ensemble_prob = EnsembleProblem(prob, prob_func=prob_func)
    if !isnothing(observables)
        t_vals = range(tspan[1], tspan[2], length=200)
        function output_func(sol, i)
            res = [ [func(sol(t) / norm(sol(t)), t, nothing) for func in values(observables)] for t in t_vals ]
            return (res, false)
        end
        ensemble_prob = EnsembleProblem(prob, prob_func=prob_func, output_func=output_func)
        sim = solve(ensemble_prob, Tsit5(), EnsembleThreads(), trajectories=n_trajectories, 
                    callback=cb_jump, reltol=reltol, abstol=abstol, saveat=t_vals)
        n_obs = length(observables)
        avg_res = [zeros(n_obs) for _ in 1:length(t_vals)]
        for traj_res in sim.u
            for (t_idx, obs_vals) in enumerate(traj_res)
                avg_res[t_idx] .+= obs_vals
            end
        end
        for t_idx in 1:length(t_vals)
            avg_res[t_idx] ./= n_trajectories
        end
        return (t_vals, avg_res)
    else
        return solve(ensemble_prob, Tsit5(), EnsembleThreads(), trajectories=n_trajectories, 
                     callback=cb_jump, reltol=reltol, abstol=abstol)
    end
end

end # module Solver
