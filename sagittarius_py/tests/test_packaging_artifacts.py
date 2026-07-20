import email
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


def _json_from_output(output: str):
    decoder = json.JSONDecoder()
    for index, char in enumerate(output):
        if char != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(output[index:])
        except json.JSONDecodeError:
            continue
        return payload
    raise AssertionError(f"No JSON object found in command output: {output}")


def _venv_python(venv_dir: Path) -> Path:
    return _venv_executable(venv_dir, "python")


def _venv_executable(venv_dir: Path, name: str) -> Path:
    suffix = ".exe" if sys.platform == "win32" else ""
    scripts = "Scripts" if sys.platform == "win32" else "bin"
    return venv_dir / scripts / f"{name}{suffix}"


def _clean_wheel_cpu_probe_script(output_name: str = "result.json") -> str:
    return f"""
import json
import os
from pathlib import Path

import numpy as np
import sagittarius
from importlib.resources import files

source_root = Path(os.environ["SAGITTARIUS_SOURCE_ROOT_FOR_TEST"]).resolve()
package_file = Path(sagittarius.__file__).resolve()
assert not package_file.is_relative_to(source_root), package_file

default_juliapkg = json.loads(files("sagittarius").joinpath("juliapkg.json").read_text())
cuda_juliapkg = json.loads(files("sagittarius").joinpath("juliapkg-cuda.json").read_text())
assert "CUDA" not in default_juliapkg["packages"]
assert set(cuda_juliapkg["packages"]) == {{"CUDA"}}

report = sagittarius.doctor()
assert report["backend_source"] == "package_resource", report["julia_backend"]
assert report["runtime"]["julia"]["source"] == "package_resource"
assert report["runtime"]["julia"]["available"] is True
assert report["runtime"]["julia_version"] is None
assert report["runtime"]["schema_version"] == sagittarius.VERSION_INFO_SCHEMA_VERSION
assert Path(report["runtime"]["julia"]["project_path"]).as_posix().endswith("sagittarius/julia/Sagittarius.jl")

reg = sagittarius.Register([sagittarius.Atom(0.0, 0.0, 0.0)], C6=0.0)
sim = sagittarius.Simulation(
    reg,
    sagittarius.PulseSequence(omega=0.0, delta=0.0),
    sagittarius.SolverConfig(saveat=[0.0, 0.1]),
)
result = sim.run(np.array([1.0, 0.0], dtype=complex), 0.0, 0.1, observables={{"pop0": 0}})
df = result.to_pandas()
assert "pop0" in df.columns
out = Path({output_name!r})
result.save(out)
payload = json.loads(out.read_text())
assert payload["schema_version"] == sagittarius.RESULT_ARTIFACT_SCHEMA_VERSION
assert payload["manifest"]["schema_version"] == sagittarius.RUN_MANIFEST_SCHEMA_VERSION
assert payload["manifest"]["versions"]["schema_version"] == sagittarius.VERSION_INFO_SCHEMA_VERSION
assert payload["manifest"]["versions"]["julia"]["source"] == "package_resource"
assert payload["manifest"]["versions"]["julia"]["available"] is True
assert payload["shared_result"]["schema_version"] == sagittarius.SHARED_RESULT_SCHEMA_VERSION
assert "pop0" in payload["shared_result"]["series"]
print(json.dumps({{
    "backend_source": report["backend_source"],
    "artifact_schema": payload["schema_version"],
    "manifest_schema": payload["manifest"]["schema_version"],
    "shared_result_schema": payload["shared_result"]["schema_version"],
    "rows": len(df),
}}, sort_keys=True))
"""


@pytest.fixture(scope="session")
def built_artifacts(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("sagittarius-artifacts")
    _run(["uv", "build", "--wheel", "--sdist", "--out-dir", str(out_dir)])
    wheel = next(out_dir.glob("*.whl"))
    sdist = next(out_dir.glob("*.tar.gz"))
    return wheel, sdist


def test_packaging_readme_and_license_match_repository_root():
    assert (PY_PACKAGE_ROOT / "README.md").read_bytes() == (REPO_ROOT / "README.md").read_bytes()
    assert (PY_PACKAGE_ROOT / "LICENSE").read_bytes() == (REPO_ROOT / "LICENSE").read_bytes()


def test_python_package_metadata_is_release_ready():
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
        import tomli as tomllib

    pyproject = tomllib.loads((PY_PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert project["readme"] == "README.md"
    assert project["license"] == "MIT"
    assert project["license-files"] == ["LICENSE"]
    assert project["authors"] == [{"name": "Sagittarius contributors"}]
    assert "neutral atoms" in project["keywords"]
    assert "Programming Language :: Python :: 3.10" in project["classifiers"]
    assert "Programming Language :: Python :: 3.11" in project["classifiers"]
    assert "Programming Language :: Python :: 3.12" in project["classifiers"]
    assert "Programming Language :: Julia" not in project["classifiers"]
    assert {"Homepage", "Documentation", "Source", "Issues"} <= project["urls"].keys()


def test_wheel_metadata_contains_release_fields(built_artifacts):
    wheel, _ = built_artifacts

    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        metadata = email.message_from_bytes(archive.read(metadata_name))
        names = set(archive.namelist())

    assert metadata["Name"] == "sagittarius-py"
    assert metadata["Summary"] == "A neutral-atom quantum emulator with Julia and Python SDKs"
    assert metadata["License-Expression"] == "MIT" or metadata["License"] == "MIT"
    classifiers = metadata.get_all("Classifier")
    assert "Programming Language :: Python :: 3.10" in classifiers
    assert "Programming Language :: Python :: 3.11" in classifiers
    assert "Programming Language :: Python :: 3.12" in classifiers
    assert "Programming Language :: Julia" not in classifiers
    assert metadata["Project-URL"] is not None
    assert any(name.endswith(".dist-info/licenses/LICENSE") for name in names)
    assert "Sagittarius is a research SDK" in metadata.get_payload()


def test_sdist_contains_readme_license_and_pyproject_metadata(built_artifacts):
    _, sdist = built_artifacts

    with tarfile.open(sdist) as archive:
        names = {name.partition("/")[2] for name in archive.getnames() if "/" in name}

    assert "README.md" in names
    assert "LICENSE" in names
    assert "pyproject.toml" in names


def test_built_artifacts_pass_twine_check(built_artifacts):
    wheel, sdist = built_artifacts

    _run([sys.executable, "-m", "twine", "check", str(wheel), str(sdist)])


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
    env["PYTHONNOUSERSITE"] = "1"
    env["SAGITTARIUS_SOURCE_ROOT_FOR_TEST"] = str(REPO_ROOT)
    _run([str(python), "-m", "pip", "install", "--force-reinstall", str(wheel)], cwd=work_dir, env=env)
    sagittarius_cli = _venv_executable(venv_dir, "sagittarius")
    _run([str(sagittarius_cli), "backend", "resolve"], cwd=work_dir, env=env)

    completed = _run([str(python), "-c", _clean_wheel_cpu_probe_script()], cwd=work_dir, env=env)
    result = json.loads(completed.stdout.strip().splitlines()[-1])

    assert result["backend_source"] == "package_resource"
    assert result["artifact_schema"] == "result-artifact/v1"
    assert result["manifest_schema"] == "run-manifest/v1"
    assert result["shared_result_schema"] == "shared-result/v1"
    assert result["rows"] >= 2


@pytest.mark.requires_julia_backend
def test_clean_venv_installed_wheel_uninstall_reinstall_smoke(built_artifacts, tmp_path):
    if os.environ.get("SAGITTARIUS_RUN_RELEASE_ARTIFACT_SMOKE") != "1":
        pytest.skip("Set SAGITTARIUS_RUN_RELEASE_ARTIFACT_SMOKE=1 to run the uninstall/reinstall smoke test.")

    wheel, _ = built_artifacts
    venv_dir = tmp_path / "reinstall-venv"
    work_dir = tmp_path / "outside-repo-reinstall"
    work_dir.mkdir()

    _run(["uv", "venv", "--seed", str(venv_dir)])
    python = _venv_python(venv_dir)
    sagittarius_cli = _venv_executable(venv_dir, "sagittarius")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("SAGITTARIUS_JULIA_BACKEND_PATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["SAGITTARIUS_SOURCE_ROOT_FOR_TEST"] = str(REPO_ROOT)

    _run([str(python), "-m", "pip", "install", "--force-reinstall", str(wheel)], cwd=work_dir, env=env)
    _run([str(sagittarius_cli), "backend", "resolve"], cwd=work_dir, env=env)
    first = json.loads(
        _run([str(python), "-c", _clean_wheel_cpu_probe_script("first-result.json")], cwd=work_dir, env=env)
        .stdout.strip()
        .splitlines()[-1]
    )
    assert first["backend_source"] == "package_resource"

    _run([str(python), "-m", "pip", "uninstall", "-y", "sagittarius-py"], cwd=work_dir, env=env)
    _run(
        [
            str(python),
            "-c",
            "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('sagittarius') is None else 1)",
        ],
        cwd=work_dir,
        env=env,
    )

    _run([str(python), "-m", "pip", "install", str(wheel)], cwd=work_dir, env=env)
    _run([str(sagittarius_cli), "backend", "resolve"], cwd=work_dir, env=env)
    second = json.loads(
        _run([str(python), "-c", _clean_wheel_cpu_probe_script("second-result.json")], cwd=work_dir, env=env)
        .stdout.strip()
        .splitlines()[-1]
    )

    assert second["backend_source"] == "package_resource"
    assert second["artifact_schema"] == "result-artifact/v1"
    assert second["manifest_schema"] == "run-manifest/v1"
    assert second["rows"] >= 2


def test_clean_venv_installed_wheel_cuda_smoke_and_parity(built_artifacts, tmp_path):
    if os.environ.get("SAGITTARIUS_RUN_CUDA_WHEEL_SMOKE") != "1":
        pytest.skip("Set SAGITTARIUS_RUN_CUDA_WHEEL_SMOKE=1 to run the clean wheel CUDA smoke test.")
    if os.environ.get("SAGITTARIUS_ENABLE_GPU_TESTS") != "1":
        pytest.skip("Set SAGITTARIUS_ENABLE_GPU_TESTS=1 to confirm CUDA hardware-backed tests are allowed.")

    wheel, _ = built_artifacts
    venv_dir = tmp_path / "cuda-venv"
    work_dir = tmp_path / "outside-repo-cuda"
    work_dir.mkdir()

    _run(["uv", "venv", "--seed", str(venv_dir)])
    python = _venv_python(venv_dir)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("SAGITTARIUS_JULIA_BACKEND_PATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["SAGITTARIUS_SOURCE_ROOT_FOR_TEST"] = str(REPO_ROOT)
    _run([str(python), "-m", "pip", "install", "--force-reinstall", str(wheel)], cwd=work_dir, env=env)
    sagittarius_cli = _venv_executable(venv_dir, "sagittarius")

    install_report = _json_from_output(
        _run([str(sagittarius_cli), "backend", "install", "cuda"], cwd=work_dir, env=env).stdout
    )
    assert install_report["schema_version"] == "backend-setup/v1"
    assert install_report["backend"] == "CUDA"
    assert install_report["profile"]["schema_version"] == "backend-profile/v1"
    assert install_report["profile"]["packages"]["CUDA"]["version"] == "6.2.0"
    assert install_report["resolved_default_profile"] is True

    doctor_report = _json_from_output(
        _run([str(sagittarius_cli), "doctor", "--backend", "CUDA", "--initialize-backend"], cwd=work_dir, env=env).stdout
    )
    assert doctor_report["available"] is True
    assert doctor_report["backend_source"] == "package_resource"
    probe = doctor_report["backend_probe"]
    assert probe["backend"] == "CUDA"
    assert probe["available"] is True
    assert probe["versions"]["CUDA.jl"]
    assert probe["runtime"]["cuda_functional"] is True
    assert probe["runtime"]["driver_version"]
    assert probe["runtime"]["runtime_version"]
    assert probe["devices"]

    script = """
import json
import os
from pathlib import Path

import numpy as np
import sagittarius

source_root = Path(os.environ["SAGITTARIUS_SOURCE_ROOT_FOR_TEST"]).resolve()
package_file = Path(sagittarius.__file__).resolve()
assert not package_file.is_relative_to(source_root), package_file

doctor_report = sagittarius.doctor(backend="CUDA", initialize_backend=True)
assert doctor_report["available"] is True
assert doctor_report["backend_source"] == "package_resource"
assert doctor_report["backend_probe"]["versions"].get("CUDA.jl")
assert doctor_report["backend_probe"].get("devices")

register = sagittarius.Register.chain(3, spacing=5.0, C6=25.0)
sequence = sagittarius.PulseSequence(omega=2 * np.pi * 0.35, delta=2 * np.pi * 0.05)
psi0 = np.zeros(2 ** len(register.atoms), dtype=complex)
psi0[0] = 1.0
observables = {"left": 0, "right": len(register.atoms) - 1}
saveat = np.linspace(0.0, 0.2, 5)

cpu_config = sagittarius.SolverConfig(saveat=saveat, reltol=1e-7, abstol=1e-7, use_gpu=False)
gpu_config = sagittarius.SolverConfig(saveat=saveat, reltol=1e-7, abstol=1e-7, use_gpu=True, gpu_backend="CUDA")

cpu_result = sagittarius.Simulation(register, sequence, cpu_config).run(psi0, 0.0, 0.2, observables=observables)
gpu_result = sagittarius.Simulation(register, sequence, gpu_config).run(psi0, 0.0, 0.2, observables=observables)

max_abs_error = 0.0
for name in observables:
    cpu_values = np.asarray(cpu_result.data[name], dtype=float)
    gpu_values = np.asarray(gpu_result.data[name], dtype=float)
    max_abs_error = max(max_abs_error, float(np.max(np.abs(cpu_values - gpu_values))))
    assert np.allclose(cpu_values, gpu_values, rtol=5e-4, atol=5e-5), name

out = Path("cuda-result.json")
gpu_result.save(out)
payload = json.loads(out.read_text())
assert payload["schema_version"] == sagittarius.RESULT_ARTIFACT_SCHEMA_VERSION
assert payload["manifest"]["schema_version"] == sagittarius.RUN_MANIFEST_SCHEMA_VERSION
assert payload["manifest"]["versions"]["julia"]["source"] == "package_resource"
assert payload["diagnostics"]["requested_backend"] == "CUDA"
assert payload["diagnostics"]["simulation"]["use_gpu"] is True
assert payload["shared_result"]["schema_version"] == sagittarius.SHARED_RESULT_SCHEMA_VERSION

print(json.dumps({
    "backend_source": doctor_report["backend_source"],
    "cuda_jl": doctor_report["backend_probe"]["versions"]["CUDA.jl"],
    "device_count": len(doctor_report["backend_probe"].get("devices", [])),
    "driver_version": doctor_report["backend_probe"]["runtime"]["driver_version"],
    "runtime_version": doctor_report["backend_probe"]["runtime"]["runtime_version"],
    "max_abs_error": max_abs_error,
    "artifact_schema": payload["schema_version"],
    "manifest_schema": payload["manifest"]["schema_version"],
}, sort_keys=True))
"""
    completed = _run([str(python), "-c", script], cwd=work_dir, env=env)
    result = json.loads(completed.stdout.strip().splitlines()[-1])

    assert result["backend_source"] == "package_resource"
    assert result["cuda_jl"]
    assert result["device_count"] >= 1
    assert result["driver_version"]
    assert result["runtime_version"]
    assert result["max_abs_error"] <= 1e-4
    assert result["artifact_schema"] == "result-artifact/v1"
    assert result["manifest_schema"] == "run-manifest/v1"
