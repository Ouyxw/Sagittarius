import json
from importlib.resources import files
from pathlib import Path

from juliapkg.deps import deps_files


REQUIRED_JULIA_PACKAGES = {
    "DiffEqCallbacks",
    "OrdinaryDiffEq",
    "OrdinaryDiffEqLowOrderRK",
    "SciMLBase",
    "StaticArrays",
}


def test_juliapkg_config_is_packaged_and_discoverable():
    config = files("sagittarius").joinpath("juliapkg.json")

    assert config.is_file()
    assert Path(config).resolve() in {Path(path).resolve() for path in deps_files()}

    payload = json.loads(config.read_text())
    assert REQUIRED_JULIA_PACKAGES <= payload["packages"].keys()
    assert "CUDA" not in payload["packages"]


def test_cuda_juliapkg_profile_is_packaged_but_not_default_discoverable():
    config = files("sagittarius").joinpath("juliapkg-cuda.json")

    assert config.is_file()
    assert Path(config).resolve() not in {Path(path).resolve() for path in deps_files()}

    payload = json.loads(config.read_text())
    assert payload["schema_version"] == "backend-profile/v1"
    assert payload["backend"] == "CUDA"
    assert payload["maturity"] == "experimental"
    assert payload["default"] is False
    assert set(payload["packages"]) == {"CUDA"}
    assert payload["packages"]["CUDA"]["version"] == "6.2.0"
