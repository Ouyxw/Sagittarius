import os
import numpy as np
from juliacall import Main as jl

def test_vector_order():
    data = [10.0, 20.0, 30.0]
    jl_vec = jl.Vector[jl.Float64](data)
    print(f"Python list: {data}")
    print(f"Julia vector [1]: {jl_vec[0]}")
    print(f"Julia vector [2]: {jl_vec[1]}")
    print(f"Julia vector [3]: {jl_vec[2]}")
    
    # In Julia
    jl.v = jl_vec
    res = jl.seval("[v[1], v[2], v[3]]")
    print(f"Julia access [1, 2, 3]: {list(res)}")

if __name__ == "__main__":
    test_vector_order()
