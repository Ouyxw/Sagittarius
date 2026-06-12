from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, Optional

from .events import EVENT_CATALOG, EVENT_TAXONOMY_SCHEMA_VERSION, SEVERITY_LEVELS, validate_event_payload


LOGGER_NAME = "sagittarius"
DOCTOR_SCHEMA_VERSION = "doctor/v2.1"
BACKEND_PROBE_SCHEMA_VERSION = "backend-probe/v2.1"

BACKEND_MATURITY: Dict[str, Dict[str, str]] = {
    "CPU": {
        "status": "stable",
        "notes": "Default SciML/OrdinaryDiffEq execution path covered by the regular test suite.",
    },
    "CUDA": {
        "status": "experimental",
        "notes": "Primary GPU target for containerized development; requires runtime capability checks.",
    },
    "AMDGPU": {
        "status": "planned",
        "notes": "Julia package hook exists, but parity and container tests are not established.",
    },
    "METAL": {
        "status": "planned",
        "notes": "Julia package hook exists, but parity and CI coverage are not established.",
    },
}

_logger = logging.getLogger(LOGGER_NAME)
_json_logging = False
_jl = None
_sgr = None


@dataclass
class RuntimeInfo:
    python_version: str
    package_version: str
    julia_version: Optional[str]
    sagittarius_julia_version: Optional[str]
    platform: str
    in_container: bool


@dataclass
class DiagnosticIssue:
    code: str
    message: str
    remediation: str
    severity: str = "error"


class SagittariusRuntimeError(RuntimeError):
    """Raised when a Sagittarius runtime backend cannot be initialized."""

    def __init__(self, issue: DiagnosticIssue):
        super().__init__(f"{issue.code}: {issue.message} {issue.remediation}")
        self.issue = issue


def configure_logging(level: int | str = logging.INFO, *, json_output: bool = False) -> None:
    """Configure Sagittarius structured logging."""
    global _json_logging
    _json_logging = json_output
    _logger.setLevel(level)
    if not _logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        _logger.addHandler(handler)


def log_event(event: str, level: Optional[int] = None, **fields: Any) -> None:
    validate_event_payload(event, fields)
    spec = EVENT_CATALOG.get(event)
    severity = spec.severity if spec is not None else logging.getLevelName(level or logging.INFO).lower()
    log_level = level if level is not None else SEVERITY_LEVELS.get(severity, logging.INFO)
    payload = {
        "event": event,
        "event_id": spec.event_id if spec is not None else None,
        "event_schema": EVENT_TAXONOMY_SCHEMA_VERSION if spec is not None else None,
        "severity": severity,
        **fields,
    }
    if _json_logging:
        _logger.log(log_level, json.dumps(payload, sort_keys=True, default=str))
    else:
        detail_fields = dict(fields)
        if spec is not None:
            detail_fields = {"event_id": spec.event_id, "severity": severity, **detail_fields}
        detail = " ".join(f"{key}={value}" for key, value in sorted(detail_fields.items()))
        _logger.log(log_level, "%s%s", event, f" {detail}" if detail else "")


def backend_maturity() -> Dict[str, Dict[str, str]]:
    return {name: dict(values) for name, values in BACKEND_MATURITY.items()}


def package_version() -> str:
    try:
        return metadata.version("sagittarius-py")
    except metadata.PackageNotFoundError:
        return "0.1.0"


def _project_path() -> Path:
    return Path(__file__).resolve().parents[2] / "Sagittarius.jl"


def _julia_project_version() -> Optional[str]:
    project = _project_path() / "Project.toml"
    try:
        for line in project.read_text().splitlines():
            if line.strip().startswith("version"):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        return None
    return None


def _in_container() -> bool:
    if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
        return True
    try:
        cgroup = Path("/proc/1/cgroup").read_text(errors="ignore").lower()
    except OSError:
        return False
    return any(token in cgroup for token in ("docker", "kubepods", "containerd", "podman"))


def _issue(code: str, message: str, remediation: str, *, severity: str = "error") -> Dict[str, str]:
    return asdict(DiagnosticIssue(code=code, message=message, remediation=remediation, severity=severity))


def _append_issue(report: Dict[str, Any], code: str, message: str, remediation: str, *, severity: str = "error") -> None:
    item = _issue(code, message, remediation, severity=severity)
    report.setdefault("issue_details", []).append(item)
    report.setdefault("issues", []).append(f"{code}: {message}")
    if severity == "error":
        report["available"] = False


def _new_backend_probe(backend: str) -> Dict[str, Any]:
    return {
        "schema_version": BACKEND_PROBE_SCHEMA_VERSION,
        "backend": backend,
        "available": False,
        "checks": {},
        "versions": {},
        "devices": [],
        "driver": {},
        "runtime": {},
        "errors": [],
    }


def _set_check(
    probe: Dict[str, Any],
    name: str,
    ok: bool,
    *,
    message: str = "",
    severity: str = "error",
    code: Optional[str] = None,
) -> None:
    probe.setdefault("checks", {})[name] = {
        "ok": bool(ok),
        "severity": severity,
        "message": message,
        "code": code,
    }


def _required_checks_ok(probe: Dict[str, Any], names: tuple[str, ...]) -> bool:
    return all(bool(probe.get("checks", {}).get(name, {}).get("ok")) for name in names)


def _parse_nvidia_smi_csv(output: Optional[str]) -> list[Dict[str, Optional[str]]]:
    if not output:
        return []
    devices = []
    for line in output.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if not parts or not parts[0]:
            continue
        devices.append({
            "name": parts[0],
            "driver_version": parts[1] if len(parts) > 1 else None,
            "memory_total_mib": parts[2] if len(parts) > 2 else None,
        })
    return devices


def _probe_failure_issue(probe: Dict[str, Any]) -> Dict[str, str]:
    checks = probe.get("checks", {})
    if not checks.get("package_loadable", {"ok": True}).get("ok", True):
        return _issue("JULIA_PACKAGE_LOAD_FAILED", "The Julia backend package could not be loaded.", "Install or instantiate the Julia project and retry `doctor(initialize_backend=True)`.")
    if checks.get("cuda_functional", {"ok": True}).get("ok") is False:
        return _issue("CUDA_DRIVER_RUNTIME_MISMATCH", "CUDA.jl is not functional in this runtime.", "Check NVIDIA driver compatibility, CUDA.jl artifacts, and container GPU passthrough.")
    if probe.get("backend") in {"CUDA", "AMDGPU", "METAL"} and not probe.get("devices"):
        return _issue("GPU_DEVICE_NOT_FOUND", "No usable GPU device was found for the requested backend.", "Check hardware availability, host drivers, and container/device passthrough.")
    if checks.get("device_allocation", {"ok": True}).get("ok") is False:
        return _issue("GPU_ALLOCATION_FAILED", "The backend could not allocate a minimal GPU array.", "Check runtime permissions, memory availability, and backend package configuration.")
    if checks.get("sparse_backend", {"ok": True}).get("ok") is False:
        return _issue("GPU_SPARSE_BACKEND_UNAVAILABLE", "The GPU sparse matrix backend is unavailable.", "Install or configure the sparse backend package required by the selected GPU runtime.")
    if checks.get("sparse_matvec", {"ok": True}).get("ok") is False:
        return _issue("CPU_SPARSE_PROBE_FAILED", "The CPU sparse matrix probe failed.", "Verify Julia standard libraries and SciML dependencies are correctly instantiated.")
    return _issue(f"{probe.get('backend', 'BACKEND')}_PROBE_FAILED", "The backend probe did not pass all required checks.", "Inspect `backend_probe.checks` and configure the missing runtime components.")


def _classify_exception(exc: Exception) -> Dict[str, str]:
    if isinstance(exc, SagittariusRuntimeError):
        return asdict(exc.issue)
    text = str(exc)
    lowered = text.lower()
    if "pythoncall.jl did not start properly" in lowered:
        return _issue(
            "JULIA_PYTHONCALL_INIT_FAILED",
            "PythonCall.jl failed during juliacall startup.",
            "Run `cd sagittarius_py && uv run python -m juliapkg resolve`, then retry with `doctor(initialize_backend=True)`. If it persists, rebuild the Julia environment.",
        )
    if "pkg.instantiate" in lowered or "does not seem to be installed" in lowered:
        return _issue(
            "JULIA_PROJECT_NOT_INSTANTIATED",
            "The Julia project dependencies are not instantiated.",
            "Run `julia --project=Sagittarius.jl -e 'using Pkg; Pkg.instantiate()'` or `cd sagittarius_py && uv run python -m juliapkg resolve`.",
        )
    if "package" in lowered and ("not found" in lowered or "not installed" in lowered or "could not be loaded" in lowered):
        return _issue(
            "JULIA_PACKAGE_LOAD_FAILED",
            "A required Julia package could not be loaded.",
            "Run Julia project instantiation and verify optional backend packages are installed for the selected backend.",
        )
    if "no devices" in lowered or "device not found" in lowered or "no gpu" in lowered:
        return _issue(
            "GPU_DEVICE_NOT_FOUND",
            "No usable GPU device was found for the requested backend.",
            "Check hardware availability, host drivers, and container/device passthrough.",
        )
    if "allocation" in lowered or "out of memory" in lowered:
        return _issue(
            "GPU_ALLOCATION_FAILED",
            "The backend failed during a minimal device allocation.",
            "Check device memory, runtime permissions, and backend package configuration.",
        )
    if "sparse" in lowered and ("cuda" in lowered or "gpu" in lowered or "backend" in lowered):
        return _issue(
            "GPU_SPARSE_BACKEND_UNAVAILABLE",
            "The GPU sparse matrix backend could not be used.",
            "Install or configure the sparse backend package required by the selected GPU runtime.",
        )
    if "cuda" in lowered and ("driver" in lowered or "runtime" in lowered):
        return _issue(
            "CUDA_DRIVER_RUNTIME_MISMATCH",
            "CUDA driver/runtime initialization failed.",
            "Check host NVIDIA driver compatibility, container GPU passthrough, and CUDA.jl runtime configuration.",
        )
    return _issue(
        "BACKEND_INITIALIZATION_FAILED",
        "Backend initialization failed.",
        "Inspect the original error in `backend_probe.error` and rerun the relevant setup or doctor command.",
    )


def get_julia(*, setup: bool = True):
    """Return ``juliacall.Main`` and initialize the Julia backend on first use."""
    global _jl, _sgr
    if _jl is not None and _sgr is not None:
        return _jl, _sgr

    log_event("backend_init_start", setup=setup)
    try:
        from juliacall import Main as jl

        if setup:
            jl.seval(
                """
                using Pkg
                function ensure_pkg(pkg_name)
                    if !haskey(Pkg.project().dependencies, pkg_name)
                        Pkg.add(pkg_name)
                    end
                end

                ensure_pkg("SciMLBase")
                ensure_pkg("Distributed")

                using OrdinaryDiffEq, StaticArrays, DiffEqCallbacks, LinearAlgebra, SparseArrays, SciMLBase, Distributed
                """
            )

        jl.include(str(_project_path() / "src" / "Sagittarius.jl"))
        _jl = jl
        _sgr = jl.Sagittarius
        log_event("backend_init_finish", julia_version=str(jl.VERSION))
        return _jl, _sgr
    except Exception as exc:
        detail = _classify_exception(exc)
        log_event("backend_init_failed", level=logging.ERROR, code=detail["code"], message=detail["message"])
        raise SagittariusRuntimeError(DiagnosticIssue(**detail)) from exc


def get_modules():
    jl, sgr = get_julia()
    return jl, sgr, sgr.Physics, sgr.Solver


def version_info(*, initialize_backend: bool = False) -> Dict[str, Any]:
    julia_version = str(_jl.VERSION) if _jl is not None else None
    if initialize_backend and julia_version is None:
        jl, _ = get_julia()
        julia_version = str(jl.VERSION)

    info = RuntimeInfo(
        python_version=sys.version.split()[0],
        package_version=package_version(),
        julia_version=julia_version,
        sagittarius_julia_version=_julia_project_version(),
        platform=platform.platform(),
        in_container=_in_container(),
    )
    return asdict(info)


def _run_command(command: list[str], *, timeout: int = 5) -> Dict[str, Any]:
    if not shutil.which(command[0]):
        return {"ok": False, "missing": True, "returncode": None, "output": None}
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "missing": False, "returncode": None, "output": None, "error": "timeout"}
    except OSError as exc:
        return {"ok": False, "missing": False, "returncode": None, "output": None, "error": str(exc)}
    output = (completed.stdout or completed.stderr).strip()
    return {
        "ok": completed.returncode == 0,
        "missing": False,
        "returncode": completed.returncode,
        "output": output.splitlines()[0] if output else None,
        "raw_output": output,
    }


def _command_version(command: list[str]) -> Optional[str]:
    result = _run_command(command)
    return result.get("output") if result.get("ok") else None


def _probe_julia_backend(jl: Any, backend: str) -> Dict[str, Any]:
    probe = _new_backend_probe(backend)
    probe["versions"]["julia"] = str(jl.VERSION)

    try:
        probe["versions"].update(dict(jl.seval(
            """
            begin
                using Pkg
                deps = Pkg.dependencies()
                wanted = ["OrdinaryDiffEq", "SciMLBase", "StaticArrays", "DiffEqCallbacks", "CUDA", "AMDGPU", "Metal"]
                Dict(string(dep.name) => string(dep.version) for dep in values(deps) if dep.name in wanted && dep.version !== nothing)
            end
            """
        )))
        _set_check(probe, "julia_package_versions", True, message="Collected Julia package versions.", severity="info")
    except Exception as exc:  # pragma: no cover - depends on Julia environment
        probe["errors"].append(str(exc))
        _set_check(probe, "julia_package_versions", False, message=str(exc), code="JULIA_PACKAGE_VERSION_PROBE_FAILED")

    jl.seval("using LinearAlgebra, SparseArrays")
    sparse_ok = bool(jl.seval("begin H = spzeros(ComplexF64, 2, 2); x = ComplexF64[1, 0]; length(H * x) == 2 end"))
    _set_check(probe, "sparse_matvec", sparse_ok, message="CPU sparse matrix-vector multiplication probe.")

    if backend == "CPU":
        probe["available"] = _required_checks_ok(probe, ("sparse_matvec",))
        return probe

    if backend == "CUDA":
        jl.seval("using CUDA")
        _set_check(probe, "package_loadable", True, message="CUDA.jl loaded.", severity="info")
        probe["versions"]["CUDA.jl"] = str(jl.seval("""begin using Pkg; deps = Pkg.dependencies(); only([string(dep.version) for dep in values(deps) if dep.name == \"CUDA\" && dep.version !== nothing]) end"""))
        probe["runtime"]["cuda_functional"] = bool(jl.seval("CUDA.functional()"))
        _set_check(probe, "cuda_functional", probe["runtime"]["cuda_functional"], message="CUDA.jl functional runtime check.", code="CUDA_DRIVER_RUNTIME_MISMATCH")
        device_count = int(jl.seval("try length(CUDA.devices()) catch; 0 end"))
        if device_count > 0:
            names = list(jl.seval("[string(CUDA.name(dev)) for dev in CUDA.devices()]"))
            probe["devices"] = [{"index": idx, "name": name} for idx, name in enumerate(names)]
        _set_check(probe, "device_visible", device_count > 0, message="CUDA device enumeration.", code="GPU_DEVICE_NOT_FOUND")
        if probe["runtime"]["cuda_functional"] and device_count > 0:
            alloc_ok = bool(jl.seval("begin x = CUDA.zeros(Float32, 1); Array(x)[1] == 0f0 end"))
            _set_check(probe, "device_allocation", alloc_ok, message="Minimal CUDA array allocation.", code="GPU_ALLOCATION_FAILED")
            jl.seval("using CUDA.CUSPARSE")
            sparse_backend_ok = bool(jl.seval("isdefined(CUDA, :CUSPARSE)"))
            _set_check(probe, "sparse_backend", sparse_backend_ok, message="CUDA sparse backend availability.", code="GPU_SPARSE_BACKEND_UNAVAILABLE")
        else:
            _set_check(probe, "device_allocation", False, message="Skipped because CUDA is not functional or no device is visible.", code="GPU_ALLOCATION_FAILED")
            _set_check(probe, "sparse_backend", False, message="Skipped because CUDA is not functional or no device is visible.", code="GPU_SPARSE_BACKEND_UNAVAILABLE")
        probe["available"] = _required_checks_ok(probe, ("sparse_matvec", "package_loadable", "cuda_functional", "device_visible", "device_allocation", "sparse_backend"))
        return probe

    if backend == "AMDGPU":
        jl.seval("using AMDGPU")
        _set_check(probe, "package_loadable", True, message="AMDGPU.jl loaded.", severity="info")
        alloc_ok = bool(jl.seval("try x = AMDGPU.zeros(Float32, 1); Array(x)[1] == 0f0 catch; false end"))
        _set_check(probe, "device_allocation", alloc_ok, message="Minimal AMDGPU array allocation.", code="GPU_ALLOCATION_FAILED")
        probe["available"] = _required_checks_ok(probe, ("sparse_matvec", "package_loadable", "device_allocation"))
        return probe

    if backend == "METAL":
        jl.seval("using Metal")
        _set_check(probe, "package_loadable", True, message="Metal.jl loaded.", severity="info")
        alloc_ok = bool(jl.seval("try x = Metal.zeros(Float32, 1); Array(x)[1] == 0f0 catch; false end"))
        _set_check(probe, "device_allocation", alloc_ok, message="Minimal Metal array allocation.", code="GPU_ALLOCATION_FAILED")
        probe["available"] = _required_checks_ok(probe, ("sparse_matvec", "package_loadable", "device_allocation"))
        return probe

    probe["available"] = False
    return probe


def doctor(*, backend: str = "CPU", initialize_backend: bool = False) -> Dict[str, Any]:
    """Inspect runtime capabilities without forcing Julia startup by default."""
    requested = backend.upper()
    maturity = backend_maturity()
    report: Dict[str, Any] = {
        "schema_version": DOCTOR_SCHEMA_VERSION,
        "runtime": version_info(initialize_backend=False),
        "requested_backend": requested,
        "backend_maturity": maturity,
        "container": {"detected": _in_container()},
        "gpu": {},
        "backend_probe": None,
        "available": True,
        "issues": [],
        "issue_details": [],
    }

    if requested not in maturity:
        _append_issue(
            report,
            "UNSUPPORTED_BACKEND",
            f"Unsupported backend: {requested}",
            f"Choose one of: {', '.join(sorted(maturity))}.",
        )
    elif requested == "CUDA":
        smi = _run_command(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader,nounits"])
        nvcc = _run_command(["nvcc", "--version"])
        report["gpu"]["nvidia_smi"] = smi
        report["gpu"]["nvcc"] = nvcc
        report["gpu"]["devices"] = _parse_nvidia_smi_csv(smi.get("raw_output") or smi.get("output"))
        if report["gpu"]["devices"]:
            report["gpu"]["driver"] = {"version": report["gpu"]["devices"][0].get("driver_version")}
        if not smi.get("ok"):
            _append_issue(
                report,
                "CUDA_PASSTHROUGH_UNAVAILABLE",
                "CUDA requested but nvidia-smi is unavailable or failed.",
                "Check NVIDIA drivers, container GPU passthrough, and whether the process can see the GPU.",
            )
    elif requested in {"AMDGPU", "METAL"}:
        _append_issue(
            report,
            "BACKEND_NOT_PARITY_TESTED",
            f"{requested} is marked {maturity[requested]['status']} and has no parity-tested runtime path.",
            "Use CPU or CUDA for validated workflows, or run backend-specific probes on an experimental machine.",
        )

    if initialize_backend and requested in maturity:
        try:
            jl, _ = get_julia()
            report["julia_loaded"] = True
            report["runtime"] = version_info(initialize_backend=False)
            try:
                probe = _probe_julia_backend(jl, requested)
                report["backend_probe"] = probe
                report["available"] = report["available"] and bool(probe.get("available"))
                if not probe.get("available"):
                    detail = _probe_failure_issue(probe)
                    _append_issue(report, detail["code"], detail["message"], detail["remediation"], severity=detail["severity"])
            except Exception as exc:  # pragma: no cover - environment dependent
                probe = _new_backend_probe(requested)
                probe["errors"].append(str(exc))
                report["backend_probe"] = probe
                detail = _classify_exception(exc)
                _append_issue(report, detail["code"], detail["message"], detail["remediation"], severity=detail["severity"])
        except Exception as exc:  # pragma: no cover - environment dependent
            report["available"] = False
            report["julia_loaded"] = False
            probe = _new_backend_probe(requested)
            probe["errors"].append(str(exc))
            report["backend_probe"] = probe
            detail = _classify_exception(exc)
            _append_issue(report, detail["code"], detail["message"], detail["remediation"], severity=detail["severity"])

    log_event("doctor_report", backend=requested, available=report["available"], issues=report["issues"])
    return report
