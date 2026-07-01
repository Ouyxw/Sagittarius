# Backend Maturity Matrix

Spec ID: `SPEC-BACKEND-001`
Status: `Current`
Roadmap: Phase 5, Phase 10
Version: `backend-maturity/v1`
Last reviewed: 2026-06-30


Sagittarius exposes backend names through the Python API, but backend availability and test coverage are not equivalent. Treat this matrix as the public maturity contract until parity tests and reproducible benchmark artifacts say otherwise.

| Backend | Status | Runtime notes |
| :--- | :---: | :--- |
| CPU | stable | Default SciML/OrdinaryDiffEq execution path used by regular API and physics tests. |
| CUDA | experimental | Main GPU development target for container workflows. CUDA 12.8+ and Blackwell-class GPUs require current NVIDIA drivers and the pinned CUDA.jl 6.2.x environment; use `doctor(backend="CUDA")` to confirm GPU passthrough, host driver visibility, compute capability, and Julia CUDA availability at runtime. |
| AMDGPU | planned | API name exists for future support, but parity tests and deployment documentation are not established. |
| Metal | planned | API name exists for future support, but parity tests and deployment documentation are not established. |

## Diagnostics

Use the lightweight Python diagnostics path before selecting a GPU backend:

```python
from sagittarius import doctor, backend_maturity

print(backend_maturity())
print(doctor(backend="CUDA"))
```

`doctor()` does not initialize Julia by default. Its top-level report uses schema version `doctor/v2.1` and includes a compatibility-oriented `issues` list, machine-readable `issue_details`, CUDA host visibility from `nvidia-smi` when available, compute capability, CUDA 12.8/Blackwell driver compatibility, `version-info/v1` runtime metadata, and a `capabilities` section with backend maturity, ABI/toolchain metadata, and parity-test status. Pass `initialize_backend=True` when you want the diagnostics call to also validate Julia startup and run backend-specific probes. Initialized probes use schema version `backend-probe/v2.1` with stable `checks`, `versions`, `devices`, `driver`, `runtime`, `errors`, and `abi` fields. Simulation runs include runtime metadata and diagnostics in `SimulationResult.metadata` and `SimulationResult.diagnostics`; `SimulationResult.save()` persists results using the `result-artifact/v1` envelope with data, metadata, diagnostics, and manifest fields.

Common issue codes include `CUDA_PASSTHROUGH_UNAVAILABLE`, `CUDA_BLACKWELL_DRIVER_BELOW_RECOMMENDED`, `CUDAJL_VERSION_BELOW_RECOMMENDED`, `JULIA_PYTHONCALL_INIT_FAILED`, `JULIA_PROJECT_NOT_INSTANTIATED`, `JULIA_PACKAGE_LOAD_FAILED`, `CUDA_DRIVER_RUNTIME_MISMATCH`, `GPU_DEVICE_NOT_FOUND`, `GPU_ALLOCATION_FAILED`, `GPU_SPARSE_BACKEND_UNAVAILABLE`, `BACKEND_NOT_PARITY_TESTED`, and `UNSUPPORTED_BACKEND`. Hardware-backed numerical parity remains part of the CPU/GPU parity suite rather than the lightweight doctor path; `doctor().capabilities.parity` reports where that parity evidence lives.

## CUDA parity container policy

The default `sagittarius_py/juliapkg.json` environment is CPU-first and intentionally excludes CUDA.jl. CUDA setup is explicit through the packaged `sagittarius_py/sagittarius/juliapkg-cuda.json` profile and `sagittarius backend install cuda`; the gated clean-wheel CUDA smoke and the devcontainer remain the CUDA parity paths for hardware-backed validation. The planned AMDGPU/Metal packages currently introduce dependency constraints that can prevent CUDA.jl 6.2.x from resolving. Use a separate backend-specific Julia environment when experimenting with AMDGPU or Metal.
