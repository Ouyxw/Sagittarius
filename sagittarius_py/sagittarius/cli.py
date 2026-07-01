from __future__ import annotations

import json
from typing import Any

import click

from .runtime import (
    SagittariusError,
    doctor as runtime_doctor,
    install_backend_profile,
    package_version,
    resolve_backend_dependencies,
)


def _echo_json(payload: Any) -> None:
    click.echo(json.dumps(payload, indent=2, sort_keys=True, default=str))


def _raise_click_error(exc: Exception) -> None:
    if isinstance(exc, SagittariusError):
        issue = exc.issue
        raise click.ClickException(f"{issue.code}: {issue.message} {issue.remediation}") from exc
    raise click.ClickException(str(exc)) from exc


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_version(), prog_name="sagittarius")
def main() -> None:
    """Sagittarius command line utilities."""


@main.command("doctor")
@click.option("--backend", default="CPU", show_default=True, help="Backend to diagnose: CPU, CUDA, AMDGPU, or Metal.")
@click.option("--initialize-backend", is_flag=True, help="Initialize Julia and run backend package probes.")
def doctor_command(backend: str, initialize_backend: bool) -> None:
    """Print runtime and backend diagnostics as JSON."""
    try:
        _echo_json(runtime_doctor(backend=backend, initialize_backend=initialize_backend))
    except Exception as exc:
        _raise_click_error(exc)


@main.group("backend")
def backend_group() -> None:
    """Manage Julia backend dependencies."""


@backend_group.command("resolve")
def backend_resolve_command() -> None:
    """Resolve the default CPU-first JuliaPkg environment."""
    try:
        _echo_json(resolve_backend_dependencies())
    except Exception as exc:
        _raise_click_error(exc)


@backend_group.command("install")
@click.argument("backend", type=click.Choice(["cuda"], case_sensitive=False))
@click.option("--skip-resolve", is_flag=True, help="Do not run the default CPU resolve step before installing the backend profile.")
@click.option("--initialize-backend", is_flag=True, help="Run initialized doctor diagnostics after installation.")
def backend_install_command(backend: str, skip_resolve: bool, initialize_backend: bool) -> None:
    """Install an explicit optional backend profile."""
    try:
        _echo_json(
            install_backend_profile(
                backend,
                resolve=not skip_resolve,
                initialize_backend=initialize_backend,
            )
        )
    except Exception as exc:
        _raise_click_error(exc)


if __name__ == "__main__":
    main()
