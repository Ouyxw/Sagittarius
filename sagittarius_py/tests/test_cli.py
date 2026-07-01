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

    def fake_install(backend, *, resolve, initialize_backend, dry_run):
        calls.append((backend, resolve, initialize_backend, dry_run))
        return {
            "schema_version": "backend-setup/v1",
            "action": "install",
            "backend": backend.upper(),
            "packages": ["CUDA"],
        }

    monkeypatch.setattr(cli, "install_backend_profile", fake_install)

    result = CliRunner().invoke(cli.main, ["backend", "install", "cuda", "--skip-resolve", "--initialize-backend"])

    assert result.exit_code == 0
    assert calls == [("cuda", False, True, False)]
    payload = json.loads(result.output)
    assert payload["backend"] == "CUDA"
    assert payload["packages"] == ["CUDA"]


def test_backend_profiles_command_lists_cuda_profile():
    result = CliRunner().invoke(cli.main, ["backend", "profiles"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    cuda = payload["profiles"]["CUDA"]
    assert cuda["schema_version"] == "backend-profile/v1"
    assert cuda["maturity"] == "experimental"
    assert cuda["default"] is False
    assert cuda["package_names"] == ["CUDA"]
    assert cuda["packages"]["CUDA"]["version"] == "6.2.0"
    assert cuda["install_command"] == "sagittarius backend install cuda"


def test_backend_install_cuda_dry_run_reports_profile_without_installing():
    result = CliRunner().invoke(cli.main, ["backend", "install", "cuda", "--dry-run"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "backend-setup/v1"
    assert payload["backend"] == "CUDA"
    assert payload["dry_run"] is True
    assert payload["packages"] == ["CUDA"]
    assert payload["profile"]["resource"] == "juliapkg-cuda.json"
    assert payload["profile"]["packages"]["CUDA"]["uuid"] == "052768ef-5323-5732-b1bb-66c8b64840ba"


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

    assert profiles["CUDA"]["schema_version"] == "backend-profile/v1"
    assert profiles["CUDA"]["resource"] == "juliapkg-cuda.json"
    assert profiles["CUDA"]["maturity"] == "experimental"
    assert profiles["CUDA"]["default"] is False
    assert profiles["CUDA"]["package_names"] == ["CUDA"]
    assert profiles["CUDA"]["packages"]["CUDA"]["version"] == "6.2.0"


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
