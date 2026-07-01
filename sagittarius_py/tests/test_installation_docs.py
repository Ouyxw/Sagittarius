from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_phase13_source_install_baseline_is_documented():
    docs = "\n\n".join(
        [
            _read("README.md"),
            _read("docs/getting-started/installation.md"),
            _read("docs/getting-started/python/source-installation.md"),
            _read("docs/getting-started/python/package-installation.md"),
        ]
    )

    assert "complete source checkout" in docs or "complete repository checkout" in docs
    assert "uv sync" in docs
    assert "python -m juliapkg resolve" in docs
    assert "pip install -e ." in docs
    assert "development-only" in docs
    assert "source checkout" in docs
    assert "embedded Julia backend" in docs
    assert "not supported yet" in docs
    assert "pip install sagittarius-py" in docs


def test_source_install_docs_do_not_contain_control_characters():
    guide = _read("docs/getting-started/python/source-installation.md")

    assert all(ord(character) >= 32 or character in "\n\r" for character in guide)
    assert r"C:\absolute\path\to\julia.exe" in guide


def test_phase13_source_install_baseline_roadmap_status_is_done():
    roadmap = _read("REQUIREMENTS.md")

    assert "| **Source Installation Baseline** | High | Done |" in roadmap
