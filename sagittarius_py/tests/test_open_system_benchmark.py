"""Frozen local-noise matrix, numerical references, supervision and evidence."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest
from sagittarius import SolverConfig
from sagittarius.open_system_benchmark import (COUNTS, SEEDS, SIZES, basis, benchmark_open_system, bound,
    density_metrics, density_passed, dimension, make_row, record_plan, reference,
    resource_exclusion, scenario, scenarios)
SPEC=importlib.util.spec_from_file_location("audit_open_system_campaign",Path(__file__).resolve().parents[2]/"scripts/audit_open_system_campaign.py")
AUDIT=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(AUDIT)
CFG={"warmups":2,"repeat_count":5,"accuracy_atol":1e-6,"reference_stability_atol":1e-9,"stochastic_alpha":1e-6,
    "timeout_seconds":1800.,"memory_limit_bytes":4096*1024**2,"max_density_dimension":256,"max_state_dimension":1024}


def test_frozen_matrix_and_resource_boundaries():
    matrix=scenarios()
    assert len(matrix)==len({s["scenario_id"] for s in matrix})==99
    assert len(scenarios("performance"))==89 and len(scenarios("correctness"))==10
    for n in SIZES:
        for reduced in (False,True):
            group=[s for s in matrix if s["N"]==n and s["basis_mode"]==("reduced" if reduced else "full") and s["kind"]=="performance" and s["rate_form"]=="scalar" and s["fixture"]=="chain" and not s["store_trajectories"]]
            assert len(group)==4 and {s["trajectories"] for s in group if s["path"]=="mcwf"}==set(COUNTS)
    for s in matrix:
        SolverConfig(**s["solver"])
        assert s["solver"]["saveat"][0]==0 and s["solver"]["saveat"][-1]==s["duration"]
    assert dimension(20,True)==907
    assert basis(scenario(8))==[b for b in range(256) if not (b & (b<<1)) and not (b & (b<<2)) and not (b & (b<<3))]
    assert scenario(20,reduced=False)["resource_estimate"]["density_storage_bytes"]==16*1024**4
    assert resource_exclusion(scenario(20),CFG)
    assert resource_exclusion(scenario(20,"mcwf",reduced=False),CFG)
    assert resource_exclusion(scenario(20,"mcwf"),CFG) is None


def test_analytic_decay_and_coherence_density():
    ref,_=reference(scenario(1,reduced=False,fixture="decay",model="decay"))
    np.testing.assert_allclose(ref["values"][0],np.exp(-.5*ref["t"]))
    assert density_passed(density_metrics(ref["density"]))
    ref,_=reference(scenario(1,reduced=False,fixture="coherence",model="dephasing",kind="correctness"))
    np.testing.assert_allclose(ref["density"][:,0,1],.5*np.exp(-.125/2*ref["t"]))
    np.testing.assert_allclose(ref["values"],.5)
    assert not density_passed(density_metrics(np.array([[[1.1,0],[0,-.1]]])))
    with pytest.raises(AssertionError): reference(scenario(2),stability_atol=1e-30)


@pytest.mark.parametrize("reduced",[False,True])
@pytest.mark.parametrize("model",["decay","dephasing","combined"])
def test_independent_per_atom_dense_reference(reduced,model):
    s=scenario(2,reduced=reduced,model=model,per_atom=True)
    ref,meta=reference(s)
    assert ref["density"].shape==(101,s["basis_size"],s["basis_size"])
    assert meta["independent"] and meta["stable"] and meta["stability_error"]<1e-9
    assert density_passed(density_metrics(ref["density"]))


def test_large_reference_gap_and_uncertainty_rule():
    s=scenario(20,"mcwf"); ref,meta=reference(s)
    assert set(ref)=={"t"} and meta["independent"] is False
    assert len(record_plan(s,CFG))==13
    assert [seed for phase,_,seed in record_plan(s,CFG) if phase=="statistical"]==list(SEEDS)
    np.testing.assert_allclose(bound(s,CFG,count=1000),bound(s,CFG,count=100)/np.sqrt(10))
    ref,meta=reference(scenario(20,"mcwf",fixture="decay",model="decay",kind="correctness"))
    assert meta["independent"] and ref["values"][0,0]==1. and ref["values"][-1,0]==1.


def fake_state(s,cfg=CFG):
    ref,_=reference(s)
    return {"complete":True,"reference_values":ref["values"].tolist(),"reference":{"independent":True},
        "records":[{"row_id":f"test-{phase}-{i}","phase":phase,"repeat_index":i,"seed":seed,"runtime_seconds":float(i+1),"trajectories_per_second":s["trajectories"]/(i+1) if s["trajectories"] else None,
            "eligible":True,"gate":{"passed":True,"max_abs_error":0.},**({"values":ref["values"].tolist()} if phase=="statistical" else {})} for phase,i,seed in record_plan(s,cfg)]}


def test_runtime_throughput_and_membership():
    s=scenario(1,"mcwf"); state=fake_state(s)
    records=[r for r in state["records"] if r["phase"]=="measured"]
    records[-1].update(runtime_seconds=100.,trajectories_per_second=5.)
    row=make_row(s,CFG,state,{})
    assert row["status"]=="passed" and row["median_s"]==3. and row["max_s"]==100.
    assert row["throughput_median"]==pytest.approx(500/3)
    assert row["metrics"]["convergence"]["pooled_trajectories"]==2500
    records[-1]["eligible"]=False; records[-1]["gate"]["passed"]=False
    row=make_row(s,CFG,state,{})
    assert row["status"]=="failed" and row["eligible"]==4 and row["max_s"]==4.
    assert row["metrics"]["statistics"]["input_row_ids"]==[r["row_id"] for r in records[:-1]]


@pytest.mark.parametrize("reason,status",[("timeout","incomplete"),("interrupted","incomplete"),("memory","failed"),("unexpected","failed")])
def test_supervisor_retains_partial_data(reason,status):
    s=scenario(1); row=make_row(s,CFG,fake_state(s),{"reason":reason})
    assert row["status"]==status and row["eligible"]==5
    assert row["failure"]["limits"]["max_density_dimension"]==256


def test_resource_campaign_backend_free_audit(tmp_path):
    paths=benchmark_open_system(tmp_path,scenario_ids=[scenario(20)["scenario_id"]])
    assert paths["artifact"]["timings"][0]["status"]=="skipped"
    assert AUDIT.audit(tmp_path)["checked_results"]==0
    with pytest.raises(FileExistsError): benchmark_open_system(tmp_path)


@pytest.mark.parametrize("options",[{"warmups":True},{"repeat_count":0},{"max_density_dimension":0},{"max_density_dimension":1.5},{"max_state_dimension":0},{"memory_limit_mb":-1},
    {"accuracy_atol":float("nan")},{"stochastic_alpha":1.},{"scenario_ids":[]},{"scenario_ids":["unknown"]},{"tier":"invalid"}])
def test_invalid_options_before_output(tmp_path,options):
    with pytest.raises(ValueError): benchmark_open_system(tmp_path/"new",**options)
    assert not (tmp_path/"new").exists()


@pytest.mark.requires_julia_backend
def test_real_small_density_storage_audit_corruption(tmp_path):
    ids=[scenario(1,reduced=False,fixture="coherence",model="dephasing",kind="correctness")["scenario_id"],scenario(2,"mcwf",store=True)["scenario_id"]]
    paths=benchmark_open_system(tmp_path,scenario_ids=ids)
    assert all(r["status"]=="passed" for r in paths["artifact"]["timings"]),[r["failure"] for r in paths["artifact"]["timings"]]
    report=AUDIT.audit(tmp_path)
    assert report["checked_results"]==14 and report["density_controls"]==2
    import sagittarius.runtime as runtime
    original=runtime.get_julia
    try:
        runtime.get_julia=lambda: (_ for _ in ()).throw(AssertionError("audit initialized Julia"))
        assert AUDIT.audit(tmp_path)==report
    finally: runtime.get_julia=original
    for name,mutate,match in [
        ("open_system_performance.csv",lambda t:t.replace("passed","failed",1),"CSV mismatch"),
        ("open_system_performance.md",lambda t:t+"bad","Markdown mismatch"),
        ("convergence.json",lambda t:t.replace('"pooled_trajectories": 2500','"pooled_trajectories": 1'),"Convergence report mismatch"),
        (ids[1]+"/measured-0.manifest.json",lambda t:t.replace('"seed": 20260811','"seed": 0'),"Standalone manifest"),
    ]:
        p=tmp_path/name; before=p.read_text(); p.write_text(mutate(before))
        with pytest.raises((ValueError,AssertionError),match=match): AUDIT.audit(tmp_path)
        p.write_text(before)
    p=tmp_path/ids[0]/"density-validation.npz"; before=p.read_bytes(); saved=dict(np.load(p)); saved["density"][:,0,1]=0
    np.savez_compressed(p,**saved)
    with pytest.raises((ValueError,AssertionError),match="Trace/positivity/hermiticity|Density/coherence|Raw density initial state"): AUDIT.audit(tmp_path)
    p.write_bytes(before)


def test_missing_seeds_and_failed_pooled_bounds_do_not_pass():
    s=scenario(1,"mcwf"); state=fake_state(s)
    state["records"]=state["records"][:-1]
    assert make_row(s,CFG,state,{})["status"]=="incomplete"
    state=fake_state(s)
    for r in state["records"]:
        if r["phase"]=="statistical": r["values"]=(np.asarray(r["values"])+1).tolist()
    assert make_row(s,CFG,state,{})["status"]=="failed"
    state=fake_state(s); state["records"][-1].pop("gate")
    state["records"][-1]["eligible"]=False
    assert make_row(s,CFG,state,{})["status"]=="incomplete"
