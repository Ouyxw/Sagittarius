# Backend Maturity Matrix

Sagittarius exposes backend names through the Python API, but backend availability and test coverage are not equivalent. Treat this matrix as the public maturity contract until parity tests and reproducible benchmark artifacts say otherwise.

| Backend | Status | Runtime notes |
| :--- | :---: | :--- |
| CPU | stable | Default SciML/OrdinaryDiffEq execution path used by regular API and physics tests. |
| CUDA | experimental | Main GPU development target for container workflows. Requires `doctor(backend="CUDA")` to confirm GPU passthrough, host driver visibility, and Julia CUDA availability at runtime. |
| AMDGPU | planned | API name exists for future support, but parity tests and deployment documentation are not established. |
| Metal | planned | API name exists for future support, but parity tests and deployment documentation are not established. |

## Diagnostics

Use the lightweight Python diagnostics path before selecting a GPU backend:

```python
from sagittarius import doctor, backend_maturity

print(backend_maturity())
print(doctor(backend="CUDA"))
```

`doctor()` does not initialize Julia by default. Pass `initialize_backend=True` when you want the diagnostics call to also validate Julia package loading. Simulation runs include runtime metadata and diagnostics in `SimulationResult.metadata` and `SimulationResult.diagnostics`; `SimulationResult.save()` persists those fields using an envelope format when they are present.
