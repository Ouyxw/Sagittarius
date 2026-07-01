from pathlib import Path


def test_julia_project_declares_direct_standard_library_dependencies():
    project_path = Path(__file__).resolve().parents[2] / "Sagittarius.jl" / "Project.toml"
    project_text = project_path.read_text(encoding="utf-8")

    assert 'Logging = "56ddb016-857b-54e1-b83d-db4d58db5568"' in project_text


def test_julia_project_does_not_make_cuda_a_default_dependency():
    project_path = Path(__file__).resolve().parents[2] / "Sagittarius.jl" / "Project.toml"
    project_text = project_path.read_text(encoding="utf-8")

    assert 'CUDA = "052768ef-5323-5732-b1bb-66c8b64840ba"' not in project_text


def test_julia_manifest_does_not_resolve_cuda_package_by_default():
    manifest_path = Path(__file__).resolve().parents[2] / "Sagittarius.jl" / "Manifest.toml"
    manifest_text = manifest_path.read_text(encoding="utf-8")

    assert "[[deps.CUDA]]" not in manifest_text
    assert "[[deps.CUDA_Runtime_jll]]" not in manifest_text
    assert "[[deps.cuSPARSE]]" not in manifest_text
