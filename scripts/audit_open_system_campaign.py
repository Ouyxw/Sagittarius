"""Audit retained local-noise references, density/seed gates, statistics and companions without Julia."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"sagittarius_py"))
from sagittarius import SimulationResult
from sagittarius.benchmark_measurement import write_json
from sagittarius.benchmarking import markdown_table, validate_benchmark_row
from sagittarius.benchmark_suite import load_benchmark_suite_artifact, _csv_rows, _markdown_summary
from sagittarius.open_system_benchmark import (COLUMNS, WORKLOAD_VERSION, SEEDS, convergence, coverage,
    density_metrics, density_passed, initial_state, make_row, observable_values, record_plan, reference,
    resource_exclusion, result_gate, scenarios, executed_options, basis)


def audit(directory):
    directory=Path(directory).resolve()
    def read(name): return json.loads((directory/name).read_text())
    campaign=read("campaign.json"); cfg=campaign["settings"]
    def resolve(value):
        path=Path(value)
        if path.is_absolute(): path=path.relative_to(campaign["output_dir"])
        target=(directory/path).resolve()
        if not target.is_relative_to(directory) or not target.is_file(): raise ValueError("Missing/outside retained evidence: "+str(target))
        return target
    frozen={k:campaign[k] for k in ("scenarios","settings","source_sha256")}
    if hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()!=campaign["config_sha256"] or campaign["workload_version"]!=WORKLOAD_VERSION: raise ValueError("Frozen configuration/workload mismatch")
    expected={s["scenario_id"]:s for s in scenarios(cfg["tier"])}
    if not campaign["scenarios"] or len({s["scenario_id"] for s in campaign["scenarios"]})!=len(campaign["scenarios"]) or any(expected.get(s["scenario_id"])!=s for s in campaign["scenarios"]): raise ValueError("Unexpected matrix/configuration")
    for name,digest in campaign["source_sha256"].items():
        if hashlib.sha256(resolve("source/"+name).read_bytes()).hexdigest()!=digest: raise ValueError("Frozen source hash mismatch")
    artifact=read("open_system_performance.json")
    if artifact.get("schema_version")!="benchmark-artifact/v1" or artifact.get("artifact_type")!="sagittarius.benchmark": raise ValueError("Benchmark artifact envelope mismatch")
    suite=load_benchmark_suite_artifact(directory/"open_system_performance_suite.json"); rows=suite["rows"]
    if artifact["timings"]!=rows or artifact["parameters"]!=campaign or [r["scenario_id"] for r in rows]!=[s["scenario_id"] for s in campaign["scenarios"]]: raise ValueError("Artifact/suite/campaign mismatch")
    raw=[]; checked=density_count=sensitivity_count=0; maximum_density_error=0.; maximum_trace=0.; minimum_eigenvalue=0.
    for s,row in zip(campaign["scenarios"],rows):
        validate_benchmark_row(row); state=row["metrics"]["state"]
        child=json.loads(resolve(row["artifacts"]["config"]).read_text())
        if child!={"scenario":s,"settings":cfg,"source_root":campaign["source_root"],"source_sha256":campaign["source_sha256"]}: raise ValueError("Child config mismatch")
        if row["artifacts"]["checkpoint"] and json.loads(resolve(row["artifacts"]["checkpoint"]).read_text())!=state: raise ValueError("Checkpoint mismatch")
        exclusion=resource_exclusion(s,cfg)
        if (row["status"]=="skipped") != bool(exclusion): raise ValueError("Resource exclusion mismatch")
        rebuilt=make_row(s,cfg,state,row["metrics"]["supervision"],exclusion); rebuilt["artifacts"]=row["artifacts"]
        if rebuilt!=row: raise ValueError("Statistics/count/membership/status mismatch")
        records=state.get("records",[])
        if row["status"]=="passed":
            if not state.get("complete") or [(r["phase"],r["repeat_index"],r["seed"]) for r in records]!=record_plan(s,cfg): raise ValueError("Missing declared calls")
            supervision=row["metrics"]["supervision"]
            if supervision["reason"] is not None or supervision["returncode"]!=0: raise ValueError("Unsuccessful worker passed")
            if state["memory"]["peak_bytes"] is None or state["memory_baseline"]["rss_bytes"] is None: raise ValueError("Missing attributable memory")
        ref=None
        if state.get("reference") and (directory/s["scenario_id"]/"reference.npz").exists():
            if state["reference"]!=read(s["scenario_id"]+"/reference.json"): raise ValueError("Reference report mismatch")
            ref=dict(np.load(directory/s["scenario_id"]/"reference.npz",allow_pickle=False)); replay,description=reference(s,cfg["reference_stability_atol"])
            if description["independent"]!=state["reference"]["independent"] or description["type"]!=state["reference"]["type"] or description["stable"]!=state["reference"]["stable"]: raise ValueError("Reference scope mismatch")
            if description["stability_error"] is not None and not np.isclose(description["stability_error"],state["reference"]["stability_error"],rtol=1e-4,atol=1e-11): raise ValueError("Reference stability mismatch")
            if any(ref[k].shape!=replay[k].shape or not np.allclose(ref[k],replay[k],rtol=1e-10,atol=1e-11) for k in replay): raise ValueError("Independent saved reference mismatch")
            if state["reference_values"]!=ref["values"].tolist(): raise ValueError("Reference values mismatch")
            if state["initial_state_sha256"]!=hashlib.sha256(initial_state(s).tobytes()).hexdigest(): raise ValueError("Initial state identity mismatch")
            if not state["doctor"]["available"] or not state["doctor"]["backend_probe"]["available"] or any(state["runtime_context"]["threads"][k]!=1 for k in ("julia","blas")): raise ValueError("Initialized doctor/effective threads mismatch")
            if set(state["runtime_files"])!={"Project.toml","Manifest.toml"}: raise ValueError("Missing runtime dependency identity")
            for name,digest in state["runtime_files"].items():
                if hashlib.sha256(resolve(s["scenario_id"]+"/"+name).read_bytes()).hexdigest()!=digest: raise ValueError("Runtime hash mismatch")
            density=state["density_validation"]
            if density.get("arrays"):
                saved=dict(np.load(resolve(density["arrays"]),allow_pickle=False)); matrices=saved["density"]
                expected_options={**executed_options(s,None,tighter=True),"use_mc":False,"store_trajectories":False}
                if density["options"]!=expected_options or density["basis"]!=basis(s): raise ValueError("Raw density configuration/basis mismatch")
                initial=initial_state(s)
                if not np.allclose(matrices[0],np.outer(initial,initial.conj()),rtol=0,atol=1e-12): raise ValueError("Raw density initial state mismatch")
                if matrices.shape!=(101,s["basis_size"],s["basis_size"]) or not np.isfinite(matrices).all() or not np.allclose(saved["t"],ref["t"],rtol=0,atol=1e-14): raise ValueError("Raw density shape/grid mismatch")
                metrics=density_metrics(matrices)
                if any(not np.isclose(value,density["metrics"][key],rtol=1e-5,atol=1e-12) for key,value in metrics.items()) or not density_passed(metrics): raise ValueError("Trace/positivity/hermiticity mismatch")
                error=float(np.max(abs(matrices-replay["density"]))) if "density" in replay else None
                if error is not None and (not np.isclose(error,density["max_abs_density_error"],rtol=1e-5,atol=1e-11) or error>cfg["accuracy_atol"]): raise ValueError("Density/coherence reference mismatch")
                if not state["reference"]["independent"] and not np.allclose(observable_values(s,np.diagonal(matrices,axis1=1,axis2=2).real.T),ref["values"],rtol=0,atol=1e-12): raise ValueError("Tighter density reference values mismatch")
                maximum_density_error=max(maximum_density_error,error or 0.); maximum_trace=max(maximum_trace,metrics["trace_error"]); minimum_eigenvalue=min(minimum_eigenvalue,metrics["min_density_eigenvalue"]); density_count+=1
            sensitivity=state.get("sensitivity")
            if sensitivity:
                tight=SimulationResult.load(str(resolve(sensitivity["result_artifact"])))
                if tight.manifest!=json.loads(resolve(sensitivity["run_manifest"]).read_text()): raise ValueError("Sensitivity manifest mismatch")
                if result_gate(tight,s,cfg,ref,seed=sensitivity["seed"],tighter=True)!=sensitivity["gate"]: raise ValueError("Sensitivity gate mismatch")
                if not state["reference"]["independent"] and s["path"]=="mcwf" and [tight.data[d["name"]] for d in s["declarations"]]!=ref["values"].tolist(): raise ValueError("Sensitivity reference values mismatch")
                sensitivity_count+=1
        for record in records:
            raw.append({"scenario_id":s["scenario_id"],**record})
            if record["row_id"]!=f"{s['scenario_id']}-{record['phase']}-{record['repeat_index']}" or record["operation_count"]!=1: raise ValueError("Call identity mismatch")
            if "runtime_seconds" in record and (not np.isfinite(record["runtime_seconds"]) or record["runtime_seconds"]<=0): raise ValueError("Invalid timing")
            if record["artifacts"].get("result_artifact"):
                if resolve(record["artifacts"]["reference_arrays"]) != directory/s["scenario_id"]/"reference.npz" or resolve(record["artifacts"]["reference_report"]) != directory/s["scenario_id"]/"reference.json": raise ValueError("Reference link mismatch")
                path=resolve(record["artifacts"]["result_artifact"]); result=SimulationResult.load(str(path)); envelope=json.loads(path.read_text())
                if result.manifest!=json.loads(resolve(record["artifacts"]["run_manifest"]).read_text()): raise ValueError("Standalone manifest mismatch")
                names=[d["name"] for d in s["declarations"]]
                if envelope["shared_result"]!=result.to_shared_result() or list(envelope["data"])!=names+["t"]: raise ValueError("Saved shared output/order mismatch")
                if ref is not None and "gate" in record:
                    gate=result_gate(result,s,cfg,ref,seed=record["seed"])
                    if gate!=record["gate"] or gate["passed"]!=record["eligible"] or result.diagnostics["simulation"]!=record["effective_solver"]: raise ValueError("Saved value/effective gate mismatch")
                    if s["path"]=="mcwf":
                        if record["requested_trajectories"]!=s["trajectories"] or record["completed_trajectories"]!=s["trajectories"] or record["trajectories_per_second"]!=s["trajectories"]/record["runtime_seconds"]: raise ValueError("Trajectory count/throughput mismatch")
                    elif record["requested_trajectories"] is not None or record["completed_trajectories"] is not None: raise ValueError("Lindblad trajectory count must be unavailable")
                    if record["phase"]=="statistical" and record["values"]!=[result.data[name] for name in names]: raise ValueError("Seed convergence values mismatch")
                elif record["eligible"]: raise ValueError("Eligible call lacks reference/gate")
                checked+=1
            elif record["eligible"]: raise ValueError("Eligible call lacks output")
    if artifact["run_manifests"] != [{"label":r["row_id"],"path":r["artifacts"]["run_manifest"]} for r in raw if r["artifacts"].get("run_manifest")]: raise ValueError("Aggregate manifest links mismatch")
    if resolve(artifact["artifacts"]["csv"]) != directory/"open_system_performance.csv" or resolve(artifact["artifacts"]["markdown"]) != directory/"open_system_performance.md": raise ValueError("Aggregate companion links mismatch")
    if read("open_system_repeats.json")!=raw or read("progress.json")!=rows or read("coverage.json")!=coverage(rows): raise ValueError("Raw/coverage/progress mismatch")
    convergence_report=convergence(rows,cfg)
    if read("convergence.json")!=convergence_report: raise ValueError("Convergence report mismatch")
    limit=csv.field_size_limit(); csv.field_size_limit(sys.maxsize)
    try:
        with (directory/"open_system_performance.csv").open(newline="") as f:
            if list(csv.DictReader(f))!=[{k:str(row[k]) if row[k] is not None else "" for k in COLUMNS} for row in rows]: raise ValueError("Performance CSV mismatch")
        table=markdown_table(rows,columns=COLUMNS)
        if (directory/"open_system_performance.md").read_text()!=table+"\n" or artifact["markdown_table"]!=table: raise ValueError("Performance Markdown mismatch")
        with (directory/"open_system_performance_suite.csv").open(newline="") as f:
            if list(csv.DictReader(f))!=_csv_rows(rows): raise ValueError("Suite CSV mismatch")
        if (directory/"open_system_performance_suite.md").read_text()!=_markdown_summary(suite): raise ValueError("Suite Markdown mismatch")
    finally: csv.field_size_limit(limit)
    coverage_report=coverage(rows)
    acceptance=coverage_report["all_declared_rows_accounted"] and coverage_report["all_attempted_rows_passed"] and coverage_report["reduced_n20_mcwf_counts_passed"] and coverage_report["small_reference_group_passed"] and coverage_report["analytic_control_group_passed"] and convergence_report["all_available_comparisons_passed"]
    return {"contract_audit_passed":True,**coverage_report,"bounded_campaign_accepted":acceptance,
        "scenario_count":len(rows),"checked_results":checked,"density_controls":density_count,"sensitivity_controls":sensitivity_count,
        "maximum_density_error":maximum_density_error,"maximum_trace_error":maximum_trace,"minimum_density_eigenvalue":minimum_eigenvalue,
        "cross_count_comparisons":len(convergence_report["cross_count_comparisons"]),"convergence_passed":convergence_report["all_available_comparisons_passed"],
        "eligible_measured_count":sum(r["eligible"] for r in raw if r["phase"]=="measured"),"status_counts":suite["summary"]["status_counts"]}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("directory",type=Path); parser.add_argument("--allow-partial",action="store_true")
    args=parser.parse_args(); report=audit(args.directory); write_json(args.directory/"audit.json",report); print(json.dumps(report,indent=2))
    raise SystemExit(0 if report["bounded_campaign_accepted"] or args.allow_partial else 1)
