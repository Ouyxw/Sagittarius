import numpy as np
import pytest
from sagittarius import ParallelSimulation
from juliacall import Main as jl

def test_parallel_setup():
    # Test that we can spin up workers
    psim = ParallelSimulation(n_workers=2)
    n = jl.Distributed.nprocs()
    print(f"Number of processes: {n}")
    assert n >= 2

def test_parallel_map():
    psim = ParallelSimulation(n_workers=2)
    
    # Define a simple function on all workers
    jl.seval("using Distributed")
    jl.seval("@everywhere square(x) = x^2")
    
    params = [1, 2, 3, 4, 5]
    # We call pmap directly via juliacall for this test
    res = list(jl.Distributed.pmap(jl.seval("square"), params))
    
    print(f"Results: {res}")
    assert res == [1, 4, 9, 16, 25]

def test_psim_map_method():
    psim = ParallelSimulation(n_workers=2)
    jl.seval("@everywhere cube(x) = x^3")
    res = psim.map("cube", [1, 2, 3])
    print(f"Cube results: {res}")
    assert res == [1, 8, 27]

if __name__ == "__main__":
    test_parallel_setup()
    test_parallel_map()
    test_psim_map_method()
    print("Clustered solver foundation verified!")
