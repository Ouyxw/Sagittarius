"""Tests for the repository-local documentation governance validator."""
from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "validate_documentation.py"
SPEC = importlib.util.spec_from_file_location("validate_documentation", SCRIPT_PATH)
assert SPEC and SPEC.loader
documentation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(documentation)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _docs_tree(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    tick = chr(96)
    _write(
        docs / "api" / "SPEC-API-999-example.md",
        "\n".join((
            "# Example",
            "",
            f"Spec ID: {tick}SPEC-API-999{tick}",
            "Status: Current",
            "Roadmap: Phase 15",
            f"Version: {tick}example/v1{tick}",
            "Last reviewed: 2026-07-29",
            "",
            "[Local readme](README.md)",
            "",
        )),
    )
    _write(docs / "api" / "README.md", "# API\n")
    _write(
        docs / "development" / "status.md",
        "\n".join((
            "# Status",
            "",
            f"| {tick}SPEC-API-999{tick} | [Example](../api/SPEC-API-999-example.md) | test |",
            "",
        )),
    )
    return docs


def test_valid_documentation_tree_passes(tmp_path):
    assert documentation.validate_docs(_docs_tree(tmp_path)) == []


def test_validator_reports_missing_metadata_and_local_links(tmp_path):
    docs = _docs_tree(tmp_path)
    spec = docs / "api" / "SPEC-API-999-example.md"
    spec.write_text(spec.read_text(encoding="utf-8").replace("Last reviewed: 2026-07-29\n", ""), encoding="utf-8")
    _write(docs / "api" / "broken.md", "[missing](does-not-exist.md)\n")

    errors = documentation.validate_docs(docs)

    assert any("missing Last reviewed" in error for error in errors)
    assert any("does-not-exist.md" in error for error in errors)


def test_validator_requires_status_entry_to_link_to_specification(tmp_path):
    docs = _docs_tree(tmp_path)
    status = docs / "development" / "status.md"
    status.write_text(status.read_text(encoding="utf-8").replace("SPEC-API-999-example.md", "README.md"), encoding="utf-8")
    errors = documentation.validate_docs(docs)

    assert any("does not link" in error for error in errors)

