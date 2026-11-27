"""Accept frozen open-system evidence including direct retained Lindblad/MCWF comparisons.

Measurement sources stay immutable. This review layer has its own retained
source hashes and only reads saved outputs; it performs no backend execution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_open_system_campaign import audit
from sagittarius import SimulationResult
from sagittarius.benchmark_measurement import write_json
from sagittarius.open_system_benchmark import SEEDS, bound, observable_values


def physical_key(s):
    """Match physical/solver/output inputs; retention/count/seed are separate axes."""
    fields=("N","coordinates","C6","blockade_radius","omega","delta","duration","basis_mode","basis_size","initial_state","precision","declarations","units")
    values={k:s[k] for k in fields}
    values["solver"]={k:s["solver"][k] for k in ("method","adaptive","dt","reltol","abstol","saveat","gamma","gamma_phi")}
    return json.dumps(values,sort_keys=True)


def compare(values,reference,s,cfg,count):
    values=np.asarray(values,float);reference=np.asarray(reference,float)
    expected=(len(s["declarations"]),s["output_count"])
    if values.shape!=expected or reference.shape!=expected or not np.isfinite(values).all() or not np.isfinite(reference).all(): raise ValueError("Invalid cross-path arrays")
    errors=np.max(abs(values-reference),axis=1)
    bounds=bound(s,cfg,count=count)[:,0]+2*cfg["accuracy_atol"]
    return {"passed":bool(np.all(errors<=bounds)),"max_error_per_observable":errors.tolist(),"bounds":bounds.tolist()}


def cross_path(directory,rows,campaign):
    directory=Path(directory).resolve();cfg=campaign["settings"]
    def resolve(value):
        p=Path(value)
        if p.is_absolute():p=p.relative_to(campaign["output_dir"])
        target=(directory/p).resolve()
        if not target.is_relative_to(directory) or not target.is_file():raise ValueError("Missing/outside cross-path evidence: "+str(target))
        return target
    def values(link,s):
        result=SimulationResult.load(str(resolve(link)))
        if not np.allclose(result.data["t"],s["solver"]["saveat"],rtol=0,atol=1e-14):raise ValueError("Cross-path time grid mismatch")
        return np.array([result.data[d["name"]] for d in s["declarations"]],float)
    lindblad={physical_key(r["problem"]):r for r in rows if r["problem"]["path"]=="lindblad"}
    reports=[];reference_cache={}
    for row in rows:
        s=row["problem"];state=row["metrics"]["state"]
        if s["path"]!="mcwf" or row["status"]!="passed":continue
        key=physical_key(s);lb=lindblad.get(key);reference=None;links=[];kind=None
        if lb and lb["status"]=="passed":
            if key not in reference_cache:
                records=[r for r in lb["metrics"]["state"]["records"] if r["phase"]=="measured" and r["eligible"]]
                if not records:raise ValueError("Passing Lindblad row lacks measured reference")
                refs=[values(r["artifacts"]["result_artifact"],s) for r in records]
                if any(not np.allclose(refs[0],v,rtol=0,atol=1e-12) for v in refs[1:]):raise ValueError("Deterministic Lindblad repeats differ")
                reference_cache[key]=(refs[0],[r["artifacts"]["result_artifact"] for r in records])
            reference,links=reference_cache[key];kind="matching retained measured Lindblad (no statistical pooling benefit)"
        elif state.get("density_validation",{}).get("arrays"):
            link=state["density_validation"]["arrays"]
            arrays=dict(np.load(resolve(link),allow_pickle=False))
            if not np.allclose(arrays["t"],s["solver"]["saveat"],rtol=0,atol=1e-14):raise ValueError("Raw Lindblad grid mismatch")
            reference=observable_values(s,np.diagonal(arrays["density"],axis1=1,axis2=2).real.T)
            links=[link];kind="worker retained tighter raw Lindblad; separate untimed control"
        if reference is None:
            reports.append({"scenario_id":s["scenario_id"],"available":False,"passed":None,
                "reason":lb["failure"]["message"] if lb and lb.get("failure") else "No matching retained Lindblad path; analytic special-case gate remains separate",
                "lindblad_scenario":lb["scenario_id"] if lb else None,"reference_scope":s["reference_scope"]})
            continue
        checks=[];statistical=[]
        for record in state["records"]:
            v=values(record["artifacts"]["result_artifact"],s)
            checks.append({"row_id":record["row_id"],"phase":record["phase"],"seed":record["seed"],
                **compare(v,reference,s,cfg,s["trajectories"])})
            if record["phase"]=="statistical":statistical.append((record["seed"],v))
        if [seed for seed,_ in statistical]!=list(SEEDS):raise ValueError("Missing cross-path statistical seeds")
        if state.get("sensitivity"):
            checks.append({"row_id":s["scenario_id"]+"-sensitivity","phase":"sensitivity","seed":state["sensitivity"]["seed"],
                **compare(values(state["sensitivity"]["result_artifact"],s),reference,s,cfg,s["trajectories"])})
        pooled=compare(np.array([v for _,v in statistical]).mean(axis=0),reference,s,cfg,len(SEEDS)*s["trajectories"])
        pooled.update(input_row_ids=[r["row_id"] for r in state["records"] if r["phase"]=="statistical"],seeds=list(SEEDS),trajectories_per_seed=s["trajectories"],pooled_trajectories=len(SEEDS)*s["trajectories"])
        reports.append({"scenario_id":s["scenario_id"],"available":True,"reference_type":kind,"reference_links":links,
            "checks":checks,"pooled_five_seed_check":pooled,"passed":all(c["passed"] for c in checks) and pooled["passed"]})
    available=[r for r in reports if r["available"]]
    return {"all_available_comparisons_passed":all(r["passed"] for r in available),"available_configurations":len(available),
        "unavailable_configurations":len(reports)-len(available),"individual_comparisons":sum(len(r["checks"]) for r in available),
        "pooled_comparisons":len(available),"reports":reports,
        "rule":"Frozen simultaneous Hoeffding bounds (32 slots include direct cross-path individual/tighter/pooled checks) plus two frozen deterministic accuracy floors; no per-seed monotonic requirement",
        "limitations":"Lindblad/MCWF same-model numerical consistency; no independent large interacting oracle or physical validation; resource gaps stay explicit"}


def accept(directory):
    directory=Path(directory).resolve();base=audit(directory)
    campaign=json.loads((directory/"campaign.json").read_text())
    rows=json.loads((directory/"open_system_performance.json").read_text())["timings"]
    cross=cross_path(directory,rows,campaign)
    sources={str(Path(__file__).resolve().relative_to(Path(__file__).resolve().parents[1])):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    tests=Path(__file__).resolve().parents[1]/"sagittarius_py/tests/test_open_system_cross_path_audit.py"
    if tests.exists():sources[str(tests.relative_to(Path(__file__).resolve().parents[1]))]=hashlib.sha256(tests.read_bytes()).hexdigest()
    report={"accepted":base["bounded_campaign_accepted"] and cross["all_available_comparisons_passed"],
        "measurement_audit":base,"lindblad_mcwf":cross,"review_source_sha256":sources,
        "review_scope":"Post-measurement saved-output review; measurement configuration/sources/raw outputs remain unchanged"}
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("directory",type=Path)
    args=parser.parse_args();report=accept(args.directory)
    write_json(args.directory/"audit.json",report["measurement_audit"])
    write_json(args.directory/"lindblad_mcwf.json",report["lindblad_mcwf"])
    write_json(args.directory/"acceptance.json",report)
    print(json.dumps({"accepted":report["accepted"],"measurement_audit":report["measurement_audit"],
        "cross_path_available":report["lindblad_mcwf"]["available_configurations"],"cross_path_unavailable":report["lindblad_mcwf"]["unavailable_configurations"],
        "cross_path_individual":report["lindblad_mcwf"]["individual_comparisons"]},indent=2))
    raise SystemExit(0 if report["accepted"] else 1)
