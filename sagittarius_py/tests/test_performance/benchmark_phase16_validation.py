"""Phase 16 cold-atom and open-system correctness benchmark families."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from sagittarius import (Atom, PulseSequence, Register, Simulation, SolverConfig,
    dense_vs_reduced_validation, open_system_sanity_checks, make_benchmark_row,
    benchmark_failure_from_exception, write_benchmark_artifacts,
    write_benchmark_suite_artifact)


def _row(name, family, tier, problem, metrics, *, status="passed", failure=None, artifacts=None):
    return make_benchmark_row(row_id=f"{family}-{name}", scenario_id=name,
        family=family, tier=tier, status=status,
        stage="validation", problem=problem,
        solver={"reference": "projected_dense_vs_reduced" if family == "cold_atom_dynamics" else "lindblad_mcwf"},
        backend={"requested_backend": "CPU", "path": "cpu"},
        observables={"names": ["total_rydberg_population"], "count": 1, "output_sample_count": 5},
        metrics=metrics, failure=failure, artifacts=artifacts, disclosure_status="local_only")


def benchmark_cold_atom_dynamics(output_dir="."):
    """Cross-check chain/local/Z2/2D cases against projected dense evolution."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    cases = [
        ("chain_global_n3", Register.chain(3, spacing=.5, C6=10), PulseSequence(omega=.3, delta=.05), .6),
        ("local_addressing_n3", Register.chain(3, spacing=.5, C6=10), PulseSequence(omega=[.2,.35,.15], delta={1:.1}), .6),
        ("z2_chain_n4", Register.chain(4, spacing=.5, C6=10), PulseSequence(omega=.25, delta=[.15,-.15,.15,-.15]), .6),
        ("square_2x2_n4", Register.square_lattice(2,2, spacing=.5, C6=10), PulseSequence(omega=[.2,.3,.25,.35], delta=.0), .6),
    ]
    rows=[]
    for name, reg, seq, radius in cases:
        try:
            report=dense_vs_reduced_validation(reg, seq, blockade_radius=radius, duration=.4, atol=1e-8)
            if not report["ok"]: raise AssertionError("dense/reduced reference mismatch")
            reference_file=Path(output_dir) / f"{name}.dense-vs-reduced.json"; reference_file.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
            rows.append(_row(name,"cold_atom_dynamics","correctness", {"geometry":reg.topology,"atom_count":len(reg.atoms),"blockade_radius":radius}, {"reference_kind":"projected_dense_matrix_exponential","reference_tolerance":1e-8,"max_hamiltonian_error":report["max_hamiltonian_error"],"max_state_error":report["max_state_error"],"basis_size":report["reduced_basis_size"]},artifacts={"reference_report":str(reference_file)}))
        except Exception as exc:
            rows.append(_row(name,"cold_atom_dynamics","correctness", {"atom_count":len(reg.atoms),"blockade_radius":radius}, {}, status="failed", failure=benchmark_failure_from_exception(exc,stage="validation")))
    paths=write_benchmark_artifacts(output_dir=output_dir,stem="cold_atom_dynamics",name="Phase 16 cold-atom dynamics correctness",description="Small chain, local-addressing, Z2, and 2D cases against projected dense references.",parameters={"reference_tolerance":1e-8},rows=rows,columns=["scenario_id","status","metrics","artifacts","failure"])
    paths["suite"]=write_benchmark_suite_artifact(output_dir=output_dir,stem="cold_atom_dynamics_suite",suite_id="phase16-cold-atom-dynamics",family="cold_atom_dynamics",tier="correctness",rows=rows,source=paths["artifact"]["versions"])
    return paths


def benchmark_open_system_dynamics(output_dir="."):
    """Analytic decay and 100/500-trajectory Lindblad cross-checks."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    reg=Register([Atom(0,0)],C6=0); seq=PulseSequence(omega=0.,delta=0.); psi=np.array([0.,1.],complex); rows=[]
    for trajectories in (100,500):
        try:
            report=open_system_sanity_checks(reg,seq,config=SolverConfig(gamma=.5,gamma_phi=.125,seed=20260811,reltol=1e-8,abstol=1e-10),psi0=psi,t_end=2.,observables={"pop":0},n_trajectories=trajectories,mc_mean_abs_atol=.08)
            rho_final=np.asarray(Simulation(reg,seq,SolverConfig(gamma=.5,gamma_phi=.125,seed=20260811,reltol=1e-8,abstol=1e-10)).run(psi,0.,2.).u[-1]); analytic_decay_actual=float(np.real(rho_final[1,1])); analytic_decay_error=abs(analytic_decay_actual-float(np.exp(-1.0)))
            metrics={"reference_kind":"analytic_decay_and_mcwf_lindblad","analytic_decay_expected":float(np.exp(-1.0)),"analytic_decay_actual":analytic_decay_actual,"analytic_decay_error":analytic_decay_error,"analytic_decay_atol":1e-6,"trace_error":report["lindblad_trace"]["max_error"],"min_density_eigenvalue":report["lindblad_positivity"]["min_eigenvalue"],"mcwf_lindblad_mean_abs_error":report["mcwf_vs_lindblad"]["max_mean_abs_error"],"trajectory_count":trajectories,"seed":20260811,"reference_tolerance":.08}
            if analytic_decay_error > 1e-6: raise AssertionError("analytic decay reference mismatch")
            if not report["ok"]: raise AssertionError("open-system sanity check failed")
            reference_file=Path(output_dir) / f"decay_dephasing_mcwf_n{trajectories}.reference.json"; reference_file.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
            rows.append(_row(f"decay_dephasing_mcwf_n{trajectories}","open_system_dynamics","correctness",{"atom_count":1,"gamma":.5,"gamma_phi":.125,"seed":20260811},metrics,artifacts={"reference_report":str(reference_file)}))
        except Exception as exc:
            rows.append(_row(f"decay_dephasing_mcwf_n{trajectories}","open_system_dynamics","correctness",{"atom_count":1,"gamma":.5,"gamma_phi":.125,"seed":20260811}, {},status="failed",failure=benchmark_failure_from_exception(exc,stage="validation")))
    paths=write_benchmark_artifacts(output_dir=output_dir,stem="open_system_dynamics",name="Phase 16 open-system correctness",description="Analytic decay plus Lindblad/MCWF trajectory-count cross-checks.",parameters={"trajectory_counts":[100,500],"seed":20260811,"mcwf_lindblad_atol":.08,"trajectory_sensitivity":"500_not_worse_than_100"},rows=rows,columns=["scenario_id","status","metrics","artifacts","failure"])
    paths["suite"]=write_benchmark_suite_artifact(output_dir=output_dir,stem="open_system_dynamics_suite",suite_id="phase16-open-system-dynamics",family="open_system_dynamics",tier="correctness",rows=rows,source=paths["artifact"]["versions"])
    return paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Phase 16 cold-atom and open-system correctness benchmarks.")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()
    cold = benchmark_cold_atom_dynamics(args.output_dir)
    open_system = benchmark_open_system_dynamics(args.output_dir)
    print(f"Phase 16 validation benchmarks complete. Results saved to {cold['json']} and {open_system['json']}")
