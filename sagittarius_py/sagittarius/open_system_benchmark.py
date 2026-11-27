"""Plan-v2 bounded local-noise CPU Lindblad/MCWF measurement and evidence."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time
from datetime import datetime, timezone
from functools import lru_cache
import numpy as np
from .benchmark_measurement import linux_process_memory, runtime_summary, supervise, write_json
from .benchmark_failures import benchmark_failure_context
from .benchmarking import current_memory_usage, make_benchmark_row, write_benchmark_artifacts
from .benchmark_suite import write_benchmark_suite_artifact
from .observable_benchmark import basis, hamiltonian, occupation_values, ordered_write

WORKLOAD_VERSION = "open-system-performance/v1"
FAMILY, TIER = "open_system_dynamics", "correctness"
SIZES = (1, 2, 4, 6, 8, 10, 12, 16, 20)
SEEDS = (20260811, 20260812, 20260813, 20260814, 20260815)
COUNTS = (100, 500, 1000)
THREAD_KEYS = ("JULIA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
TIMER = "Simulation.run including validation, construction, collection and manifest; reset/reference/density checks/serialization/convergence excluded"
STATISTICAL_RULE = "Simultaneous two-sided Hoeffding absolute bounds alpha=1e-6 by default, union over frozen full matrix, five seeds, counts, observables and 101 times; independent seeds pooled separately; no monotonic per-seed error requirement"
COLUMNS = ["scenario_id", "status", "kind", "N", "basis_size", "basis_mode", "path", "model", "rate_form", "gamma", "gamma_phi", "timing_seed", "execution_mode", "trajectories", "completed_trajectories_per_repeat", "store_trajectories", "eligible", "median_s", "min_s", "max_s", "p25_s", "p75_s", "throughput_median", "max_abs_error", "reference_gate", "convergence_gate", "reference_scope", "peak_bytes", "raw_records"]


def dimension(n, reduced):
    # Independent counting of no occupations within three sites on the reduced chain.
    if not reduced: return 2**n
    counts = [1]
    for i in range(1, n+1): counts.append(counts[-1] + counts[max(0, i-4)])
    return counts[-1]


def scenario(n, path="lindblad", *, reduced=True, model="combined", fixture="chain", per_atom=False, trajectories=500, kind="performance", store=False):
    radius = 12.4 if reduced else 0.
    ds = [{"name": f"pop{i}", "declaration": {"type": "rydberg_population", "atom": i}} for i in sorted({0, n//2, n-1})]
    ds += [{"name": "total", "declaration": {"type": "total_rydberg_population"}}]
    if n > 1: ds += [{"name": "pair", "declaration": {"type": "pair_correlation", "atoms": [0, n-1]}}]
    gamma = .5 if model in ("decay", "combined") else 0.
    phi = .125 if model in ("dephasing", "combined") else 0.
    if per_atom:
        gamma, phi = [gamma * (1 + i/2) for i in range(n)], [phi * (1 + i/3) for i in range(n)]
    duration = 2. if fixture != "chain" else .05
    d = dimension(n, reduced)
    s = {"N": n, "kind": kind, "path": path, "fixture": fixture, "model": model,
        "coordinates": [[4.*i, 0., 0.] for i in range(n)], "C6": 100. if fixture == "chain" else 0.,
        "omega": 2*math.pi if fixture in ("chain", "driven") else 0., "delta": .3 if fixture == "chain" else 0.,
        "duration": duration, "blockade_radius": radius, "basis_mode": "reduced" if reduced else "full",
        "basis_size": d, "full_dim": 2**n, "precision": "complex128", "declarations": ds, "output_count": 101,
        "trajectories": trajectories if path == "mcwf" else None, "store_trajectories": store,
        "rate_form": "per_atom" if per_atom else "scalar", "required": True,
        "initial_state": "ground" if fixture in ("chain", "driven") else "coherent" if fixture == "coherence" else "excited_endpoints",
        "atom_order": "Python atom i is LSB bit i; Julia i+1; ascending basis integers",
        "units": {"length": "um", "time": "us", "angular_frequency": "rad/us", "rates": "1/us", "C6": "rad*um^6/us"},
        "execution_mode": "EnsembleSerial (explicit fixed seed)" if path == "mcwf" else "deterministic CPU",
        "storage_policy": "observable series; raw trajectories retained" if store else "observable series; store_trajectories=False (internal solver histories/ensemble outputs still allocated)"}
    s["solver"] = {"method": "Tsit5", "adaptive": True, "dt": None, "reltol": 1e-8, "abstol": 1e-10,
        "blockade_radius": radius, "saveat": np.linspace(0., duration, 101).tolist(), "gamma": gamma, "gamma_phi": phi,
        "use_mc": path == "mcwf", "n_trajectories": trajectories if path == "mcwf" else 100,
        "store_trajectories": store, "seed": SEEDS[0] if path == "mcwf" else None}
    s["scenario_id"] = f"{kind}-n{n}-{s['basis_mode']}-{fixture}-{model}-{s['rate_form']}-{path}" + (f"-k{trajectories}" if path == "mcwf" else "") + ("-raw" if store else "")
    s["reference_scope"] = "analytic local-noise density" if fixture in ("decay", "coherence") else "independent dense master equation" if d <= 64 else "tighter same-method sensitivity and multi-seed consistency; independent interacting reference unavailable"
    # Include retained solver history, adaptive/dense interpolation workspaces,
    # sparse jumps/mappings, output and JIT. Full dimension is not allocated here.
    s["resource_estimate"] = {"density_storage_bytes": 16*d*d if path == "lindblad" else None,
        "jit_reserve_bytes": 2*1024**3, "nominal_readout_manifest_bytes": 384*2**n if path == "mcwf" else 64*d, "operator_mapping_bytes": d*n*512,
        "state_history_workspace_bytes": 16*(d*d if path == "lindblad" else d)*(101+64),
        "observable_ensemble_bytes": len(ds)*101*(trajectories if path == "mcwf" else 1)*32*(3 if store else 1),
        "independent_density_reference_bytes": 16*d*d*101*3 if d <= 64 else 0}
    s["estimated_peak_bytes"] = sum(v for k,v in s["resource_estimate"].items() if v is not None and k != "density_storage_bytes")
    return s


def scenarios(tier="all"):
    if tier not in ("all", "performance", "correctness"): raise ValueError("Unknown tier")
    rows = []
    if tier in ("all", "performance"):
        for n in SIZES:
            for reduced in (False, True):
                rows.append(scenario(n, reduced=reduced))
                rows += [scenario(n, "mcwf", reduced=reduced, trajectories=k) for k in COUNTS]
        for model in ("decay", "dephasing"):
            rows += [scenario(1, path, reduced=False, model=model, fixture="decay" if model == "decay" else "driven") for path in ("lindblad", "mcwf")]
        for reduced in (False, True):
            for model in ("decay", "dephasing", "combined"):
                rows += [scenario(2, path, reduced=reduced, model=model, per_atom=True) for path in ("lindblad", "mcwf")]
        rows += [scenario(2, "mcwf", reduced=True, store=True)]
    if tier in ("all", "correctness"):
        rows += [scenario(n, "mcwf", model="decay", fixture="decay", kind="correctness", trajectories=500) for n in SIZES]
        rows += [scenario(1, reduced=False, model="dephasing", fixture="coherence", kind="correctness")]
    return rows


def resource_exclusion(s, cfg):
    if s["estimated_peak_bytes"] > cfg["memory_limit_bytes"]: return "Construction/history/reference estimate exceeds frozen memory budget"
    if s["path"] == "mcwf" and s["basis_size"] > cfg["max_state_dimension"]: return "State dimension exceeds frozen MCWF history/collection time budget"
    if s["path"] == "lindblad" and s["basis_size"] > cfg["max_density_dimension"]: return "Density dimension exceeds frozen validation/time budget (raw histories and 101 eigendecompositions)"
    return None


def initial_state(s):
    psi = np.zeros(s["basis_size"], dtype=complex)
    if s["initial_state"] == "ground": psi[0] = 1
    elif s["initial_state"] == "coherent": psi[:2] = 1/math.sqrt(2)
    else:
        target = 1 | (1 << (s["N"]-1))
        represented = basis(s)
        if target not in represented: target = 1
        psi[represented.index(target)] = 1
    return psi


def rates(s, key):
    a = np.asarray(s["solver"][key], dtype=float)
    return np.full(s["N"], a.item()) if a.ndim == 0 else a


def observable_values(s, probabilities):
    return np.array([occupation_values(probabilities, basis(s), d["declaration"]) for d in s["declarations"]])


def jumps(s):
    b = basis(s); index = {v:i for i,v in enumerate(b)}
    result = []
    for atom in range(s["N"]):
        for key in ("gamma", "gamma_phi"):
            rate = rates(s, key)[atom]
            if not rate: continue
            j = np.zeros((len(b), len(b)), complex)
            for col, bit in enumerate(b):
                if bit & (1 << atom): j[index[bit if key == "gamma_phi" else bit ^ (1 << atom)], col] = math.sqrt(rate)
            result.append(j)
    return result


def density_metrics(states):
    return {"trace_error": float(max(abs(np.trace(r)-1) for r in states)),
        "hermiticity_error": float(max(np.max(abs(r-r.conj().T)) for r in states)),
        "min_density_eigenvalue": float(min(np.linalg.eigvalsh((r+r.conj().T)/2).min() for r in states))}


def density_passed(metrics):
    return metrics["trace_error"] <= 1e-6 and metrics["hermiticity_error"] <= 1e-6 and metrics["min_density_eigenvalue"] >= -1e-7


def reference(s, stability_atol=1e-9):
    t = np.array(s["solver"]["saveat"]); d = s["basis_size"]
    if s["fixture"] in ("chain", "driven") and d > 64:
        return {"t": t}, {"type": s["reference_scope"], "independent": False, "stable": None, "stability_error": None}
    psi = initial_state(s)
    if s["fixture"] in ("decay", "coherence"):
        if s["fixture"] == "coherence":
            rho = np.zeros((len(t), d, d), complex)
            rho[:,0,0] = 1-.5*np.exp(-rates(s,"gamma")[0]*t)
            rho[:,1,1] = .5*np.exp(-rates(s,"gamma")[0]*t)
            rho[:,0,1] = rho[:,1,0] = .5*np.exp(-.5*(rates(s,"gamma")[0]+rates(s,"gamma_phi")[0])*t)
            values = observable_values(s, np.diagonal(rho, axis1=1, axis2=2).real.T)
        else:
            target = basis(s)[int(np.argmax(abs(psi)))]
            excited = [i for i in range(s["N"]) if target & (1 << i)]
            surv = np.exp(-rates(s,"gamma")[:,None]*t)
            values=[]
            for item in s["declarations"]:
                decl=item["declaration"]; typ=decl["type"]
                if typ == "rydberg_population": value=surv[decl["atom"]] if decl["atom"] in excited else np.zeros(len(t))
                elif typ == "total_rydberg_population": value=sum((surv[i] for i in excited), np.zeros(len(t)))
                else: value=np.prod([surv[i] if i in excited else np.zeros(len(t)) for i in decl["atoms"]], axis=0)
                values.append(value)
            arrays={"t":t, "values":np.array(values)}
            if d <= 64:
                rho=np.zeros((len(t),d,d),complex)
                for k,bit in enumerate(basis(s)):
                    if bit & ~target: continue
                    rho[:,k,k]=np.prod([surv[i] if bit & (1<<i) else 1-surv[i] for i in excited],axis=0)
                arrays["density"]=rho
            return arrays, {"type": "analytic independent bitstring population decay", "independent": True, "stable": True, "stability_error": 0.}
        stability=0.
    else:
        from scipy.integrate import solve_ivp
        h=hamiltonian(s).toarray(); js=jumps(s); products=[j.conj().T@j for j in js]
        def rhs(time, flat):
            r=flat.reshape(d,d)
            out=-1j*(h@r-r@h)
            for j, product in zip(js,products): out += j@r@j.conj().T-.5*(product@r+r@product)
            return out.ravel()
        def integrate(rtol,atol):
            sol=solve_ivp(rhs,(0.,s["duration"]),np.outer(psi,psi.conj()).ravel(),t_eval=t,method="DOP853",rtol=rtol,atol=atol)
            if not sol.success: raise RuntimeError("Independent density reference failed")
            return sol.y.T.reshape(len(t),d,d)
        rho=integrate(1e-11,1e-13); control=integrate(1e-12,1e-14)
        stability=float(np.max(abs(rho-control)))
        values=observable_values(s,np.diagonal(rho,axis1=1,axis2=2).real.T)
    metrics=density_metrics(rho)
    if stability > stability_atol or not density_passed(metrics): raise AssertionError("Independent density stability/invariant failure")
    return {"t":t, "values":values, "density":rho}, {"type":s["reference_scope"], "independent":True, "stable":True, "stability_error":stability, "density_metrics":metrics}


@lru_cache(maxsize=1)
def multiplicity():
    # Includes timing, seeds, tighter controls, raw samples and pooled/count
    # comparisons. A conservative union bound independent of CLI subsets.
    return sum(len(s["declarations"])*101*32 for s in scenarios())


def widths(s):
    return np.array([s["N"] if d["declaration"]["type"] == "total_rydberg_population" else 1. for d in s["declarations"]])


def bound(s, cfg, count=None):
    return widths(s)[:,None]*np.sqrt(np.log(2*multiplicity()/cfg["stochastic_alpha"])/(2*(count or s["trajectories"])))


def record_plan(s,cfg):
    if s["kind"] == "correctness": return [("statistical",i,seed) for i,seed in enumerate(SEEDS)] if s["path"] == "mcwf" else [("correctness",0,None)]
    seed=SEEDS[0] if s["path"] == "mcwf" else None
    records=[("first",0,seed)]+[("warmup",i,seed) for i in range(cfg["warmups"])]+[("measured",i,seed) for i in range(cfg["repeat_count"])]
    if s["path"] == "mcwf": records += [("statistical",i,seed) for i,seed in enumerate(SEEDS)]
    return records


def executed_options(s, seed, *, tighter=False):
    return {**s["solver"], "seed": seed, **({"reltol":1e-11,"abstol":1e-13} if tighter else {})}


def result_gate(result,s,cfg,ref,*,seed, tighter=False):
    from .api import validate_run_manifest, _pulse_manifest
    validate_run_manifest(result.manifest)
    manifest=result.manifest; solver=manifest["solver"]
    expected={**executed_options(s,seed,tighter=tighter), "effective_method":"Tsit5", "effective_adaptive":True, "effective_dt":None,
        "effective_saveat":s["solver"]["saveat"], "use_gpu":False, "t_span":[0.,s["duration"]]}
    if any(solver.get(k)!=v for k,v in expected.items() if k != "seed"): raise AssertionError("Requested/effective configuration mismatch")
    ds={d["name"]:d["declaration"] for d in s["declarations"]}; names=list(ds)
    if list(result.data)!=names+["t"] or solver["observables"]!=ds or result.to_shared_result()["observable_names"]!=names: raise AssertionError("Observable mapping/order mismatch")
    if manifest["register"]["atoms"]!=s["coordinates"] or manifest["register"]["C6"]!=s["C6"] or manifest["initial_state"]["basis_size"]!=s["basis_size"]: raise AssertionError("Executed register/basis mismatch")
    if manifest["pulse"]!={"omega":_pulse_manifest(s["omega"]),"delta":_pulse_manifest(s["delta"])}: raise AssertionError("Pulse mismatch")
    if abs(manifest["initial_state"]["norm"]-1)>1e-12 or manifest["backend_diagnostics"]["requested_backend"]!="CPU": raise AssertionError("Initial norm/backend mismatch")
    for k in ("effective_method","effective_adaptive","effective_dt","effective_saveat","reltol","abstol"):
        if result.diagnostics["simulation"].get(k)!=expected[k]: raise AssertionError("Backend effective solver mismatch")
    if manifest["random"]["effective_seed"]!=seed or manifest["random"]["seed"]!=seed: raise AssertionError("Requested/effective seed mismatch")
    times=np.array(result.data["t"]); values=np.array([result.data[n] for n in names],float)
    if times.shape!=ref["t"].shape or not np.allclose(times,ref["t"],rtol=0,atol=1e-14) or values.shape!=(len(names),101) or not np.isfinite(values).all(): raise AssertionError("Invalid output grid/values")
    sample_error=None
    if s["path"] == "mcwf":
        if manifest["random"]["n_trajectories"]!=s["trajectories"]: raise AssertionError("Effective trajectory count mismatch")
        if s["store_trajectories"]:
            if result.trajectories is None or list(result.trajectories)!=names: raise AssertionError("Missing raw trajectories")
            sample_error=0.
            for i,name in enumerate(names):
                samples=np.asarray(result.trajectories[name])
                if samples.shape!=(s["trajectories"],101) or not np.isfinite(samples).all() or np.min(samples)<-cfg["accuracy_atol"] or np.max(samples)>widths(s)[i]+cfg["accuracy_atol"]: raise AssertionError("Raw sample shape/finite failure")
                sample_error=max(sample_error,float(np.max(abs(samples.mean(axis=0)-values[i]))))
        elif result.trajectories is not None: raise AssertionError("Unrequested raw trajectories")
    numerical_bound=np.full((len(names),1),cfg["accuracy_atol"])
    if s["path"] == "mcwf": numerical_bound += bound(s,cfg)*(1 if s["reference_scope"] != "tighter same-method sensitivity and multi-seed consistency; independent interacting reference unavailable" else 2)
    errors=np.max(abs(values-ref["values"]),axis=1) if "values" in ref else None
    valid_range=bool(np.all(values>=-cfg["accuracy_atol"]) and np.all(values<=widths(s)[:,None]+cfg["accuracy_atol"]))
    passed=valid_range and (errors is None or bool(np.all(errors<=numerical_bound[:,0]))) and (sample_error is None or sample_error<=1e-12)
    return {"passed":passed,"max_abs_error":float(errors.max()) if errors is not None else None,
        "per_observable_error":errors.tolist() if errors is not None else None,"per_observable_bound":numerical_bound[:,0].tolist(),
        "sample_mean_error":sample_error,"range_passed":valid_range,"reference_scope":s["reference_scope"]}


def statistical_check(s, cfg, state):
    records=[r for r in state.get("records",[]) if r["phase"]=="statistical" and "values" in r]
    if s["path"] != "mcwf": return {"applicable":False,"reason":"Deterministic Lindblad workload"}
    if [r["seed"] for r in records] != list(SEEDS): return {"applicable":True,"complete":False,"passed":False,"reason":"Five independent statistical seeds required"}
    values=np.array([r["values"] for r in records]); mean=values.mean(axis=0)
    ref=np.asarray(state["reference_values"])
    uncertainty=bound(s,cfg,count=len(SEEDS)*s["trajectories"])
    if not state["reference"]["independent"]: uncertainty=uncertainty+bound(s,cfg)
    errors=np.max(abs(mean-ref),axis=1)
    return {"applicable":True,"complete":True,"passed":bool(np.all(errors<=uncertainty[:,0]+cfg["accuracy_atol"])),
        "seeds":list(SEEDS),"trajectories_per_seed":s["trajectories"],"pooled_trajectories":len(SEEDS)*s["trajectories"],
        "input_row_ids":[r["row_id"] for r in records],"mean":mean.tolist(),
        "sample_standard_error":(values.std(axis=0,ddof=1)/math.sqrt(len(SEEDS))).tolist(),
        "max_error_per_observable":errors.tolist(),"simultaneous_bound_per_observable":uncertainty[:,0].tolist(),
        "interpretation":"Absolute conservative envelope; observed errors need not decrease monotonically; standard errors descriptive only"}


def convergence(rows,cfg):
    groups={}; reports=[]
    for row in rows:
        s=row["problem"]
        report=statistical_check(s,cfg,row["metrics"]["state"])
        reports.append({"scenario_id":s["scenario_id"],"status":row["status"],**report})
        if s["path"]=="mcwf" and s["kind"]=="performance" and not s["store_trajectories"] and report.get("complete"):
            key=(s["N"],s["basis_mode"],s["fixture"],s["model"],s["rate_form"])
            groups.setdefault(key,[]).append((s,report))
    pairs=[]
    for key, group in groups.items():
        for i,(s,a) in enumerate(group):
            for other,b in group[i+1:]:
                err=np.max(abs(np.array(a["mean"])-np.array(b["mean"])),axis=1)
                limits=(bound(s,cfg,count=5*s["trajectories"])+bound(other,cfg,count=5*other["trajectories"]))[:,0]+2*cfg["accuracy_atol"]
                pairs.append({"scenarios":[s["scenario_id"],other["scenario_id"]],"counts":[s["trajectories"],other["trajectories"]],
                    "max_error_per_observable":err.tolist(),"bounds":limits.tolist(),"passed":bool(np.all(err<=limits))})
    return {"rule":STATISTICAL_RULE,"alpha":cfg["stochastic_alpha"],"multiplicity":multiplicity(),"reports":reports,
        "cross_count_comparisons":pairs,"all_available_comparisons_passed":all(p["passed"] for p in pairs) and all(r.get("passed",True) for r in reports if r.get("complete")),
        "limitations":"Five fixed seeds; absolute bounds, no relative-precision or independent large interacting reference claim"}


def _child(config_path, checkpoint_path):
    from . import Atom, Register, PulseSequence, Simulation, SimulationResult, SolverConfig, doctor
    from .runtime import get_julia
    from .scaling_benchmark import _runtime_context
    from .ablation_benchmark import _blas_threads
    config=json.loads(Path(config_path).read_text()); s,cfg=config["scenario"],config["settings"]
    directory=Path(checkpoint_path).parent
    state={"records":[],"timing":{},"stage":"setup"}
    def checkpoint(stage):
        state.update(stage=stage,memory=linux_process_memory(os.getpid()),memory_source=current_memory_usage())
        write_json(checkpoint_path,state)
    checkpoint("setup")
    try:
        for name,digest in config["source_sha256"].items():
            if hashlib.sha256((Path(config["source_root"])/name).read_bytes()).hexdigest()!=digest: raise RuntimeError("Frozen source changed")
        started=time.perf_counter(); state["doctor"]=doctor(backend="CPU",initialize_backend=True)
        state["timing"]["initialized_doctor_seconds"]=time.perf_counter()-started
        if not state["doctor"].get("available") or not (state["doctor"].get("backend_probe") or {}).get("available"): raise RuntimeError("Initialized CPU doctor failed")
        state["runtime_context"]=_runtime_context(); state["runtime_context"]["python_blas"]=_blas_threads()
        if any(state["runtime_context"]["threads"][k]!=1 for k in ("julia","blas")): raise RuntimeError("Effective threads differ from freeze")
        jl,_=get_julia(); project=Path(str(jl.seval("Base.active_project()"))); state["runtime_files"]={}
        for p in (project,project.with_name("Manifest.toml")):
            shutil.copyfile(p,directory/p.name); state["runtime_files"][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
        state["memory_baseline"]=linux_process_memory(os.getpid())
        started=time.perf_counter()
        reg=Register([Atom(*c) for c in s["coordinates"]],C6=s["C6"]); seq=PulseSequence(omega=s["omega"],delta=s["delta"])
        ds={d["name"]:d["declaration"] for d in s["declarations"]}
        def simulation(options): return Simulation(reg,seq,SolverConfig(**options))
        sim=simulation(s["solver"]); d=sim.validate()
        executed_basis=list(map(int,sim._basis)) if sim._basis is not None else list(range(2**s["N"]))
        if executed_basis!=basis(s) or d!=s["basis_size"]: raise AssertionError("Independent/SDK basis mismatch")
        initial=initial_state(s)
        state["initial_state_sha256"]=hashlib.sha256(initial.tobytes()).hexdigest()
        state["timing"]["setup_basis_seconds"]=time.perf_counter()-started
        checkpoint("reference"); started=time.perf_counter()
        ref,description=reference(s,cfg["reference_stability_atol"])
        # Raw density validation is a separate execution outside all workload
        # timers. It is bounded by a frozen dimension cap even for MCWF workers.
        if d <= 64 or s["path"]=="lindblad":
            raw_options={**executed_options(s,None,tighter=True),"use_mc":False,"store_trajectories":False}
            raw=simulation(raw_options).run(initial.copy(),0.,s["duration"],observables={})
            density=np.array([np.asarray(v,dtype=complex) for v in raw.u]); times=np.array(list(raw.t))
            if density.shape!=(101,d,d) or not np.allclose(times,ref["t"],rtol=0,atol=1e-14): raise AssertionError("Raw density grid/shape mismatch")
            metrics=density_metrics(density)
            error=float(np.max(abs(density-ref["density"]))) if "density" in ref else None
            if not density_passed(metrics) or (error is not None and error>cfg["accuracy_atol"]): raise AssertionError("Raw density/reference trace/positivity/coherence gate failed")
            np.savez_compressed(directory/"density-validation.npz",t=times,density=density)
            state["density_validation"]={"arrays":str(directory/"density-validation.npz"),"metrics":metrics,"max_abs_density_error":error,"passed":True,
                "options":raw_options,"timer_scope":"separate untimed correctness execution", "basis":executed_basis}
            if "values" not in ref:
                ref["values"]=observable_values(s,np.diagonal(density,axis1=1,axis2=2).real.T)
        else: state["density_validation"]={"passed":None,"unavailable_reason":"D-squared raw histories/eigendecompositions exceed independent-reference dimension policy"}
        state["timing"]["reference_seconds"]=time.perf_counter()-started
        state["reference"]=description
        # A tighter seeded solve is retained independently from first/warm/
        # measured/statistical calls. Large interacting means are sensitivity
        # controls with sampling uncertainty, not an independent physics oracle.
        if s["path"]=="mcwf" or "values" not in ref:
            seed=SEEDS[0] if s["path"]=="mcwf" else None
            checkpoint("reference"); started=time.perf_counter()
            tight=simulation(executed_options(s,seed,tighter=True)).run(initial.copy(),0.,s["duration"],observables=ds)
            state["timing"]["tighter_sensitivity_seconds"]=time.perf_counter()-started
            tight_path=directory/"sensitivity.result.json"; tight.save(str(tight_path)); ordered_write(directory/"sensitivity.manifest.json",tight.manifest)
            if "values" not in ref: ref["values"]=np.array([tight.data[name] for name in ds])
            state["sensitivity"]={"result_artifact":str(tight_path),"run_manifest":str(directory/"sensitivity.manifest.json"),
                "seed":seed,"gate":result_gate(tight,s,cfg,ref,seed=seed,tighter=True)}
            if not state["sensitivity"]["gate"]["passed"]: raise AssertionError("Tighter sensitivity/reference gate failed")
        np.savez_compressed(directory/"reference.npz",**ref); write_json(directory/"reference.json",description)
        state["reference_values"]=ref["values"].tolist()
        for phase,index,seed in record_plan(s,cfg):
            record={"row_id":f"{s['scenario_id']}-{phase}-{index}","phase":phase,"repeat_index":index,"seed":seed,"operation_count":1,"eligible":False,"artifacts":{}}
            state["records"].append(record)
            runner=simulation(executed_options(s,seed)); reset=initial.copy()
            checkpoint("solve"); started=time.perf_counter()
            result=runner.run(reset,0.,s["duration"],observables=ds)
            record["runtime_seconds"]=time.perf_counter()-started
            record["requested_trajectories"]=s["trajectories"]; record["completed_trajectories"]=s["trajectories"]
            # Successful SDK ensemble return validates its requested number of
            # outputs; no independent trajectory progress counter is exposed.
            record["completed_count_method"]="successful SDK ensemble return and manifest count" if s["path"]=="mcwf" else "not applicable"
            if s["path"]=="mcwf": record["trajectories_per_second"]=s["trajectories"]/record["runtime_seconds"]
            checkpoint("artifact"); started=time.perf_counter()
            result_path=directory/f"{phase}-{index}.result.json"; manifest_path=directory/f"{phase}-{index}.manifest.json"
            result.save(str(result_path)); ordered_write(manifest_path,result.manifest)
            record["artifacts"]={"result_artifact":str(result_path),"run_manifest":str(manifest_path),"reference_arrays":str(directory/"reference.npz"),"reference_report":str(directory/"reference.json")}
            record["serialization_seconds"]=time.perf_counter()-started
            checkpoint("validation"); started=time.perf_counter()
            record["gate"]=result_gate(result,s,cfg,ref,seed=seed)
            loaded=SimulationResult.load(str(result_path))
            if loaded.manifest!=result.manifest or result_gate(loaded,s,cfg,ref,seed=seed)!=record["gate"]: raise AssertionError("Result round trip changed")
            record["eligible"]=record["gate"]["passed"]; record["effective_solver"]=result.diagnostics["simulation"]
            if phase=="statistical": record["values"]=[result.data[name] for name in ds]
            record["validation_seconds"]=time.perf_counter()-started
            checkpoint("validation")
        state["complete"]=True; checkpoint("artifact")
    except Exception as exc:
        state["failure"]=benchmark_failure_context(exc,stage=state["stage"],timeout_seconds=cfg["timeout_seconds"],backend_probe=state.get("doctor",{}).get("backend_probe"))
        checkpoint(state["stage"])


def throughput_summary(records,requested):
    samples=[{**r,"runtime_seconds":r["trajectories_per_second"]} for r in records if r.get("eligible")]
    if not samples: return {"unavailable_reason":"No eligible MCWF measurements"}
    out=runtime_summary(samples,requested)
    out["completed"]=len(records)
    out["trajectories_per_second"]=out.pop("runtime_seconds")
    return out


def make_row(s,cfg,state,supervision,exclusion=None):
    records=state.get("records",[])
    measured=[r for r in records if r["phase"]=="measured" and "runtime_seconds" in r]
    summary=runtime_summary(measured,cfg["repeat_count"]) if s["kind"]=="performance" else None
    statistical=statistical_check(s,cfg,state)
    failure=state.get("failure"); status="passed"; reason=supervision.get("reason")
    if exclusion:
        status="skipped"; failure={"stage":"setup","code":"BENCHMARK_RESOURCE_EXCLUDED","message":exclusion,"remediation":"Retain boundary; freeze adequate resources before a new campaign"}
    elif reason in ("timeout","interrupted"):
        status="incomplete"; failure={"stage":state.get("stage","setup"),"code":"BENCHMARK_"+reason.upper(),"message":"Stopped worker; partial evidence retained","remediation":"Inspect checkpoint; rerun in new directory"}
    elif reason or supervision.get("returncode",0)!=0:
        status="failed"; failure=benchmark_failure_context(MemoryError("RSS budget exceeded") if reason=="memory" else RuntimeError("Unexpected worker exit"),stage=state.get("stage","setup"))
    elif failure or any("gate" in r and not r["gate"]["passed"] for r in records): status="failed"
    elif not state.get("complete") or [(r["phase"],r["repeat_index"],r["seed"]) for r in records]!=record_plan(s,cfg) or any(not r.get("eligible") for r in records): status="incomplete"
    elif statistical.get("applicable") and not statistical["passed"]: status="failed"
    elif s["kind"]=="performance" and (cfg["warmups"]<2 or cfg["repeat_count"]<5): status="incomplete"
    if status!="passed" and not failure: failure={"stage":"validation","code":"BENCHMARK_ACCURACY_FAILED" if status=="failed" else "BENCHMARK_INSUFFICIENT_EVIDENCE","message":"All reference/seed gates and two warmups/five repeats required","remediation":"Retain diagnostics and resolve gates before comparisons"}
    if failure: failure={**failure,"limits":{k:cfg[k] for k in ("timeout_seconds","memory_limit_bytes","max_density_dimension","max_state_dimension")},"backend_probe":state.get("doctor",{}).get("backend_probe")}
    throughput=throughput_summary(measured,cfg["repeat_count"]) if s["path"]=="mcwf" and s["kind"]=="performance" else {"unavailable_reason":"Not a measured MCWF workload"}
    metrics={"state":state,"supervision":supervision,"statistics":summary,"throughput_statistics":throughput,"convergence":statistical,
        "statistics_reason":None if summary else "Correctness-only control", "timer_scope":TIMER,
        "memory_scope":"worker lifetime including initialization, reference histories, validation and writes; /proc HWM and 50ms sampled RSS budget"}
    row=make_benchmark_row(row_id=s["scenario_id"],scenario_id=s["scenario_id"],family=FAMILY,tier=TIER,status=status,stage=failure["stage"] if failure else "artifact",
        problem=s,solver=s["solver"],backend={"requested_backend":"CPU","path":s["path"],"precision":"complex128","execution_mode":s["execution_mode"]},
        observables={"declarations":s["declarations"],"names":[d["name"] for d in s["declarations"]],"output_sample_count":101},metrics=metrics,artifacts={},failure=failure,disclosure_status="local_only")
    row.update({k:s[k] for k in ("kind","N","basis_size","basis_mode","path","model","trajectories","store_trajectories","reference_scope")})
    gates=[r["gate"] for r in records if "gate" in r]
    reference_gate=all(g["passed"] for g in gates) if gates else None
    row.update(rate_form=s["rate_form"],gamma=s["solver"]["gamma"],gamma_phi=s["solver"]["gamma_phi"],
        timing_seed=s["solver"]["seed"] if s["kind"]=="performance" else None, execution_mode=s["execution_mode"],
        completed_trajectories_per_repeat=s["trajectories"] if s["path"]=="mcwf" and len(measured)==cfg["repeat_count"] and all(r.get("completed_trajectories")==s["trajectories"] for r in measured) else None,
        reference_gate=reference_gate, convergence_gate=statistical.get("passed") if statistical.get("complete") else None)
    errors=[r["gate"]["max_abs_error"] for r in records if r.get("gate",{}).get("max_abs_error") is not None]
    row.update(eligible=summary["eligible"] if summary else None,max_abs_error=max(errors,default=None),peak_bytes=state.get("memory",{}).get("peak_bytes"),raw_records="open_system_repeats.json",
        throughput_median=throughput.get("trajectories_per_second",{}).get("median"))
    row.update({k+"_s":v for k,v in (summary["runtime_seconds"] if summary else dict.fromkeys(("median","min","max","p25","p75"))).items()})
    return row


def coverage(rows):
    passed={r["scenario_id"] for r in rows if r["status"]=="passed"}; expected=scenarios()
    return {"selected_campaign_passed":all(r["status"]=="passed" for r in rows),"full_matrix_passed":{s["scenario_id"] for s in expected}<=passed,
        "all_declared_rows_accounted":{s["scenario_id"] for s in expected}=={r["scenario_id"] for r in rows},
        "all_attempted_rows_passed":all(r["status"] in ("passed","skipped") for r in rows),
        "small_reference_group_passed":all(s["scenario_id"] in passed for s in expected if s["basis_size"]<=64),
        "analytic_control_group_passed":all(s["scenario_id"] in passed for s in expected if s["kind"]=="correctness"),
        "reduced_n20_mcwf_counts_passed":all(scenario(20,"mcwf",trajectories=k)["scenario_id"] in passed for k in COUNTS),
        "missing_successful_scenarios":[s["scenario_id"] for s in expected if s["scenario_id"] not in passed],
        "classification":"local_only; software/numerical/statistical checks, large interacting reference gaps; no scientific validation or public/release approval"}


def benchmark_open_system(output_dir, *, tier="all", scenario_ids=None, warmups=2, repeat_count=5,
                          timeout_seconds=1800., memory_limit_mb=4096., max_density_dimension=256, max_state_dimension=1024, accuracy_atol=1e-6,
                          reference_stability_atol=1e-9, stochastic_alpha=1e-6):
    from .runtime import version_info
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (warmups, repeat_count, max_density_dimension, max_state_dimension)) or warmups < 0 or repeat_count < 1 or max_density_dimension < 1 or max_state_dimension < 1: raise ValueError("Invalid warmup/repeat counts")
    if not all(math.isfinite(v) and v > 0 for v in (timeout_seconds, memory_limit_mb, accuracy_atol, reference_stability_atol, stochastic_alpha)) or stochastic_alpha >= 1: raise ValueError("Limits/tolerances must be finite positive, alpha below one")
    selected = scenarios(tier)
    if scenario_ids is not None:
        if not scenario_ids or len(set(scenario_ids)) != len(scenario_ids) or set(scenario_ids) - {s["scenario_id"] for s in selected}: raise ValueError("Select unique known nonempty scenario IDs")
        selected = [s for s in selected if s["scenario_id"] in scenario_ids]
    cfg = {"tier": tier, "warmups": warmups, "repeat_count": repeat_count, "timeout_seconds": timeout_seconds,
        "memory_limit_bytes": int(memory_limit_mb * 1024**2), "max_density_dimension": max_density_dimension, "max_state_dimension": max_state_dimension, "accuracy_atol": accuracy_atol,
        "reference_stability_atol": reference_stability_atol, "stochastic_alpha": stochastic_alpha}
    output = Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()): raise FileExistsError("Use a new empty output directory")
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    names = [f"sagittarius_py/sagittarius/{n}.py" for n in ("open_system_benchmark", "observable_benchmark", "benchmark_measurement", "benchmarking", "benchmark_suite", "benchmark_failures", "api", "pulse", "runtime", "scaling_benchmark", "ablation_benchmark")]
    names += ["sagittarius_py/pyproject.toml", "sagittarius_py/uv.lock", "Sagittarius.jl/Project.toml", "sagittarius_py/tests/test_performance/benchmark_open_system_performance.py"]
    names += [str(p.relative_to(root)) for p in (root / "Sagittarius.jl/src").glob("*.jl")]
    names += [n for n in ("scripts/audit_open_system_campaign.py", "sagittarius_py/tests/test_open_system_benchmark.py") if (root / n).exists()]
    hashes = {}
    for name in names:
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
        hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    frozen = {"scenarios": selected, "settings": cfg, "source_sha256": hashes}
    env = {**os.environ, **{key: "1" for key in THREAD_KEYS}}
    campaign = {**frozen, "config_sha256": hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest(),
        "output_dir": str(output), "source_root": str(root), "source": version_info(initialize_backend=False),
        "workload_version": WORKLOAD_VERSION, "plan_version": "benchmark-implementation-plan/v2", "protocol_version": "benchmark-protocol/v1",
        "created_at": datetime.now(timezone.utc).isoformat(), "command": sys.argv, "cwd": str(Path.cwd()), "python_executable": sys.executable,
        "thread_environment": {k: env[k] for k in THREAD_KEYS}, "timer_scope": TIMER,
        "cache_policy": "fresh worker per configuration; initialized doctor/setup/reference/tighter control before first; reset state and seed; new Simulation wrapper per call with shared backend/JIT caches",
        "stop_policy": "continue after failures; interruption retains unstarted rows as incomplete", "stochastic_comparisons": multiplicity(),
        "statistical_seed_set": list(SEEDS), "performance_seed": SEEDS[0], "statistical_rule": STATISTICAL_RULE,
        "classification": "shared-workstation local_only; no affinity/exclusive-load controls; large interacting independent-reference gaps remain explicit"}
    try:
        campaign["host"] = {"cpu_model": next(line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")), "logical_cpus": os.cpu_count(), "memory_bytes": os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")}
    except (OSError, ValueError, StopIteration): campaign["host"] = {"unavailable_reason": "Host metadata unavailable"}
    write_json(output / "campaign.json", campaign)
    rows, interrupted = [], False
    for s in selected:
        directory = output / s["scenario_id"]
        directory.mkdir()
        config_path, checkpoint_path = directory / "config.json", directory / "checkpoint.json"
        write_json(config_path, {"scenario": s, "settings": cfg, "source_root": str(root), "source_sha256": hashes})
        state, supervision = {}, {}
        exclusion = resource_exclusion(s, cfg)
        if interrupted: supervision = {"reason": "interrupted"}
        elif not exclusion:
            command = [sys.executable, "-m", "sagittarius.open_system_benchmark", "--child", str(config_path), str(checkpoint_path)]
            write_json(directory / "command.json", {"argv": command, "cwd": str(Path.cwd())})
            try:
                supervision = supervise(command, cwd=str(Path.cwd()), env=env, log_path=directory / "child.log", timeout_seconds=timeout_seconds, memory_limit_bytes=cfg["memory_limit_bytes"])
            except KeyboardInterrupt: interrupted, supervision = True, {"reason": "interrupted"}
            except Exception as exc: state["failure"] = benchmark_failure_context(exc, stage="setup")
            if checkpoint_path.exists(): state = json.loads(checkpoint_path.read_text())
        row = make_row(s, cfg, state, supervision, exclusion)
        row["artifacts"] = {"config": str(config_path), "checkpoint": str(checkpoint_path) if checkpoint_path.exists() else None}
        rows.append(row)
        write_json(output / "progress.json", rows)
        print(f"{s['scenario_id']}: {row['status']}", flush=True)
    raw = [{"scenario_id": row["scenario_id"], **record} for row in rows for record in row["metrics"]["state"].get("records", [])]
    write_json(output / "open_system_repeats.json", raw)
    paths = write_benchmark_artifacts(output_dir=output, stem="open_system_performance", name="P1 local-noise runtime and convergence",
        description="Local Lindblad/MCWF end-to-end costs, analytic/dense and bounded statistical gates",
        parameters=campaign, rows=rows, backend="CPU", diagnostics={"doctor": "per-worker checkpoints"},
        run_manifests=[{"label": r["row_id"], "path": r["artifacts"]["run_manifest"]} for r in raw if r["artifacts"].get("run_manifest")],
        columns=COLUMNS, benchmark_context={"family": FAMILY, "tier": TIER, "config_sha256": campaign["config_sha256"], "disclosure_status": "local_only"})
    paths["suite"] = write_benchmark_suite_artifact(output_dir=output, stem="open_system_performance_suite", suite_id="phase16-p1-open-system-v2",
        family=FAMILY, tier=TIER, rows=rows, source=campaign["source"], environment={"thread_environment": campaign["thread_environment"]},
        scenario_defaults={"settings": cfg, "campaign": str(output / "campaign.json")})
    write_json(output / "coverage.json", coverage(rows))
    write_json(output / "convergence.json", convergence(rows, cfg))
    return paths


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--child": _child(sys.argv[2], sys.argv[3])
    else: raise SystemExit("Use tests/test_performance/benchmark_open_system_performance.py")
