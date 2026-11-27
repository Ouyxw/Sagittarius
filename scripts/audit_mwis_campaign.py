"""Audit retained MWIS graphs, independent numerics, ILP proofs and statistics."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sagittarius_py"))
from sagittarius import SimulationResult
from sagittarius.benchmark_measurement import write_json
from sagittarius.benchmarking import markdown_table, validate_benchmark_row
from sagittarius.benchmark_suite import load_benchmark_suite_artifact, _csv_rows, _markdown_summary
from sagittarius.mwis_benchmark import (WORKLOAD_VERSION, graph_from_scenario, independent_basis,
    basis_objectives, independent_reference, path_summary, phases, quality_metrics, result_gate, scenarios)


def audit(directory):
    directory = Path(directory).resolve()
    def read(name):
        return json.loads((directory / name).read_text())
    campaign = read("campaign.json")
    def resolve(value):
        path = Path(value)
        if path.is_absolute():
            path = path.relative_to(campaign["output_dir"])
        target = directory / path
        if not target.is_file():
            raise ValueError(f"Missing retained evidence: {target}")
        return target
    frozen = {key: campaign[key] for key in ("scenarios", "settings", "source_sha256")}
    if hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest() != campaign["config_sha256"] or campaign["workload_version"] != WORKLOAD_VERSION:
        raise ValueError("Frozen configuration/workload mismatch")
    for name, digest in campaign["source_sha256"].items():
        if hashlib.sha256((directory / "source" / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Retained source hash mismatch")
    artifact, suite = read("mwis_aqc_performance.json"), load_benchmark_suite_artifact(directory / "mwis_aqc_performance_suite.json")
    rows, cfg = suite["rows"], campaign["settings"]
    if artifact["timings"] != rows or artifact["parameters"] != campaign or [r["scenario_id"] for r in rows] != [s["scenario_id"] for s in campaign["scenarios"]]:
        raise ValueError("Artifact/suite/campaign order mismatch")
    raw, checked_aqc, checked_ilp, maximum = [], 0, 0, 0.
    for s, row in zip(campaign["scenarios"], rows):
        validate_benchmark_row(row)
        graph_from_scenario(s)
        basis = independent_basis(s)
        optimum = float(np.max(basis_objectives(s, basis)))
        if row["problem"] != s or row["solver"] != cfg or row["basis_size"] != len(basis):
            raise ValueError("Frozen scenario/solver/basis mismatch")
        metrics = row["metrics"]
        if metrics["paths"] != read(f"{s['scenario_id']}/paths.json") or metrics["generation_seconds"] != campaign["generation_seconds"][s["scenario_id"]]:
            raise ValueError("Raw path/generation record mismatch")
        exact_values = []
        results = {}
        for path, evidence in metrics["paths"].items():
            state = evidence["state"]
            config = json.loads(resolve(evidence["config"]).read_text())
            if config["scenario"] != s or config["settings"] != cfg or config["source_sha256"] != campaign["source_sha256"] or config["path"] != path:
                raise ValueError("Child config mismatch")
            if evidence["checkpoint"] and json.loads(resolve(evidence["checkpoint"]).read_text()) != state:
                raise ValueError("Child checkpoint mismatch")
            records = state.get("records", [])
            if row["status"] == "passed":
                if cfg["warmups"] < 2 or cfg["repeat_count"] < 5 or not state["complete"] or [(r["phase"], r["repeat_index"]) for r in records] != phases(cfg):
                    raise ValueError("Missing complete first/warm/measured path evidence")
                if evidence["supervision"]["reason"] is not None or evidence["supervision"]["returncode"] != 0:
                    raise ValueError("Passed path has unsuccessful supervision")
                if state["memory"]["peak_bytes"] is None or state["memory_baseline"]["rss_bytes"] is None:
                    raise ValueError("Missing per-path memory provenance")
            saved_reference = None
            if path == "aqc" and state.get("reference"):
                reference = state["reference"]
                saved_reference = dict(np.load(resolve(reference["arrays"]), allow_pickle=False))
                replay, coarse = independent_reference(s), independent_reference(s, rtol=1e-10, atol=1e-12)
                if not np.array_equal(saved_reference["basis"], basis) or any(not np.allclose(saved_reference[k], replay[k], rtol=1e-11, atol=1e-12) for k in ("t", "pop0", "probabilities")):
                    raise ValueError("Saved independent reference differs from recomputation")
                stability = max(float(np.max(np.abs(replay[k] - coarse[k]))) for k in ("pop0", "probabilities"))
                if stability > cfg["reference_stability_atol"] or not np.isclose(stability, reference["stability_error"], rtol=1e-3, atol=1e-12):
                    raise ValueError("Independent reference refinement gate mismatch")
                if not state["doctor"]["available"] or not state["doctor"]["backend_probe"]["available"] or any(state["runtime_context"]["threads"][k] != 1 for k in ("julia", "blas")):
                    raise ValueError("Initialized doctor/effective thread mismatch")
                for name, digest in state["runtime_files"].items():
                    file = directory / s["scenario_id"] / path / name
                    if hashlib.sha256(file.read_bytes()).hexdigest() != digest:
                        raise ValueError("Runtime file hash mismatch")
            for record in records:
                raw.append({"scenario_id": s["scenario_id"], "path": path, **record})
                if record["row_id"] != f"{s['scenario_id']}-{path}-{record['phase']}-{record['repeat_index']}" or record["operation_count"] != 1:
                    raise ValueError("Repeat identity/operation-count mismatch")
                if path == "aqc" and record.get("artifacts", {}).get("result_artifact"):
                    result = SimulationResult.load(str(resolve(record["artifacts"]["result_artifact"])))
                    if result.manifest != json.loads(resolve(record["artifacts"]["run_manifest"]).read_text()):
                        raise ValueError("Standalone manifest differs from actual result")
                    results[record["row_id"]] = result
                    if saved_reference is not None and "gate" in record:
                        gate = result_gate(result, s, cfg, saved_reference)
                        if gate != record["gate"] or gate["passed"] != record["eligible"]:
                            raise ValueError("Saved numerical gate mismatch")
                        maximum = max(maximum, gate["numerical_max_abs_error"] or 0.)
                    elif record["eligible"]:
                        raise ValueError("Eligible AQC result lacks reference/gate")
                    checked_aqc += 1
                if path == "ilp" and "reference" in record:
                    reference = record["reference"]
                    if reference != json.loads(resolve(record["artifacts"]["reference_report"]).read_text()):
                        raise ValueError("ILP reference report mismatch")
                    log = resolve(record["artifacts"]["solver_log"]).read_text()
                    for flag, value in (("sec", cfg["ilp_time_limit"]), ("threads", cfg["cbc_threads"]), ("randomSeed", cfg["cbc_seed"]), ("ratio", 0.), ("allow", 0.)):
                        match = re.search(r"-" + flag + r"\s+([-+0-9.eE]+)", log)
                        if not match or float(match.group(1)) != value:
                            raise ValueError("Effective CBC command flags mismatch")
                    bits = reference["candidate_bitstring"]
                    if bits is not None:
                        if any(v not in (0, 1) for v in bits) or len(bits) != s["N"] or any(bits[i] and bits[j] for i, j in s["edges"]):
                            raise ValueError("Infeasible/nonbinary ILP incumbent")
                        weight = sum(node["weight"] * bits[i] for i, node in enumerate(s["nodes"]))
                        if weight != reference["incumbent_objective"]:
                            raise ValueError("ILP objective/bitstring mismatch")
                    if reference["proven_optimal"]:
                        if reference["problem_status"] != "Optimal" or reference["solution_status"] != "Optimal Solution Found" or "Result - Optimal solution found" not in log or reference["exact_objective"] is None or abs(reference["exact_objective"] - optimum) > cfg["objective_atol"]:
                            raise ValueError("ILP exact-optimality proof mismatch")
                        exact_values.append(reference["exact_objective"])
                    elif reference["exact_objective"] is not None:
                        raise ValueError("Nonoptimal incumbent reported as exact")
                    if record["eligible"] != reference["proven_optimal"]:
                        raise ValueError("ILP timing eligibility mismatch")
                    checked_ilp += 1
            summary = path_summary(state, cfg)
            if summary != metrics["statistics"][path] or row[f"{path}_eligible"] != summary["eligible"]:
                raise ValueError("Repeat statistics/count/member mismatch")
            for name, value in summary["runtime_seconds"].items():
                if row[f"{path}_{name}_s"] != value:
                    raise ValueError("Flat runtime summary mismatch")
        exact = exact_values[0] if exact_values else None
        quality = {key: quality_metrics(s, result.final_bitstring_distribution(), exact, objective_atol=cfg["objective_atol"]) for key, result in results.items()}
        if metrics["quality_by_aqc_row_id"] != quality or metrics["exact_objective"] != exact or row["exact_objective"] != exact:
            raise ValueError("Feasibility/objective/gap/ratio/optimal-mass mismatch")
        measured = [r for r in metrics["paths"]["aqc"]["state"].get("records", []) if r["phase"] == "measured" and r["row_id"] in quality]
        representative = quality[measured[0]["row_id"]] if measured else {}
        for key in ("candidate_objective", "feasible", "objective_gap", "approximation_ratio", "optimal_success_probability"):
            if row[key] != representative.get(key):
                raise ValueError("Flat quality summary mismatch")
        if row["status"] == "passed" and (exact is None or any(not q["feasible"] for q in quality.values()) or any(summary["eligible"] != cfg["repeat_count"] for summary in metrics["statistics"].values())):
            raise ValueError("Passed row lacks applicable reference/feasibility/repeats")
    if read("mwis_repeats.json") != raw or len({r["row_id"] for r in raw}) != len(raw):
        raise ValueError("Raw repeats missing/duplicated/mismatched")
    previous_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(max(previous_limit, (directory / "mwis_aqc_performance_suite.csv").stat().st_size))
        with (directory / "mwis_aqc_performance.csv").open() as handle:
            reader = csv.DictReader(handle)
            columns, actual = reader.fieldnames, list(reader)
        expected = [{k: "" if row.get(k) is None else str(row.get(k, "")) for k in columns} for row in rows]
        table = markdown_table(rows, columns=columns)
        if actual != expected or (directory / "mwis_aqc_performance.md").read_text() != table + "\n" or artifact["markdown_table"] != table:
            raise ValueError("CSV/Markdown companion values mismatch")
        with (directory / "mwis_aqc_performance_suite.csv").open() as handle:
            if list(csv.DictReader(handle)) != _csv_rows(rows):
                raise ValueError("Suite CSV mismatch")
        if (directory / "mwis_aqc_performance_suite.md").read_text() != _markdown_summary(suite):
            raise ValueError("Suite Markdown mismatch")
    finally:
        csv.field_size_limit(previous_limit)
    expected = scenarios()
    passed = {r["scenario_id"] for r in rows if r["status"] == "passed"}
    complete = all(s in campaign["scenarios"] for s in expected) and {s["scenario_id"] for s in expected} <= passed
    if read("coverage.json")["all_p1_mwis_passed"] != complete or not read("coverage.json")["declared_rows_accounted"]:
        raise ValueError("Coverage mismatch")
    return {"contract_audit_passed": True, "all_p1_mwis_passed": complete, "scenario_count": len(rows),
            "checked_aqc_results": checked_aqc, "checked_ilp_references": checked_ilp,
            "maximum_numerical_error": maximum, "status_counts": suite["summary"]["status_counts"],
            "classification": "local_only; reduced-model numerical/software verification, not scientific validation or optimization advantage"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    report = audit(args.directory)
    write_json(args.directory / "audit.json", report)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["all_p1_mwis_passed"] or args.allow_partial else 1)
