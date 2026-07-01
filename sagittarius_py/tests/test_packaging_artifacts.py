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
def test_installed_wheel_uses_embedded_backend_outside_repo(built_artifacts, tmp_path):
    wheel, _ = built_artifacts
    install_dir = tmp_path / "installed"
    work_dir = tmp_path / "outside-repo"
    install_dir.mkdir()
    work_dir.mkdir()

    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(install_dir)

    script = """
import json
import numpy as np
import sagittarius

info = sagittarius.version_info()
assert info["julia"]["source"] == "package_resource", info["julia"]
assert "outside-repo" not in info["julia"]["project_path"]

reg = sagittarius.Register([sagittarius.Atom(0.0, 0.0, 0.0)], C6=0.0)
sim = sagittarius.Simulation(
    reg,
    sagittarius.PulseSequence(omega=0.0, delta=0.0),
    sagittarius.SolverConfig(saveat=[0.0, 0.1]),
)
result = sim.run(np.array([1.0, 0.0], dtype=complex), 0.0, 0.1, observables={"pop0": 0})
df = result.to_pandas()
assert "pop0" in df.columns
print(json.dumps({"backend_source": info["julia"]["source"], "points": len(df)}))
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(install_dir) + os.pathsep + env.get("PYTHONPATH", "")
    env.pop("SAGITTARIUS_JULIA_BACKEND_PATH", None)

    completed = _run([sys.executable, "-c", script], cwd=work_dir, env=env)

    assert "package_resource" in completed.stdout
