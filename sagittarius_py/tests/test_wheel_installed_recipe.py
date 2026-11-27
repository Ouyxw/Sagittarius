"""External-project smoke for the Phase 15 wheel-installed recipe.

The smoke is opt-in because it builds a wheel, creates an isolated environment,
and initializes the Julia backend.  Its project directory is deliberately
created below ``/tmp`` to emulate a clean Ubuntu WSL user project.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PY_PACKAGE_ROOT = REPO_ROOT / "sagittarius_py"
WHEEL_RECIPE = REPO_ROOT / "workspace" / "examples" / "recipes" / "wheel_installed_mwis_udg.py"


def _run(command, *, cwd: Path, env=None):
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )


def _venv_executable(venv_dir: Path, name: str) -> Path:
    scripts = "Scripts" if sys.platform == "win32" else "bin"
    suffix = ".exe" if sys.platform == "win32" else ""
    return venv_dir / scripts / f"{name}{suffix}"


def _json_from_output(output: str) -> dict:
    decoder = json.JSONDecoder()
    for index, character in enumerate(output):
        if character == "{":
            try:
                payload, _ = decoder.raw_decode(output[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
    raise AssertionError(f"No JSON object found in command output: {output}")


def test_wheel_recipe_template_is_self_contained_and_documented():
    template = WHEEL_RECIPE.read_text(encoding="utf-8")
    guide = (REPO_ROOT / "docs" / "getting-started" / "python" / "wheel-experiment-recipe.md").read_text(
        encoding="utf-8"
    )

    assert "from common import" not in template
    assert "workspace." not in template
    assert "from sagittarius import" in template
    assert "package_resource" in guide
    assert "SAGITTARIUS_RUN_WHEEL_RECIPE_SMOKE=1" in guide


@pytest.mark.requires_julia_backend
def test_clean_venv_installed_wheel_mwis_recipe_smoke():
    if os.environ.get("SAGITTARIUS_RUN_WHEEL_RECIPE_SMOKE") != "1":
        pytest.skip("Set SAGITTARIUS_RUN_WHEEL_RECIPE_SMOKE=1 to run the external wheel recipe smoke test.")
    if os.name == "nt":
        pytest.skip("The external wheel recipe smoke creates its project under /tmp and is intended for Linux/WSL.")

    with tempfile.TemporaryDirectory(prefix="sagittarius-wheel-mwis-", dir="/tmp") as project_dir:
        external_repo = Path(project_dir)
        dist_dir = external_repo / "dist"
        _run(["uv", "build", "--wheel", "--out-dir", str(dist_dir)], cwd=PY_PACKAGE_ROOT)
        wheel = next(dist_dir.glob("*.whl"))

        work_dir = external_repo / "mwis-user-project"
        script_dir = work_dir / "scripts"
        script_dir.mkdir(parents=True)
        script_path = script_dir / "mwis_udg.py"
        shutil.copyfile(WHEEL_RECIPE, script_path)

        venv_dir = external_repo / ".venv"
        _run(["uv", "venv", "--seed", str(venv_dir)], cwd=external_repo)
        python = _venv_executable(venv_dir, "python")
        sagittarius_cli = _venv_executable(venv_dir, "sagittarius")
        env = os.environ.copy()
        for name in ("PYTHONPATH", "SAGITTARIUS_JULIA_BACKEND_PATH", "PYTHON_JULIACALL_PROJECT", "JULIA_PROJECT"):
            env.pop(name, None)
        env["PYTHONNOUSERSITE"] = "1"
        env["SAGITTARIUS_SOURCE_ROOT_FOR_TEST"] = str(REPO_ROOT)

        _run([str(python), "-m", "pip", "install", "--force-reinstall", str(wheel)], cwd=work_dir, env=env)
        _run([str(sagittarius_cli), "backend", "resolve"], cwd=work_dir, env=env)
        completed = _run(
            [str(python), str(script_path), "--output-dir", "artifacts/mwis-udg"],
            cwd=work_dir,
            env=env,
        )
        summary = _json_from_output(completed.stdout)
        artifact_path = Path(summary["result_artifact"])
        samples_path = Path(summary["measurement_samples"])
        assert artifact_path.is_file()
        assert samples_path.is_file()

        inspection = _run(
            [
                str(python),
                "-c",
                """
import json
import os
from pathlib import Path
import sagittarius

source_root = Path(os.environ["SAGITTARIUS_SOURCE_ROOT_FOR_TEST"]).resolve()
assert not Path(sagittarius.__file__).resolve().is_relative_to(source_root)
report = sagittarius.doctor()
assert report["backend_source"] == "package_resource"
result = sagittarius.load_result(Path(os.environ["RECIPE_ARTIFACT"]))
sagittarius.validate_run_manifest(result.manifest)
assert result.manifest["versions"]["julia"]["source"] == "package_resource"
samples = json.loads(Path(os.environ["RECIPE_SAMPLES"]).read_text())
assert samples["schema_version"] == "measurement-samples/v1"
assert sum(samples["counts"].values()) == 64
print(json.dumps({"backend_source": report["backend_source"], "manifest_schema": result.manifest["schema_version"]}))
""",
            ],
            cwd=work_dir,
            env={**env, "RECIPE_ARTIFACT": str(artifact_path), "RECIPE_SAMPLES": str(samples_path)},
        )
        assert _json_from_output(inspection.stdout) == {
            "backend_source": "package_resource",
            "manifest_schema": "run-manifest/v1",
        }
