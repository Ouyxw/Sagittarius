import os
import numpy as np
import pytest
from sagittarius import Atom, Register, Simulation, PulseSequence, SimulationResult, load_result

def test_json_serialization():
    # 1. Generate some data
    data = {
        "t": [0.0, 0.5, 1.0],
        "atom0": [1.0, 0.5, 0.0],
        "atom1": [0.0, 0.5, 1.0]
    }
    res = SimulationResult(data)
    
    # 2. Save to JSON
    filepath = "test_result.json"
    try:
        res.save(filepath)
        assert os.path.exists(filepath)
        
        # 3. Load back
        res_loaded = load_result(filepath)
        
        # 4. Compare
        assert np.allclose(res.t, res_loaded.t)
        assert np.allclose(res.data["atom0"], res_loaded.data["atom0"])
        assert res.data.keys() == res_loaded.data.keys()
        
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == "__main__":
    test_json_serialization()
    print("Serialization test passed!")
