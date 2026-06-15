import importlib.util
import json
from pathlib import Path

from sagittarius import BENCHMARK_ARTIFACT_SCHEMA_VERSION, PulseSequence, Register
from sagittarius.ablation import ABLATION_BENCHMARK_MODES, benchmark_ablation_modes


def _load_benchmark_script():
    script_path = Path(__file__).parent / "test_performance" / "benchmark_ablation.py"
    spec = importlib.util.spec_from_file_location("benchmark_ablation_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_ablation_mode_contract_lists_required_execution_paths():
    modes = [item["mode"] for item in ABLATION_BENCHMARK_MODES]

    assert modes == [
        "full_dense",
        "full_sparse",
        "reduced_matrix_free",
        "reduced_sparse",
        "reduced_sparse_gpu_cached",
    ]


def test_benchmark_ablation_modes_records_cpu_paths_and_gpu_skip():
    register = Register.chain(4, spacing=0.6, C6=10.0)
    sequence = PulseSequence(omega=0.5, delta=[0.0, 0.1, -0.1, 0.2])

    rows, run_manifests = benchmark_ablation_modes(
        register,
        sequence,
        blockade_radius=0.8,
        repeats=3,
        warmups=1,
        include_gpu=False,
    )

    by_mode = {row["mode"]: row for row in rows}
    assert set(by_mode) == {item["mode"] for item in ABLATION_BENCHMARK_MODES}
    assert by_mode["full_dense"]["status"] == "ok"
    assert by_mode["full_sparse"]["status"] == "ok"
    assert by_mode["reduced_matrix_free"]["status"] == "ok"
    assert by_mode["reduced_sparse"]["status"] == "ok"
    assert by_mode["reduced_sparse_gpu_cached"]["status"] == "skipped"
    assert by_mode["reduced_matrix_free"]["reference_error"] < 1e-10
    assert by_mode["reduced_sparse"]["reference_error"] < 1e-10
    assert run_manifests == []


def test_ablation_benchmark_script_writes_artifact(tmp_path):
    paths = _load_benchmark_script().benchmark_ablation(
        atom_count=4,
        spacing=0.6,
        blockade_radius=0.8,
        repeats=2,
        include_gpu=False,
        output_dir=tmp_path,
    )

    with open(paths["json"], encoding="utf-8") as fh:
        payload = json.load(fh)

    assert payload["schema_version"] == BENCHMARK_ARTIFACT_SCHEMA_VERSION
    assert payload["parameters"]["include_gpu"] is False
    assert {row["mode"] for row in payload["timings"]} == {item["mode"] for item in ABLATION_BENCHMARK_MODES}
    assert "reduced_sparse_gpu_cached" in payload["markdown_table"]
