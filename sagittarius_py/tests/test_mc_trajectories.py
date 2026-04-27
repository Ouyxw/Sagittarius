import numpy as np
import pytest
from sagittarius import Atom, Register, Simulation, PulseSequence, SolverConfig

def test_mc_vs_lindblad():
    # 1. Setup a simple system: 1 atom, no drive, just decay
    reg = Register([Atom(0,0)], C6=0.0)
    seq = PulseSequence(omega=0.0, delta=0.0) # No drive
    
    # Start in excited state |r>
    psi0 = np.array([0, 1], dtype=complex)
    
    gamma = 0.5
    t_end = 4.0
    
    # Lindblad simulation
    config_lindblad = SolverConfig(gamma=gamma)
    sim_lindblad = Simulation(reg, seq, config_lindblad)
    res_lindblad = sim_lindblad.run(psi0, 0.0, t_end, observables={"pop": 0}) # pop 0 is Rydberg? Wait, let's check mapping.
    # In Sagittarius, RydbergPopulation(idx) calculates population of Rydberg state for atom idx.
    # Actually, pop 0 in observables means atom index 0.
    
    # MC simulation
    config_mc = SolverConfig(gamma=gamma, use_mc=True, n_trajectories=500)
    sim_mc = Simulation(reg, seq, config_mc)
    res_mc = sim_mc.run(psi0, 0.0, t_end, observables={"pop": 0})
    
    # Compare populations
    # Theoretical: P(r) = exp(-gamma * t)
    t_l = np.array(res_lindblad.data['t'])
    pop_l = np.array(res_lindblad.data['pop'])
    
    t_mc = np.array(res_mc.data['t'])
    pop_mc = np.array(res_mc.data['pop'])
    
    # Interpolate Lindblad to MC times for comparison
    pop_l_interp = np.interp(t_mc, t_l, pop_l)
    
    # Check if they are close
    # With 500 trajectories, we expect some noise, but general agreement.
    mean_diff = np.mean(np.abs(pop_l_interp - pop_mc))
    print(f"Mean difference: {mean_diff}")
    
    assert mean_diff < 0.05 # Reasonable tolerance for 500 trajectories

def test_mc_blockade():
    # 2 atoms, strong blockade, drive one atom
    reg = Register([Atom(0,0), Atom(2,0)], C6=100.0) # Atom at 2.0 is within blockade if radius > 2.0
    
    # Drive atom 0
    seq = PulseSequence(omega={0: 2*np.pi * 1.0}, delta=0.0)
    
    # Start in |gg>
    # Reduced basis for blockade radius 3.0: |gg>, |rg>, |gr>
    # Size 3.
    psi0 = np.array([1, 0, 0], dtype=complex)
    
    gamma = 0.1
    t_end = 2.0
    
    config_mc = SolverConfig(
        blockade_radius=3.0, 
        gamma=gamma, 
        use_mc=True, 
        n_trajectories=200
    )
    
    sim = Simulation(reg, seq, config_mc)
    res = sim.run(psi0, 0.0, t_end, observables={"atom0": 0, "atom1": 1})
    
    # Check that atom1 population remains very low due to blockade
    pop1 = np.array(res.data['atom1'])
    print(f"Max atom1 population: {np.max(pop1)}")
    assert np.max(pop1) < 0.1 # Blockade should prevent populating atom 1

if __name__ == "__main__":
    test_mc_vs_lindblad()
    test_mc_blockade()
