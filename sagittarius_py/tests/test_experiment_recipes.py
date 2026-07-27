"""Julia-backed acceptance coverage for the Phase 15 executable recipes."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sagittarius import RESULT_ARTIFACT_SCHEMA_VERSION, load_result, validate_run_manifest


ROOT = Path(__file__).resolve().parents[2]
RECIPE_DIR = ROOT / "workspace" / "examples" / "recipes"
if str(RECIPE_DIR) not in sys.path:
    sys.path.insert(0, str(RECIPE_DIR))

import landau_zener  # noqa: E402
import mwis_udg  # noqa: E402
import open_system_decay  # noqa: E402
import rabi  # noqa: E402
import two_atom_blockade  # noqa: E402


pytestmark = pytest.mark.requires_julia_backend


@pytest.mark.parametrize(
    ("name", "runner"),
    [
        ("rabi", rabi.run_recipe),
        ("two_atom_blockade", two_atom_blockade.run_recipe),
        ("landau_zener", landau_zener.run_recipe),
        ("open_system_decay", open_system_decay.run_recipe),
        ("mwis_udg", mwis_udg.run_recipe),
    ],
)
def test_recipe_runs_and_writes_reproducible_artifacts(tmp_path, name, runner):
    run = runner(tmp_path / name)

    assert run.artifact_path.is_file()
    assert run.manifest_path.is_file()
    loaded = load_result(str(run.artifact_path))
    validate_run_manifest(loaded.manifest)
    assert loaded.manifest["schema_version"] == "run-manifest/v1"
    assert loaded.to_envelope()["schema_version"] == RESULT_ARTIFACT_SCHEMA_VERSION
    assert len(loaded.data["t"]) == len(run.result.data["t"])
    if name == "open_system_decay":
        assert loaded.manifest["solver"]["gamma"] == 0.5
        assert loaded.manifest["solver"]["gamma_phi"] == 0.25
