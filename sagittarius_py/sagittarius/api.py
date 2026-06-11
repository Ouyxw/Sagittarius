import numpy as np
import json
from dataclasses import dataclass
from typing import Optional, Dict, Union, Any, List
from .runtime import doctor, get_julia, get_modules, log_event, version_info

@dataclass
class Atom:
    x: float
    y: float
    z: float = 0.0

    @property
    def jl_obj(self):
        jl, _, phys, _ = get_modules()
        return phys.Atom(jl.SVector(float(self.x), float(self.y), float(self.z)))

@dataclass
class Register:
    atoms: List[Atom]
    C6: float = 1.0

    @property
    def jl_obj(self):
        jl, _, phys, _ = get_modules()
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
    def __init__(
        self,
        data: Dict[str, List[float]],
        metadata: Optional[Dict[str, Any]] = None,
        diagnostics: Optional[Dict[str, Any]] = None,
    ):
        self.data = data
        self.metadata = metadata or {}
        self.diagnostics = diagnostics or {}
        self.t = np.array(data.get('t', []))
    
    def to_pandas(self):
        import pandas as pd

        return pd.DataFrame(self.data)
    
    def save(self, filepath: str):
        """Save results to a JSON file."""
        # Convert numpy arrays to lists for JSON serialization
        serializable_data = {k: list(v) if isinstance(v, (np.ndarray, list)) else v 
                             for k, v in self.data.items()}
        if self.metadata or self.diagnostics:
            serializable_data = {
                "data": serializable_data,
                "metadata": self.metadata,
                "diagnostics": self.diagnostics,
            }
        with open(filepath, 'w') as f:
            json.dump(serializable_data, f)
    
    @classmethod
    def load(cls, filepath: str):
        """Load results from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict) and "data" in data:
            return cls(data["data"], metadata=data.get("metadata"), diagnostics=data.get("diagnostics"))
        return cls(data)

    def plot(self, show: bool = True):
        import matplotlib.pyplot as plt

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
    def __init__(self, register: Register, sequence: PulseSequence, config: SolverConfig = SolverConfig()):
        self.register = register
        self.sequence = sequence
        self.config = config
        self._basis = None
        self._mapping = None

    def validate(self) -> int:
        """Returns the size of the Hilbert space after pruning."""
        if self.config.blockade_radius > 0:
            _, _, phys, _ = get_modules()
            res = phys.generate_reduced_basis(self.register.jl_obj, float(self.config.blockade_radius))
            self._basis = res[0]
            self._mapping = res[1]
            return len(self._basis)
        else:
            return 2**len(self.register.atoms)

    def _get_compiled_func(self, p_config: Any, N: int) -> Any:
        """Compiles a pulse configuration into a Julia-side closure t -> Vector{Float64}."""
        from .pulse import is_pulse
        jl, sgr = get_julia()

        if callable(p_config):
            # Use pyconvert to bridge the Py -> Float64 gap for each element
            return jl.seval("f -> (t -> [pyconvert(Float64, x) for x in f(t)])")(p_config)

        if isinstance(p_config, (dict, list)):
            # Local addressing
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

    def run(self, psi0: np.ndarray, t_start: float, t_end: float, observables: Optional[Dict[str, int]] = None) -> SimulationResult:
        jl, sgr, phys, solv = get_modules()
        backend_report = doctor(backend=self.config.gpu_backend if self.config.use_gpu else "CPU")
        log_event(
            "solver_start",
            backend=backend_report["requested_backend"],
            use_gpu=self.config.use_gpu,
            reltol=self.config.reltol,
            abstol=self.config.abstol,
            blockade_radius=self.config.blockade_radius,
        )
        N = len(self.register.jl_obj.atoms)
        basis_size = self.validate()
        diagnostics = dict(backend_report)
        diagnostics["simulation"] = {
            "solver_method": self.config.method,
            "reltol": self.config.reltol,
            "abstol": self.config.abstol,
            "basis_size": basis_size,
            "full_basis_size": 2**N,
            "reduced_basis_pruning_ratio": 1.0 - (basis_size / (2**N)),
            "use_gpu": self.config.use_gpu,
            "use_mc": self.config.use_mc,
        }
        
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
                    data = {name: [avg_res[t_idx][i] for t_idx in range(len(times))] 
                            for i, name in enumerate(observables.keys())}
                    data['t'] = times
                    log_event("solver_finish", result_type="mcwf_observables", basis_size=basis_size)
                    return SimulationResult(data, metadata=version_info(), diagnostics=diagnostics)
                log_event("solver_finish", result_type="raw_mcwf", basis_size=basis_size)
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
                    jl.seval("using CUDA")
                    jl_psi0 = jl.CUDA.CuVector[jl.ComplexF64](psi0)
                elif backend == "AMDGPU":
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
            log_event("solver_finish", result_type="observables", basis_size=basis_size)
            return SimulationResult(data, metadata=version_info(), diagnostics=diagnostics)
        
        log_event("solver_finish", result_type="raw", basis_size=basis_size)
        return result

def solve(register, sequence, config=SolverConfig(), psi0=None, t_start=0.0, t_end=1.0, observables=None):
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
    _, _, phys, _ = get_modules()
    res = phys.generate_reduced_basis(register.jl_obj, float(blockade_radius))
    return list(res[0])

def load_result(filepath: str) -> SimulationResult:
    """Load a SimulationResult from a file."""
    return SimulationResult.load(filepath)
