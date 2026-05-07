import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from numbers import Integral
from dataclasses import dataclass
from typing import Optional, Dict, Union, Any, List
from juliacall import Main as jl

def _julia_package_path() -> str:
    env_path = os.environ.get("SAGITTARIUS_JL_PATH")
    candidates = [
        env_path,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Sagittarius.jl")),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(os.path.join(candidate, "src", "Sagittarius.jl")):
            return candidate
    raise RuntimeError(
        "Could not find Sagittarius.jl. Set SAGITTARIUS_JL_PATH to the Julia package directory "
        "or run from the source checkout."
    )


pkg_path = _julia_package_path()

# Pre-load Julia dependencies. juliapkg.json owns dependency resolution; imports
# should not mutate the user's Julia environment.
jl.seval("""
using OrdinaryDiffEq, StaticArrays, DiffEqCallbacks, LinearAlgebra, SparseArrays, SciMLBase, CUDA, Distributed
""")

# Manually include the Sagittarius module
jl.include(os.path.join(pkg_path, "src", "Sagittarius.jl"))
sgr = jl.Sagittarius
phys = sgr.Physics  # Direct access to the Physics module
solv = sgr.Solver   # Direct access to the Solver module

@dataclass
class Atom:
    x: float
    y: float
    z: float = 0.0

    @property
    def jl_obj(self):
        return phys.Atom(jl.SVector(float(self.x), float(self.y), float(self.z)))

@dataclass
class Register:
    atoms: List[Atom]
    C6: float = 1.0

    @property
    def jl_obj(self):
        jl_atoms = jl.Vector[phys.Atom]([a.jl_obj for a in self.atoms])
        return phys.Register(jl_atoms, float(self.C6))

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

    def validate(self) -> int:
        """Returns the size of the Hilbert space after pruning."""
        if not self.register.atoms:
            raise ValueError("Register must contain at least one atom")
        if self.config.blockade_radius < 0:
            raise ValueError("blockade_radius must be non-negative")
        if self.config.blockade_radius > 0:
            res = phys.generate_reduced_basis(self.register.jl_obj, float(self.config.blockade_radius))
            self._basis = res[0]
            self._mapping = res[1]
            return len(self._basis)
        else:
            self._basis = None
            self._mapping = None
            return 2**len(self.register.atoms)

    def _get_compiled_func(self, p_config: Any, N: int) -> Any:
        """Compiles a pulse configuration into a Julia-side closure t -> Vector{Float64}."""
        from .pulse import is_pulse

        if callable(p_config):
            # Use pyconvert to bridge the Py -> Float64 gap for each element
            return jl.seval("f -> (t -> [pyconvert(Float64, x) for x in f(t)])")(p_config)

        if isinstance(p_config, (dict, list)):
            # Local addressing
            if isinstance(p_config, list) and len(p_config) != N:
                raise ValueError(f"Local pulse list must have length {N}")
            compiled_funcs = []
            for i in range(N):
                p = p_config.get(i, 0.0) if isinstance(p_config, dict) else p_config[i]
                if is_pulse(p):
                    compiled_funcs.append(sgr.compile_pulse(p.jl_obj))
                else:
                    v = float(p)
                    compiled_funcs.append(sgr.compile_pulse(sgr.ConstantPulse(v, 1e12)))

            compiled_funcs.reverse()
            jl_vec = jl.Vector[jl.Any](compiled_funcs)
            return jl.seval("funcs -> (t -> Float64[f(t) for f in funcs])")(jl_vec)
        else:
            # Global addressing
            if is_pulse(p_config):
                f = sgr.compile_pulse(p_config.jl_obj)
                jl_vec = jl.Vector[jl.Any]([f for _ in range(N)])
                return jl.seval("funcs -> (t -> Float64[f(t) for f in funcs])")(jl_vec)
            else:
                v = float(p_config)
                return sgr.create_const_vec_func(v, N)

    def _validate_config(self):
        supported_methods = {"TSIT5", "DP5", "VERN7", "VERN9"}
        method = str(self.config.method).upper()
        if method not in supported_methods:
            raise ValueError(
                f"Unsupported solver method: {self.config.method}. "
                "Supported methods: Tsit5, DP5, Vern7, Vern9."
            )
        if self.config.n_trajectories < 1:
            raise ValueError("n_trajectories must be at least 1")
        if self.config.reltol <= 0 or self.config.abstol <= 0:
            raise ValueError("reltol and abstol must be positive")
        if self.config.use_gpu and self.config.gpu_backend.upper() != "CUDA":
            raise NotImplementedError(
                "Only CUDA is currently wired through the optimized GPU solver. "
                "AMDGPU and Metal remain experimental Julia dependencies."
            )

    def _validate_observables(self, observables: Optional[Dict[str, int]], N: int):
        if observables is None:
            return
        for name, idx in observables.items():
            if not isinstance(name, str):
                raise ValueError("Observable names must be strings")
            if not isinstance(idx, Integral) or idx < 0 or idx >= N:
                raise ValueError(f"Observable '{name}' atom index must be an integer in [0, {N - 1}]")

    def run(self, psi0: np.ndarray, t_start: float, t_end: float, observables: Optional[Dict[str, int]] = None) -> SimulationResult:
        self._validate_config()
        if t_end <= t_start:
            raise ValueError("t_end must be greater than t_start")
        N = len(self.register.jl_obj.atoms)
        basis_size = self.validate()
        self._validate_observables(observables, N)
        psi0 = np.asarray(psi0, dtype=np.complex128)
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
                    abstol=float(self.config.abstol),
                    method=str(self.config.method)
                )
                
                if jl_obs:
                    t_vals, avg_res = result
                    times = list(t_vals)
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
                    abstol=float(self.config.abstol),
                    method=str(self.config.method)
                )
        else:
            # Solve Schrodinger Equation
            if self.config.use_gpu:
                backend = self.config.gpu_backend.upper()
                if backend == "CUDA":
                    jl_psi0 = jl.CUDA.CuVector[jl.ComplexF64](psi0)
                else:
                    raise ValueError(f"Unsupported GPU backend: {backend}")

                result = solv.solve_schrodinger_gpu(
                    jl_psi0,
                    H_func,
                    jl.SVector(float(t_start), float(t_end)),
                    observables=jl_obs,
                    reltol=float(self.config.reltol),
                    abstol=float(self.config.abstol),
                    method=str(self.config.method)
                )
            else:
                jl_psi0 = jl.Vector[jl.ComplexF64](psi0)
                result = solv.solve_schrodinger(
                    jl_psi0, 
                    H_func, 
                    jl.SVector(float(t_start), float(t_end)), 
                    observables=jl_obs,
                    reltol=float(self.config.reltol),
                    abstol=float(self.config.abstol),
                    method=str(self.config.method)
                )
        
        if jl_obs:
            sol, saved = result
            times = list(saved.t)
            data = {name: [v[i] for v in saved.saveval] for i, name in enumerate(observables.keys())}
            data['t'] = times
            return SimulationResult(data)
        
        return result

def solve(register, sequence, config=None, psi0=None, t_start=0.0, t_end=1.0, observables=None):
    sim = Simulation(register, sequence, config)
    if psi0 is None:
        dim = sim.validate()
        psi0 = np.zeros(dim, dtype=complex)
        psi0[0] = 1.0
    
    res = sim.run(psi0, t_start, t_end, observables)
    
    if isinstance(res, SimulationResult):
        return res.data
    return res

def get_basis(register, blockade_radius):
    res = phys.generate_reduced_basis(register.jl_obj, float(blockade_radius))
    return list(res[0])

def load_result(filepath: str) -> SimulationResult:
    """Load a SimulationResult from a file."""
    return SimulationResult.load(filepath)
