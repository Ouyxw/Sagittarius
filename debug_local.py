import os
import numpy as np
from juliacall import Main as jl

# Load Sagittarius
pkg_path = os.path.join(os.getcwd(), "Sagittarius.jl")
jl.include(os.path.join(pkg_path, "src", "Sagittarius.jl"))
sgr = jl.Sagittarius

def test_debug():
    N = 2
    # Mocking a pulse config
    p_config = {0: 10.0, 1: 5.0}
    
    compiled_funcs = []
    for i in range(N):
        v = float(p_config.get(i, 0.0))
        compiled_funcs.append(jl.seval(f"t -> {v}"))
    
    jl_vec_funcs = jl.Vector[jl.Any](compiled_funcs)
    vec_func = jl.seval("funcs -> (t -> Float64[f(t) for f in funcs])")(jl_vec_funcs)
    
    res = vec_func(0.0)
    print(f"Result at t=0.0: {res} (Type: {type(res)})")
    print(f"Values: {list(res)}")

if __name__ == "__main__":
    test_debug()
