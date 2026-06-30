module Solver

using OrdinaryDiffEq
using OrdinaryDiffEqLowOrderRK: RK4
using LinearAlgebra
using DiffEqCallbacks
using SparseArrays
using Random
using SciMLBase
using ..Physics: BasisContext
using ..StructuredLogging: log_event

# Optional dependencies handled via requires or dynamic checks in real packages,
# but for this prototype we'll assume they are available if selected.
# using AMDGPU
# using Metal

export solve_schrodinger, solve_lindblad, solve_mc_trajectories, RydbergPopulation, resolve_solver_algorithm
export TotalRydbergPopulation, PairCorrelation, ConnectedPairCorrelation, BlockadeViolation
export BitstringProbability, MWISCost, PauliZ, PauliZZ, Parity
export solve_schrodinger_gpu

"""
    RydbergPopulation(atom_idx, N_atoms; basis=nothing)
Returns a function that calculates the population of the Rydberg state for atom `atom_idx`.
"""
function _observable_basis(N_atoms; basis=nothing, basis_context=nothing)
    if !isnothing(basis_context)
        basis_context.N == N_atoms || throw(ArgumentError("basis_context atom count $(basis_context.N) does not match N_atoms=$N_atoms"))
        return basis_context.basis
    end
    return basis
end

function _state_probability(state, idx::Int)
    if state isa AbstractMatrix
        return Float64(real(state[idx, idx]))
    end
    if isdefined(@__MODULE__, :CUDA) && state isa CUDA.CuVector
        return Float64(abs2(Array(state)[idx]))
    end
    return Float64(abs2(state[idx]))
end

function _diagonal_expectation(state, N_atoms::Integer, basis, value_func)
    total = 0.0
    if isnothing(basis)
        for bitstring in 0:(2^N_atoms - 1)
            total += _state_probability(state, bitstring + 1) * Float64(value_func(bitstring))
        end
    else
        for (idx, bitstring) in enumerate(basis)
            total += _state_probability(state, idx) * Float64(value_func(bitstring))
        end
    end
    return Float64(total)
end

function _atom_masks(atoms)
    return [1 << (Int(atom) - 1) for atom in atoms]
end

function _occupied(bitstring::Integer, mask::Integer)
    return (bitstring & mask) != 0
end

function RydbergPopulation(atom_idx, N_atoms; basis=nothing, basis_context=nothing)
    basis = _observable_basis(N_atoms; basis=basis, basis_context=basis_context)
    mask = 1 << (Int(atom_idx) - 1)
    return (state, t, integrator) -> _diagonal_expectation(state, N_atoms, basis, bitstring -> _occupied(bitstring, mask) ? 1.0 : 0.0)
end

function TotalRydbergPopulation(N_atoms; atoms=nothing, basis=nothing, basis_context=nothing)
    basis = _observable_basis(N_atoms; basis=basis, basis_context=basis_context)
    selected = isnothing(atoms) ? collect(1:N_atoms) : collect(atoms)
    masks = _atom_masks(selected)
    return (state, t, integrator) -> _diagonal_expectation(state, N_atoms, basis, bitstring -> sum(_occupied(bitstring, mask) ? 1.0 : 0.0 for mask in masks))
end

function PairCorrelation(atoms, N_atoms; basis=nothing, basis_context=nothing)
    basis = _observable_basis(N_atoms; basis=basis, basis_context=basis_context)
    masks = _atom_masks(atoms)
    length(masks) == 2 || throw(ArgumentError("PairCorrelation requires exactly two atoms"))
    return (state, t, integrator) -> _diagonal_expectation(state, N_atoms, basis, bitstring -> (_occupied(bitstring, masks[1]) && _occupied(bitstring, masks[2])) ? 1.0 : 0.0)
end

function ConnectedPairCorrelation(atoms, N_atoms; basis=nothing, basis_context=nothing)
    pair = PairCorrelation(atoms, N_atoms; basis=basis, basis_context=basis_context)
    pop_i = RydbergPopulation(atoms[1], N_atoms; basis=basis, basis_context=basis_context)
    pop_j = RydbergPopulation(atoms[2], N_atoms; basis=basis, basis_context=basis_context)
    return (state, t, integrator) -> Float64(pair(state, t, integrator) - pop_i(state, t, integrator) * pop_j(state, t, integrator))
end

function BlockadeViolation(edges, N_atoms; basis=nothing, basis_context=nothing)
    basis = _observable_basis(N_atoms; basis=basis, basis_context=basis_context)
    edge_masks = [Tuple(_atom_masks(edge)) for edge in edges]
    return (state, t, integrator) -> _diagonal_expectation(
        state,
        N_atoms,
        basis,
        bitstring -> sum((_occupied(bitstring, edge[1]) && _occupied(bitstring, edge[2])) ? 1.0 : 0.0 for edge in edge_masks),
    )
end

function BitstringProbability(target, N_atoms; basis=nothing, basis_context=nothing)
    basis = _observable_basis(N_atoms; basis=basis, basis_context=basis_context)
    target_int = Int(target)
    return (state, t, integrator) -> _diagonal_expectation(state, N_atoms, basis, bitstring -> bitstring == target_int ? 1.0 : 0.0)
end

function MWISCost(weights, edges, penalty, N_atoms; basis=nothing, basis_context=nothing)
    basis = _observable_basis(N_atoms; basis=basis, basis_context=basis_context)
    weight_values = [Float64(w) for w in weights]
    edge_masks = [Tuple(_atom_masks(edge)) for edge in edges]
    penalty_value = Float64(penalty)
    return (state, t, integrator) -> _diagonal_expectation(
        state,
        N_atoms,
        basis,
        bitstring -> begin
            reward = sum(_occupied(bitstring, 1 << (i - 1)) ? weight_values[i] : 0.0 for i in 1:length(weight_values))
            violations = sum((_occupied(bitstring, edge[1]) && _occupied(bitstring, edge[2])) ? 1.0 : 0.0 for edge in edge_masks)
            reward - penalty_value * violations
        end,
    )
end

function _z_value(bitstring, mask, convention)
    convention == "ground_plus" || throw(ArgumentError("unsupported Pauli-Z convention: $convention"))
    return _occupied(bitstring, mask) ? -1.0 : 1.0
end

function PauliZ(atom, N_atoms; convention="ground_plus", basis=nothing, basis_context=nothing)
    basis = _observable_basis(N_atoms; basis=basis, basis_context=basis_context)
    mask = 1 << (Int(atom) - 1)
    return (state, t, integrator) -> _diagonal_expectation(state, N_atoms, basis, bitstring -> _z_value(bitstring, mask, convention))
end

function PauliZZ(atoms, N_atoms; convention="ground_plus", basis=nothing, basis_context=nothing)
    basis = _observable_basis(N_atoms; basis=basis, basis_context=basis_context)
    masks = _atom_masks(atoms)
    length(masks) == 2 || throw(ArgumentError("PauliZZ requires exactly two atoms"))
    return (state, t, integrator) -> _diagonal_expectation(state, N_atoms, basis, bitstring -> _z_value(bitstring, masks[1], convention) * _z_value(bitstring, masks[2], convention))
end

function Parity(atoms, N_atoms; convention="ground_plus", basis=nothing, basis_context=nothing)
    basis = _observable_basis(N_atoms; basis=basis, basis_context=basis_context)
    masks = _atom_masks(atoms)
    return (state, t, integrator) -> _diagonal_expectation(state, N_atoms, basis, bitstring -> prod(_z_value(bitstring, mask, convention) for mask in masks))
end

function _log_solver_start(; backend="CPU", use_gpu=false, reltol=1e-8, abstol=1e-8, blockade_radius=0.0, method="Tsit5", adaptive=true, dt=nothing, use_mc=false)
    return log_event(
        "solver_start";
        backend=backend,
        use_gpu=use_gpu,
        reltol=reltol,
        abstol=abstol,
        blockade_radius=blockade_radius,
        method=String(method),
        adaptive=Bool(adaptive),
        dt=dt,
        use_mc=Bool(use_mc),
    )
end


function resolve_solver_algorithm(method::AbstractString; adaptive::Bool=true, dt=nothing)
    if method == "Tsit5"
        adaptive || throw(ArgumentError("Tsit5 supports only adaptive=true in the Sagittarius public solver contract"))
        isnothing(dt) || throw(ArgumentError("Tsit5 adaptive runs require dt=nothing in the Sagittarius public solver contract"))
        return Tsit5()
    elseif method == "Vern9"
        adaptive || throw(ArgumentError("Vern9 supports only adaptive=true in the Sagittarius public solver contract"))
        isnothing(dt) || throw(ArgumentError("Vern9 adaptive runs require dt=nothing in the Sagittarius public solver contract"))
        return Vern9()
    elseif method == "RK4"
        adaptive && throw(ArgumentError("RK4 requires adaptive=false in the Sagittarius public solver contract"))
        (isnothing(dt) || !(Float64(dt) > 0.0) || !isfinite(Float64(dt))) && throw(ArgumentError("RK4 requires a finite positive dt"))
        return RK4()
    end
    throw(ArgumentError("unsupported solver method: $method. Supported methods: Tsit5, Vern9, RK4"))
end

function _solver_kwargs(method; adaptive=true, dt=nothing, reltol=1e-8, abstol=1e-8, saveat=nothing)
    algorithm = resolve_solver_algorithm(String(method); adaptive=Bool(adaptive), dt=dt)
    save_kwargs = isnothing(saveat) ? NamedTuple() : (saveat=collect(saveat),)
    step_kwargs = Bool(adaptive) ? (reltol=reltol, abstol=abstol) : (adaptive=false, dt=Float64(dt))
    return algorithm, merge(step_kwargs, save_kwargs)
end


function _saveat_kwargs(saveat)
    return isnothing(saveat) ? NamedTuple() : (saveat=collect(saveat),)
end

function _saving_callback(save_func, saved_values, saveat)
    if isnothing(saveat)
        return SavingCallback(save_func, saved_values)
    end
    return SavingCallback(save_func, saved_values; saveat=collect(saveat))
end

function _ensemble_algorithm_for_seed(seed)
    return isnothing(seed) ? EnsembleThreads() : EnsembleSerial()
end

function _log_solver_finish(result_type::AbstractString, basis_size::Integer; backend=nothing)
    if isnothing(backend)
        return log_event("solver_finish"; result_type=String(result_type), basis_size=basis_size)
    end
    return log_event("solver_finish"; result_type=String(result_type), basis_size=basis_size, backend=backend)
end

function solve_schrodinger(ψ0::Vector{ComplexF64}, H_func, tspan; observables=nothing, reltol=1e-8, abstol=1e-8, backend="CPU", use_gpu=false, blockade_radius=0.0, saveat=nothing, method="Tsit5", adaptive=true, dt=nothing)
    _log_solver_start(; backend=backend, use_gpu=use_gpu, reltol=reltol, abstol=abstol, blockade_radius=blockade_radius, method=method, adaptive=adaptive, dt=dt)
    f(ψ, p, t) = (H_func(t) * ψ) .* (-1im)
    saved_values = SavedValues(Float64, Any)
    cb = nothing
    if !isnothing(observables)
        save_func = (ψ, t, integrator) -> [func(ψ, t, integrator) for func in values(observables)]
        cb = _saving_callback(save_func, saved_values, saveat)
    end
    prob = ODEProblem(f, ψ0, tspan)
    algorithm, solver_kwargs = _solver_kwargs(method; adaptive=adaptive, dt=dt, reltol=reltol, abstol=abstol, saveat=saveat)
    sol = solve(prob, algorithm; callback=cb, solver_kwargs...)
    result_type = isnothing(observables) ? "schrodinger" : "schrodinger_observables"
    _log_solver_finish(result_type, length(ψ0); backend=backend)
    return isnothing(observables) ? sol : (sol, saved_values)
end

function _copy_sparse_values_to_gpu!(gpu_sparse, cpu_sparse)
    if hasproperty(gpu_sparse, :nzVal)
        copyto!(gpu_sparse.nzVal, cpu_sparse.nzval)
        return gpu_sparse
    elseif hasproperty(gpu_sparse, :nzval)
        copyto!(gpu_sparse.nzval, cpu_sparse.nzval)
        return gpu_sparse
    end
    return nothing
end

function _cached_gpu_sparse!(op)
    @eval using CUDA
    @eval using CUDA.CUSPARSE
    cpu_sparse = sparse(op)
    if isnothing(op.cached_sparse_H)
        op.cached_sparse_H = CUDA.CUSPARSE.CuSparseMatrixCSC(cpu_sparse)
    else
        updated = _copy_sparse_values_to_gpu!(op.cached_sparse_H, cpu_sparse)
        if isnothing(updated)
            op.cached_sparse_H = CUDA.CUSPARSE.CuSparseMatrixCSC(cpu_sparse)
        end
    end
    return op.cached_sparse_H
end

function solve_schrodinger_gpu(ψ0, H_func, tspan; observables=nothing, reltol=1e-8, abstol=1e-8, backend="CUDA", blockade_radius=0.0, saveat=nothing, method="Tsit5", adaptive=true, dt=nothing)
    _log_solver_start(; backend=backend, use_gpu=true, reltol=reltol, abstol=abstol, blockade_radius=blockade_radius, method=method, adaptive=adaptive, dt=dt)
    @eval using CUDA
    @eval using CUDA.CUSPARSE
    function f(ψ, p, t)
        op = H_func(t)
        if hasproperty(op, :use_gpu) && op.use_gpu
            if ψ isa CUDA.CuVector
                return (_cached_gpu_sparse!(op) * ψ) .* (-1im)
            else
                return (sparse(op) * ψ) .* (-1im)
            end
        else
            H_sparse = sparse(op)
            if ψ isa CUDA.CuVector
                return (CUDA.CUSPARSE.CuSparseMatrixCSC(H_sparse) * ψ) .* (-1im)
            else
                return (H_sparse * ψ) .* (-1im)
            end
        end
    end

    saved_values = SavedValues(Float64, Any)
    cb = nothing
    if !isnothing(observables)
        save_func = (ψ, t, integrator) -> [func(ψ, t, integrator) for func in values(observables)]
        cb = _saving_callback(save_func, saved_values, saveat)
    end
    prob = ODEProblem(f, ψ0, tspan)
    algorithm, solver_kwargs = _solver_kwargs(method; adaptive=adaptive, dt=dt, reltol=reltol, abstol=abstol, saveat=saveat)
    sol = solve(prob, algorithm; callback=cb, solver_kwargs...)
    result_type = isnothing(observables) ? "schrodinger_gpu" : "schrodinger_gpu_observables"
    _log_solver_finish(result_type, length(ψ0); backend=backend)
    return isnothing(observables) ? sol : (sol, saved_values)
end

function solve_lindblad(ρ0::Matrix{ComplexF64}, H_func, J_ops, tspan; observables=nothing, reltol=1e-8, abstol=1e-8, backend="CPU", use_gpu=false, blockade_radius=0.0, saveat=nothing, method="Tsit5", adaptive=true, dt=nothing)
    _log_solver_start(; backend=backend, use_gpu=use_gpu, reltol=reltol, abstol=abstol, blockade_radius=blockade_radius, method=method, adaptive=adaptive, dt=dt)
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
        cb = _saving_callback(save_func, saved_values, saveat)
    end
    prob = ODEProblem(f, ρ0, tspan)
    algorithm, solver_kwargs = _solver_kwargs(method; adaptive=adaptive, dt=dt, reltol=reltol, abstol=abstol, saveat=saveat)
    sol = solve(prob, algorithm; callback=cb, solver_kwargs...)
    result_type = isnothing(observables) ? "lindblad" : "lindblad_observables"
    _log_solver_finish(result_type, size(ρ0, 1); backend=backend)
    return isnothing(observables) ? sol : (sol, saved_values)
end

function solve_mc_trajectories(ψ0::Vector{ComplexF64}, H_func, J_ops, tspan;
                               n_trajectories=100, observables=nothing,
                               reltol=1e-8, abstol=1e-8, backend="CPU", use_gpu=false, blockade_radius=0.0,
                               seed=nothing, saveat=nothing, method="Tsit5", adaptive=true, dt=nothing)
    _log_solver_start(; backend=backend, use_gpu=use_gpu, reltol=reltol, abstol=abstol, blockade_radius=blockade_radius, method=method, adaptive=adaptive, dt=dt, use_mc=true)
    if !isnothing(seed)
        Random.seed!(Int(seed))
    end
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
        t_vals = isnothing(saveat) ? collect(range(tspan[1], tspan[2], length=200)) : collect(saveat)
        function output_func(sol, i)
            res = [ [func(sol(t) / norm(sol(t)), t, nothing) for func in values(observables)] for t in t_vals ]
            return (res, false)
        end
        ensemble_prob = EnsembleProblem(prob, prob_func=prob_func, output_func=output_func)
        ensemble_alg = _ensemble_algorithm_for_seed(seed)
        algorithm, solver_kwargs = _solver_kwargs(method; adaptive=adaptive, dt=dt, reltol=reltol, abstol=abstol, saveat=t_vals)
        sim = solve(ensemble_prob, algorithm, ensemble_alg; trajectories=n_trajectories,
                    callback=cb_jump, solver_kwargs...)
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
        _log_solver_finish("mcwf_observables", length(ψ0); backend=backend)
        return (t_vals, avg_res)
    else
        ensemble_alg = _ensemble_algorithm_for_seed(seed)
        algorithm, solver_kwargs = _solver_kwargs(method; adaptive=adaptive, dt=dt, reltol=reltol, abstol=abstol, saveat=saveat)
        sim = solve(ensemble_prob, algorithm, ensemble_alg; trajectories=n_trajectories,
                    callback=cb_jump, solver_kwargs...)
        _log_solver_finish("mcwf", length(ψ0); backend=backend)
        return sim
    end
end

end # module Solver
