"""Backend-free audit of frozen P1 GPU campaigns and saved CPU/CUDA results."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sagittarius_py"))
from sagittarius import SimulationResult
from sagittarius.benchmark_measurement import write_json
from sagittarius.benchmarking import markdown_table, validate_benchmark_row
from sagittarius.benchmark_suite import load_benchmark_suite_artifact, _csv_rows, _markdown_summary
from sagittarius.gpu_benchmark import WORKLOAD_VERSION, pair_statistics, scenario_gate, scenarios, basis_values


def audit(directory, stem="gpu_bench_results"):
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
            raise ValueError(f"Missing evidence: {target}")
        return target
    frozen = {k: campaign[k] for k in ("scenarios", "settings", "source_sha256")}
    digest = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    if digest != campaign["config_sha256"] or campaign["workload_version"] != WORKLOAD_VERSION:
        raise ValueError("Frozen config/workload mismatch")
    for relative, expected in campaign["source_sha256"].items():
        if hashlib.sha256((directory / "source" / relative).read_bytes()).hexdigest() != expected:
            raise ValueError("Retained source hash mismatch")
    artifact = read(f"{stem}.json")
    suite = load_benchmark_suite_artifact(directory / f"{stem}_suite.json")
    rows = suite["rows"]
    if artifact["timings"] != rows or artifact["parameters"] != campaign:
        raise ValueError("Benchmark/suite/campaign mismatch")
    if [r["scenario_id"] for r in rows] != [s["scenario_id"] for s in campaign["scenarios"]]:
        raise ValueError("Missing, duplicate or reordered scenarios")
    cfg = campaign["settings"]
    expected_raw, pair_count, measured_count, maximum = [], 0, 0, 0.
    for s, row in zip(campaign["scenarios"], rows):
        validate_benchmark_row(row)
        if any(row["problem"].get(k) != v for k, v in s.items()) or row["solver"] != cfg:
            raise ValueError("Row differs from frozen scenario/settings")
        if row["basis_size"] != len(basis_values(s)):
            raise ValueError("Basis dimension mismatch")
        config = json.loads(resolve(row["artifacts"]["config"]).read_text())
        if config["scenario"] != s or config["settings"] != cfg or config["source_sha256"] != campaign["source_sha256"]:
            raise ValueError("Worker config differs from freeze")
        metrics = row["metrics"]
        pairs = metrics["pairs"]
        if row["status"] == "passed" and (cfg["warmups"] < 2 or cfg["repeat_count"] < 5):
            raise ValueError("Insufficient warmups/repeats for passed scenario")
        expected_raw.extend({"scenario_id": s["scenario_id"], **p} for p in pairs)
        if pairs != (json.loads(resolve(row["artifacts"]["paired_records"]).read_text()) if pairs else []):
            raise ValueError("Paired records mismatch")
        for backend, state in metrics["paths"].items():
            checkpoint = read(f"{s['scenario_id']}/{backend.lower()}/checkpoint.json")
            if state != checkpoint:
                raise ValueError("Worker checkpoint mismatch")
            for name, expected in state.get("runtime_files", {}).items():
                if hashlib.sha256((directory / s["scenario_id"] / backend.lower() / name).read_bytes()).hexdigest() != expected:
                    raise ValueError("Runtime file hash mismatch")
            if row["status"] == "passed":
                if not state["doctor"]["available"] or not state["doctor"]["backend_probe"]["available"]:
                    raise ValueError("Missing initialized diagnostics")
                if backend == "CUDA" and not state["doctor"]["backend_probe"]["devices"]:
                    raise ValueError("Missing CUDA device identity")
                if state["runtime_context"]["threads"]["julia"] != 1 or state["runtime_context"]["threads"]["blas"] != 1:
                    raise ValueError("Effective Julia/BLAS threads mismatch")
                if state["memory"]["peak_bytes"] is None or state["baseline_memory"]["rss_bytes"] is None:
                    raise ValueError("Missing attributable process memory")
        expected_phases = [("first", 0)] + [("warmup", i) for i in range(cfg["warmups"])] + [("measured", i) for i in range(cfg["repeat_count"])]
        if row["status"] == "passed" and [(p["phase"], p["index"]) for p in pairs] != expected_phases:
            raise ValueError("Missing first/warm/measured pairs")
        for pair in pairs:
            order = ["CPU", "CUDA"] if pair["index"] % 2 == 0 else ["CUDA", "CPU"]
            if pair["pair_order"] != order or pair["row_id"] != f"{s['scenario_id']}-{pair['phase']}-{pair['index']}":
                raise ValueError("Pair order/identity mismatch")
            outputs = {}
            for backend, record in pair["paths"].items():
                worker_records = metrics["paths"][backend]["records"]
                if record not in worker_records:
                    raise ValueError("Pair runtime differs from worker checkpoint")
                if not record["artifacts"]:
                    continue
                result = SimulationResult.load(str(resolve(record["artifacts"]["result_artifact"])))
                if result.manifest != json.loads(resolve(record["artifacts"]["run_manifest"]).read_text()):
                    raise ValueError("Standalone manifest differs from result")
                outputs[backend] = result
            if set(outputs) != {"CPU", "CUDA"}:
                if pair.get("gate", {}).get("passed") or row["status"] == "passed":
                    raise ValueError("Eligible pair lacks saved outputs")
                continue
            gate = scenario_gate(outputs["CPU"], outputs["CUDA"], s, cfg)
            if pair.get("gate") != gate:
                raise ValueError("Saved trajectory gate differs from reported gate")
            if row["status"] == "passed" and not gate["passed"]:
                raise ValueError("Passed scenario has a failed pair")
            if pair["paths"][order[0]]["call_finished_monotonic"] > pair["paths"][order[1]]["call_started_monotonic"]:
                raise ValueError("Executed calls overlap or contradict declared order")
            pair_count += 1
            measured_count += pair["phase"] == "measured"
            maximum = max(maximum, gate["parity_max_abs_error"] or 0.)
        summaries = pair_statistics(pairs, cfg, valid_campaign=row["status"] == "passed")
        if any(metrics[k] != v for k, v in summaries.items()) or row["speedup"] != summaries["median_cpu_over_cuda"]:
            raise ValueError("Statistics/ratio mismatch")
        measured = [p for p in pairs if p["phase"] == "measured"]
        first_measured = measured[0]["paths"] if measured else {}
        for backend, flat in (("CPU", "t_cpu_s"), ("CUDA", "t_gpu_s")):
            if row[flat] != first_measured.get(backend, {}).get("runtime_seconds"):
                raise ValueError("Legacy first measured time mismatch")
        maximum_for_row = max((p["gate"]["parity_max_abs_error"] for p in pairs if p.get("gate", {}).get("parity_max_abs_error") is not None), default=None)
        if row["max_trajectory_error"] != maximum_for_row:
            raise ValueError("Scenario maximum error mismatch")
        for backend in ("CPU", "CUDA"):
            summary = summaries["statistics"][backend]
            if row[f"{backend.lower()}_eligible"] != summary["eligible"]:
                raise ValueError("Eligible count mismatch")
            for statistic, value in summary["runtime_seconds"].items():
                if row[f"{backend.lower()}_{statistic}_s"] != value:
                    raise ValueError("Flat runtime statistic mismatch")
    if read("gpu_repeats.json") != expected_raw:
        raise ValueError("Raw repeat file mismatch")
    # Compare every published CSV cell and the complete regenerated tables.
    previous_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(max(previous_limit, (directory / f"{stem}_suite.csv").stat().st_size))
        with (directory / f"{stem}.csv").open() as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames
            actual = list(reader)
        expected = [{k: "" if r.get(k) is None else str(r.get(k, "")) for k in columns} for r in rows]
        if actual != expected:
            raise ValueError("CSV values mismatch")
        table = markdown_table(rows, columns=columns)
        if (directory / f"{stem}.md").read_text() != table + "\n" or artifact["markdown_table"] != table:
            raise ValueError("Markdown values mismatch")
        with (directory / f"{stem}_suite.csv").open() as handle:
            if list(csv.DictReader(handle)) != _csv_rows(rows):
                raise ValueError("Suite CSV mismatch")
        if (directory / f"{stem}_suite.md").read_text() != _markdown_summary(suite):
            raise ValueError("Suite Markdown mismatch")
    finally:
        csv.field_size_limit(previous_limit)
    expected_scenarios = scenarios()
    passed = {r["scenario_id"] for r in rows if r["status"] == "passed"}
    complete = all(s in campaign["scenarios"] for s in expected_scenarios) and {s["scenario_id"] for s in expected_scenarios} <= passed
    coverage = read("coverage.json")
    if coverage["all_p1_gpu_passed"] != complete or not coverage["declared_rows_accounted"]:
        raise ValueError("Coverage mismatch")
    return {"contract_audit_passed": True, "all_p1_gpu_passed": complete, "scenario_count": len(rows),
            "checked_pairs": pair_count, "checked_measured_pairs": measured_count,
            "maximum_trajectory_error": maximum, "status_counts": suite["summary"]["status_counts"],
            "classification": "local_only; saved numerical/software verification, no independent governance or scientific validation"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    report = audit(args.directory)
    write_json(args.directory / "audit.json", report)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["all_p1_gpu_passed"] or args.allow_partial else 1)
