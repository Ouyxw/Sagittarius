from pathlib import Path


def test_julia_project_declares_direct_standard_library_dependencies():
    project_path = Path(__file__).resolve().parents[2] / "Sagittarius.jl" / "Project.toml"
    project_text = project_path.read_text(encoding="utf-8")

    assert 'Logging = "56ddb016-857b-54e1-b83d-db4d58db5568"' in project_text


def test_gpu_solver_uses_latest_world_after_dynamic_cuda_load():
    solver_path = Path(__file__).resolve().parents[2] / "Sagittarius.jl" / "src" / "solver.jl"
    solver_text = solver_path.read_text(encoding="utf-8")

    assert "function _ensure_cuda_loaded!()" in solver_text
    assert "modules = Core.eval(@__MODULE__, quote" in solver_text
    assert "(CUDA, CUDA.CUSPARSE)" in solver_text
    assert "function _solve_schrodinger_gpu_loaded" in solver_text
    assert "cuda, cusparse = _ensure_cuda_loaded!()" in solver_text
    assert "_cached_gpu_sparse!(op, cusparse)" in solver_text
    assert "Base.invokelatest(" in solver_text


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
