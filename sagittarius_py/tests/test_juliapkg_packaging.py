import json
from importlib.resources import files
from pathlib import Path

from juliapkg.deps import deps_files


REQUIRED_JULIA_PACKAGES = {
    "DiffEqCallbacks",
    "OrdinaryDiffEq",
    "SciMLBase",
    "StaticArrays",
}


def test_juliapkg_config_is_packaged_and_discoverable():
    config = files("sagittarius").joinpath("juliapkg.json")

    assert config.is_file()
    assert Path(config).resolve() in {Path(path).resolve() for path in deps_files()}

    payload = json.loads(config.read_text())
    assert REQUIRED_JULIA_PACKAGES <= payload["packages"].keys()
