"""Audit saved P0 ablation configuration, repeats, numerical outputs and companions."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sagittarius_py"))
from sagittarius import Register
from sagittarius.ablation import CPU_MODES, WORKLOAD_VERSION, _seeded_state, independent_reference, output_gate
from sagittarius.ablation_benchmark import scenarios
from sagittarius.benchmark_measurement import runtime_summary, write_json
from sagittarius.benchmark_suite import load_benchmark_suite_artifact
from sagittarius.benchmarking import validate_benchmark_row


def audit(directory):
    directory = Path(directory).resolve()
    def read(name):
        return json.loads((directory / name).read_text())
    campaign = read("campaign.json")
    def resolve(value):
        path = Path(value)
        path = directory / path.relative_to(campaign["output_dir"]) if path.is_absolute() else directory / path
        if not path.is_file():
            raise ValueError(f"Missing retained evidence: {path}")
        return path
    frozen = {key: campaign[key] for key in ("scenarios", "settings")}
    digest = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    if digest != campaign["config_sha256"] or campaign["workload_version"] != WORKLOAD_VERSION:
        raise ValueError("Frozen configuration/workload mismatch")
    for name, expected in campaign["source_file_sha256"].items():
        if hashlib.sha256((directory / "source" / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Retained source hash mismatch")
    suite = load_benchmark_suite_artifact(directory / "ablation_bench_results_suite.json")
    artifact = read("ablation_bench_results.json")
    if artifact["schema_version"] != "benchmark-artifact/v1" or artifact["timings"] != suite["rows"]:
        raise ValueError("Benchmark/suite companion mismatch")
    if [row["problem"] for row in suite["rows"]] != campaign["scenarios"]:
        raise ValueError("Declared scenarios/order differ from measured rows")
    measurements = read("ablation_repeats.json")
    if len({r["row_id"] for r in measurements}) != len(measurements):
        raise ValueError("Duplicate repeat IDs")
    settings = campaign["settings"]["measurement"]
    checked, max_abs, max_relative = 0, 0., 0.
    expected_repeat_ids = []
    for row in suite["rows"]:
        validate_benchmark_row(row)
        s, metrics = row["problem"], row["metrics"]
        if metrics["config_sha256"] != digest:
            raise ValueError("Path configuration identity mismatch")
        config = json.loads(resolve(row["artifacts"]["config"]).read_text())
        if config["scenario"] != s or config["settings"] != campaign["settings"] or config["config_sha256"] != digest:
            raise ValueError("Child configuration differs from frozen campaign")
        summary = runtime_summary(metrics.get("measurements", []), settings["repeat_count"])
        if metrics["statistics"] != summary:
            raise ValueError("Statistics differ from retained measurements")
        scenario_repeats = [r for r in measurements if r["scenario_id"] == row["scenario_id"]]
        expected_repeat_ids.extend(r["row_id"] for r in metrics.get("measurements", []))
        if [r["row_id"] for r in scenario_repeats] != [r["row_id"] for r in metrics.get("measurements", [])]:
            raise ValueError("Repeat companion mismatch")
        for actual, repeated in zip(metrics.get("measurements", []), scenario_repeats):
            validate_benchmark_row(repeated)
            if any(repeated["metrics"].get(k) != v for k, v in actual.items() if k != "artifacts"):
                raise ValueError("Repeat metrics mismatch")
            if any(repeated["artifacts"].get(k) != v for k, v in actual["artifacts"].items()):
                raise ValueError("Repeat artifact mismatch")
        if row["status"] == "passed":
            if s["mode"] not in CPU_MODES or not metrics.get("complete") or summary["eligible"] != settings["repeat_count"] or settings["repeat_count"] < 5 or len(metrics["warmups"]) < 2:
                raise ValueError("Passed path lacks required CPU repeated evidence")
            checkpoint = json.loads(resolve(row["artifacts"]["checkpoint"]).read_text())
            if not checkpoint["doctor"]["available"] or not checkpoint["doctor"]["backend_probe"]["available"]:
                raise ValueError("Passed path lacks initialized CPU diagnostics")
            if metrics["memory"]["peak_bytes"] is None or metrics["supervision"].get("returncode") != 0 or metrics["supervision"].get("reason"):
                raise ValueError("Passed path lacks attributable memory/successful supervision")
            if metrics["runtime_context"]["threads"]["blas"] != 1 or metrics["runtime_context"]["threads"]["julia"] != 1:
                raise ValueError("Effective thread configuration differs from anchor")
            if not metrics["runtime_context"]["python_blas"]["providers"] or any(p["effective_threads"] != 1 for p in metrics["runtime_context"]["python_blas"]["providers"]):
                raise ValueError("Missing or mismatched effective Python BLAS threads")
            for project_file in metrics["runtime_context"].get("project_files", {}).values():
                if hashlib.sha256(resolve(project_file["path"]).read_bytes()).hexdigest() != project_file["sha256"]:
                    raise ValueError("Julia runtime project mismatch")
            if not all(w["passed"] and w["finite"] for w in metrics["warmups"]):
                raise ValueError("Warmups failed numerical gates")
        if not metrics.get("artifacts", {}).get("reference_arrays"):
            if row["status"] == "passed":
                raise ValueError("Passed CPU path lacks saved reference arrays")
            continue
        reference = np.load(resolve(row["artifacts"]["reference_arrays"]))
        basis, initial, expected = (reference[k] for k in ("basis", "input", "expected"))
        if len(basis) != s["basis_size"] or not np.array_equal(initial, _seeded_state(len(basis), settings["seed"])) or abs(np.linalg.norm(initial) - 1.) > 1e-14:
            raise ValueError("Input seed/norm/dimension mismatch")
        if hashlib.sha256(initial.tobytes()).hexdigest() != metrics["input"]["sha256"]:
            raise ValueError("Input checksum mismatch")
        register = Register.chain(s["N"], spacing=s["spacing"], C6=s["C6"])
        recomputed, kind = independent_reference(register, [s["omega"]]*s["N"], [s["delta"]]*s["N"], basis, initial,
                                                 reduced=not s["mode"].startswith("full_"), radius=s["blockade_radius"])
        if kind != metrics["reference"]["type"] or not np.allclose(recomputed, expected, rtol=1e-14, atol=1e-14):
            raise ValueError("Saved independent reference differs from replay")
        for repeat in scenario_repeats:
            actual = repeat["metrics"]
            if not repeat["artifacts"].get("output_array"):
                if actual["eligible"]:
                    raise ValueError("Eligible CPU repeat lacks saved output")
                continue
            output = np.load(resolve(repeat["artifacts"]["output_array"]))
            checked_gate = output_gate(output, expected, full=s["mode"].startswith("full_"), full_rtol=settings["full_rtol"], reduced_atol=settings["reduced_atol"])
            if any(actual.get(k) != v for k, v in checked_gate.items()):
                raise ValueError("Reported numerical gate differs from saved output")
            if actual["eligible"] != checked_gate["passed"] or actual["operation_count"] != settings["repeats"] or actual["time_per_operation_s"] != actual["runtime_seconds"] / settings["repeats"]:
                raise ValueError("Eligibility/operation-count/timing mismatch")
            checked += 1
            max_abs = max(max_abs, checked_gate["reference_error"] or 0.)
            max_relative = max(max_relative, checked_gate["reference_relative_error"] or 0.)
    if [r["row_id"] for r in measurements] != expected_repeat_ids:
        raise ValueError("Orphan/missing repeat rows")
    for stem in ("ablation_bench_results", "ablation_bench_results_suite"):
        with (directory / f"{stem}.csv").open() as handle:
            csv_rows = list(csv.DictReader(handle))
        if [(r["row_id"], r["status"]) for r in csv_rows] != [(r["row_id"], r["status"]) for r in suite["rows"]]:
            raise ValueError("CSV companion differs from JSON")
        if any(row["row_id"] not in (directory / f"{stem}.md").read_text() for row in suite["rows"]):
            raise ValueError("Markdown companion omits declared path")
    passed = {r["scenario_id"] for r in suite["rows"] if r["status"] == "passed"}
    expected = scenarios()
    required = {s["scenario_id"] for s in expected if s["required"]}
    cpu = {s["scenario_id"] for s in expected if s["mode"] in CPU_MODES and (s["N"] <= 12 or not s["mode"].startswith("full_"))}
    # Custom spacing/radius campaigns cannot silently close the anchor campaign.
    anchor = all(s in campaign["scenarios"] for s in expected)
    report = {"contract_audit_passed": True, "required_small_cpu_passed": anchor and required <= passed,
              "all_target_cpu_paths_passed": anchor and cpu <= passed, "scenario_count": len(suite["rows"]),
              "status_counts": suite["summary"]["status_counts"], "checked_cpu_outputs": checked,
              "max_absolute_error": max_abs, "max_relative_error": max_relative,
              "classification": "local_only; software/numerical audit, not independent governance review or physical validation"}
    coverage = read("coverage.json")
    if coverage["required_small_cpu_passed"] != (anchor and required <= passed) or coverage["all_target_cpu_paths_passed"] != (anchor and cpu <= passed):
        raise ValueError("Coverage companion mismatch")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    report = audit(args.directory)
    write_json(args.directory / "audit.json", report)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["all_target_cpu_paths_passed"] or args.allow_partial else 1)
