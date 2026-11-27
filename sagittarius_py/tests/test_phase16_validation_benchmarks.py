from pathlib import Path
import importlib.util, json
import pytest
_p=Path(__file__).parent/"test_performance"/"benchmark_phase16_validation.py"; _s=importlib.util.spec_from_file_location("phase16_validation",_p); _m=importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
pytestmark=pytest.mark.requires_julia_backend
def test_phase16_validation_families_emit_reference_rows(tmp_path):
    cold=_m.benchmark_cold_atom_dynamics(tmp_path); open_=_m.benchmark_open_system_dynamics(tmp_path)
    assert all(r["status"]=="passed" for r in json.loads(Path(cold["json"]).read_text())["timings"])
    assert all(r["status"]=="passed" for r in json.loads(Path(open_["json"]).read_text())["timings"])
    open_rows = json.loads(Path(open_["json"]).read_text())["timings"]
    errors = {row["metrics"]["trajectory_count"]: row["metrics"]["mcwf_lindblad_mean_abs_error"] for row in open_rows}
    assert errors[500] <= errors[100]
    assert all(row["problem"]["gamma_phi"] == .125 and row["metrics"]["seed"] == 20260811 for row in open_rows)
    assert all(Path(row["artifacts"]["reference_report"]).is_file() for row in open_rows)
    cold_rows = json.loads(Path(cold["json"]).read_text())["timings"]
    assert all(Path(row["artifacts"]["reference_report"]).is_file() for row in cold_rows)
    assert all(row["metrics"]["analytic_decay_error"] <= row["metrics"]["analytic_decay_atol"] for row in open_rows)
