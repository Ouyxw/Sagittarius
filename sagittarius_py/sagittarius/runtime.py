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


LOGGER_NAME = "sagittarius"

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
    "Metal": {
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


def configure_logging(level: int | str = logging.INFO, *, json_output: bool = False) -> None:
    """Configure Sagittarius structured logging."""
    global _json_logging
    _json_logging = json_output
    _logger.setLevel(level)
    if not _logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        _logger.addHandler(handler)


def log_event(event: str, level: int = logging.INFO, **fields: Any) -> None:
    payload = {"event": event, **fields}
    if _json_logging:
        _logger.log(level, json.dumps(payload, sort_keys=True, default=str))
    else:
        detail = " ".join(f"{key}={value}" for key, value in sorted(fields.items()))
        _logger.log(level, "%s%s", event, f" {detail}" if detail else "")


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


def get_julia(*, setup: bool = True):
    """Return ``juliacall.Main`` and initialize the Julia backend on first use."""
    global _jl, _sgr
    if _jl is not None and _sgr is not None:
        return _jl, _sgr

    log_event("backend_init_start", setup=setup)
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


def _command_version(command: list[str]) -> Optional[str]:
    if not shutil.which(command[0]):
        return None
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    output = (completed.stdout or completed.stderr).strip()
    return output.splitlines()[0] if output else None


def doctor(*, backend: str = "CPU", initialize_backend: bool = False) -> Dict[str, Any]:
    """Inspect runtime capabilities without forcing Julia startup by default."""
    requested = backend.upper()
    maturity = backend_maturity()
    report: Dict[str, Any] = {
        "runtime": version_info(initialize_backend=initialize_backend),
        "requested_backend": requested,
        "backend_maturity": maturity,
        "container": {"detected": _in_container()},
        "gpu": {},
        "available": True,
        "issues": [],
    }

    if requested not in maturity:
        report["available"] = False
        report["issues"].append(f"Unsupported backend: {requested}")
    elif requested == "CUDA":
        nvidia_smi = _command_version(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"])
        nvcc = _command_version(["nvcc", "--version"])
        report["gpu"]["nvidia_smi"] = nvidia_smi
        report["gpu"]["nvcc"] = nvcc
        if nvidia_smi is None:
            report["available"] = False
            report["issues"].append("CUDA requested but nvidia-smi is unavailable; GPU passthrough or drivers may be missing.")
    elif requested in {"AMDGPU", "METAL"}:
        report["available"] = False
        report["issues"].append(f"{requested} is marked {maturity[requested]['status']} and has no parity-tested runtime path.")

    if initialize_backend:
        try:
            get_julia()
            report["julia_loaded"] = True
        except Exception as exc:  # pragma: no cover - environment dependent
            report["available"] = False
            report["julia_loaded"] = False
            report["issues"].append(f"Julia backend failed to initialize: {exc}")

    log_event("doctor_report", backend=requested, available=report["available"], issues=report["issues"])
    return report
