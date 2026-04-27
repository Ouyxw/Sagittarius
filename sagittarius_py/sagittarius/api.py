import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import Optional, Dict, Union, Any, List
from juliacall import Main as jl

# Path to the Julia core
pkg_path = os.path.join(os.path.dirname(__file__), "..", "..", "Sagittarius.jl")

# Pre-load dependencies into Main
jl.seval("""
using Pkg
function ensure_pkg(pkg_name)
    if !haskey(Pkg.project().dependencies, pkg_name)
        Pkg.add(pkg_name)
    end
end

ensure_pkg("SciMLBase")
ensure_pkg("CUDA")
ensure_pkg("Distributed")
# We don't auto-install AMDGPU/Metal yet to avoid heavy downloads unless needed
# but we ensure the environment is ready for them.

using OrdinaryDiffEq, StaticArrays, DiffEqCallbacks, LinearAlgebra, SparseArrays, SciMLBase, CUDA, Distributed
""")

# Manually include the Sagittarius module
jl.include(os.path.join(pkg_path, "src", "Sagittarius.jl"))
sgr = jl.Sagittarius
phys = sgr.Physics  # Direct access to the Physics module
solv = sgr.Solver   # Direct access to the Solver module

class Atom:
    def __init__(self, x, y, z=0.0):
        self._atom = phys.Atom(jl.SVector(float(x), float(y), float(z)))
    
    @property
    def jl_obj(self):
        return self._atom

class Register:
    def __init__(self, atoms, C6=1.0):
        jl_atoms = jl.Vector[phys.Atom[3]]([a.jl_obj for a in atoms])
        self._register = phys.Register(jl_atoms, float(C6))
    
    @property
    def jl_obj(self):
        return self._register

@dataclass
class SolverConfig:
    reltol: float = 1e-8
    abstol: float = 1e-8
    blockade_radius: float = 0.0
    method: str = "Tsit5"
    gamma: Union[float, List[float]] = 0.0      # T1 decay rate
    gamma_phi: Union[float, List[float]] = 0.0  # T2 dephasing rate
    use_mc: bool = False                        # Use Monte Carlo Trajectories instead of Lindblad
    n_trajectories: int = 100                   # Number of trajectories for Monte Carlo
    use_gpu: bool = False                       # Use GPU acceleration
    gpu_backend: str = "CUDA"                   # GPU backend: "CUDA", "AMDGPU", or "Metal"

@dataclass
class PulseSequence:
    omega: Any = 1.0
    delta: Any = 0.0

import json

class SimulationResult:
    def __init__(self, data: Dict[str, List[float]]):
        self.data = data
        self.t = np.array(data.get('t', []))
    
    def to_pandas(self) -> pd.DataFrame:
        return pd.DataFrame(self.data)
    
    def save(self, filepath: str):
        """Save results to a JSON file."""
        # Convert numpy arrays to lists for JSON serialization
        serializable_data = {k: list(v) if isinstance(v, (np.ndarray, list)) else v 
                             for k, v in self.data.items()}
        with open(filepath, 'w') as f:
            json.dump(serializable_data, f)
    
    @classmethod
    def load(cls, filepath: str):
        """Load results from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(data)

    def plot(self, show: bool = True):
        plt.figure(figsize=(10, 6))
        for key, values in self.data.items():
            if key == 't':
                continue
            plt.plot(self.t, values, label=key)
        plt.xlabel("Time (μs)")
        plt.ylabel("Observable Value")
        plt.title("Simulation Results")
        plt.legend()
        plt.grid(True)
        if show:
            plt.show()

class Simulation:
    def __init__(self, register: Register, sequence: PulseSequence, config: Optional[SolverConfig] = None):
        self.register = register
        self.sequence = sequence
        self.config = config or SolverConfig()
        self._basis = None
        self._mapping = None
    
    def validate(self):
        N = len(self.register.jl_obj.atoms)
        if self.config.blockade_radius <= 0:
            basis_size = 2**N
            if basis_size > 10000:
                print(f"Warning: Large Hilbert space (size {basis_size}) without blockade pruning.")
        else:
            # We pre-calculate basis to validate size and reuse in run()
            res = phys.generate_reduced_basis(self.register.jl_obj, float(self.config.blockade_radius))
            self._basis = res[0]
            self._mapping = res[1]
            basis_size = len(self._basis)
        
        return basis_size

    def _get_compiled_func(self, p_config, N):
        is_pulse = lambda x: hasattr(x, 'jl_obj')
        if isinstance(p_config, dict):
            # Local addressing
            compiled_funcs = []
            for i in range(N):
                p = p_config.get(i, 0.0)
                if is_pulse(p):
                    compiled_funcs.append(sgr.compile_pulse(p.jl_obj))
                else:
                    v = float(p)
                    compiled_funcs.append(sgr.compile_pulse(sgr.ConstantPulse(v, 1e12)))

            # Atom 0 corresponds to bit 0, but Julia's 1-indexing and 
            # our bitwise mapping requires careful alignment.
            # Empirical evidence shows a reversal is needed for Python-Julia bridge.
            compiled_funcs.reverse()
            
            jl_vec = jl.Vector[jl.Any](compiled_funcs)
            return jl.seval("funcs -> (t -> Float64[f(t) for f in funcs])")(jl_vec)
        else:
            # Global addressing
            if is_pulse(p_config):
                f = sgr.compile_pulse(p_config.jl_obj)
                # Correctly handle global pulse by creating N identical Julia functions
                jl_vec = jl.Vector[jl.Any]([f for _ in range(N)])
                return jl.seval("funcs -> (t -> Float64[f(t) for f in funcs])")(jl_vec)
            else:
                v = float(p_config)
                return sgr.create_const_vec_func(v, N)

    def run(self, psi0: np.ndarray, t_start: float, t_end: float, observables: Optional[Dict[str, int]] = None) -> SimulationResult:
        N = len(self.register.jl_obj.atoms)
        basis_size = self.validate()
        
        if len(psi0) != basis_size:
            raise ValueError(f"Initial state psi0 must have size {basis_size} (current basis size)")

        # 1. Compile pulses
        omega_func = self._get_compiled_func(self.sequence.omega, N)
        delta_func = self._get_compiled_func(self.sequence.delta, N)

        # 2. Build Hamiltonian
        H_func = phys.build_hamiltonian_func(
            self.register.jl_obj, 
            omega_func, 
            delta_func, 
            blockade_radius=float(self.config.blockade_radius),
            use_gpu=bool(self.config.use_gpu)
        )

        # 3. Handle observables
        jl_obs = None
        if observables:
            if self.config.blockade_radius > 0:
                jl_obs = jl.Dict[jl.String, jl.Any]({
                    name: solv.RydbergPopulation(idx + 1, N, basis=self._basis) 
                    for name, idx in observables.items()
                })
            else:
                jl_obs = jl.Dict[jl.String, jl.Any]({
                    name: solv.RydbergPopulation(idx + 1, N) 
                    for name, idx in observables.items()
                })

        # 4. Determine if we use Lindblad, MC, or Schrodinger
        is_noisy = (np.any(np.array(self.config.gamma) > 0) or 
                    np.any(np.array(self.config.gamma_phi) > 0))

        if is_noisy:
            # Get jump operators
            if self.config.blockade_radius > 0:
                j_ops = phys.get_jump_operators(N, self.config.gamma, self.config.gamma_phi, 
                                               basis=self._basis, mapping=self._mapping)
            else:
                j_ops = phys.get_jump_operators(N, self.config.gamma, self.config.gamma_phi)

            if self.config.use_mc:
                # Solve Monte Carlo Trajectories
                jl_psi0 = jl.Vector[jl.ComplexF64](psi0)
                result = solv.solve_mc_trajectories(
                    jl_psi0,
                    H_func,
                    j_ops,
                    jl.SVector(float(t_start), float(t_end)),
                    n_trajectories=int(self.config.n_trajectories),
                    observables=jl_obs,
                    reltol=float(self.config.reltol),
                    abstol=float(self.config.abstol)
                )
                
                if jl_obs:
                    t_vals, avg_res = result
                    times = list(t_vals)
                    # avg_res is a Vector of Vectors in Julia
                    data = {name: [avg_res[t_idx][i] for t_idx in range(len(times))] 
                            for i, name in enumerate(observables.keys())}
                    data['t'] = times
                    return SimulationResult(data)
                return result

            else:
                # Solve Lindblad Master Equation
                rho0 = np.outer(psi0, psi0.conj())
                jl_rho0 = jl.convert(jl.Matrix[jl.ComplexF64], rho0)
                
                result = solv.solve_lindblad(
                    jl_rho0,
                    H_func,
                    j_ops,
                    jl.SVector(float(t_start), float(t_end)),
                    observables=jl_obs,
                    reltol=float(self.config.reltol),
                    abstol=float(self.config.abstol)
                )
        else:
            # Solve Schrodinger Equation
            if self.config.use_gpu:
                backend = self.config.gpu_backend.upper()
                if backend == "CUDA":
                    jl_psi0 = jl.CUDA.CuVector[jl.ComplexF64](psi0)
                elif backend == "AMDGPU":
                    # Dynamic pre-loading if needed
                    jl.seval("using AMDGPU")
                    jl_psi0 = jl.AMDGPU.ROCVector[jl.ComplexF64](psi0)
                elif backend == "METAL":
                    jl.seval("using Metal")
                    jl_psi0 = jl.Metal.MtlVector[jl.ComplexF64](psi0)
                else:
                    raise ValueError(f"Unsupported GPU backend: {backend}")

                result = solv.solve_schrodinger_gpu(
                    jl_psi0,
                    H_func,
                    jl.SVector(float(t_start), float(t_end)),
                    observables=jl_obs,
                    reltol=float(self.config.reltol),
                    abstol=float(self.config.abstol)
                )
            else:
                jl_psi0 = jl.Vector[jl.ComplexF64](psi0)
                result = solv.solve_schrodinger(
                    jl_psi0, 
                    H_func, 
                    jl.SVector(float(t_start), float(t_end)), 
                    observables=jl_obs,
                    reltol=float(self.config.reltol),
                    abstol=float(self.config.abstol)
                )
        
        if jl_obs:
            sol, saved = result
            times = list(saved.t)
            data = {name: [v[i] for v in saved.saveval] for i, name in enumerate(observables.keys())}
            data['t'] = times
            return SimulationResult(data)
        
        return result

def solve(register, psi0, t_start, t_end, omega=1.0, delta=0.0, blockade_radius=0.0, observables=None):
    """
    Backward compatible solve function.
    """
    config = SolverConfig(blockade_radius=blockade_radius)
    sequence = PulseSequence(omega=omega, delta=delta)
    sim = Simulation(register, sequence, config)
    
    res = sim.run(psi0, t_start, t_end, observables=observables)
    
    if isinstance(res, SimulationResult):
        return res.data
    return res

def get_basis(register, blockade_radius):
    res = phys.generate_reduced_basis(register.jl_obj, float(blockade_radius))
    return list(res[0])

def load_result(filepath: str) -> SimulationResult:
    """Load a SimulationResult from a file."""
    return SimulationResult.load(filepath)
