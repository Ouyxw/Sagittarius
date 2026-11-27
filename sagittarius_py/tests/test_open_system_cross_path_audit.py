"""Independent review of matched saved Lindblad and MCWF evidence."""
import copy
import importlib.util
from pathlib import Path
import numpy as np
import pytest
p=Path(__file__).resolve().parents[2]/"scripts/accept_open_system_campaign.py"
spec=importlib.util.spec_from_file_location("accept_open_system_campaign",p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from sagittarius.open_system_benchmark import scenario
CFG={"stochastic_alpha":1e-6,"accuracy_atol":1e-6}


def test_matching_retains_physics_and_ignores_only_mc_count_seed_storage():
    lb=scenario(2);mc=scenario(2,"mcwf",store=True)
    assert module.physical_key(lb)==module.physical_key(mc)
    for mutate in (lambda s:s.update(C6=101),lambda s:s["solver"].update(gamma=.6),lambda s:s.update(initial_state="coherent"),lambda s:s["solver"].update(reltol=1e-9)):
        changed=copy.deepcopy(mc);mutate(changed)
        assert module.physical_key(lb)!=module.physical_key(changed)
    assert module.physical_key(scenario(2,reduced=False))!=module.physical_key(lb)


def test_direct_and_pooled_absolute_bounds_reject_corruption():
    s=scenario(2,"mcwf");reference=np.zeros((4,101))
    assert module.compare(reference,reference,s,CFG,500)["passed"]
    limits=np.asarray(module.compare(reference,reference,s,CFG,500)["bounds"])
    within=reference+limits[:,None]*.9
    assert module.compare(within,reference,s,CFG,500)["passed"]
    assert not module.compare(within,reference,s,CFG,2500)["passed"]
    assert not module.compare(reference+1,reference,s,CFG,500)["passed"]


@pytest.mark.parametrize("bad",[np.zeros((3,101)),np.full((4,101),np.nan),np.full((4,101),np.inf)])
def test_invalid_cross_path_payload_rejected(bad):
    with pytest.raises(ValueError,match="Invalid cross-path arrays"):
        module.compare(bad,np.zeros((4,101)),scenario(2,"mcwf"),CFG,500)


@pytest.mark.requires_julia_backend
def test_real_per_atom_reduced_noise_and_saved_cross_path_review(tmp_path,monkeypatch):
    from sagittarius.open_system_benchmark import benchmark_open_system
    from sagittarius import runtime
    ids=[scenario(2,path,per_atom=True)["scenario_id"] for path in ("lindblad","mcwf")]
    output=benchmark_open_system(tmp_path,scenario_ids=ids)
    assert all(r["status"]=="passed" for r in output["artifact"]["timings"]),[r["failure"] for r in output["artifact"]["timings"]]
    monkeypatch.setattr(runtime,"get_julia",lambda: (_ for _ in ()).throw(AssertionError("review initialized Julia")))
    report=module.accept(tmp_path)
    assert report["measurement_audit"]["contract_audit_passed"]
    assert report["accepted"] is False  # Selected smoke is not the full campaign.
    assert report["lindblad_mcwf"]["available_configurations"]==1
    assert report["lindblad_mcwf"]["individual_comparisons"]==14
    assert report["lindblad_mcwf"]["all_available_comparisons_passed"]
