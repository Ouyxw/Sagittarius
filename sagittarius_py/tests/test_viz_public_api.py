"""Public visualization API contract tests."""

from pathlib import Path

import sagittarius.viz as viz


def test_public_visualization_exports_are_documented_and_resolvable():
    """Keep the root export contract synchronized with its canonical API catalog."""
    docs = (Path(__file__).resolve().parents[2] / "docs/api/SPEC-API-006-visualization.md").read_text()

    assert len(viz.__all__) == 63
    assert len(viz.__all__) == len(set(viz.__all__))
    for name in viz.__all__:
        assert hasattr(viz, name), f"Missing sagittarius.viz export: {name}"
        assert f"`{name}`" in docs, f"Missing API catalog entry: {name}"
