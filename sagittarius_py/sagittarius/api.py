import os
from juliacall import Main as jl

# Path to the Julia core
pkg_path = os.path.join(os.path.dirname(__file__), "..", "..", "Sagittarius.jl")

# Pre-load dependencies into Main
jl.seval("using OrdinaryDiffEq, StaticArrays, DiffEqCallbacks, LinearAlgebra, SparseArrays")

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

def solve(register, psi0, t_start, t_end, omega=1.0, delta=0.0, blockade_radius=0.0, observables=None):
    """
    Solves the dynamics. 
    If blockade_radius > 0, automatically prunes the Hilbert space.
    omega and delta can be constant floats or PulseNode objects.
    """
    N = len(register.jl_obj.atoms)
    
    # 1. Compile pulses or create constant functions
    # Avoid circular imports by doing lazy import or checking type name
    is_pulse = lambda x: hasattr(x, 'jl_obj') and type(x).__name__ in ('Constant', 'Ramp', 'Piecewise')
    
    if is_pulse(omega):
        omega_func = sgr.compile_pulse(omega.jl_obj)
    else:
        # Constant wrapper
        v_omega = float(omega)
        omega_func = jl.seval(f"t -> {v_omega}")
        
    if is_pulse(delta):
        delta_func = sgr.compile_pulse(delta.jl_obj)
    else:
        v_delta = float(delta)
        delta_func = jl.seval(f"t -> {v_delta}")

    # 2. Build the optimized H(t) closure
    H_func = phys.build_hamiltonian_func(register.jl_obj, omega_func, delta_func, blockade_radius=float(blockade_radius))
    
    # We still need to know the basis size for psi0 validation
    if blockade_radius > 0:
        basis, _ = phys.generate_reduced_basis(register.jl_obj, float(blockade_radius))
        basis_size = len(basis)
    else:
        basis_size = 2**N

    jl_obs = None
    if observables:
        if blockade_radius > 0:
            def make_pop_tracker(atom_idx):
                mask = 1 << atom_idx
                indices = [i for i, state in enumerate(basis) if (state & mask) != 0]
                return lambda ψ, t, integrator: sum(abs(ψ[idx])**2 for idx in indices)
            
            jl_obs = jl.Dict[jl.String, jl.Any]({name: make_pop_tracker(idx) for name, idx in observables.items()})
        else:
            jl_obs = jl.Dict[jl.String, jl.Any]({name: solv.RydbergPopulation(idx + 1, N) for name, idx in observables.items()})
        
    if len(psi0) != basis_size:
        raise ValueError(f"Initial state psi0 must have size {basis_size} (current basis size)")

    jl_psi0 = jl.Vector[jl.ComplexF64](psi0)
    result = solv.solve_schrodinger(jl_psi0, H_func, jl.SVector(float(t_start), float(t_end)), observables=jl_obs)
    
    if jl_obs:
        sol, saved = result
        times = list(saved.t)
        data = {name: [v[i] for v in saved.saveval] for i, name in enumerate(observables.keys())}
        data['t'] = times
        return data
    
    return result

def get_basis(register, blockade_radius):
    res = phys.generate_reduced_basis(register.jl_obj, float(blockade_radius))
    return list(res[0])
