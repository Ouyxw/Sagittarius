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


## 6. Visualization-Ready Observable Series

Sagittarius.jl does not yet expose a dedicated Julia plotting API. Current Julia-native solver outputs are visualization-ready: `saved.t` stores output times and `saved.saveval` stores observable values in declaration order. These arrays can be passed to plotting packages such as Plots.jl or Makie.jl. The example below keeps the check dependency-free by printing a small ASCII population bar.

```julia
using Sagittarius

reg = chain_register(1; spacing=1.0, C6=0.0)
H_func = build_hamiltonian_func(reg, t -> [2π], t -> [0.0])
psi0 = ComplexF64[1.0, 0.0]
obs = Dict("pop0" => RydbergPopulation(1, 1))

sol, saved = solve_schrodinger(
    psi0,
    H_func,
    (0.0, 0.5);
    observables=obs,
    saveat=[0.0, 0.25, 0.5],
    reltol=1e-8,
    abstol=1e-8,
)

times = collect(saved.t)
populations = [Float64(values[1]) for values in saved.saveval]

for (t, pop) in zip(times, populations)
    width = round(Int, 10 * pop)
    println(round(t, digits=2), " ", repeat("#", width), " ", round(pop, digits=2))
end
```

Expected output shape:

```text
0.0  0.0
0.25 ##### 0.5
0.5 ########## 1.0
```

Small numerical variation is expected if solver tolerances or output times change. For graphical output, use the same `times` and `populations` arrays with a plotting package in the user's Julia project.
