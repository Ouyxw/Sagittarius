module Cluster

using Distributed
using ..Program
using ..Physics
using ..Solver
using ..StructuredLogging: log_event

export setup_workers, run_parallel_sweep

function setup_workers(n::Int)
    log_event("cluster_setup_start"; n_workers=n)
    if nprocs() < n
        addprocs(n - nprocs())
    end
    # Sagittarius loading must be done from Main or via proper package load
    worker_count = nprocs()
    log_event("cluster_setup_finish"; n_workers=worker_count)
    return worker_count
end

"""
    run_parallel_sweep(sim_configs, psi0, t_span, observables)

Runs a list of simulation configurations in parallel.
`sim_configs` should be a list of dicts or objects that can be 
used to construct/run simulations on workers.
"""
function run_parallel_sweep(run_func, params)
    # run_func is a function that takes one element of params
    # and returns the result.
    return pmap(run_func, params)
end

end # module Cluster
