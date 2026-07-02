import json
import tempfile
from sagittarius import SimulationResult, load_result

result = SimulationResult(
    {"t": [0.0, 1.0], "pop": [0.0, 1.0]},
    metadata={"example": "minimal"},
    diagnostics={"backend": "CPU"},
)

with tempfile.NamedTemporaryFile(suffix=".json") as f:
    result.save(f.name)
    with open(f.name) as saved:
        envelope = json.load(saved)
    loaded = load_result(f.name)
    print(envelope["schema_version"])
    print(loaded.data["pop"][-1])
    print(loaded.metadata["example"])
    print(loaded.diagnostics["backend"])