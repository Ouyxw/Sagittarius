import sys


def test_import_does_not_initialize_juliacall():
    sys.modules.pop("sagittarius", None)
    sys.modules.pop("juliacall", None)

    import sagittarius

    assert "juliacall" not in sys.modules
    assert sagittarius.backend_maturity()["CUDA"]["status"] == "experimental"


def test_doctor_cpu_without_backend_initialization():
    from sagittarius import doctor, version_info

    report = doctor()

    assert report["requested_backend"] == "CPU"
    assert report["available"] is True
    assert report["runtime"]["package_version"]
    assert version_info()["julia_version"] is None


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
