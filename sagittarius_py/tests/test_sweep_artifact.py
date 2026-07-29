import pytest

from sagittarius import make_sweep_artifact, resume_item_ids, save_sweep_artifact, load_sweep_artifact
from sagittarius.runtime import SagittariusValidationError


def _items():
    return [
        {"item_id": "omega-1", "parameters": {"omega": 1.0}, "status": "succeeded", "attempts": 1, "result_path": "runs/omega-1.result.json", "manifest_path": "runs/omega-1.manifest.json", "failure": None},
        {"item_id": "omega-2", "parameters": {"omega": 2.0}, "status": "failed", "attempts": 1, "result_path": None, "manifest_path": None, "failure": {"code": "SOLVER_EXECUTION_FAILED", "message": "synthetic failure", "remediation": "retry"}},
    ]


def test_sweep_artifact_preserves_axes_status_links_failures_and_resume(tmp_path):
    artifact = make_sweep_artifact(
        axes=[{"name": "omega", "path": "pulse.omega", "values": [1.0, 2.0]}],
        items=_items(), base_config={"schema_version": "experiment-config/v1"},
    )
    assert artifact["purpose"] == "scientific_exploration"
    assert artifact["artifact_type"] == "sagittarius.experiment_sweep"
    assert resume_item_ids(artifact) == ["omega-2"]
    saved = save_sweep_artifact(artifact, tmp_path / "sweep.json")
    loaded = load_sweep_artifact(tmp_path / "sweep.json")
    assert loaded["resumability"]["artifact_path"].endswith("sweep.json")
    assert loaded["items"] == saved["items"]


def test_succeeded_sweep_item_requires_result_and_manifest_links():
    bad = _items(); bad[0] = dict(bad[0], manifest_path=None)
    with pytest.raises(SagittariusValidationError) as excinfo:
        make_sweep_artifact(axes=[{"name": "omega", "path": "pulse.omega", "values": [1.0, 2.0]}], items=bad, base_config={})
    assert excinfo.value.issue.code == "VALIDATION_SWEEP_ARTIFACT_SUCCESS_LINKS"
