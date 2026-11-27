"""Recompute retained observable references, order/value gates and timing reports without Julia."""
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
from sagittarius.observable_benchmark import (COLUMNS, WORKLOAD_VERSION, coverage, make_row,
    ordered_declarations, record_plan, reference, result_gate, scenarios)


def audit(directory):
    directory = Path(directory).resolve()
    def read(name): return json.loads((directory / name).read_text())
    campaign = read("campaign.json")
    def resolve(value):
        p = Path(value)
        if p.is_absolute(): p = p.relative_to(campaign["output_dir"])
        target = (directory / p).resolve()
        if not target.is_relative_to(directory) or not target.is_file(): raise ValueError("Missing/outside retained evidence: " + str(target))
        return target
    frozen = {k: campaign[k] for k in ("scenarios", "settings", "source_sha256")}
    if hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest() != campaign["config_sha256"] or campaign["workload_version"] != WORKLOAD_VERSION:
        raise ValueError("Frozen configuration/workload mismatch")
    expected = {s["scenario_id"]: s for s in scenarios(campaign["settings"]["tier"])}
    if not campaign["scenarios"] or len({s["scenario_id"] for s in campaign["scenarios"]}) != len(campaign["scenarios"]): raise ValueError("Empty/duplicate scenarios")
    if any(expected.get(s["scenario_id"]) != s for s in campaign["scenarios"]): raise ValueError("Unexpected matrix/configuration")
    for name, digest in campaign["source_sha256"].items():
        if hashlib.sha256((directory / "source" / name).read_bytes()).hexdigest() != digest: raise ValueError("Frozen source hash mismatch")
    artifact = read("observable_performance.json")
    suite = load_benchmark_suite_artifact(directory / "observable_performance_suite.json")
    rows, cfg = suite["rows"], campaign["settings"]
    if artifact["timings"] != rows or artifact["parameters"] != campaign or [r["scenario_id"] for r in rows] != [s["scenario_id"] for s in campaign["scenarios"]]: raise ValueError("Artifact/suite/campaign mismatch")
    raw, checked, deterministic, stochastic, maximum_deterministic = [], 0, 0, 0, 0.
    maximum_stability, empty_controls, order_pairs = 0., 0, []
    # Cross-order controls compare the same seed or performance phase/index;
    # shared reference gates already check every individual named output.
    cross_order = {}
    for s, row in zip(campaign["scenarios"], rows):
        validate_benchmark_row(row)
        state = row["metrics"]["state"]
        config = json.loads(resolve(row["artifacts"]["config"]).read_text())
        if config != {"scenario": s, "settings": cfg, "source_root": campaign["source_root"], "source_sha256": campaign["source_sha256"]}: raise ValueError("Child config mismatch")
        if row["artifacts"]["checkpoint"] and json.loads(resolve(row["artifacts"]["checkpoint"]).read_text()) != state: raise ValueError("Checkpoint mismatch")
        rebuilt = make_row(s, cfg, state, row["metrics"]["supervision"], row["failure"]["message"] if row["status"] == "skipped" else None)
        rebuilt["artifacts"] = row["artifacts"]
        if rebuilt != row: raise ValueError("Statistics/count/membership/status mismatch")
        records = state.get("records", [])
        if row["status"] == "passed":
            if not state["complete"] or [(r["phase"], r["repeat_index"], r["order"], r["seed"]) for r in records] != record_plan(s, cfg): raise ValueError("Missing declared calls")
            if row["metrics"]["supervision"]["reason"] is not None or row["metrics"]["supervision"]["returncode"] != 0: raise ValueError("Unsuccessful worker passed")
            if state["memory"]["peak_bytes"] is None or state["memory_baseline"]["rss_bytes"] is None: raise ValueError("Missing attributable memory")
        if state.get("reference"):
            if state["reference"] != read(f"{s['scenario_id']}/reference.json"): raise ValueError("Reference report mismatch")
            saved = dict(np.load(directory / s["scenario_id"] / "reference.npz", allow_pickle=False))
            replay, description = reference(s, cfg["reference_stability_atol"])
            if set(saved) != set(replay) or any(saved[k].shape != replay[k].shape or not np.allclose(saved[k], replay[k], rtol=1e-11, atol=1e-12) for k in replay): raise ValueError("Independent saved reference mismatch")
            if not state["reference"]["stable"] or not np.isclose(description["stability_error"], state["reference"]["stability_error"], rtol=1e-2, atol=1e-12): raise ValueError("Reference stability mismatch")
            maximum_stability = max(maximum_stability, description["stability_error"])
            if not state["doctor"]["available"] or not state["doctor"]["backend_probe"]["available"] or any(state["runtime_context"]["threads"][k] != 1 for k in ("julia", "blas")): raise ValueError("Initialized doctor/effective threads mismatch")
            if set(state["runtime_files"]) != {"Project.toml", "Manifest.toml"}: raise ValueError("Missing runtime dependency identity")
            for name, digest in state["runtime_files"].items():
                if hashlib.sha256((directory / s["scenario_id"] / name).read_bytes()).hexdigest() != digest: raise ValueError("Runtime hash mismatch")
        else: saved = None
        if state.get("empty_observables"):
            empty = state["empty_observables"]
            if empty["state_count"] != s["output_count"] or empty["state_dimension"] != s["basis_size"] or empty["times"] != s["solver"]["saveat"]: raise ValueError("Empty-observable policy mismatch")
            if "arrays" in empty:
                arrays = dict(np.load(resolve(empty["arrays"]), allow_pickle=False))
                if arrays["states"].shape != (s["output_count"], s["basis_size"]) or not np.allclose(arrays["states"], np.array([1.] + [0.] * (s["basis_size"] - 1)), rtol=0, atol=1e-14) or arrays["t"].tolist() != empty["times"]: raise ValueError("Empty-observable saved history mismatch")
            empty_controls += 1
        for record in records:
            raw.append({"scenario_id": s["scenario_id"], **record})
            if record["row_id"] != f"{s['scenario_id']}-{record['phase']}-{record['repeat_index']}" or record["operation_count"] != 1: raise ValueError("Call identity mismatch")
            if "runtime_seconds" in record and (not np.isfinite(record["runtime_seconds"]) or record["runtime_seconds"] < 0): raise ValueError("Invalid timing")
            if record["artifacts"].get("result_artifact"):
                path = resolve(record["artifacts"]["result_artifact"])
                envelope = json.loads(path.read_text())
                result = SimulationResult.load(str(path))
                manifest = json.loads(resolve(record["artifacts"]["run_manifest"]).read_text())
                if result.manifest != manifest: raise ValueError("Standalone manifest differs from actual result")
                ds = ordered_declarations(s, record["order"])
                names = list(ds)
                if list(manifest["solver"]["observables"]) != names or list(envelope["manifest"]["solver"]["observables"]) != names or list(envelope["data"]) != names + ["t"] or envelope["shared_result"]["observable_names"] != names or list(envelope["shared_result"]["series"])[:len(names)] != names: raise ValueError("Serialized declaration order mismatch")
                if saved is not None and "gate" in record:
                    gate = result_gate(result, s, cfg, saved, order=record["order"], seed=record["seed"])
                    if gate != record["gate"] or gate["passed"] != record["eligible"]: raise ValueError("Saved value/order gate mismatch")
                    if record["effective_solver"] != result.diagnostics["simulation"]: raise ValueError("Effective solver record mismatch")
                    if s["fixture"] != "mcwf": deterministic += 1; maximum_deterministic = max(maximum_deterministic, gate["max_abs_error"])
                    else: stochastic += 1
                    # Include exact output policy and declarations, ignoring only
                    # mapping insertion order. Do not compare different sizes/grids.
                    key = (s["kind"], s["N"], s["basis_mode"], s["fixture"], s["count"], s["output_count"], s["collection"], record["phase"], record["seed"], record["repeat_index"] if s["kind"] == "performance" else 0)
                    values = {name: result.data[name] for name in sorted(ds)}
                    if key in cross_order:
                        other_order, previous = cross_order[key]
                        if any(not np.allclose(values[name], previous[name], rtol=0, atol=2 * cfg["accuracy_atol"]) for name in values): raise ValueError("Reordered named values differ")
                        order_pairs.append([other_order, record["order"]])
                    else: cross_order[key] = record["order"], values
                elif record["eligible"]: raise ValueError("Eligible call lacks reference/gate")
                checked += 1
            elif record["eligible"]: raise ValueError("Eligible call lacks actual output")
    if read("observable_repeats.json") != raw or read("progress.json") != rows or read("coverage.json") != coverage(rows): raise ValueError("Raw/coverage/progress mismatch")
    limit = csv.field_size_limit()
    csv.field_size_limit(sys.maxsize)
    try:
        with (directory / "observable_performance.csv").open(newline="") as f: actual_csv = list(csv.DictReader(f))
        if actual_csv != [{k: str(row[k]) if row[k] is not None else "" for k in COLUMNS} for row in rows]: raise ValueError("Performance CSV mismatch")
        table = markdown_table(rows, columns=COLUMNS)
        if (directory / "observable_performance.md").read_text() != table + "\n" or artifact["markdown_table"] != table: raise ValueError("Performance Markdown mismatch")
        with (directory / "observable_performance_suite.csv").open(newline="") as f:
            if list(csv.DictReader(f)) != _csv_rows(rows): raise ValueError("Suite CSV mismatch")
        if (directory / "observable_performance_suite.md").read_text() != _markdown_summary(suite): raise ValueError("Suite Markdown mismatch")
    finally: csv.field_size_limit(limit)
    return {"contract_audit_passed": True, **coverage(rows), "scenario_count": len(rows), "checked_results": checked,
        "deterministic_results": deterministic, "stochastic_results": stochastic, "empty_policy_controls": empty_controls,
        "cross_order_pairs": len(order_pairs), "maximum_deterministic_error": maximum_deterministic,
        "maximum_reference_stability_error": maximum_stability,
        "eligible_measured_count": sum(r["eligible"] for r in raw if r["phase"] == "measured"),
        "status_counts": suite["summary"]["status_counts"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    report = audit(args.directory)
    write_json(args.directory / "audit.json", report)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["full_matrix_passed"] or args.allow_partial else 1)
