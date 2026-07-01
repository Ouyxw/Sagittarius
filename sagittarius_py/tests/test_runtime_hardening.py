import sys
from pathlib import Path

import pytest


def test_import_does_not_initialize_juliacall():
    sys.modules.pop("sagittarius", None)
    sys.modules.pop("juliacall", None)

    import sagittarius

    assert "juliacall" not in sys.modules
    assert sagittarius.backend_maturity()["CUDA"]["status"] == "experimental"


def test_doctor_cpu_without_backend_initialization(monkeypatch):
    import sagittarius.runtime as runtime
    from sagittarius import doctor, version_info

    monkeypatch.setattr(runtime, "_jl", None)
    monkeypatch.setattr(runtime, "_sgr", None)

    report = doctor()

    assert report["requested_backend"] == "CPU"
    assert report["available"] is True
    assert report["runtime"]["package_version"]
    assert version_info()["julia_version"] is None


def _make_backend_tree(path: Path) -> Path:
    (path / "src").mkdir(parents=True)
    (path / "Project.toml").write_text('name = "Sagittarius"\nversion = "0.1.0"\n', encoding="utf-8")
    (path / "src" / "Sagittarius.jl").write_text("module Sagittarius\nend\n", encoding="utf-8")
    return path


def test_julia_backend_path_prefers_env_override(monkeypatch, tmp_path):
    import sagittarius.runtime as runtime

    override = _make_backend_tree(tmp_path / "override" / "Sagittarius.jl")
    package_backend = _make_backend_tree(tmp_path / "package" / "julia" / "Sagittarius.jl")

    monkeypatch.setenv(runtime.JULIA_BACKEND_PATH_ENV, str(override))
    monkeypatch.setattr(runtime.resources, "files", lambda package: package_backend.parents[1])

    assert runtime._project_path() == override.resolve()
    assert runtime._julia_backend_metadata()["source"] == "env_override"
    assert runtime._julia_backend_metadata()["path_env"] == runtime.JULIA_BACKEND_PATH_ENV


def test_julia_backend_path_prefers_source_checkout_over_package_resource(monkeypatch, tmp_path):
    import sagittarius.runtime as runtime

    source_backend = _make_backend_tree(tmp_path / "checkout" / "Sagittarius.jl")
    package_root = tmp_path / "package"
    _make_backend_tree(package_root / "julia" / "Sagittarius.jl")

    monkeypatch.delenv(runtime.JULIA_BACKEND_PATH_ENV, raising=False)
    monkeypatch.setattr(runtime, "_source_checkout_backend_path", lambda: source_backend)
    monkeypatch.setattr(runtime.resources, "files", lambda package: package_root)

    assert runtime._project_path() == source_backend
    assert runtime._julia_backend_metadata()["source"] == "source_checkout"
    assert runtime._julia_backend_metadata()["available"] is True


def test_julia_backend_path_uses_package_resource_when_source_checkout_missing(monkeypatch, tmp_path):
    import sagittarius.runtime as runtime

    package_root = tmp_path / "package"
    package_backend = _make_backend_tree(package_root / "julia" / "Sagittarius.jl")

    monkeypatch.delenv(runtime.JULIA_BACKEND_PATH_ENV, raising=False)
    monkeypatch.setattr(runtime, "_source_checkout_backend_path", lambda: tmp_path / "missing" / "Sagittarius.jl")
    monkeypatch.setattr(runtime.resources, "files", lambda package: package_root)

    assert runtime._project_path() == package_backend
    assert runtime._julia_backend_metadata()["source"] == "package_resource"
    assert runtime._julia_backend_metadata()["available"] is True


def test_julia_backend_path_falls_back_to_missing_source_checkout(monkeypatch, tmp_path):
    import sagittarius.runtime as runtime

    missing_source = tmp_path / "missing" / "Sagittarius.jl"
    monkeypatch.delenv(runtime.JULIA_BACKEND_PATH_ENV, raising=False)
    monkeypatch.setattr(runtime, "_source_checkout_backend_path", lambda: missing_source)
    monkeypatch.setattr(runtime, "_package_backend_resource_path", lambda: None)

    assert runtime._project_path() == missing_source
    assert runtime._julia_backend_metadata()["source"] == "source_checkout"
    assert runtime._julia_backend_metadata()["available"] is False


def test_invalid_julia_backend_path_fails_before_juliacall_import(monkeypatch, tmp_path):
    import sagittarius.runtime as runtime

    monkeypatch.setattr(runtime, "_jl", None)
    monkeypatch.setattr(runtime, "_sgr", None)
    monkeypatch.setenv(runtime.JULIA_BACKEND_PATH_ENV, str(tmp_path / "missing" / "Sagittarius.jl"))
    monkeypatch.delitem(sys.modules, "juliacall", raising=False)

    with pytest.raises(runtime.SagittariusRuntimeError) as exc_info:
        runtime.get_julia()

    assert exc_info.value.issue.code == "JULIA_BACKEND_PATH_INVALID"
    assert "juliacall" not in sys.modules



def test_version_info_records_build_and_backend_metadata(monkeypatch):
    import sagittarius.runtime as runtime
    from sagittarius import VERSION_INFO_SCHEMA_VERSION, version_info

    def fake_command(command, *, timeout=3):
        joined = " ".join(command)
        if "rev-parse HEAD" in joined:
            return {"ok": True, "missing": False, "returncode": 0, "output": "abc123def", "raw_output": "abc123def"}
        if "rev-parse --short HEAD" in joined:
            return {"ok": True, "missing": False, "returncode": 0, "output": "abc123", "raw_output": "abc123"}
        if "rev-parse --abbrev-ref HEAD" in joined:
            return {"ok": True, "missing": False, "returncode": 0, "output": "main", "raw_output": "main"}
        if "status --porcelain" in joined:
            return {"ok": True, "missing": False, "returncode": 0, "output": None, "raw_output": ""}
        if command[0] == "nvidia-smi":
            return {"ok": True, "missing": False, "returncode": 0, "output": "NVIDIA A100, 550.54.14, 40960, 8.0", "raw_output": "NVIDIA A100, 550.54.14, 40960, 8.0"}
        if command[0] == "nvcc":
            return {"ok": True, "missing": False, "returncode": 0, "output": "Cuda compilation tools, release 12.1", "raw_output": "Cuda compilation tools, release 12.1"}
        return {"ok": False, "missing": True, "returncode": None, "output": None}

    monkeypatch.setattr(runtime, "_metadata_command", fake_command)
    monkeypatch.setattr(runtime, "_in_container", lambda: True)
    monkeypatch.setenv("SAGITTARIUS_CONTAINER_IMAGE", "sagittarius:test")
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")

    info = version_info()

    assert info["schema_version"] == VERSION_INFO_SCHEMA_VERSION
    assert info["package_version"] == info["python"]["packages"]["sagittarius-py"]
    assert info["julia"]["sagittarius_julia_version"] == info["sagittarius_julia_version"]
    assert info["build"]["source"]["git_commit"] == "abc123def"
    assert info["build"]["source"]["git_dirty"] is False
    assert info["build"]["build_id"] == "12345"
    assert info["container"]["detected"] is True
    assert info["container"]["image"] == "sagittarius:test"
    assert "devcontainer" in info["container"]
    assert info["backend_toolchains"]["CUDA"]["devices"][0]["driver_version"] == "550.54.14"
    assert info["backend_toolchains"]["CUDA"]["nvcc"]["output"] == "Cuda compilation tools, release 12.1"
    assert {"CUDA", "AMDGPU", "METAL"} <= set(info["backend_toolchains"])
    assert info["python"]["packages"]["sagittarius-py"] == info["package_version"]
    assert info["julia"]["project_path"].endswith("Sagittarius.jl")
    assert info["abi"]["python"]["implementation"]
    assert "cache_tag" in info["abi"]["python"]


def test_doctor_runtime_includes_version_metadata(monkeypatch):
    import sagittarius.runtime as runtime

    monkeypatch.setattr(runtime, "_metadata_command", lambda command, *, timeout=3: {"ok": False, "missing": True, "returncode": None, "output": None})

    report = runtime.doctor()

    assert report["runtime"]["schema_version"] == "version-info/v1"
    assert {"python", "julia", "build", "container", "backend_toolchains", "abi"} <= set(report["runtime"])
    assert report["backend_source"] == report["runtime"]["julia"]["source"]
    assert report["julia_backend"] == report["runtime"]["julia"]
    assert report["backend_source"] in {"env_override", "source_checkout", "package_resource"}
    assert report["container"] == report["runtime"]["container"]
    assert report["capabilities"]["backend"] == report["requested_backend"]
    assert report["capabilities"]["abi"]["host"] == report["runtime"]["abi"]


def test_doctor_unknown_backend_has_actionable_issue():
    from sagittarius import doctor

    report = doctor(backend="not-a-backend")

    assert report["available"] is False
    assert report["issue_details"][0]["code"] == "UNSUPPORTED_BACKEND"
    assert "Choose one of" in report["issue_details"][0]["remediation"]


def test_doctor_cuda_missing_passthrough_is_classified(monkeypatch):
    import sagittarius.runtime as runtime

    def fake_run(command, *, timeout=5):
        return {"ok": False, "missing": True, "returncode": None, "output": None}

    monkeypatch.setattr(runtime, "_run_command", fake_run)

    report = runtime.doctor(backend="CUDA")

    assert report["available"] is False
    assert report["issue_details"][0]["code"] == "CUDA_PASSTHROUGH_UNAVAILABLE"
    assert report["backend_probe"] is None


def test_runtime_exception_classification():
    import sagittarius.runtime as runtime

    issue = runtime._classify_exception(Exception("PythonCall.jl did not start properly"))

    assert issue["code"] == "JULIA_PYTHONCALL_INIT_FAILED"
    assert "juliapkg resolve" in issue["remediation"]


def test_missing_julia_package_classification_names_package():
    import sagittarius.runtime as runtime

    issue = runtime._classify_exception(Exception("ArgumentError: Package OrdinaryDiffEq not found in current path."))

    assert issue["code"] == "JULIA_PACKAGE_LOAD_FAILED"
    assert "OrdinaryDiffEq" in issue["message"]
    assert "juliapkg resolve" in issue["remediation"]
    assert "--reinstall-package sagittarius-py" in issue["remediation"]


def test_required_cpu_julia_packages_include_solver_dependencies():
    import sagittarius.runtime as runtime

    assert set(runtime.REQUIRED_CPU_JULIA_PACKAGES) == {
        "OrdinaryDiffEq",
        "OrdinaryDiffEqLowOrderRK",
        "StaticArrays",
        "DiffEqCallbacks",
        "SciMLBase",
    }


def test_backend_maturity_uses_normalized_keys():
    from sagittarius import backend_maturity

    maturity = backend_maturity()

    assert set(maturity) == {"CPU", "CUDA", "AMDGPU", "METAL"}
    assert maturity["METAL"]["status"] == "planned"


def test_sagittarius_runtime_error_is_classified():
    import sagittarius.runtime as runtime

    issue = runtime.DiagnosticIssue(
        code="JULIA_PROJECT_NOT_INSTANTIATED",
        message="Project missing dependencies.",
        remediation="Run instantiate.",
    )
    exc = runtime.SagittariusRuntimeError(issue)

    assert runtime._classify_exception(exc)["code"] == "JULIA_PROJECT_NOT_INSTANTIATED"


def test_planned_backend_reports_unavailable_without_probe():
    from sagittarius import doctor

    report = doctor(backend="Metal")

    assert report["requested_backend"] == "METAL"
    assert report["available"] is False
    assert report["issue_details"][0]["code"] == "BACKEND_NOT_PARITY_TESTED"


def test_doctor_report_schema_is_stable():
    from sagittarius import doctor

    report = doctor()

    assert report["schema_version"] == "doctor/v2.1"
    assert {"runtime", "requested_backend", "available", "issues", "issue_details", "backend_probe", "capabilities"} <= set(report)
    assert report["backend_probe"] is None
    assert report["capabilities"]["backend"] == "CPU"
    assert report["capabilities"]["parity"]["status"] == "regular_test_suite"
    assert "abi" in report["capabilities"]


def test_backend_probe_schema_helpers():
    import sagittarius.runtime as runtime

    probe = runtime._new_backend_probe("CUDA")
    runtime._set_check(probe, "device_visible", False, message="No device", code="GPU_DEVICE_NOT_FOUND")

    assert probe["schema_version"] == "backend-probe/v2.1"
    assert {"checks", "versions", "devices", "driver", "runtime", "errors", "abi"} <= set(probe)
    assert probe["checks"]["device_visible"]["ok"] is False
    assert probe["checks"]["device_visible"]["code"] == "GPU_DEVICE_NOT_FOUND"


def test_parse_nvidia_smi_csv():
    import sagittarius.runtime as runtime

    devices = runtime._parse_nvidia_smi_csv("NVIDIA A100, 550.54.14, 40960, 8.0")

    assert devices == [{"name": "NVIDIA A100", "driver_version": "550.54.14", "memory_total_mib": "40960", "compute_capability": "8.0"}]


def test_probe_failure_issue_selects_specific_code():
    import sagittarius.runtime as runtime

    probe = runtime._new_backend_probe("CUDA")
    runtime._set_check(probe, "cuda_functional", False, code="CUDA_DRIVER_RUNTIME_MISMATCH")

    assert runtime._probe_failure_issue(probe)["code"] == "CUDA_DRIVER_RUNTIME_MISMATCH"


def test_doctor_cuda_records_driver_and_devices(monkeypatch):
    import sagittarius.runtime as runtime

    def fake_run(command, *, timeout=5):
        if command[0] == "nvidia-smi":
            return {
                "ok": True,
                "missing": False,
                "returncode": 0,
                "output": "NVIDIA A100, 550.54.14, 40960, 8.0",
                "raw_output": "NVIDIA A100, 550.54.14, 40960, 8.0",
            }
        return {"ok": False, "missing": True, "returncode": None, "output": None}

    monkeypatch.setattr(runtime, "_run_command", fake_run)

    report = runtime.doctor(backend="CUDA")

    assert report["available"] is True
    assert report["gpu"]["driver"]["version"] == "550.54.14"
    assert report["gpu"]["devices"][0]["memory_total_mib"] == "40960"


def test_doctor_cuda_capabilities_include_parity_and_abi(monkeypatch):
    import sagittarius.runtime as runtime

    def fake_run(command, *, timeout=5):
        joined = " ".join(command)
        if command[0] == "nvidia-smi":
            return {
                "ok": True,
                "missing": False,
                "returncode": 0,
                "output": "NVIDIA A100, 550.54.14, 40960, 8.0",
                "raw_output": "NVIDIA A100, 550.54.14, 40960, 8.0",
            }
        if command[0] == "nvcc":
            return {"ok": True, "missing": False, "returncode": 0, "output": "Cuda compilation tools, release 12.1", "raw_output": "Cuda compilation tools, release 12.1"}
        if "git" in joined:
            return {"ok": True, "missing": False, "returncode": 0, "output": "test", "raw_output": ""}
        return {"ok": False, "missing": True, "returncode": None, "output": None}

    monkeypatch.setattr(runtime, "_run_command", fake_run)
    monkeypatch.setattr(runtime, "_metadata_command", fake_run)

    report = runtime.doctor(backend="CUDA")

    assert report["capabilities"]["backend"] == "CUDA"
    assert report["capabilities"]["parity"]["status"] == "opt_in_hardware_parity_suite"
    assert report["capabilities"]["parity"]["hardware_validated_by_doctor"] is False
    assert report["capabilities"]["abi"]["driver"]["version"] == "550.54.14"
    assert report["capabilities"]["abi"]["devices"][0]["compute_capability"] == "8.0"
    assert report["capabilities"]["abi"]["runtime"]["nvcc"]["output"] == "Cuda compilation tools, release 12.1"




def test_doctor_cuda_falls_back_when_compute_cap_query_is_unavailable(monkeypatch):
    import sagittarius.runtime as runtime

    def fake_run(command, *, timeout=5):
        joined = " ".join(command)
        if "compute_cap" in joined:
            return {"ok": False, "missing": False, "returncode": 1, "output": "unsupported query"}
        if command[0] == "nvidia-smi":
            return {
                "ok": True,
                "missing": False,
                "returncode": 0,
                "output": "NVIDIA A100, 550.54.14, 40960",
                "raw_output": "NVIDIA A100, 550.54.14, 40960",
            }
        return {"ok": False, "missing": True, "returncode": None, "output": None}

    monkeypatch.setattr(runtime, "_run_command", fake_run)

    report = runtime.doctor(backend="CUDA")

    assert report["available"] is True
    assert report["gpu"]["nvidia_smi"]["fallback_from_compute_cap"] is True
    assert report["gpu"]["devices"][0]["compute_capability"] is None


def test_doctor_cuda_warns_for_blackwell_driver_below_cuda_12_8(monkeypatch):
    import sagittarius.runtime as runtime

    def fake_run(command, *, timeout=5):
        if command[0] == "nvidia-smi":
            return {
                "ok": True,
                "missing": False,
                "returncode": 0,
                "output": "NVIDIA RTX 5090, 565.57.01, 32768, 12.0",
                "raw_output": "NVIDIA RTX 5090, 565.57.01, 32768, 12.0",
            }
        return {"ok": False, "missing": True, "returncode": None, "output": None}

    monkeypatch.setattr(runtime, "_run_command", fake_run)

    report = runtime.doctor(backend="CUDA")

    assert report["available"] is True
    assert report["gpu"]["compatibility"]["blackwell_detected"] is True
    assert report["gpu"]["compatibility"]["cuda_12_8_driver_ok"] is False
    assert report["issue_details"][0]["code"] == "CUDA_BLACKWELL_DRIVER_BELOW_RECOMMENDED"
    assert report["issue_details"][0]["severity"] == "warning"


def test_cuda_version_helpers_compare_dotted_versions():
    import sagittarius.runtime as runtime

    assert runtime._version_at_least("570.86.10", "570.26") is True
    assert runtime._version_at_least("565.57.01", "570.26") is False
    assert runtime._version_at_least(None, "570.26") is None


def test_failed_backend_probe_uses_v21_schema(monkeypatch):
    import sagittarius.runtime as runtime

    def fail_get_julia():
        raise runtime.SagittariusRuntimeError(runtime.DiagnosticIssue(
            code="JULIA_PROJECT_NOT_INSTANTIATED",
            message="Missing project deps.",
            remediation="Instantiate.",
        ))

    monkeypatch.setattr(runtime, "get_julia", fail_get_julia)

    report = runtime.doctor(initialize_backend=True)

    assert report["backend_probe"]["schema_version"] == "backend-probe/v2.1"
    assert report["backend_probe"]["available"] is False
    assert report["issue_details"][0]["code"] == "JULIA_PROJECT_NOT_INSTANTIATED"
