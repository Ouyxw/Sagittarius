import json
import os

import numpy as np
import pytest

from sagittarius import (
    RESULT_ARTIFACT_SCHEMA_VERSION,
    RESULT_ARTIFACT_TYPE,
    SHARED_RESULT_SCHEMA_VERSION,
    SHARED_RESULT_TYPE,
    RUN_MANIFEST_SCHEMA,
    RUN_MANIFEST_SCHEMA_VERSION,
    Register,
    SagittariusSerializationError,
    SimulationResult,
    load_result,
    PulseSequence,
    SolverConfig,
    validate_run_manifest,
    validate_shared_result,
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
    assert payload["shared_result"]["schema_version"] == SHARED_RESULT_SCHEMA_VERSION
    assert payload["shared_result"]["artifact_type"] == SHARED_RESULT_TYPE
    assert payload["shared_result"]["series"] == payload["data"]
    assert payload["shared_result"]["time_key"] == "t"
    assert payload["shared_result"]["observable_names"] == ["atom0"]
    validate_shared_result(payload["shared_result"])
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


def test_run_manifest_schema_validates_generated_manifest():
    from sagittarius.api import _build_run_manifest

    reg = Register.chain(2, spacing=0.5, C6=2.0)
    seq = PulseSequence(omega=[1.0, 2.0], delta={0: 0.25})
    cfg = SolverConfig(reltol=1e-7, abstol=1e-9, blockade_radius=0.6)
    metadata = {
        "schema_version": "version-info/v1",
        "python_version": "3.test",
        "package_version": "0.test",
        "julia_version": None,
        "sagittarius_julia_version": "0.test",
        "platform": "test",
        "in_container": False,
        "python": {"packages": {"sagittarius-py": "0.test"}},
        "julia": {"project_path": "Sagittarius.jl"},
        "build": {"source": {"git_commit": "abc123"}},
        "container": {"detected": False},
        "backend_toolchains": {},
        "abi": {"python": {"cache_tag": "cpython-test"}},
    }
    diagnostics = {
        "schema_version": "doctor/v2.1",
        "requested_backend": "CPU",
        "available": True,
        "issues": [],
        "issue_details": [],
        "runtime": metadata,
        "capabilities": {"backend": "CPU", "parity": {"status": "regular_test_suite"}},
    }

    manifest = _build_run_manifest(
        register=reg,
        sequence=seq,
        config=cfg,
        t_start=0.0,
        t_end=1.0,
        observables={"pop0": 0},
        psi0=np.array([1.0, 0.0, 0.0], dtype=complex),
        diagnostics=diagnostics,
        metadata=metadata,
        result_type="observables",
    )

    validate_run_manifest(manifest)
    assert RUN_MANIFEST_SCHEMA["schema_version"] == RUN_MANIFEST_SCHEMA_VERSION
    assert manifest["schema_version"] == RUN_MANIFEST_SCHEMA_VERSION
    assert manifest["register"]["atom_count"] == 2
    assert manifest["register"]["geometry"]["blockade_edge_count"] == 1
    assert manifest["pulse"]["omega"]["kind"] == "local_vector"
    assert manifest["solver"]["observables"] == {"pop0": 0}
    assert manifest["solver"]["observable_metadata"] == []
    assert manifest["backend_diagnostics"]["requested_backend"] == "CPU"
    assert manifest["backend_diagnostics"]["issue_details"] == []
    assert manifest["versions"] == metadata
    assert manifest["versions"]["schema_version"] == "version-info/v1"
    assert manifest["versions"]["build"]["source"]["git_commit"] == "abc123"
    assert manifest["event_taxonomy_schema"] == "event-taxonomy/v1"
    assert manifest["event_ids"] == ["SAG-EVT-0004", "SAG-EVT-0005", "SAG-EVT-0006"]
    assert manifest["solver"]["saveat"] is None
    assert manifest["solver"]["effective_saveat"] is None
    assert manifest["random"] == {"seed": None, "effective_seed": None, "n_trajectories": None}


def test_validate_run_manifest_rejects_unknown_event_id():
    manifest = {
        "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
        "created_at": "2026-06-15T00:00:00+00:00",
        "result_type": "observables",
        "register": {"atom_count": 0, "C6": 1.0, "atoms": [], "geometry": {}},
        "pulse": {"omega": {"kind": "scalar", "value": 1.0}, "delta": {"kind": "scalar", "value": 0.0}},
        "solver": {
            "method": "Tsit5",
            "t_span": [0.0, 1.0],
            "reltol": 1e-8,
            "abstol": 1e-8,
            "blockade_radius": 0.0,
            "gamma": 0.0,
            "gamma_phi": 0.0,
            "use_mc": False,
            "n_trajectories": 100,
            "use_gpu": False,
            "gpu_backend": "CUDA",
            "observables": {},
            "observable_metadata": [],
            "saveat": None,
            "effective_saveat": None,
        },
        "initial_state": {"basis_size": 1, "norm": 1.0},
        "backend_diagnostics": {
            "requested_backend": "CPU",
            "available": True,
            "issues": [],
            "issue_details": [],
            "backend_probe_schema": None,
            "backend_probe_available": None,
            "versions": {},
            "devices": [],
        },
        "versions": {},
        "event_taxonomy_schema": "event-taxonomy/v1",
        "event_ids": ["SAG-EVT-9999"],
        "random": {"seed": None, "effective_seed": None, "n_trajectories": None},
    }

    with pytest.raises(SagittariusSerializationError) as excinfo:
        validate_run_manifest(manifest)

    assert excinfo.value.issue.code == "SERIALIZATION_RUN_MANIFEST_SCHEMA_INVALID"
    assert "event_ids" in excinfo.value.issue.message


def test_shared_result_validation_rejects_missing_observable_series():
    with pytest.raises(SagittariusSerializationError) as excinfo:
        validate_shared_result({
            "schema_version": SHARED_RESULT_SCHEMA_VERSION,
            "artifact_type": SHARED_RESULT_TYPE,
            "result_type": "observables",
            "series": {"t": [0.0]},
            "time_key": "t",
            "observable_names": ["missing"],
            "basis_size": 2,
            "manifest_schema": RUN_MANIFEST_SCHEMA_VERSION,
        })

    assert excinfo.value.issue.code == "SERIALIZATION_SHARED_RESULT_SCHEMA_INVALID"
    assert "missing" in excinfo.value.issue.message


def test_simulation_result_to_shared_result_uses_manifest_semantics():
    result = SimulationResult(
        {"t": [0.0], "pop": [1.0]},
        manifest={
            "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
            "result_type": "observables",
            "initial_state": {"basis_size": 4},
        },
    )

    shared = result.to_shared_result()

    assert shared["schema_version"] == SHARED_RESULT_SCHEMA_VERSION
    assert shared["result_type"] == "observables"
    assert shared["basis_size"] == 4
    assert shared["manifest_schema"] == RUN_MANIFEST_SCHEMA_VERSION
    assert shared["observable_names"] == ["pop"]
