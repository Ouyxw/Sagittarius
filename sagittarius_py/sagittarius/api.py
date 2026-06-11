import json
import numbers
from collections.abc import Sequence as ABCSequence
from dataclasses import dataclass
from typing import Optional, Dict, Union, Any, List

import numpy as np
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


def _is_bool(value: Any) -> bool:
    return isinstance(value, (bool, np.bool_))


def _is_numeric_scalar(value: Any) -> bool:
    return isinstance(value, numbers.Real) and not _is_bool(value)


def _validate_atom_index(index: Any, N: int, *, context: str) -> int:
    if _is_bool(index) or not isinstance(index, (int, np.integer)):
        raise ValueError(f"{context} atom index must be an integer in [0, {N - 1}], got {index!r}")
    idx = int(index)
    if idx < 0 or idx >= N:
        raise ValueError(f"{context} atom index {idx} is out of range for {N} atoms")
    return idx


def _validate_pulse_value(value: Any, *, field_name: str, atom_index: Optional[int] = None) -> None:
    from .pulse import is_pulse

    if is_pulse(value) or _is_numeric_scalar(value):
        return

    suffix = "" if atom_index is None else f" for atom {atom_index}"
    raise ValueError(
        f"PulseSequence.{field_name}{suffix} must be a numeric scalar or Pulse node, got {type(value).__name__}"
    )


def _coerce_callable_vector(values: Any, N: int, *, field_name: str) -> List[float]:
    if isinstance(values, np.ndarray):
        raw_values = values.tolist()
    elif isinstance(values, ABCSequence) and not isinstance(values, (str, bytes, bytearray)):
        raw_values = list(values)
    else:
        raise ValueError(
            f"Callable PulseSequence.{field_name} must return a sequence of {N} numeric values, "
            f"got {type(values).__name__}"
        )

    if len(raw_values) != N:
        raise ValueError(
            f"Callable PulseSequence.{field_name} returned {len(raw_values)} values for {N} atoms"
        )

    coerced = []
    for i, value in enumerate(raw_values):
        if not _is_numeric_scalar(value):
            raise ValueError(
                f"Callable PulseSequence.{field_name} value for atom {i} must be numeric, got {type(value).__name__}"
            )
        coerced.append(float(value))
    return coerced


def _validate_pulse_config(p_config: Any, N: int, *, field_name: str, sample_time: Optional[float] = None) -> None:
    from .pulse import is_pulse

    if callable(p_config):
        if sample_time is not None:
            _coerce_callable_vector(p_config(float(sample_time)), N, field_name=field_name)
        return

    if isinstance(p_config, dict):
        for key, value in p_config.items():
            idx = _validate_atom_index(key, N, context=f"PulseSequence.{field_name}")
            _validate_pulse_value(value, field_name=field_name, atom_index=idx)
        return

    if isinstance(p_config, list):
        if len(p_config) != N:
            raise ValueError(f"PulseSequence.{field_name} list length {len(p_config)} does not match {N} atoms")
        for idx, value in enumerate(p_config):
            _validate_pulse_value(value, field_name=field_name, atom_index=idx)
        return

    if is_pulse(p_config) or _is_numeric_scalar(p_config):
        return

    raise ValueError(
        f"PulseSequence.{field_name} must be a scalar, Pulse node, list, dict, or callable; "
        f"got {type(p_config).__name__}"
    )


def _local_pulse_values_in_register_order(p_config: Union[Dict[int, Any], List[Any]], N: int) -> List[Any]:
    if isinstance(p_config, dict):
        return [p_config.get(i, 0.0) for i in range(N)]
    return list(p_config)

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

    def validate_inputs(self, *, sample_time: Optional[float] = None, observables: Optional[Dict[str, int]] = None) -> None:
        N = len(self.register.atoms)
        _validate_pulse_config(self.sequence.omega, N, field_name="omega", sample_time=sample_time)
        _validate_pulse_config(self.sequence.delta, N, field_name="delta", sample_time=sample_time)
        if observables:
            for name, idx in observables.items():
                if not isinstance(name, str):
                    raise ValueError(f"Observable names must be strings, got {type(name).__name__}")
                _validate_atom_index(idx, N, context=f"Observable {name!r}")

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
            # Callable pulses return one numeric value per Python atom index, in Register.atoms order.
            return jl.seval("""
                (f, n) -> (t -> begin
                    vals = [pyconvert(Float64, x) for x in f(t)]
                    length(vals) == n || throw(ArgumentError("callable pulse returned $(length(vals)) values for $n atoms"))
                    vals
                end)
            """)(p_config, int(N))

        if isinstance(p_config, (dict, list)):
            # Local addressing follows Python's 0-based Register.atoms order.
            compiled_funcs = []
            for i, p in enumerate(_local_pulse_values_in_register_order(p_config, N)):
                if is_pulse(p):
                    compiled_funcs.append(sgr.compile_pulse(p.jl_obj))
                else:
                    v = float(p)
                    compiled_funcs.append(sgr.compile_pulse(sgr.ConstantPulse(v, 1e12)))

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
        self.validate_inputs(sample_time=float(t_start), observables=observables)
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
