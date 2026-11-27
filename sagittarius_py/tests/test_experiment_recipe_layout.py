"""Backend-free checks for the public Phase 15 recipe surface."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECIPE_DIR = ROOT / "workspace" / "examples" / "recipes"
RECIPE_NAMES = ("rabi", "two_atom_blockade", "landau_zener", "open_system_decay", "mwis_udg")


def test_phase15_recipe_sources_and_documentation_are_present():
    for name in RECIPE_NAMES:
        assert (RECIPE_DIR / f"{name}.py").is_file()

    guide = ROOT / "docs" / "getting-started" / "python" / "experiment-recipes.md"
    guide_text = guide.read_text(encoding="utf-8")
    for name in RECIPE_NAMES:
        assert f"{name}.py" in guide_text
    assert "result-artifact/v1" in guide_text
    assert "run-manifest/v1" in guide_text
