# Julia Minimal Examples with Expected Output

These examples are intended for quick Julia-native verification. They assume `Sagittarius.jl` has been added to the active project with `Pkg.develop(path="...")`. See [Julia projects](projects.md).

## 1. Load Sagittarius

```julia
using Sagittarius
println("loaded")
```

Expected output:

```text
loaded
```

## 2. Chain Register and Reduced Basis

```julia
using Sagittarius

reg = chain_register(3; spacing=0.5, C6=100.0)
context = reduced_basis_context(reg; blockade_radius=0.6)
println(length(context.basis))
println(context.basis)
```

Expected output:

```text
5
[0, 1, 2, 4, 5]
```

## 3. Hamiltonian Construction

```julia
using Sagittarius
using SparseArrays

reg = chain_register(3; spacing=0.5, C6=10.0)
context = reduced_basis_context(reg; blockade_radius=0.6)
H = hamiltonian(reg, [0.2, 0.3, 0.4], [-0.1, 0.0, 0.2]; basis_context=context)
println(size(sparse(H)))
```

Expected output:

```text
(5, 5)
```

## 4. Solver Configuration

```julia
using Sagittarius

reg = chain_register(1; spacing=1.0, C6=0.0)
H_func = build_hamiltonian_func(reg, t -> [0.0], t -> [0.0])
psi0 = ComplexF64[1.0, 0.0]
sol = solve_schrodinger(psi0, H_func, (0.0, 0.1); method="RK4", adaptive=false, dt=0.01)
println(length(sol.t) > 0)
```

Expected output:

```text
true
```

## 5. Observable Callback

```julia
using Sagittarius

reg = chain_register(1; spacing=1.0, C6=0.0)
H_func = build_hamiltonian_func(reg, t -> [0.0], t -> [0.0])
psi0 = ComplexF64[1.0, 0.0]
obs = Dict("pop0" => RydbergPopulation(1, 1))
sol, saved = solve_schrodinger(psi0, H_func, (0.0, 0.1); observables=obs, saveat=[0.0, 0.1])
println(length(saved.t))
```

Expected output:

```text
2
```
