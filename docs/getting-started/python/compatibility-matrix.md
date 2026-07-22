# Python Compatibility Matrix

This matrix records the Phase 13 validation completed for the published `1.0.10` wheel and source distribution. CUDA remains experimental even though it passed validation on a separate CUDA runner.

## Supported CPU Artifact Matrix

| Operating system | Python | Julia | Status | Validation command | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Linux x86_64 | 3.10 | 1.10.3 | Validated for 1.0.10 | `SAGITTARIUS_RUN_RELEASE_ARTIFACT_SMOKE=1 uv run python -m pytest tests/test_packaging_artifacts.py::test_clean_venv_installed_wheel_release_smoke -q` | Minimum declared Python and Julia baseline. |
| Linux x86_64 | 3.11 | 1.11 | Validated for 1.0.10 | Same clean wheel smoke | Primary development and container baseline. |
| Linux x86_64 | 3.12 | 1.11 | Validated for 1.0.10 | Same clean wheel smoke | Newest declared Python line. |
| macOS x86_64/arm64 runner | 3.11 | 1.11 | Validated for 1.0.10 | Same clean wheel smoke | CUDA is not supported on macOS; Metal remains planned/experimental outside the default package profile. |
| Windows x86_64 | 3.11 | 1.11 | Validated for 1.0.10 | Same clean wheel smoke | Path handling and Julia executable discovery passed the clean wheel smoke. |

## Policy

- The default CPU install path must not require CUDA.jl, NVIDIA drivers, or GPU hardware.
- The MIT `1.0.8` candidate remains historical evidence. Apache-2.0 `1.0.10` passed every declared matrix row before production publication.
- Cross-platform validation uses installed wheel artifacts outside the source checkout and requires `backend_source=package_resource` in doctor/version metadata.
- CUDA release claims require the separate `phase13-cuda-wheel.yml` workflow on real NVIDIA GPU hardware.
- AMDGPU and Metal package profiles remain future work and are not part of the Phase 13 CPU artifact matrix.

## Workflow

Run `.github/workflows/phase13-cross-platform.yml` manually for release candidates. The workflow downloads and verifies the canonical artifacts rather than rebuilding them, then installs the wheel in a fresh virtual environment outside the repository, runs `sagittarius backend resolve`, and executes the minimal CPU simulation smoke.

Each passing matrix row writes a `phase13-cross-platform-evidence/*.md` file and uploads it with an artifact name of the form `phase13-cross-platform-<os>-py<python>-julia<julia>`. Keep those artifacts, the workflow run URL, the commit SHA, and the release-candidate tag or branch together with release notes as release evidence.
