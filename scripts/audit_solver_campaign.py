"""Backend-free audit of saved solver sensitivity outputs, references and reports."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sagittarius_py"))
from sagittarius import SimulationResult
from sagittarius.benchmark_measurement import write_json
from sagittarius.benchmarking import markdown_table, validate_benchmark_row
from sagittarius.benchmark_suite import load_benchmark_suite_artifact, _csv_rows, _markdown_summary
from sagittarius.solver_benchmark import (COLUMNS, WORKLOAD_VERSION, coverage, make_row,
    phases, result_gate, scenarios, stable_reference)


def audit(directory):
    directory = Path(directory).resolve()
    def read(name):
        return json.loads((directory / name).read_text())
    campaign = read("campaign.json")
    def resolve(value):
        path = Path(value)
        if path.is_absolute():
            path = path.relative_to(campaign["output_dir"])
        target = (directory / path).resolve()
        if not target.is_relative_to(directory) or not target.is_file():
            raise ValueError(f"Missing/outside retained evidence: {target}")
        return target
    frozen = {key: campaign[key] for key in ("scenarios", "settings", "source_sha256")}
    if hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest() != campaign["config_sha256"] or campaign["workload_version"] != WORKLOAD_VERSION:
        raise ValueError("Frozen configuration/workload mismatch")
    expected = {s["scenario_id"]: s for s in scenarios()}
    if not campaign["scenarios"] or len({s["scenario_id"] for s in campaign["scenarios"]}) != len(campaign["scenarios"]):
        raise ValueError("Empty/duplicate frozen scenarios")
    for s in campaign["scenarios"]:
        if s != expected.get(s["scenario_id"]):
            raise ValueError("Scenario differs from declared workload matrix")
    for name, digest in campaign["source_sha256"].items():
        if hashlib.sha256((directory / "source" / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Retained source hash mismatch")
    artifact = read("solver_sensitivity.json")
    suite = load_benchmark_suite_artifact(directory / "solver_sensitivity_suite.json")
    rows, cfg = suite["rows"], campaign["settings"]
    if artifact["timings"] != rows or artifact["parameters"] != campaign or [r["scenario_id"] for r in rows] != [s["scenario_id"] for s in campaign["scenarios"]]:
        raise ValueError("Artifact/suite/campaign mismatch")
    raw, checked, maximum, norm_error = [], 0, 0., 0.
    for s, row in zip(campaign["scenarios"], rows):
        validate_benchmark_row(row)
        state = row["metrics"]["state"]
        child_config = json.loads(resolve(row["artifacts"]["config"]).read_text())
        if child_config != {"scenario": s, "settings": cfg, "source_root": campaign["source_root"], "source_sha256": campaign["source_sha256"]}:
            raise ValueError("Child configuration mismatch")
        if row["artifacts"]["checkpoint"] and json.loads(resolve(row["artifacts"]["checkpoint"]).read_text()) != state:
            raise ValueError("Checkpoint mismatch")
        rebuilt = make_row(s, cfg, state, row["metrics"]["supervision"],
                           exclusion=row["failure"]["message"] if row["status"] == "skipped" else None)
        rebuilt["artifacts"] = row["artifacts"]
        if rebuilt != row:
            raise ValueError("Summary/statistics/status mismatch")
        records = state.get("records", [])
        if row["status"] == "passed":
            if [(r["phase"], r["repeat_index"]) for r in records] != phases(cfg) or cfg["warmups"] < 2 or cfg["repeat_count"] < 5:
                raise ValueError("Missing first/warmup/measured evidence")
            if not state["complete"] or row["metrics"]["supervision"]["returncode"] != 0 or row["metrics"]["supervision"]["reason"] is not None:
                raise ValueError("Unsuccessful process marked passed")
            if state["memory"]["peak_bytes"] is None or state["memory_baseline"]["rss_bytes"] is None:
                raise ValueError("Missing attributable process memory")
        reference = state.get("reference")
        if reference:
            if reference != read(f"{s['scenario_id']}/reference.json"):
                raise ValueError("Reference companion mismatch")
            replay = stable_reference(s, cfg["reference_stability_atol"])
            for key in ("basis", "t"):
                if reference[key] != replay[key]:
                    raise ValueError("Reference basis/grid mismatch")
            for key in ("pop0", "z0", "raw_norm", "final_probabilities"):
                if not np.allclose(reference[key], replay[key], rtol=1e-11, atol=1e-12):
                    raise ValueError("Saved reference differs from independent replay")
            if not reference["stable"] or reference["stability_error"] > cfg["reference_stability_atol"] or not np.isclose(reference["stability_error"], replay["stability_error"], rtol=1e-2, atol=1e-12):
                raise ValueError("Reference stability mismatch")
            if not state["doctor"]["available"] or not state["doctor"]["backend_probe"]["available"] or any(state["runtime_context"]["threads"][k] != 1 for k in ("julia", "blas")):
                raise ValueError("Initialized doctor/effective threads mismatch")
            if set(state["runtime_files"]) != {"Project.toml", "Manifest.toml"}:
                raise ValueError("Missing runtime dependency files")
            for name, digest in state["runtime_files"].items():
                if hashlib.sha256((directory / s["scenario_id"] / name).read_bytes()).hexdigest() != digest:
                    raise ValueError("Runtime file hash mismatch")
        for record in records:
            raw.append({"scenario_id": s["scenario_id"], **record})
            if record["row_id"] != f"{s['scenario_id']}-{record['phase']}-{record['repeat_index']}" or record["operation_count"] != 1:
                raise ValueError("Record identity/workload mismatch")
            if "runtime_seconds" in record and (not np.isfinite(record["runtime_seconds"]) or record["runtime_seconds"] < 0):
                raise ValueError("Invalid raw timing")
            if record["artifacts"].get("result_artifact"):
                result = SimulationResult.load(str(resolve(record["artifacts"]["result_artifact"])))
                if result.manifest != json.loads(resolve(record["artifacts"]["run_manifest"]).read_text()):
                    raise ValueError("Actual result and standalone manifest differ")
                if reference is not None and "gate" in record:
                    gate = result_gate(result, s, cfg, reference)
                    if gate != record["gate"] or gate["passed"] != record["eligible"]:
                        raise ValueError("Saved-output numerical gate mismatch")
                    if record["effective_solver"] != result.diagnostics["simulation"] or record["effective_times"] != np.asarray(result.data["t"]).tolist() or record["output_sample_count"] != s["output_count"]:
                        raise ValueError("Actual effective configuration/grid mismatch")
                    maximum = max(maximum, gate["max_abs_error"])
                    norm_error = max(norm_error, gate["raw_norm_error"])
                elif record["eligible"]:
                    raise ValueError("Eligible result lacks reference/gate")
                checked += 1
            elif record["eligible"]:
                raise ValueError("Eligible record lacks saved output")
    if raw != read("solver_repeats.json") or read("coverage.json") != coverage(rows) or read("progress.json") != rows:
        raise ValueError("Raw records/coverage/progress mismatch")
    previous_limit = csv.field_size_limit()
    csv.field_size_limit(sys.maxsize)
    try:
        with (directory / "solver_sensitivity.csv").open(newline="") as handle:
            actual = list(csv.DictReader(handle))
        expected_csv = [{k: str(row[k]) if row[k] is not None else "" for k in COLUMNS} for row in rows]
        if actual != expected_csv:
            raise ValueError("Performance CSV mismatch")
        table = markdown_table(rows, columns=COLUMNS)
        if (directory / "solver_sensitivity.md").read_text() != table + "\n" or artifact["markdown_table"] != table:
            raise ValueError("Performance Markdown mismatch")
        with (directory / "solver_sensitivity_suite.csv").open(newline="") as handle:
            if list(csv.DictReader(handle)) != _csv_rows(rows):
                raise ValueError("Suite CSV mismatch")
        if (directory / "solver_sensitivity_suite.md").read_text() != _markdown_summary(suite):
            raise ValueError("Suite Markdown mismatch")
    finally:
        csv.field_size_limit(previous_limit)
    return {"contract_audit_passed": True, "full_v2_matrix_passed": coverage(rows)["full_v2_matrix_passed"],
            "scenario_count": len(rows), "checked_results": checked,
            "measured_count": sum(r["phase"] == "measured" and "runtime_seconds" in r for r in raw),
            "eligible_measured_count": sum(r["phase"] == "measured" and r["eligible"] for r in raw),
            "max_abs_error": maximum, "raw_norm_error": norm_error, "status_counts": suite["summary"]["status_counts"],
            "classification": coverage(rows)["classification"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    report = audit(args.directory)
    write_json(args.directory / "audit.json", report)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["full_v2_matrix_passed"] or args.allow_partial else 1)
