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

`doctor()` does not initialize Julia by default. Its top-level report uses schema version `doctor/v2.1` and includes a compatibility-oriented `issues` list, machine-readable `issue_details`, CUDA host visibility from `nvidia-smi` when available, and runtime metadata. Pass `initialize_backend=True` when you want the diagnostics call to also validate Julia startup and run backend-specific probes. Initialized probes use schema version `backend-probe/v2.1` with stable `checks`, `versions`, `devices`, `driver`, `runtime`, and `errors` fields. Simulation runs include runtime metadata and diagnostics in `SimulationResult.metadata` and `SimulationResult.diagnostics`; `SimulationResult.save()` persists those fields using an envelope format when they are present.

Common issue codes include `CUDA_PASSTHROUGH_UNAVAILABLE`, `JULIA_PYTHONCALL_INIT_FAILED`, `JULIA_PROJECT_NOT_INSTANTIATED`, `JULIA_PACKAGE_LOAD_FAILED`, `CUDA_DRIVER_RUNTIME_MISMATCH`, `GPU_DEVICE_NOT_FOUND`, `GPU_ALLOCATION_FAILED`, `GPU_SPARSE_BACKEND_UNAVAILABLE`, `BACKEND_NOT_PARITY_TESTED`, and `UNSUPPORTED_BACKEND`. Hardware-backed parity validation remains part of the CPU/GPU parity suite rather than the lightweight doctor path.
