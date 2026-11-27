"""Apply the predeclared local characterization policy after the saved-output audit.

Run from the repository root; no Julia backend is initialized. Numerical failures
are data only when every call is retained and the fine-step/tolerance controls pass.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "sagittarius_py"))
spec = importlib.util.spec_from_file_location("audit_solver_campaign", root / "scripts/audit_solver_campaign.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from sagittarius.solver_benchmark import phases, scenarios


def review(directory):
    report = module.audit(directory)
    campaign = json.loads((directory / "campaign.json").read_text())
    rows = json.loads((directory / "solver_sensitivity_suite.json").read_text())["rows"]
    policy_path = Path(__file__).with_name("acceptance-policy.json")
    policy = json.loads(policy_path.read_text())
    cfg = campaign["settings"]
    assert cfg["accuracy_atol"] == policy["accuracy_atol"]
    assert cfg["reference_stability_atol"] == policy["reference_stability_atol"]
    assert cfg["warmups"] >= policy["minimum_warmups"] and cfg["repeat_count"] >= policy["minimum_measured_repeats"]
    assert campaign["scenarios"] == scenarios(), "Incomplete or altered matrix"
    assert report["scenario_count"] == 39 and report["checked_results"] == 39 * len(phases(cfg))
    controls = {f"{fixture}-{config}" for fixture in ("rabi", "addressed", "ramp")
                for config in ("tsit5-tol10-g101", "vern9-tol10-g101", "rk4-s400-g101")}
    assert controls <= {r["scenario_id"] for r in rows if r["status"] == "passed"}
    under_resolved = []
    for row in rows:
        state, supervision = row["metrics"]["state"], row["metrics"]["supervision"]
        assert state["complete"] and not state.get("failure")
        assert supervision["reason"] is None and supervision["returncode"] == 0
        assert [(r["phase"], r["repeat_index"]) for r in state["records"]] == phases(cfg)
        if row["status"] != "passed":
            assert row["status"] == "failed" and row["failure"]["code"] == "BENCHMARK_ACCURACY_FAILED"
            assert all("gate" in r and r["artifacts"].get("result_artifact") for r in state["records"])
            assert any(not r["gate"]["passed"] for r in state["records"])
            under_resolved.append(row["scenario_id"])
    return {**report, "local_characterization_accepted": True, "under_resolved_scenarios": under_resolved,
            "accurate_control_count": len(controls), "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
            "performance_scope": "Eligible configurations/calls only; under-resolved times remain diagnostics"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = review(args.directory.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
