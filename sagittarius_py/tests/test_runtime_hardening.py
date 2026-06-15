import sys


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
            return {"ok": True, "missing": False, "returncode": 0, "output": "NVIDIA A100, 550.54.14, 40960", "raw_output": "NVIDIA A100, 550.54.14, 40960"}
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


def test_doctor_runtime_includes_version_metadata(monkeypatch):
    import sagittarius.runtime as runtime

    monkeypatch.setattr(runtime, "_metadata_command", lambda command, *, timeout=3: {"ok": False, "missing": True, "returncode": None, "output": None})

    report = runtime.doctor()

    assert report["runtime"]["schema_version"] == "version-info/v1"
    assert {"python", "julia", "build", "container", "backend_toolchains"} <= set(report["runtime"])
    assert report["container"] == report["runtime"]["container"]


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
    assert {"runtime", "requested_backend", "available", "issues", "issue_details", "backend_probe"} <= set(report)
    assert report["backend_probe"] is None


def test_backend_probe_schema_helpers():
    import sagittarius.runtime as runtime

    probe = runtime._new_backend_probe("CUDA")
    runtime._set_check(probe, "device_visible", False, message="No device", code="GPU_DEVICE_NOT_FOUND")

    assert probe["schema_version"] == "backend-probe/v2.1"
    assert {"checks", "versions", "devices", "driver", "runtime", "errors"} <= set(probe)
    assert probe["checks"]["device_visible"]["ok"] is False
    assert probe["checks"]["device_visible"]["code"] == "GPU_DEVICE_NOT_FOUND"


def test_parse_nvidia_smi_csv():
    import sagittarius.runtime as runtime

    devices = runtime._parse_nvidia_smi_csv("NVIDIA A100, 550.54.14, 40960")

    assert devices == [{"name": "NVIDIA A100", "driver_version": "550.54.14", "memory_total_mib": "40960"}]


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
                "output": "NVIDIA A100, 550.54.14, 40960",
                "raw_output": "NVIDIA A100, 550.54.14, 40960",
            }
        return {"ok": False, "missing": True, "returncode": None, "output": None}

    monkeypatch.setattr(runtime, "_run_command", fake_run)

    report = runtime.doctor(backend="CUDA")

    assert report["available"] is True
    assert report["gpu"]["driver"]["version"] == "550.54.14"
    assert report["gpu"]["devices"][0]["memory_total_mib"] == "40960"


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
