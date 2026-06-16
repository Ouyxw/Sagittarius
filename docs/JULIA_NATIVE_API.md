# Julia Native Developer API

Sagittarius exposes a Julia-native API for users who want direct access to registers, pulse ASTs, bases, Hamiltonians, jump operators, solvers, and structured logging without going through the Python SDK. For side-by-side Python and Julia workflows, see `docs/DUAL_SDK_EXAMPLES.md`.

## Registers

```julia
using Sagittarius

reg = chain_register(4; spacing=0.5, C6=10.0)
lattice = square_lattice_register(2, 3; spacing=1.0, plane=:xy)
custom = Register([(0.0, 0.0), (0.5, 0.0), (1.0, 0.0)]; C6=10.0)
atom = Atom(0.0, 0.0, 0.0)
```

`Atom` accepts `(x, y)`, `(x, y, z)`, tuple coordinates, or 2/3 element numeric vectors. `Register` accepts atom vectors or coordinate vectors and preserves atom order.

## Bases and Hamiltonians

```julia
basis_states = basis(reg; blockade_radius=0.6)
context = reduced_basis_context(reg; blockade_radius=0.6)
reduced_states, mapping = reduced_basis(reg; blockade_radius=0.6)
H = hamiltonian(reg, [0.2, 0.3, 0.4, 0.5], zeros(4); basis_context=context)
H_func = build_hamiltonian_func(reg, t -> fill(0.2, 4), t -> zeros(4); basis_context=context)
```

`BasisContext` carries a reduced basis and its bitstring-to-index mapping so Hamiltonians, observables, and jump operators can share one ordering. The lowercase API is the stable developer-facing facade. Existing internal names such as `RydbergHamiltonian`, `generate_reduced_basis`, and `build_hamiltonian_func` remain exported for compatibility.

## Pulses and Solvers

```julia
pulse = PiecewisePulse(PulseNode[
    ConstantPulse(0.0, 1.0),
    RampPulse(0.0, 1.0, 2.0),
])
omega = compile_pulse(pulse)

psi0 = ComplexF64[1.0; zeros(ComplexF64, length(basis_states) - 1)]
obs = Dict("atom1" => RydbergPopulation(1, length(reg.atoms); basis_context=context))
sol, saved = solve_schrodinger(psi0, H_func, (0.0, 1.0); observables=obs)
```

Open-system users can call `get_jump_operators`, `solve_lindblad`, and `solve_mc_trajectories` directly. GPU users can call `solve_schrodinger_gpu` when the CUDA backend is available.

## Logging

Julia native code can emit taxonomy-aligned structured logs with:

```julia
log_event("hamiltonian_built"; atom_count=4, basis_size=8, use_gpu=false)
```

The payload fields follow `docs/EVENT_TAXONOMY.md` and can be captured with Julia's standard `Logging` tools.
