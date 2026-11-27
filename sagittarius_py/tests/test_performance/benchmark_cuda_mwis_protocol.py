"""Opt-in Phase 16 CUDA parity and weighted-MWIS GPU protocol.

This runner is deliberately local-only evidence.  It never initializes or
uses CUDA unless ``SAGITTARIUS_ENABLE_GPU_TESTS=1`` and a fully initialized
``doctor(backend="CUDA", initialize_backend=True)`` report is available.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping


from sagittarius import (
    doctor,
    make_benchmark_failure_row,
    make_benchmark_row,
    write_benchmark_artifacts,
    write_benchmark_suite_artifact,
)

DISCLOSURE_STATUS = "local_only"
PARITY_FAMILY = "backend_performance"
MWIS_FAMILY = "optimization_aqc"
TIER = "parity"
OBSERVABLES = {"names": ["pop0"], "count": 1, "output_sample_count": None}


def _json_native(value: Any) -> Any:
    """Normalize Julia bridge mappings before writing benchmark artifacts.

    ``juliacall.DictValue`` exposes ``items()`` but is not a Python
    ``Mapping``. Artifact writers require JSON-native values, so retain its
    structured device fields instead of leaking a bridge object into a row.
    """
    if isinstance(value, Mapping):
        return {str(key): _json_native(item) for key, item in value.items()}
    if hasattr(value, "items"):
        return {str(key): _json_native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_native(item) for item in value]
    return value


def _enabled() -> bool:
    return os.environ.get("SAGITTARIUS_ENABLE_GPU_TESTS") == "1"


def _cuda_metadata(report: Mapping[str, Any]) -> dict[str, Any]:
    probe = dict(report.get("backend_probe") or {})
    runtime = dict(probe.get("runtime") or {})
    versions = dict(probe.get("versions") or {})
    return {
        "requested_backend": "CUDA",
        "path": "cpu_cuda_parity",
        "devices": list(probe.get("devices") or report.get("gpu", {}).get("devices") or []),
        "driver_version": runtime.get("driver_version") or report.get("gpu", {}).get("driver", {}).get("version"),
        "cuda_runtime_version": runtime.get("runtime_version"),
        "cuda_jl_version": versions.get("CUDA.jl"),
        "julia_version": report.get("runtime", {}).get("julia", {}).get("version"),
    }


def _skip_row(*, family: str, scenario_id: str, problem: Mapping[str, Any], solver: Mapping[str, Any]) -> dict[str, Any]:
    return make_benchmark_row(
        row_id=f"{family}-{TIER}-{scenario_id}", scenario_id=scenario_id,
        family=family, tier=TIER, status="skipped", stage="setup",
        problem=problem, solver=solver, backend={"requested_backend": "CUDA", "path": "not_started"},
        observables=OBSERVABLES, metrics={},
        failure={
            "stage": "setup", "code": "BENCHMARK_GPU_OPT_IN_DISABLED",
            "message": "CUDA protocol requires SAGITTARIUS_ENABLE_GPU_TESTS=1.",
            "remediation": "Set SAGITTARIUS_ENABLE_GPU_TESTS=1 on a CUDA-capable host, then rerun the documented command.",
        },
        disclosure_status=DISCLOSURE_STATUS,
    )


def _doctor_failure_row(
    *, family: str, scenario_id: str, problem: Mapping[str, Any], solver: Mapping[str, Any], report: Mapping[str, Any]
) -> dict[str, Any]:
    error = RuntimeError("CUDA initialization failed: " + "; ".join(str(item) for item in report.get("issues", [])))
    return make_benchmark_failure_row(
        row_id=f"{family}-{TIER}-{scenario_id}", scenario_id=scenario_id,
        family=family, tier=TIER, stage="setup", exc=error, problem=problem,
        solver=solver, backend=_cuda_metadata(report), observables=OBSERVABLES,
        backend_probe=report, disclosure_status=DISCLOSURE_STATUS,
    )


def _shared_row(output_dir: Path, scenario: dict, family: str, report: Mapping[str, Any]) -> dict:
    # The protocol keeps its original small fixtures and stems, while using the
    # scan's reset, synchronized timing, symmetric warmup and saved-grid gates.
    from sagittarius.gpu_benchmark import benchmark_gpu
    paths = benchmark_gpu(output_dir=output_dir / scenario["scenario_id"], scenario_list=[scenario])
    row = json.loads(Path(paths["json"]).read_text())["timings"][0]
    row.update(family=family, tier=TIER)
    row["backend"].update(_cuda_metadata(report))
    pairs = row["metrics"]["pairs"]
    first = next((p for p in pairs if p["phase"] == "first"), None)
    warm = next((p for p in pairs if p["phase"] == "warmup"), None)
    measured = next((p for p in pairs if p["phase"] == "measured"), None)
    def seconds(pair, backend):
        return pair["paths"].get(backend, {}).get("runtime_seconds") if pair else None
    row["metrics"].update(
        cpu_seconds=seconds(measured, "CPU"),
        cuda_cold_start_seconds=seconds(first, "CUDA"),
        cuda_warmup_seconds=seconds(warm, "CUDA"),
        cuda_warm_seconds=seconds(measured, "CUDA"),
        parity_passed=row["status"] == "passed",
        cpu_cuda_max_abs_error=row["max_trajectory_error"],
        gpu_memory_before=row["metrics"]["paths"].get("CUDA", {}).get("gpu_memory", {}).get("before"),
        gpu_memory_after_cold=(first or {}).get("paths", {}).get("CUDA", {}).get("gpu_memory_snapshot"),
        gpu_memory_after_warm=(measured or {}).get("paths", {}).get("CUDA", {}).get("gpu_memory_snapshot"),
    )
    if measured and "gate" in measured:
        row["metrics"].update(measured["gate"])
    row["artifacts"]["reference_report"] = row["artifacts"]["paired_records"]
    return row


def _parity_row(output_dir: Path, report: Mapping[str, Any]) -> dict[str, Any]:
    from sagittarius.gpu_benchmark import chain_scenario
    return _shared_row(output_dir, chain_scenario(3, legacy=True), PARITY_FAMILY, report)


def _mwis_gpu_row(output_dir: Path, report: Mapping[str, Any]) -> dict[str, Any]:
    from sagittarius.gpu_benchmark import mwis_scenario
    scenario = mwis_scenario()
    row = _shared_row(output_dir, scenario, MWIS_FAMILY, report)
    if row["status"] == "passed":
        # Preserve the original ILP reference alongside the shared exhaustive
        # two-node probability/basis check, outside every SDK timer.
        import sys
        project = Path(__file__).resolve().parents[2] / "projects/mwis_udg"
        sys.path.insert(0, str(project))
        try:
            import networkx as nx
            from batch_verify import solve_mwis_ilp
            graph = nx.Graph()
            for i, (xyz, weight) in enumerate(zip(scenario["coordinates"], scenario["weights"])):
                graph.add_node(i, pos=tuple(xyz[:2]), weight=weight)
            graph.add_edges_from(scenario["edges"])
            bits, weight, ilp_status = solve_mwis_ilp(graph)
            if ilp_status != "Optimal" or abs(weight - row["metrics"]["exact_objective"]) > 1e-12:
                raise AssertionError("MWIS ILP/exhaustive reference mismatch")
            row["metrics"].update(ilp_status=ilp_status, exact_objective=weight,
                cuda_objective_gap=max(0., weight - row["metrics"]["cuda_objective"]))
            reference = output_dir / "weighted_udg_n2_seed3_cpu_cuda.ilp-reference.json"
            reference.write_text(json.dumps({"bitstring": bits, "weight": weight, "ilp_status": ilp_status}) + "\n")
            row["artifacts"]["ilp_reference"] = str(reference)
        except Exception as exc:
            from sagittarius import benchmark_failure_context
            row["status"], row["failure"] = "failed", benchmark_failure_context(exc, stage="reference")
        finally:
            sys.path.remove(str(project))
    return row


def _write_family(output: Path, *, family: str, name: str, row: Mapping[str, Any], report: Mapping[str, Any]) -> dict[str, Any]:
    artifact = write_benchmark_artifacts(
        output_dir=output, stem=name, name=f"Phase 16 CUDA {family} parity protocol",
        description="Opt-in CPU/CUDA parity evidence. Matched runtime distributions are local diagnostics; first solve after doctor is not process-cold.",
        parameters={"opt_in_environment_variable": "SAGITTARIUS_ENABLE_GPU_TESTS=1", "doctor_initialize_backend": True},
        rows=[row], backend="CUDA", diagnostics=report,
        columns=["row_id", "scenario_id", "status", "stage", "problem", "solver", "backend", "metrics", "artifacts", "failure"],
        benchmark_context={"protocol_version": "benchmark-protocol/v1", "family": family, "tier": TIER, "disclosure_status": DISCLOSURE_STATUS, "failure_policy": "Retain opt-in skips, CUDA doctor failures, and scenario failures as structured rows."},
    )
    artifact["suite"] = write_benchmark_suite_artifact(
        output_dir=output, stem=f"{name}_suite", suite_id=f"phase16-{name}",
        family=family, tier=TIER, rows=[row], source=artifact["artifact"]["versions"],
        environment={"doctor": dict(report)}, scenario_defaults={"backend": "CUDA", "opt_in": True},
    )
    return artifact


def benchmark_cuda_mwis_protocol(
    output_dir: str | Path = "benchmark-output", *, doctor_fn: Callable[..., Mapping[str, Any]] = doctor
) -> dict[str, dict[str, Any]]:
    """Emit opt-in CUDA parity and MWIS GPU protocol artifacts."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parity_problem = {"problem_type": "rydberg_chain", "atom_count": 3, "blockade_radius": 0.6}
    parity_solver = {"method": "Tsit5", "duration": 0.25}
    mwis_problem = {"problem_type": "weighted_unit_disk_mwis", "atom_count": 2, "instance_seed": 3}
    mwis_solver = {"solver_type": "MWIS_AQC", "duration": 0.1}
    if not _enabled():
        report: Mapping[str, Any] = {"available": False, "issues": ["GPU protocol opt-in disabled"], "backend_probe": None}
        parity_row = _skip_row(family=PARITY_FAMILY, scenario_id="chain_n3_cpu_cuda", problem=parity_problem, solver=parity_solver)
        mwis_row = _skip_row(family=MWIS_FAMILY, scenario_id="weighted_udg_n2_seed3_cpu_cuda", problem=mwis_problem, solver=mwis_solver)
    else:
        report = _json_native(doctor_fn(backend="CUDA", initialize_backend=True))
        if not report.get("available"):
            parity_row = _doctor_failure_row(family=PARITY_FAMILY, scenario_id="chain_n3_cpu_cuda", problem=parity_problem, solver=parity_solver, report=report)
            mwis_row = _doctor_failure_row(family=MWIS_FAMILY, scenario_id="weighted_udg_n2_seed3_cpu_cuda", problem=mwis_problem, solver=mwis_solver, report=report)
        else:
            parity_row = _parity_row(output, report)
            mwis_row = _mwis_gpu_row(output, report)
    return {
        "parity": _write_family(output, family=PARITY_FAMILY, name="cuda_parity", row=parity_row, report=report),
        "mwis": _write_family(output, family=MWIS_FAMILY, name="mwis_gpu_parity", row=mwis_row, report=report),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the opt-in Phase 16 CUDA/MWIS parity protocol.")
    parser.add_argument("--output-dir", default="benchmark-output")
    arguments = parser.parse_args()
    paths = benchmark_cuda_mwis_protocol(arguments.output_dir)
    print(f"CUDA parity artifact: {paths['parity']['json']}")
    print(f"MWIS GPU parity artifact: {paths['mwis']['json']}")
