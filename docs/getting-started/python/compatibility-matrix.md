# Python Compatibility Matrix

This matrix is the Phase 13 release-validation target for Python package artifacts. It describes the supported CPU install path for wheels and source distributions. CUDA remains experimental and is validated separately on a CUDA runner.

## Supported CPU Artifact Matrix

| Operating system | Python | Julia | Status | Validation command | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Linux x86_64 | 3.10 | 1.10.3 | Supported target | `SAGITTARIUS_RUN_RELEASE_ARTIFACT_SMOKE=1 uv run python -m pytest tests/test_packaging_artifacts.py::test_clean_venv_installed_wheel_release_smoke -q` | Minimum declared Python and Julia baseline. |
| Linux x86_64 | 3.11 | 1.11 | Supported target | Same clean wheel smoke | Primary development and container baseline. |
| Linux x86_64 | 3.12 | 1.11 | Supported target | Same clean wheel smoke | Newest declared Python line. |
| macOS x86_64/arm64 runner | 3.11 | 1.11 | Supported CPU target after CI evidence | Same clean wheel smoke | CUDA is not supported on macOS; Metal remains planned/experimental outside the default package profile. |
| Windows x86_64 | 3.11 | 1.11 | Supported CPU target after CI evidence | Same clean wheel smoke | Path handling and Julia executable discovery must pass the clean wheel smoke before release. |

## Policy

- The default CPU install path must not require CUDA.jl, NVIDIA drivers, or GPU hardware.
- A release candidate is not cross-platform ready until the matrix workflow passes for every row above.
- Cross-platform validation uses installed wheel artifacts outside the source checkout and requires `backend_source=package_resource` in doctor/version metadata.
- CUDA release claims require the separate `phase13-cuda-wheel.yml` workflow on real NVIDIA GPU hardware.
- AMDGPU and Metal package profiles remain future work and are not part of the Phase 13 CPU artifact matrix.

## Workflow

Run `.github/workflows/phase13-cross-platform.yml` manually for release candidates. The workflow builds artifacts, runs metadata checks, installs the wheel in a fresh virtual environment outside the repository, runs `sagittarius backend resolve`, and executes the minimal CPU simulation smoke.
