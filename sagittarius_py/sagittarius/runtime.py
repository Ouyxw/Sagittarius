from __future__ import annotations

import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from importlib import metadata, resources
from pathlib import Path
from typing import Any, Dict, Optional

from .events import EVENT_CATALOG, EVENT_TAXONOMY_SCHEMA_VERSION, SEVERITY_LEVELS, validate_event_payload


LOGGER_NAME = "sagittarius"
DOCTOR_SCHEMA_VERSION = "doctor/v2.1"
BACKEND_PROBE_SCHEMA_VERSION = "backend-probe/v2.1"
FAILURE_DIAGNOSTIC_SCHEMA_VERSION = "failure-diagnostic/v1"
VERSION_INFO_SCHEMA_VERSION = "version-info/v1"
BACKEND_SETUP_SCHEMA_VERSION = "backend-setup/v1"
MIN_RECOMMENDED_CUDAJL_VERSION = "6.2.0"
CUDA_12_8_MIN_LINUX_DRIVER = "570.26"
CUDA_12_8_MIN_WINDOWS_DRIVER = "570.65"
BLACKWELL_COMPUTE_MAJOR_MIN = 10
JULIA_BACKEND_PATH_ENV = "SAGITTARIUS_JULIA_BACKEND_PATH"
PACKAGE_BACKEND_RESOURCE = ("julia", "Sagittarius.jl")
OPTIONAL_BACKEND_PROFILE_RESOURCES = {
    "CUDA": "juliapkg-cuda.json",
}

REQUIRED_CPU_JULIA_PACKAGES = (
    "OrdinaryDiffEq",
    "OrdinaryDiffEqLowOrderRK",
    "StaticArrays",
    "DiffEqCallbacks",
    "SciMLBase",
)

PYTHON_PACKAGE_VERSION_FIELDS = (
    "sagittarius-py",
    "juliacall",
    "juliapkg",
    "numpy",
    "scipy",
    "pandas",
    "matplotlib",
    "networkx",
    "docplex",
    "pulp",
    "seaborn",
)

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
    schema_version: str
    python_version: str
    package_version: str
    julia_version: Optional[str]
    sagittarius_julia_version: Optional[str]
    platform: str
    in_container: bool
    python: Dict[str, Any]
    julia: Dict[str, Any]
    build: Dict[str, Any]
    container: Dict[str, Any]
    backend_toolchains: Dict[str, Any]
    abi: Dict[str, Any]


@dataclass
class DiagnosticIssue:
    code: str
    message: str
    remediation: str
    severity: str = "error"


class SagittariusError(Exception):
    """Base class for Sagittarius exceptions that carry a normalized issue."""

    issue: DiagnosticIssue


class SagittariusRuntimeError(RuntimeError, SagittariusError):
    """Raised when a Sagittarius runtime backend cannot be initialized."""

    def __init__(self, issue: DiagnosticIssue):
        super().__init__(f"{issue.code}: {issue.message} {issue.remediation}")
        self.issue = issue


class SagittariusValidationError(ValueError, SagittariusError):
    """Raised when user inputs fail validation with an actionable diagnostic."""

    def __init__(self, issue: DiagnosticIssue):
        super().__init__(f"{issue.code}: {issue.message} {issue.remediation}")
        self.issue = issue


class SagittariusSolverError(RuntimeError, SagittariusError):
    """Raised when solver execution fails with an actionable diagnostic."""

    def __init__(self, issue: DiagnosticIssue):
        super().__init__(f"{issue.code}: {issue.message} {issue.remediation}")
        self.issue = issue


class SagittariusSerializationError(RuntimeError, SagittariusError):
    """Raised when result persistence fails with an actionable diagnostic."""

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
        return "1.0.2"


def _valid_julia_backend_path(path: Path) -> bool:
    return (path / "Project.toml").is_file() and (path / "src" / "Sagittarius.jl").is_file()


def _source_checkout_backend_path() -> Path:
    return Path(__file__).resolve().parents[2] / "Sagittarius.jl"


def _package_backend_resource_path() -> Optional[Path]:
    candidate = resources.files("sagittarius")
    for part in PACKAGE_BACKEND_RESOURCE:
        candidate = candidate.joinpath(part)

    try:
        path = Path(candidate)
    except TypeError:
        return None
    return path if _valid_julia_backend_path(path) else None


def _optional_backend_profile_payload(backend: str) -> Dict[str, Any]:
    normalized = backend.upper()
    resource_name = OPTIONAL_BACKEND_PROFILE_RESOURCES.get(normalized)
    if resource_name is None:
        raise SagittariusValidationError(DiagnosticIssue(
            code="UNSUPPORTED_BACKEND_SETUP",
            message=f"Backend setup profile is not available for {backend}.",
            remediation=f"Choose one of: {', '.join(sorted(OPTIONAL_BACKEND_PROFILE_RESOURCES))}.",
        ))

    profile = resources.files("sagittarius").joinpath(resource_name)
    try:
        return json.loads(profile.read_text())
    except Exception as exc:
        raise SagittariusRuntimeError(DiagnosticIssue(
            code="BACKEND_PROFILE_LOAD_FAILED",
            message=f"Could not load backend setup profile: {resource_name}",
            remediation="Reinstall the package and verify the wheel includes Sagittarius package data.",
        )) from exc


def _backend_profile_report(backend: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = backend.upper()
    packages = payload.get("packages", {})
    return {
        "schema_version": payload.get("schema_version", "backend-profile/v1"),
        "backend": payload.get("backend", normalized),
        "resource": OPTIONAL_BACKEND_PROFILE_RESOURCES[normalized],
        "maturity": payload.get("maturity", BACKEND_MATURITY.get(normalized, {}).get("status", "unknown")),
        "default": bool(payload.get("default", False)),
        "description": payload.get("description"),
        "julia": payload.get("julia"),
        "packages": {name: dict(spec) for name, spec in sorted(packages.items())},
        "package_names": sorted(packages.keys()),
        "install_command": f"sagittarius backend install {normalized.lower()}",
        "doctor_command": f"sagittarius doctor --backend {normalized} --initialize-backend",
    }


def optional_backend_profiles() -> Dict[str, Dict[str, Any]]:
    profiles: Dict[str, Dict[str, Any]] = {}
    for backend in sorted(OPTIONAL_BACKEND_PROFILE_RESOURCES):
        payload = _optional_backend_profile_payload(backend)
        profiles[backend] = _backend_profile_report(backend, payload)
    return profiles


def resolve_backend_dependencies() -> Dict[str, Any]:
    command = [sys.executable, "-m", "juliapkg", "resolve"]
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise SagittariusRuntimeError(DiagnosticIssue(
            code="JULIAPKG_RESOLVE_FAILED",
            message="JuliaPkg dependency resolution failed.",
            remediation="Inspect command output, verify Julia is installable, then rerun `sagittarius backend resolve`.",
        )) from exc

    return {
        "schema_version": BACKEND_SETUP_SCHEMA_VERSION,
        "action": "resolve",
        "backend": "CPU",
        "command": command,
        "returncode": completed.returncode,
        "output": completed.stdout,
    }


def install_backend_profile(backend: str, *, resolve: bool = True, initialize_backend: bool = False, dry_run: bool = False) -> Dict[str, Any]:
    normalized = backend.upper()
    if normalized == "CPU":
        return resolve_backend_dependencies()

    payload = _optional_backend_profile_payload(normalized)
    profile_report = _backend_profile_report(normalized, payload)
    packages = payload.get("packages", {})
    if not packages:
        raise SagittariusValidationError(DiagnosticIssue(
            code="BACKEND_PROFILE_EMPTY",
            message=f"Backend setup profile {normalized} does not declare any packages.",
            remediation="Reinstall the package and verify the backend profile package data.",
        ))

    if dry_run:
        return {
            "schema_version": BACKEND_SETUP_SCHEMA_VERSION,
            "action": "install",
            "backend": normalized,
            "dry_run": True,
            "profile": profile_report,
            "packages": sorted(packages.keys()),
            "resolved_default_profile": False,
        }

    resolve_result = resolve_backend_dependencies() if resolve else None

    try:
        _configure_juliacall_environment()
        from juliacall import Main as jl

        specs = json.dumps([
            {"name": name, **spec}
            for name, spec in sorted(packages.items())
        ])
        jl.seval(f"""
            using Pkg
            using UUIDs
            specs = {specs}
            for spec in specs
                version = haskey(spec, "version") ? VersionNumber(spec["version"]) : nothing
                package_spec = isnothing(version) ?
                    Pkg.PackageSpec(name=spec["name"], uuid=UUID(spec["uuid"])) :
                    Pkg.PackageSpec(name=spec["name"], uuid=UUID(spec["uuid"]), version=version)
                Pkg.add(package_spec)
            end
            Pkg.resolve()
            """)
    except Exception as exc:
        detail = _classify_exception(exc)
        raise SagittariusRuntimeError(DiagnosticIssue(
            code="BACKEND_PROFILE_INSTALL_FAILED",
            message=f"Failed to install {normalized} backend dependencies: {detail['message']}",
            remediation=f"Inspect Julia package output, verify network/registry access, then rerun `sagittarius backend install {normalized.lower()}`.",
        )) from exc

    report: Dict[str, Any] = {
        "schema_version": BACKEND_SETUP_SCHEMA_VERSION,
        "action": "install",
        "backend": normalized,
        "profile": profile_report,
        "packages": sorted(packages.keys()),
        "resolved_default_profile": resolve_result is not None,
    }
    if resolve_result is not None:
        report["resolve"] = {
            "schema_version": resolve_result["schema_version"],
            "action": resolve_result["action"],
            "backend": resolve_result["backend"],
            "returncode": resolve_result["returncode"],
        }
    if initialize_backend:
        report["doctor"] = doctor(backend=normalized, initialize_backend=True)
    return report


def _project_path() -> Path:
    override = os.environ.get(JULIA_BACKEND_PATH_ENV)
    if override:
        return Path(override).expanduser().resolve()

    source_checkout = _source_checkout_backend_path()
    if _valid_julia_backend_path(source_checkout):
        return source_checkout

    packaged = _package_backend_resource_path()
    if packaged is not None:
        return packaged

    return source_checkout


def _julia_backend_source(path: Path) -> str:
    if os.environ.get(JULIA_BACKEND_PATH_ENV):
        return "env_override"
    if path == _source_checkout_backend_path() and _valid_julia_backend_path(path):
        return "source_checkout"
    if _package_backend_resource_path() == path:
        return "package_resource"
    return "source_checkout"


def _julia_backend_metadata() -> Dict[str, Any]:
    path = _project_path()
    source = _julia_backend_source(path)
    return {
        "project_path": str(path),
        "source": source,
        "path_env": JULIA_BACKEND_PATH_ENV if source == "env_override" else None,
        "available": _valid_julia_backend_path(path),
    }


def _julia_project_version() -> Optional[str]:
    project = _project_path() / "Project.toml"
    try:
        for line in project.read_text().splitlines():
            if line.strip().startswith("version"):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        return None
    return None


def _configure_juliacall_environment() -> None:
    """Fill JuliaCall env vars when juliapkg/juliaup auto-detection is incomplete."""
    if all(os.environ.get(name) for name in ("PYTHON_JULIACALL_EXE", "PYTHON_JULIACALL_PROJECT", "PYTHON_JULIACALL_BINDIR")):
        return

    try:
        import juliapkg

        exe = os.environ.get("PYTHON_JULIACALL_EXE") or shutil.which(juliapkg.executable()) or juliapkg.executable()
        project = os.environ.get("PYTHON_JULIACALL_PROJECT") or juliapkg.project()
    except Exception:
        return

    if exe and project:
        os.environ.setdefault("PYTHON_JULIACALL_EXE", exe)
        os.environ.setdefault("PYTHON_JULIACALL_PROJECT", project)

    if os.environ.get("PYTHON_JULIACALL_BINDIR"):
        return

    try:
        completed = subprocess.run(
            [exe, "--startup-file=no", "-e", "print(Sys.BINDIR)"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return
    bindir = completed.stdout.strip()
    if completed.returncode == 0 and bindir and os.path.exists(bindir):
        os.environ.setdefault("PYTHON_JULIACALL_BINDIR", bindir)


def _in_container() -> bool:
    if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
        return True
    try:
        cgroup = Path("/proc/1/cgroup").read_text(errors="ignore").lower()
    except OSError:
        return False
    return any(token in cgroup for token in ("docker", "kubepods", "containerd", "podman"))


def _metadata_command(command: list[str], *, timeout: int = 3) -> Dict[str, Any]:
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


def _installed_package_versions(names: tuple[str, ...]) -> Dict[str, Optional[str]]:
    versions: Dict[str, Optional[str]] = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = package_version() if name == "sagittarius-py" else None
    return versions


def _source_metadata() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    result: Dict[str, Any] = {"root": str(root)}
    head = _metadata_command(["git", "-C", str(root), "rev-parse", "HEAD"])
    short = _metadata_command(["git", "-C", str(root), "rev-parse", "--short", "HEAD"])
    branch = _metadata_command(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"])
    status = _metadata_command(["git", "-C", str(root), "status", "--porcelain"])
    result.update({
        "git_commit": head.get("output") if head.get("ok") else None,
        "git_commit_short": short.get("output") if short.get("ok") else None,
        "git_branch": branch.get("output") if branch.get("ok") else None,
        "git_dirty": bool(status.get("raw_output")) if status.get("ok") else None,
    })
    return result


def _container_metadata() -> Dict[str, Any]:
    image = (
        os.environ.get("SAGITTARIUS_CONTAINER_IMAGE")
        or os.environ.get("IMAGE_NAME")
        or os.environ.get("CONTAINER_IMAGE")
    )
    return {
        "detected": _in_container(),
        "image": image,
        "id": os.environ.get("HOSTNAME") if _in_container() else None,
        "devcontainer": bool(os.environ.get("REMOTE_CONTAINERS") or os.environ.get("DEVCONTAINER")),
    }


def _python_abi_metadata() -> Dict[str, Any]:
    libc_name, libc_version = platform.libc_ver()
    return {
        "implementation": platform.python_implementation(),
        "version": sys.version.split()[0],
        "cache_tag": getattr(sys.implementation, "cache_tag", None),
        "executable": sys.executable,
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "libc": {"name": libc_name or None, "version": libc_version or None},
    }


def _host_abi_metadata() -> Dict[str, Any]:
    return {
        "python": _python_abi_metadata(),
        "julia": {
            "version": str(_jl.VERSION) if _jl is not None else None,
            "sagittarius_julia_version": _julia_project_version(),
            **_julia_backend_metadata(),
        },
    }


def _backend_parity_status(backend: str) -> Dict[str, Any]:
    normalized = backend.upper()
    if normalized == "CPU":
        return {
            "status": "regular_test_suite",
            "hardware_validated_by_doctor": False,
            "test_entrypoints": ["sagittarius_py/tests/"],
            "notes": "CPU execution is covered by the regular Python/Julia test suite; doctor() is a capability probe, not a numerical parity test.",
        }
    if normalized == "CUDA":
        return {
            "status": "opt_in_hardware_parity_suite",
            "hardware_validated_by_doctor": False,
            "test_entrypoints": ["SAGITTARIUS_ENABLE_GPU_TESTS=1 uv run python -m pytest tests/test_gpu_acceleration.py"],
            "notes": "doctor(backend='CUDA', initialize_backend=True) checks runtime capability. CPU/GPU numerical parity is validated separately by the opt-in CUDA parity suite.",
        }
    if normalized in {"AMDGPU", "METAL"}:
        return {
            "status": "not_parity_tested",
            "hardware_validated_by_doctor": False,
            "test_entrypoints": [],
            "notes": f"{normalized} is maturity-tracked but does not yet have established parity tests or deployment documentation.",
        }
    return {
        "status": "unsupported",
        "hardware_validated_by_doctor": False,
        "test_entrypoints": [],
        "notes": "Unsupported backend name.",
    }


def _backend_abi_report(backend: str, runtime_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    normalized = backend.upper()
    runtime_info = runtime_info or version_info(initialize_backend=False)
    toolchains = runtime_info.get("backend_toolchains", {})
    report = {
        "backend": normalized,
        "host": runtime_info.get("abi", _host_abi_metadata()),
        "maturity": BACKEND_MATURITY.get(normalized),
        "toolchain": toolchains.get(normalized, {}),
        "compatibility": {},
    }
    if normalized == "CUDA":
        cuda = toolchains.get("CUDA", {})
        devices = cuda.get("devices", [])
        compatibility = cuda.get("compatibility", {})
        report["driver"] = {"version": compatibility.get("driver_version")}
        report["runtime"] = {"nvcc": cuda.get("nvcc")}
        report["devices"] = devices
        report["compatibility"] = compatibility
    elif normalized == "AMDGPU":
        report["runtime"] = {"rocm_smi": toolchains.get("AMDGPU", {}).get("rocm_smi")}
    elif normalized == "METAL":
        report["runtime"] = {"metal_compiler": toolchains.get("METAL", {}).get("metal_compiler")}
    return report


def _backend_capability_summary(backend: str, runtime_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    normalized = backend.upper()
    return {
        "backend": normalized,
        "maturity": BACKEND_MATURITY.get(normalized),
        "parity": _backend_parity_status(normalized),
        "abi": _backend_abi_report(normalized, runtime_info),
    }


def _backend_toolchain_metadata() -> Dict[str, Any]:
    nvidia_smi = _query_nvidia_smi()
    nvcc = _metadata_command(["nvcc", "--version"])
    rocm_smi = _metadata_command(["rocm-smi", "--showdriverversion"])
    metal = _metadata_command(["xcrun", "--find", "metal"]) if sys.platform == "darwin" else {"ok": False, "missing": True, "returncode": None, "output": None}
    cuda_devices = _parse_nvidia_smi_csv(nvidia_smi.get("raw_output") or nvidia_smi.get("output"))
    return {
        "CUDA": {
            "nvidia_smi": nvidia_smi,
            "nvcc": nvcc,
            "devices": cuda_devices,
            "compatibility": _cuda_host_compatibility(cuda_devices),
        },
        "AMDGPU": {"rocm_smi": rocm_smi},
        "METAL": {"metal_compiler": metal},
    }


def _issue(code: str, message: str, remediation: str, *, severity: str = "error") -> Dict[str, str]:
    return asdict(DiagnosticIssue(code=code, message=message, remediation=remediation, severity=severity))


def make_issue(code: str, message: str, remediation: str, *, severity: str = "error") -> DiagnosticIssue:
    return DiagnosticIssue(code=code, message=message, remediation=remediation, severity=severity)


def emit_failure_diagnostic(issue: DiagnosticIssue | Dict[str, str], *, backend: Optional[str] = None) -> None:
    detail = asdict(issue) if isinstance(issue, DiagnosticIssue) else dict(issue)
    fields: Dict[str, Any] = {
        "code": detail["code"],
        "message": detail["message"],
        "remediation": detail["remediation"],
        "severity": detail.get("severity", "error"),
    }
    if backend is not None:
        fields["backend"] = backend
    log_event("failure_diagnostic", level=SEVERITY_LEVELS.get(fields["severity"], logging.ERROR), **fields)


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
        "abi": {},
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
            "compute_capability": parts[3] if len(parts) > 3 else None,
        })
    return devices


def _version_tuple(value: Optional[str]) -> tuple[int, ...]:
    if not value:
        return ()
    parts = []
    for raw in str(value).replace("+", ".").replace("-", ".").split("."):
        digits = "".join(ch for ch in raw if ch.isdigit())
        if digits == "":
            break
        parts.append(int(digits))
    return tuple(parts)


def _version_at_least(value: Optional[str], minimum: str) -> Optional[bool]:
    current = _version_tuple(value)
    required = _version_tuple(minimum)
    if not current or not required:
        return None
    width = max(len(current), len(required))
    return current + (0,) * (width - len(current)) >= required + (0,) * (width - len(required))


def _compute_major(device: Dict[str, Optional[str]]) -> Optional[int]:
    capability = device.get("compute_capability")
    if not capability:
        return None
    try:
        return int(str(capability).split(".", 1)[0])
    except ValueError:
        return None


def _cuda_host_compatibility(devices: list[Dict[str, Optional[str]]]) -> Dict[str, Any]:
    driver_version = devices[0].get("driver_version") if devices else None
    blackwell_devices = [device for device in devices if (_compute_major(device) or 0) >= BLACKWELL_COMPUTE_MAJOR_MIN]
    return {
        "driver_version": driver_version,
        "cuda_12_8_min_linux_driver": CUDA_12_8_MIN_LINUX_DRIVER,
        "cuda_12_8_min_windows_driver": CUDA_12_8_MIN_WINDOWS_DRIVER,
        "cuda_12_8_driver_ok": _version_at_least(driver_version, CUDA_12_8_MIN_LINUX_DRIVER),
        "blackwell_detected": bool(blackwell_devices),
        "blackwell_devices": blackwell_devices,
    }


def _missing_julia_package_name(text: str) -> Optional[str]:
    match = re.search(
        r"Package\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:not found|is required but does not seem to be installed)",
        text,
    )
    return match.group(1) if match else None


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
    if "pkg.instantiate" in lowered or ("does not seem to be installed" in lowered and "package" not in lowered):
        return _issue(
            "JULIA_PROJECT_NOT_INSTANTIATED",
            "The Julia project dependencies are not instantiated.",
            "Run `julia --project=Sagittarius.jl -e 'using Pkg; Pkg.instantiate()'` or `cd sagittarius_py && uv run python -m juliapkg resolve`.",
        )
    if "package" in lowered and ("not found" in lowered or "not installed" in lowered or "could not be loaded" in lowered):
        missing = _missing_julia_package_name(text)
        package_detail = f" Missing Julia package: {missing}." if missing else ""
        return _issue(
            "JULIA_PACKAGE_LOAD_FAILED",
            f"A required Julia package could not be loaded.{package_detail}",
            "Run `uv run python -m juliapkg resolve` in the active Python project. "
            "If this is an older editable experiment environment, run `uv sync --reinstall-package sagittarius-py` first.",
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
        project_path = _project_path()
        if not _valid_julia_backend_path(project_path):
            raise SagittariusRuntimeError(DiagnosticIssue(
                code="JULIA_BACKEND_PATH_INVALID",
                message=f"Julia backend path is missing Project.toml or src/Sagittarius.jl: {project_path}",
                remediation=f"Set {JULIA_BACKEND_PATH_ENV} to a Sagittarius.jl backend directory or reinstall the package with Julia backend resources.",
            ))

        _configure_juliacall_environment()
        from juliacall import Main as jl

        if setup:
            required_packages = json.dumps(list(REQUIRED_CPU_JULIA_PACKAGES))
            jl.seval(
                f"""
                using Pkg
                function ensure_pkg(pkg_name)
                    if !haskey(Pkg.project().dependencies, pkg_name)
                        Pkg.add(pkg_name)
                    end
                end

                required_cpu_packages = {required_packages}
                for pkg_name in required_cpu_packages
                    ensure_pkg(pkg_name)
                end
                ensure_pkg("Distributed")

                using OrdinaryDiffEq, OrdinaryDiffEqLowOrderRK, StaticArrays, DiffEqCallbacks, LinearAlgebra, SparseArrays, SciMLBase, Distributed
                """
            )

        jl.include(str(project_path / "src" / "Sagittarius.jl"))
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

    python_version = sys.version.split()[0]
    packages = _installed_package_versions(PYTHON_PACKAGE_VERSION_FIELDS)
    sagittarius_julia_version = _julia_project_version()
    container = _container_metadata()
    source = _source_metadata()
    build = {
        "source": source,
        "ci": bool(os.environ.get("CI")),
        "build_id": os.environ.get("BUILD_ID") or os.environ.get("GITHUB_RUN_ID"),
        "build_number": os.environ.get("BUILD_NUMBER") or os.environ.get("GITHUB_RUN_NUMBER"),
    }
    info = RuntimeInfo(
        schema_version=VERSION_INFO_SCHEMA_VERSION,
        python_version=python_version,
        package_version=package_version(),
        julia_version=julia_version,
        sagittarius_julia_version=sagittarius_julia_version,
        platform=platform.platform(),
        in_container=bool(container["detected"]),
        python={
            "version": python_version,
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
            "packages": packages,
        },
        julia={
            "version": julia_version,
            "sagittarius_julia_version": sagittarius_julia_version,
            **_julia_backend_metadata(),
        },
        build=build,
        container=container,
        backend_toolchains=_backend_toolchain_metadata(),
        abi=_host_abi_metadata(),
    )
    return asdict(info)


def _run_command(command: list[str], *, timeout: int = 5) -> Dict[str, Any]:
    return _metadata_command(command, timeout=timeout)


def _command_version(command: list[str]) -> Optional[str]:
    result = _run_command(command)
    return result.get("output") if result.get("ok") else None


def _query_nvidia_smi() -> Dict[str, Any]:
    detailed = _run_command(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,compute_cap", "--format=csv,noheader,nounits"])
    if detailed.get("ok"):
        detailed["query_fields"] = ["name", "driver_version", "memory.total", "compute_cap"]
        return detailed

    fallback = _run_command(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader,nounits"])
    if fallback.get("ok"):
        fallback["query_fields"] = ["name", "driver_version", "memory.total"]
        fallback["fallback_from_compute_cap"] = True
        return fallback
    detailed["fallback"] = fallback
    return detailed


def _probe_julia_backend(jl: Any, backend: str) -> Dict[str, Any]:
    probe = _new_backend_probe(backend)
    probe["versions"]["julia"] = str(jl.VERSION)

    try:
        probe["versions"].update(dict(jl.seval(
            """
            begin
                using Pkg
                deps = Pkg.dependencies()
                wanted = ["OrdinaryDiffEq", "OrdinaryDiffEqLowOrderRK", "SciMLBase", "StaticArrays", "DiffEqCallbacks", "CUDA", "AMDGPU", "Metal"]
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
        cudajl_ok = _version_at_least(probe["versions"].get("CUDA.jl"), MIN_RECOMMENDED_CUDAJL_VERSION)
        _set_check(
            probe,
            "cudajl_version_recommended",
            cudajl_ok is not False,
            message=f"CUDA.jl >= {MIN_RECOMMENDED_CUDAJL_VERSION} is recommended for CUDA 12.8+/Blackwell workflows.",
            severity="warning" if cudajl_ok is False else "info",
            code="CUDAJL_VERSION_BELOW_RECOMMENDED" if cudajl_ok is False else None,
        )
        probe["runtime"].update(dict(jl.seval("""
            begin
                Dict(
                    "cuda_functional" => CUDA.functional(),
                    "runtime_version" => string(try CUDA.runtime_version() catch; missing end),
                    "driver_version" => string(try CUDA.driver_version() catch; missing end),
                )
            end
            """)))
        probe["abi"] = {
            "backend": "CUDA",
            "julia": {"version": probe["versions"].get("julia")},
            "package_versions": {"CUDA.jl": probe["versions"].get("CUDA.jl")},
            "driver": {"version": probe["runtime"].get("driver_version")},
            "runtime": {"version": probe["runtime"].get("runtime_version")},
        }
        probe["runtime"]["cuda_functional"] = bool(probe["runtime"].get("cuda_functional"))
        _set_check(probe, "cuda_functional", probe["runtime"]["cuda_functional"], message="CUDA.jl functional runtime check.", code="CUDA_DRIVER_RUNTIME_MISMATCH")
        device_count = int(jl.seval("try length(CUDA.devices()) catch; 0 end"))
        if device_count > 0:
            probe["devices"] = list(jl.seval("""
                [Dict(
                    "index" => idx - 1,
                    "name" => string(CUDA.name(dev)),
                    "compute_capability" => string(try CUDA.capability(dev) catch; missing end),
                    "total_memory_bytes" => string(try CUDA.totalmem(dev) catch; missing end),
                ) for (idx, dev) in enumerate(CUDA.devices())]
                """))
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
    runtime_info = version_info(initialize_backend=False)
    report: Dict[str, Any] = {
        "schema_version": DOCTOR_SCHEMA_VERSION,
        "runtime": runtime_info,
        "requested_backend": requested,
        "backend_maturity": maturity,
        "container": _container_metadata(),
        "gpu": {},
        "backend_probe": None,
        "capabilities": _backend_capability_summary(requested, runtime_info),
        "backend_source": runtime_info["julia"]["source"],
        "julia_backend": runtime_info["julia"],
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
        smi = _query_nvidia_smi()
        nvcc = _run_command(["nvcc", "--version"])
        report["gpu"]["nvidia_smi"] = smi
        report["gpu"]["nvcc"] = nvcc
        report["gpu"]["devices"] = _parse_nvidia_smi_csv(smi.get("raw_output") or smi.get("output"))
        report["gpu"]["compatibility"] = _cuda_host_compatibility(report["gpu"]["devices"])
        if report["gpu"]["devices"]:
            report["gpu"]["driver"] = {"version": report["gpu"]["devices"][0].get("driver_version")}
        if report["gpu"]["compatibility"].get("blackwell_detected") and report["gpu"]["compatibility"].get("cuda_12_8_driver_ok") is False:
            _append_issue(
                report,
                "CUDA_BLACKWELL_DRIVER_BELOW_RECOMMENDED",
                "Blackwell-class NVIDIA GPU detected with a driver below the CUDA 12.8 GA recommendation.",
                f"Use an NVIDIA Linux driver >= {CUDA_12_8_MIN_LINUX_DRIVER} or Windows driver >= {CUDA_12_8_MIN_WINDOWS_DRIVER} for CUDA 12.8+/Blackwell workflows.",
                severity="warning",
            )
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
            report["capabilities"] = _backend_capability_summary(requested, report["runtime"])
            report["backend_source"] = report["runtime"]["julia"]["source"]
            report["julia_backend"] = report["runtime"]["julia"]
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
