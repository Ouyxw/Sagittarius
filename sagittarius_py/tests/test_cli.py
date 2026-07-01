import json
import subprocess
import sys

from click.testing import CliRunner

from sagittarius import cli
from sagittarius.runtime import (
    DiagnosticIssue,
    SagittariusRuntimeError,
    optional_backend_profiles,
    resolve_backend_dependencies,
)


def test_cli_doctor_outputs_json(monkeypatch):
    monkeypatch.setattr(
        cli,
        "runtime_doctor",
        lambda *, backend, initialize_backend: {
            "schema_version": "doctor/v2.1",
            "backend": backend,
            "initialized": initialize_backend,
        },
    )

    result = CliRunner().invoke(cli.main, ["doctor", "--backend", "CUDA", "--initialize-backend"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["backend"] == "CUDA"
    assert payload["initialized"] is True


def test_backend_resolve_command_outputs_setup_report(monkeypatch):
    monkeypatch.setattr(
        cli,
        "resolve_backend_dependencies",
        lambda: {
            "schema_version": "backend-setup/v1",
            "action": "resolve",
            "backend": "CPU",
            "returncode": 0,
        },
    )

    result = CliRunner().invoke(cli.main, ["backend", "resolve"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "backend-setup/v1"
    assert payload["action"] == "resolve"
    assert payload["backend"] == "CPU"


def test_backend_install_cuda_command_uses_optional_profile(monkeypatch):
    calls = []

    def fake_install(backend, *, resolve, initialize_backend):
        calls.append((backend, resolve, initialize_backend))
        return {
            "schema_version": "backend-setup/v1",
            "action": "install",
            "backend": backend.upper(),
            "packages": ["CUDA"],
        }

    monkeypatch.setattr(cli, "install_backend_profile", fake_install)

    result = CliRunner().invoke(cli.main, ["backend", "install", "cuda", "--skip-resolve", "--initialize-backend"])

    assert result.exit_code == 0
    assert calls == [("cuda", False, True)]
    payload = json.loads(result.output)
    assert payload["backend"] == "CUDA"
    assert payload["packages"] == ["CUDA"]


def test_cli_errors_use_diagnostic_issue(monkeypatch):
    def fail():
        raise SagittariusRuntimeError(DiagnosticIssue(
            code="JULIAPKG_RESOLVE_FAILED",
            message="JuliaPkg dependency resolution failed.",
            remediation="Rerun setup.",
        ))

    monkeypatch.setattr(cli, "resolve_backend_dependencies", fail)

    result = CliRunner().invoke(cli.main, ["backend", "resolve"])

    assert result.exit_code != 0
    assert "JULIAPKG_RESOLVE_FAILED" in result.output
    assert "Rerun setup." in result.output


def test_optional_cuda_profile_metadata_is_available():
    profiles = optional_backend_profiles()

    assert profiles["CUDA"]["resource"] == "juliapkg-cuda.json"
    assert profiles["CUDA"]["packages"] == ["CUDA"]


def test_resolve_backend_dependencies_runs_juliapkg(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="resolved")

    monkeypatch.setattr("sagittarius.runtime.subprocess.run", fake_run)

    result = resolve_backend_dependencies()

    assert calls[0][0] == [sys.executable, "-m", "juliapkg", "resolve"]
    assert calls[0][1]["check"] is True
    assert result["schema_version"] == "backend-setup/v1"
    assert result["backend"] == "CPU"
    assert result["output"] == "resolved"
