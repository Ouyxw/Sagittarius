"""Audit retained P0 scaling evidence and write an explicit acceptance report.

Run with the source checkout's Python environment. Recorded absolute artifact
paths can be relocated using the original campaign output_dir as prefix.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sagittarius_py"))

from sagittarius import SimulationResult, validate_run_manifest
from sagittarius.benchmark_measurement import runtime_summary, write_json
from sagittarius.benchmark_suite import load_benchmark_suite_artifact
from sagittarius.benchmarking import validate_benchmark_row
from sagittarius.scaling_benchmark import basis_dimension, scenarios


def audit(directory):
    directory = Path(directory).resolve()
    campaign = json.loads((directory / "campaign.json").read_text())
    def resolve(value):
        path = Path(value)
        if path.is_absolute():
            path = directory / path.relative_to(campaign["output_dir"])
        else:
            path = directory / path
        if not path.is_file():
            raise ValueError(f"Missing retained artifact: {path}")
        return path
    frozen = {key: campaign[key] for key in ("scenarios", "settings")}
    digest = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    if digest != campaign["config_sha256"]:
        raise ValueError("Frozen configuration hash mismatch.")
    for name, expected in campaign["source_file_sha256"].items():
        if hashlib.sha256((directory / "source" / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Retained source mismatch: {name}")
    suite = load_benchmark_suite_artifact(directory / "scaling_results_suite.json")
    artifact = json.loads((directory / "scaling_results.json").read_text())
    if artifact["schema_version"] != "benchmark-artifact/v1" or artifact["timings"] != suite["rows"]:
        raise ValueError("Single-scenario and suite companions disagree.")
    if [r["scenario_id"] for r in suite["rows"]] != [s["scenario_id"] for s in campaign["scenarios"]]:
        raise ValueError("Declared scenario order/coverage differs from suite rows.")
    repeats = json.loads((directory / "scaling_repeats.json").read_text())
    if len({r["row_id"] for r in repeats}) != len(repeats):
        raise ValueError("Duplicate repeat row IDs.")
    checked_results = 0
    unavailable_failed_repeat_artifacts = []
    max_error = 0.
    max_hamiltonian_error = 0.
    for row in suite["rows"]:
        validate_benchmark_row(row)
        if row["problem"]["basis_size"] != basis_dimension(row["problem"]):
            raise ValueError("Incorrect basis dimension.")
        metrics = row["metrics"]
        if metrics["config_sha256"] != digest:
            raise ValueError("Scenario configuration identity mismatch.")
        summary = runtime_summary(metrics["repeats"], campaign["settings"]["repeat_count"])
        if metrics["statistics"] != summary:
            raise ValueError("Repeat summary does not match retained measurements.")
        scenario_repeats = [r for r in repeats if r["scenario_id"] == row["scenario_id"]]
        if [r["row_id"] for r in scenario_repeats] != [r["row_id"] for r in metrics["repeats"]]:
            raise ValueError("Repeat companion differs from scenario measurements.")
        resolve(row["artifacts"]["config"])
        if row["status"] == "passed":
            if summary["eligible"] < 5 or len(metrics["warmups"]) < 2:
                raise ValueError("Passed row lacks required warmups/repeats.")
            reference = json.loads(resolve(row["artifacts"]["reference_report"]).read_text())
            if reference != metrics["reference"]:
                raise ValueError("Reference report differs from row.")
            max_hamiltonian_error = max(max_hamiltonian_error, reference.get("hamiltonian_max_abs_error", 0.))
            if metrics["memory"]["peak_bytes"] is None:
                raise ValueError("Passed row lacks attributable lifetime memory.")
            if metrics["runtime_context"]["threads"]["julia"] != 1 or metrics["runtime_context"]["threads"]["blas"] != 1:
                raise ValueError("Effective threads differ from frozen anchor.")
            checkpoint = json.loads(resolve(row["artifacts"]["checkpoint"]).read_text())
            if not checkpoint["doctor"]["available"] or not checkpoint["doctor"]["backend_probe"]["available"]:
                raise ValueError("Passed row lacks successful initialized CPU diagnostics.")
            for project_file in metrics["runtime_context"].get("project_files", {}).values():
                if hashlib.sha256(resolve(project_file["path"]).read_bytes()).hexdigest() != project_file["sha256"]:
                    raise ValueError("Retained Julia runtime project hash mismatch.")
        for repeat in scenario_repeats:
            validate_benchmark_row(repeat)
            if not all(repeat["artifacts"].get(key) for key in ("result_artifact", "run_manifest")):
                if repeat["status"] == "passed":
                    raise ValueError("Passed repeat lacks result/manifest artifacts.")
                unavailable_failed_repeat_artifacts.append(repeat["row_id"])
                continue
            result = SimulationResult.load(str(resolve(repeat["artifacts"]["result_artifact"])))
            manifest = json.loads(resolve(repeat["artifacts"]["run_manifest"]).read_text())
            validate_run_manifest(manifest)
            if result.manifest != manifest:
                raise ValueError("Saved result and standalone manifest disagree.")
            solver = manifest["solver"]
            if solver["effective_saveat"] != row["solver"]["saveat"] or len(result.data["t"]) != 101:
                raise ValueError("Effective output grid mismatch.")
            if solver["effective_method"] != "Tsit5" or not solver["effective_adaptive"] or solver["effective_dt"] is not None:
                raise ValueError("Effective solver mismatch.")
            if any(solver[key] != row["solver"][key] for key in ("reltol", "abstol", "blockade_radius")):
                raise ValueError("Executed tolerances/radius differ from frozen request.")
            if manifest["register"]["atoms"] != row["problem"]["coordinates"] or manifest["initial_state"]["basis_size"] != row["basis_size"]:
                raise ValueError("Executed register/basis mismatch.")
            if repeat["metrics"]["eligible"]:
                error = float(np.max(np.abs(np.asarray(result.data["pop0"]) - np.asarray(reference["pop0"]))))
                if not np.isfinite(error) or error > campaign["settings"]["observable_atol"]:
                    raise ValueError("Saved trajectory fails frozen numerical gate.")
                if not np.isclose(error, repeat["metrics"]["max_abs_error"], rtol=0, atol=1e-15):
                    raise ValueError("Reported trajectory error differs from saved result/reference.")
            max_error = max(max_error, repeat["metrics"].get("max_abs_error", 0.))
            checked_results += 1
        # Audit first/reference simulation artifacts as well as measured repeats.
        for key in ("first_solve", "reference_result"):
            for path in row["artifacts"].get(key, {}).values():
                resolve(path)
        for name in ("scaling_results", "scaling_results_suite"):
            for suffix in ("json", "csv", "md"):
                resolve(str(Path(campaign["output_dir"]) / f"{name}.{suffix}"))
    expected = {s["scenario_id"] for s in scenarios()}
    for name in ("scaling_results", "scaling_results_suite"):
        with (directory / f"{name}.csv").open() as handle:
            companion = list(csv.DictReader(handle))
        if [(r["row_id"], r["status"]) for r in companion] != [(r["row_id"], r["status"]) for r in suite["rows"]]:
            raise ValueError("CSV companion rows disagree with JSON.")
        markdown = (directory / f"{name}.md").read_text()
        if any(row["row_id"] not in markdown for row in suite["rows"]):
            raise ValueError("Markdown companion omits a scenario.")
    passed = {r["scenario_id"] for r in suite["rows"] if r["status"] == "passed"}
    return {"contract_audit_passed": True, "full_v2_matrix_passed": expected <= passed,
            "scenario_count": len(suite["rows"]), "passed_scenarios": len(passed),
            "checked_measured_result_manifest_pairs": checked_results,
            "failed_repeats_with_unavailable_artifacts": unavailable_failed_repeat_artifacts,
            "max_observable_error": max_error, "max_hamiltonian_error": max_hamiltonian_error,
            "missing_successful_scenarios": sorted(expected - passed),
            "classification": "local_only; automated contract/numerical evidence audit, no independent governance review"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    report = audit(args.directory)
    write_json(args.directory / "audit.json", report)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["full_v2_matrix_passed"] or args.allow_partial else 1)
