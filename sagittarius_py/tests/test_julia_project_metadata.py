from pathlib import Path


def test_julia_project_declares_direct_standard_library_dependencies():
    project_path = Path(__file__).resolve().parents[2] / "Sagittarius.jl" / "Project.toml"
    project_text = project_path.read_text(encoding="utf-8")

    assert 'Logging = "56ddb016-857b-54e1-b83d-db4d58db5568"' in project_text
