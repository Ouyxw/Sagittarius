# Dual SDK Examples

Sagittarius supports two complementary entry points:

- **Python SDK** for notebooks, algorithm prototyping, validation scripts, artifact handling, plotting, and integration with scientific Python tools.
- **Julia native API** for direct access to registers, pulse ASTs, reduced bases, Hamiltonian operators, solver functions, jump operators, GPU entry points, and Julia logging.

Both SDKs share the physical semantics documented in [`python-julia-parity.md`](../api/python-julia-parity.md): atom order is preserved, Python indices are zero-based, Julia indices are one-based, bitstrings use the same ascending integer order, and reduced-basis Hamiltonians, observables, and jump operators should share the same basis context.

## When to Use Each SDK

| Workflow | Python SDK | Julia Native API |
| :--- | :--- | :--- |
| Algorithm prototyping | Preferred for graph/data tooling, quick validation, pandas/NumPy analysis, and artifact writing. | Useful when the prototype needs direct Hamiltonian inspection or custom Julia-side kernels. |
| Experiment-style pulse simulation | Preferred for user-facing pulse construction, input validation, and result manifests. | Preferred for low-level pulse AST compilation and direct solver control. |
| Baseline validation | Preferred for backend-free checks such as dense-vs-reduced validation and MWIS batch verification. | Preferred for exact backend parity checks, reduced-basis inspection, and solver-level comparisons. |
| Hardware-demo preparation | Preferred for diagnostics, run manifests, serialization, and reproducible artifact bundles. | Preferred for backend-specific execution paths after diagnostics pass. |

## Algorithm Prototyping

Use Python when graph construction, exact baselines, and result analysis matter more than direct solver internals. This example builds a four-atom chain from a NetworkX graph, applies a global sin-squared Rabi drive and local detuning ramps, then records atom-0 population.

```python
import numpy as np
import networkx as nx

from sagittarius import Register, Simulation, Pulse, PulseSequence, SolverConfig

n_atoms = 4
spacing = 0.5
blockade_radius = 0.6
duration = 2.0

G = nx.path_graph(n_atoms)
for node in G.nodes:
    G.nodes[node]["pos"] = (spacing * node, 0.0)
    G.nodes[node]["weight"] = 1.0 + 0.1 * node

reg = Register.from_udg_graph(G, C6=10.0, blockade_radius=blockade_radius)
seq = PulseSequence(
    omega=Pulse.global_(Pulse.sin_squared(amplitude=1.0, duration=duration)),
    delta=Pulse.local([Pulse.ramp(start=-2.0, end=G.nodes[i]["weight"], duration=duration) for i in G.nodes]),
)
sim = Simulation(reg, seq, SolverConfig(blockade_radius=blockade_radius))

basis_size = sim.validate()
psi0 = np.zeros(basis_size, dtype=complex)
psi0[0] = 1.0
result = sim.run(psi0, 0.0, duration, observables={"pop0": 0})
print(basis_size)
print(result.to_shared_result()["schema_version"])
print(len(result.data["t"]))
```

Use Julia when the same physical setup needs direct basis, Hamiltonian, or solver access. Julia atom `1` corresponds to Python atom `0`.

```julia
using Sagittarius
using SparseArrays

n_atoms = 4
spacing = 0.5
blockade_radius = 0.6
duration = 2.0

reg = chain_register(n_atoms; spacing=spacing, C6=10.0)
context = reduced_basis_context(reg; blockade_radius=blockade_radius)
omega = compile_pulse(SinSquaredPulse(1.0, duration))
deltas = [compile_pulse(RampPulse(-2.0, 1.0 + 0.1 * (i - 1), duration)) for i in 1:n_atoms]

H_func = build_hamiltonian_func(
    reg,
    t -> fill(omega(t), n_atoms),
    t -> [f(t) for f in deltas];
    basis_context=context,
)
psi0 = ComplexF64[1.0; zeros(ComplexF64, length(context.basis) - 1)]
obs = Dict("pop0" => RydbergPopulation(1, length(reg.atoms); basis_context=context))
sol, saved = solve_schrodinger(psi0, H_func, (0.0, duration); observables=obs, blockade_radius=blockade_radius)

println(length(context.basis))
println(size(sparse(H_func(0.0))))
println(length(saved.t))
```

## Experiment-Style Pulse Simulation

Python validates user-facing pulse shapes before backend initialization and records manifests with simulation results.

```python
import numpy as np
from sagittarius import Register, Simulation, Pulse, PulseSequence, SolverConfig

n_atoms = 3
spacing = 0.7
blockade_radius = 0.8
duration = 1.5

reg = Register.chain(n_atoms, spacing=spacing, C6=20.0)
seq = PulseSequence(
    omega=Pulse.global_(Pulse.blackman(amplitude=1.2, duration=duration)),
    delta=Pulse.local([
        Pulse.ramp(start=-2.0, end=0.5, duration=duration),
        Pulse.ramp(start=-2.0, end=0.8, duration=duration),
        Pulse.ramp(start=-2.0, end=1.1, duration=duration),
    ]),
)
sim = Simulation(reg, seq, SolverConfig(blockade_radius=blockade_radius, reltol=1e-7, abstol=1e-7))
sim.validate_inputs(sample_time=0.0, observables={"center": 1})

basis_size = sim.validate()
psi0 = np.zeros(basis_size, dtype=complex)
psi0[0] = 1.0
result = sim.run(psi0, 0.0, duration, observables={"center": 1})
print(basis_size)
print(result.manifest["solver"]["blockade_radius"])
print(len(result.data["t"]))
```

Julia exposes the pulse ASTs and solver call directly.

```julia
using Sagittarius

n_atoms = 3
spacing = 0.7
blockade_radius = 0.8
duration = 1.5

reg = chain_register(n_atoms; spacing=spacing, C6=20.0)
context = reduced_basis_context(reg; blockade_radius=blockade_radius)
omega = compile_pulse(BlackmanPulse(1.2, duration))
deltas = [
    compile_pulse(RampPulse(-2.0, 0.5, duration)),
    compile_pulse(RampPulse(-2.0, 0.8, duration)),
    compile_pulse(RampPulse(-2.0, 1.1, duration)),
]
H_func = build_hamiltonian_func(reg, t -> fill(omega(t), n_atoms), t -> [f(t) for f in deltas]; basis_context=context)
psi0 = ComplexF64[1.0; zeros(ComplexF64, length(context.basis) - 1)]
obs = Dict("center" => RydbergPopulation(2, length(reg.atoms); basis_context=context))
sol, saved = solve_schrodinger(psi0, H_func, (0.0, duration); observables=obs, reltol=1e-7, abstol=1e-7, blockade_radius=blockade_radius)
println(length(context.basis))
println(blockade_radius)
println(length(saved.t))
```

## Baseline Validation

Use Python for packaged validation reports and exact classical comparisons.

```python
from sagittarius import Register, PulseSequence, dense_vs_reduced_validation

report = dense_vs_reduced_validation(
    Register.chain(3, spacing=0.5, C6=10.0),
    PulseSequence(omega=[0.2, 0.3, 0.4], delta=[-0.1, 0.0, 0.2]),
    blockade_radius=0.6,
    duration=0.7,
)
print(report["ok"])
print(report["basis"])
```

Use Julia for low-level parity checks over the same basis order.

```julia
using Sagittarius
using SparseArrays

reg = chain_register(3; spacing=0.5, C6=10.0)
context = reduced_basis_context(reg; blockade_radius=0.6)
H = hamiltonian(reg, [0.2, 0.3, 0.4], [-0.1, 0.0, 0.2]; basis_context=context)
obs = RydbergPopulation(1, length(reg.atoms); basis_context=context)

println(context.basis)
println(size(sparse(H)))
println(obs(ComplexF64[1.0; zeros(ComplexF64, length(context.basis) - 1)], 0.0, nothing))
```

For MWIS-style validation, use `projects/mwis_udg/batch_verify.py` to compare AQC outputs against exact PuLP/CBC ILP solutions across seeded UDG instances. This is a Python project workflow rather than a Julia-native parity snippet.

```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path("sagittarius_py/projects/mwis_udg").resolve()))
from batch_verify import verify_mwis_batch

report = verify_mwis_batch(n_instances=4, n_nodes=6, seed=2026)
print(report.to_dict()["schema_version"])
```

## Hardware-Demo Preparation

Before enabling hardware-specific execution paths, use Python diagnostics and artifact contracts to make the runtime state explicit.

```python
import numpy as np
from sagittarius import Register, Simulation, PulseSequence, SolverConfig, doctor, version_info

n_atoms = 4
spacing = 0.7
blockade_radius = 0.8
duration = 1.0

print(version_info()["schema_version"])
report = doctor(backend="CUDA", initialize_backend=True)
print(report["schema_version"])
print(report["available"])

cfg = SolverConfig(use_gpu=True, gpu_backend="CUDA", blockade_radius=blockade_radius, reltol=1e-7, abstol=1e-7)
if report["available"]:
    reg = Register.chain(n_atoms, spacing=spacing, C6=20.0)
    sim = Simulation(reg, PulseSequence(omega=1.0, delta=0.0), cfg)
    basis_size = sim.validate()
    psi0 = np.zeros(basis_size, dtype=complex)
    psi0[0] = 1.0
    result = sim.run(psi0, 0.0, duration, observables={"pop0": 0})
    print(len(result.data["t"]))
```

Only run Julia CUDA solver calls after diagnostics indicate the CUDA backend is available in the target environment.

```julia
using Sagittarius

n_atoms = 4
spacing = 0.7
blockade_radius = 0.8
duration = 1.0

reg = chain_register(n_atoms; spacing=spacing, C6=20.0)
context = reduced_basis_context(reg; blockade_radius=blockade_radius)
H_func = build_hamiltonian_func(reg, t -> fill(1.0, n_atoms), t -> zeros(n_atoms); basis_context=context, use_gpu=true)
psi0 = ComplexF64[1.0; zeros(ComplexF64, length(context.basis) - 1)]
obs = Dict("pop0" => RydbergPopulation(1, length(reg.atoms); basis_context=context))

# Requires CUDA.jl and a working CUDA device in the active Julia environment.
sol, saved = solve_schrodinger_gpu(psi0, H_func, (0.0, duration); observables=obs, reltol=1e-7, abstol=1e-7, blockade_radius=blockade_radius)
println(length(saved.t))
```

## Cross-SDK Review Checklist

Before adding a dual SDK example or claiming parity, check:

- Python atom `0` corresponds to Julia atom `1`; local pulse vectors preserve register order.
- Both snippets use the same `C6`, coordinates, blockade radius, pulse values, solver tolerances, and time span.
- Reduced-basis snippets share a `BasisContext` on the Julia side and use the Python `Simulation.validate()` basis size on the Python side.
- Result files use `result-artifact/v1`, embedded `shared-result/v1`, and validated `run-manifest/v1` when produced by Python.
- Performance statements cite `benchmark-artifact/v1` or `mwis-batch-verification/v1` evidence as described in [`performance-claims.md`](../governance/performance-claims.md).
