import json
import os
import subprocess
import sys
import tarfile
import zipfile
from importlib.resources import files
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PY_PACKAGE_ROOT = REPO_ROOT / "sagittarius_py"
EMBEDDED_BACKEND = PY_PACKAGE_ROOT / "sagittarius" / "julia" / "Sagittarius.jl"
CANONICAL_BACKEND = REPO_ROOT / "Sagittarius.jl"
REQUIRED_BACKEND_FILES = {
    "sagittarius/juliapkg.json",
    "sagittarius/juliapkg-cuda.json",
    "sagittarius/julia/Sagittarius.jl/Project.toml",
    "sagittarius/julia/Sagittarius.jl/Manifest.toml",
    "sagittarius/julia/Sagittarius.jl/src/Sagittarius.jl",
    "sagittarius/julia/Sagittarius.jl/src/physics.jl",
    "sagittarius/julia/Sagittarius.jl/src/solver.jl",
    "sagittarius/julia/Sagittarius.jl/src/logging.jl",
    "sagittarius/julia/Sagittarius.jl/src/program.jl",
    "sagittarius/julia/Sagittarius.jl/src/cluster.jl",
}


def _run(command, *, cwd=PY_PACKAGE_ROOT, env=None):
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )


def _venv_python(venv_dir: Path) -> Path:
    binary = "python.exe" if sys.platform == "win32" else "python"
    scripts = "Scripts" if sys.platform == "win32" else "bin"
    return venv_dir / scripts / binary


@pytest.fixture(scope="session")
def built_artifacts(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("sagittarius-artifacts")
    _run(["uv", "build", "--wheel", "--sdist", "--out-dir", str(out_dir)])
    wheel = next(out_dir.glob("*.whl"))
    sdist = next(out_dir.glob("*.tar.gz"))
    return wheel, sdist


def test_embedded_julia_backend_resource_is_available():
    backend = files("sagittarius").joinpath("julia", "Sagittarius.jl")

    assert backend.joinpath("Project.toml").is_file()
    assert backend.joinpath("Manifest.toml").is_file()
    assert backend.joinpath("src", "Sagittarius.jl").is_file()


def test_embedded_julia_backend_matches_canonical_source():
    embedded_files = {path.relative_to(EMBEDDED_BACKEND) for path in EMBEDDED_BACKEND.rglob("*") if path.is_file()}
    canonical_files = {path.relative_to(CANONICAL_BACKEND) for path in CANONICAL_BACKEND.rglob("*") if path.is_file()}

    assert embedded_files == canonical_files
    for relative_path in canonical_files:
        assert (EMBEDDED_BACKEND / relative_path).read_bytes() == (CANONICAL_BACKEND / relative_path).read_bytes()


def test_wheel_contains_embedded_julia_backend(built_artifacts):
    wheel, _ = built_artifacts

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())

    assert REQUIRED_BACKEND_FILES <= names


def test_sdist_contains_embedded_julia_backend(built_artifacts):
    _, sdist = built_artifacts

    with tarfile.open(sdist) as archive:
        names = {name.partition("/")[2] for name in archive.getnames() if "/" in name}

    assert REQUIRED_BACKEND_FILES <= names


@pytest.mark.requires_julia_backend
def test_clean_venv_installed_wheel_release_smoke(built_artifacts, tmp_path):
    if os.environ.get("SAGITTARIUS_RUN_RELEASE_ARTIFACT_SMOKE") != "1":
        pytest.skip("Set SAGITTARIUS_RUN_RELEASE_ARTIFACT_SMOKE=1 to run the clean venv release artifact smoke test.")

    wheel, _ = built_artifacts
    venv_dir = tmp_path / "venv"
    work_dir = tmp_path / "outside-repo"
    work_dir.mkdir()

    _run(["uv", "venv", "--seed", str(venv_dir)])
    python = _venv_python(venv_dir)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("SAGITTARIUS_JULIA_BACKEND_PATH", None)
    _run([str(python), "-m", "pip", "install", "--force-reinstall", str(wheel)], cwd=work_dir, env=env)
    _run([str(python), "-m", "juliapkg", "resolve"], cwd=work_dir, env=env)

    script = """
import json
from pathlib import Path

import numpy as np
import sagittarius
from importlib.resources import files

default_juliapkg = json.loads(files("sagittarius").joinpath("juliapkg.json").read_text())
cuda_juliapkg = json.loads(files("sagittarius").joinpath("juliapkg-cuda.json").read_text())
assert "CUDA" not in default_juliapkg["packages"]
assert set(cuda_juliapkg["packages"]) == {"CUDA"}

report = sagittarius.doctor()
assert report["backend_source"] == "package_resource", report["julia_backend"]
assert report["runtime"]["julia"]["source"] == "package_resource"
assert report["runtime"]["julia"]["available"] is True
assert report["runtime"]["julia_version"] is None
assert report["runtime"]["schema_version"] == sagittarius.VERSION_INFO_SCHEMA_VERSION
assert report["runtime"]["julia"]["project_path"].endswith("sagittarius/julia/Sagittarius.jl")

reg = sagittarius.Register([sagittarius.Atom(0.0, 0.0, 0.0)], C6=0.0)
sim = sagittarius.Simulation(
    reg,
    sagittarius.PulseSequence(omega=0.0, delta=0.0),
    sagittarius.SolverConfig(saveat=[0.0, 0.1]),
)
result = sim.run(np.array([1.0, 0.0], dtype=complex), 0.0, 0.1, observables={"pop0": 0})
df = result.to_pandas()
assert "pop0" in df.columns
out = Path("result.json")
result.save(out)
payload = json.loads(out.read_text())
assert payload["schema_version"] == sagittarius.RESULT_ARTIFACT_SCHEMA_VERSION
assert payload["manifest"]["schema_version"] == sagittarius.RUN_MANIFEST_SCHEMA_VERSION
assert payload["manifest"]["versions"]["schema_version"] == sagittarius.VERSION_INFO_SCHEMA_VERSION
assert payload["manifest"]["versions"]["julia"]["source"] == "package_resource"
assert payload["manifest"]["versions"]["julia"]["available"] is True
assert payload["shared_result"]["schema_version"] == sagittarius.SHARED_RESULT_SCHEMA_VERSION
assert "pop0" in payload["shared_result"]["series"]
print(json.dumps({
    "backend_source": report["backend_source"],
    "artifact_schema": payload["schema_version"],
    "manifest_schema": payload["manifest"]["schema_version"],
    "shared_result_schema": payload["shared_result"]["schema_version"],
    "rows": len(df),
}, sort_keys=True))
"""
    completed = _run([str(python), "-c", script], cwd=work_dir, env=env)
    result = json.loads(completed.stdout.strip().splitlines()[-1])

    assert result["backend_source"] == "package_resource"
    assert result["artifact_schema"] == "result-artifact/v1"
    assert result["manifest_schema"] == "run-manifest/v1"
    assert result["shared_result_schema"] == "shared-result/v1"
    assert result["rows"] >= 2
