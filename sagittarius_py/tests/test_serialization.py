import json
import os

import numpy as np
import pytest

from sagittarius import (
    RESULT_ARTIFACT_SCHEMA_VERSION,
    RESULT_ARTIFACT_TYPE,
    SagittariusSerializationError,
    SimulationResult,
    load_result,
)

def test_json_serialization():
    # 1. Generate some data
    data = {
        "t": [0.0, 0.5, 1.0],
        "atom0": [1.0, 0.5, 0.0],
        "atom1": [0.0, 0.5, 1.0]
    }
    res = SimulationResult(data)
    
    # 2. Save to JSON
    filepath = "test_result.json"
    try:
        res.save(filepath)
        assert os.path.exists(filepath)
        
        # 3. Load back
        res_loaded = load_result(filepath)
        
        # 4. Compare
        assert np.allclose(res.t, res_loaded.t)
        assert np.allclose(res.data["atom0"], res_loaded.data["atom0"])
        assert res.data.keys() == res_loaded.data.keys()
        
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == "__main__":
    test_json_serialization()
    print("Serialization test passed!")


def test_result_save_always_writes_artifact_envelope(tmp_path):
    path = tmp_path / "result.json"
    res = SimulationResult(
        {"t": [0.0, 1.0], "atom0": np.array([1.0, 0.0])},
        metadata={"package_version": "test"},
        diagnostics={"requested_backend": "CPU"},
        manifest={"event_ids": ["SAG-EVT-0005"]},
    )

    res.save(str(path))

    payload = json.loads(path.read_text())
    assert payload["schema_version"] == RESULT_ARTIFACT_SCHEMA_VERSION
    assert payload["artifact_type"] == RESULT_ARTIFACT_TYPE
    assert payload["data"] == {"t": [0.0, 1.0], "atom0": [1.0, 0.0]}
    assert payload["metadata"]["package_version"] == "test"
    assert payload["diagnostics"]["requested_backend"] == "CPU"
    assert payload["manifest"]["event_ids"] == ["SAG-EVT-0005"]


def test_result_envelope_round_trips_manifest(tmp_path):
    path = tmp_path / "result.json"
    SimulationResult(
        {"t": [0.0], "atom0": [1.0]},
        metadata={"example": "roundtrip"},
        diagnostics={"available": True},
        manifest={"schema_version": "run-manifest/draft"},
    ).save(str(path))

    loaded = load_result(str(path))

    assert loaded.data["atom0"] == [1.0]
    assert loaded.metadata == {"example": "roundtrip"}
    assert loaded.diagnostics == {"available": True}
    assert loaded.manifest == {"schema_version": "run-manifest/draft"}


def test_legacy_result_dict_still_loads(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps({"t": [0.0], "atom0": [1.0]}))

    loaded = load_result(str(path))

    assert loaded.data == {"t": [0.0], "atom0": [1.0]}
    assert loaded.metadata == {}
    assert loaded.diagnostics == {}
    assert loaded.manifest == {}


def test_unsupported_result_schema_is_normalized(tmp_path):
    path = tmp_path / "future.json"
    path.write_text(json.dumps({"schema_version": "result-artifact/v99", "data": {}}))

    with pytest.raises(SagittariusSerializationError) as excinfo:
        load_result(str(path))

    assert excinfo.value.issue.code == "SERIALIZATION_SCHEMA_UNSUPPORTED"
    assert RESULT_ARTIFACT_SCHEMA_VERSION in excinfo.value.issue.remediation
