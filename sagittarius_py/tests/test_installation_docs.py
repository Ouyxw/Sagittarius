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


def test_phase13_cross_platform_matrix_is_documented():
    docs = "\n\n".join(
        [
            _read("docs/getting-started/python/package-installation.md"),
            _read("docs/getting-started/python/compatibility-matrix.md"),
            _read("REQUIREMENTS.md"),
            _read(".github/workflows/phase13-cross-platform.yml"),
        ]
    )

    assert "Python compatibility matrix" in docs or "Python Compatibility Matrix" in docs
    assert "Linux x86_64" in docs
    assert "macOS" in docs
    assert "Windows" in docs
    assert "Python 3.10" in docs or "3.10" in docs
    assert "Python 3.12" in docs or "3.12" in docs
    assert "Julia 1.10.3" in docs or "1.10.3" in docs
    assert "phase13-cross-platform.yml" in docs
    assert "Cross-Platform Installation Matrix** | High | Mixed" in docs
    assert "phase13-cross-platform-evidence" in docs
    assert "actions/upload-artifact" in docs
    assert "Run URL" in docs
    assert "Commit" in docs


def test_phase13_uninstall_reinstall_smoke_is_documented():
    docs = "\n\n".join(
        [
            _read("docs/getting-started/python/package-installation.md"),
            _read("REQUIREMENTS.md"),
            _read(".github/workflows/phase13-clean-artifact.yml"),
        ]
    )

    assert "test_clean_venv_installed_wheel_uninstall_reinstall_smoke" in docs
    assert "Uninstall/Reinstall Smoke Coverage** | Medium | Done" in docs
    assert "package_resource" in docs
    assert "no longer importable" in docs


def test_phase13_ci_workflow_policy_is_documented():
    ci_docs = _read("docs/reference/ci-workflows.md")
    package_docs = _read("docs/getting-started/python/package-installation.md")
    status_docs = _read("docs/status.md")
    roadmap = _read("REQUIREMENTS.md")

    assert "reference/ci-workflows.md" in package_docs
    assert "reference/ci-workflows.md" in status_docs
    assert "Phase 13 CI and Release Automation" in roadmap
    pr_fast_ci = _read(".github/workflows/pr-fast-ci.yml")
    assert ".github/workflows/pr-fast-ci.yml" in ci_docs
    assert "Automatic on pull requests" in ci_docs
    assert "direct pushes to `develop/**`" in ci_docs
    assert "push:" in pr_fast_ci
    assert "develop/**" in pr_fast_ci
    assert "workflow_dispatch" in _read(".github/workflows/phase13-cross-platform.yml")
    assert "pull_request" not in _read(".github/workflows/phase13-cross-platform.yml")
    assert "pull_request" not in _read(".github/workflows/phase13-testpypi.yml")
    assert "pull_request" not in _read(".github/workflows/phase13-cuda-wheel.yml")
    assert "pull_request" not in _read(".github/workflows/phase13-clean-artifact.yml")
    assert "Automatic on relevant pushes to `main`" in ci_docs
    assert "Manual only" in ci_docs
    assert "Evidence Retention" in ci_docs


def test_phase13_release_evidence_workflows_are_hardened():
    testpypi = _read(".github/workflows/phase13-testpypi.yml")
    cuda = _read(".github/workflows/phase13-cuda-wheel.yml")

    assert "environment: testpypi" in testpypi
    assert "id-token: write" in testpypi
    assert "skip-existing:" not in testpypi
    assert "Verify built package version and record distribution digests" in testpypi
    assert "phase13-testpypi-evidence/v1" in testpypi
    assert "clean-install-diagnostic.json" in testpypi
    assert "testpypi-project.json" in testpypi
    assert "phase13-testpypi-${{ inputs.expected-version }}" in testpypi

    assert "name,driver_version,memory.total" in cuda
    assert "cuda-wheel-smoke.log" in cuda
    assert "phase13-cuda-wheel-evidence/v1" in cuda
    assert "SAGITTARIUS_RUN_CUDA_WHEEL_SMOKE" in cuda
    assert "SAGITTARIUS_ENABLE_GPU_TESTS" in cuda
    assert "phase13-cuda-wheel-${{ github.run_id }}" in cuda
