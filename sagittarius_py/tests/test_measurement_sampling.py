import json

import numpy as np
import pytest

from sagittarius import (
    Register,
    PulseSequence,
    SimulationResult,
    SolverConfig,
    load_result,
    validate_run_manifest,
)
from sagittarius.api import _simulation_result_with_manifest


def _metadata():
    return {"schema_version": "version-info/v1", "package_version": "test"}


def _diagnostics(metadata):
    return {
        "schema_version": "doctor/v2.1",
        "requested_backend": "CPU",
        "available": True,
        "issues": [],
        "issue_details": [],
        "runtime": metadata,
    }


def test_simulation_result_sample_is_seed_reproducible():
    result = SimulationResult(
        {"t": [0.0, 1.0], "pop0": [0.0, 0.5]},
        metadata={
            "readout": {
                "schema_version": "readout-metadata/v1",
                "final_bitstring_probabilities": {"0": 0.25, "1": 0.75},
            }
        },
        manifest={
            "schema_version": "run-manifest/v1",
            "readout": {
                "basis_mode": "full",
                "forbidden_bitstrings_excluded": False,
                "forbidden_bitstring_count": 0,
            },
        },
    )

    first = result.sample(32, seed=1234)
    second = result.sample(32, seed=1234)

    assert first == second
    assert first["schema_version"] == "measurement-samples/v1"
    assert first["shots"] == 32
    assert first["seed"] == 1234
    assert sum(first["counts"].values()) == 32
    assert first["probabilities"] == {"0": 0.25, "1": 0.75}


def test_sample_rejects_missing_distribution_and_invalid_shots():
    result = SimulationResult({"t": [0.0], "pop0": [0.0]})

    with pytest.raises(Exception) as missing_exc:
        result.sample(1, seed=1)
    assert missing_exc.value.issue.code == "VALIDATION_READOUT_DISTRIBUTION_MISSING"

    result = SimulationResult(
        {"t": [0.0]},
        metadata={"readout": {"final_bitstring_probabilities": {"0": 1.0}}},
    )
    with pytest.raises(Exception) as shots_exc:
        result.sample(0, seed=1)
    assert shots_exc.value.issue.code == "VALIDATION_SAMPLE_SHOTS_VALUE"


def test_readout_distribution_is_in_shared_result_and_artifact_roundtrip(tmp_path):
    result = SimulationResult(
        {"t": [0.0, 1.0], "pop0": [0.0, 1.0]},
        metadata={
            "readout": {
                "schema_version": "readout-metadata/v1",
                "final_bitstring_probabilities": {"0": 0.0, "1": 1.0},
            }
        },
        manifest={"schema_version": "run-manifest/v1", "initial_state": {"basis_size": 2}},
    )

    shared = result.to_shared_result()
    assert shared["series"]["final_bitstring_probabilities"] == {"0": 0.0, "1": 1.0}
    assert "final_bitstring_probabilities" not in shared["observable_names"]

    path = tmp_path / "result.json"
    result.save(str(path))
    payload = json.loads(path.read_text())
    assert payload["shared_result"]["series"]["final_bitstring_probabilities"] == {"0": 0.0, "1": 1.0}

    loaded = load_result(str(path))
    assert loaded.final_bitstring_distribution() == {"0": 0.0, "1": 1.0}
    assert loaded.sample(4, seed=5)["counts"] == {"1": 4}


def test_manifest_readout_handles_reduced_basis_forbidden_bitstrings():
    reg = Register.chain(2, spacing=0.5, C6=2.0)
    metadata = _metadata()
    result = _simulation_result_with_manifest(
        {"t": [0.0, 1.0], "pop0": [0.0, 0.5]},
        metadata=metadata,
        diagnostics=_diagnostics(metadata),
        register=reg,
        sequence=PulseSequence(),
        config=SolverConfig(blockade_radius=0.6),
        t_start=0.0,
        t_end=1.0,
        observables={"pop0": 0},
        observable_metadata=[],
        psi0=np.array([1.0, 0.0, 0.0], dtype=complex),
        result_type="observables",
        final_state=np.array([0.0, 1.0, 0.0], dtype=complex),
        basis=[0, 1, 2],
    )

    validate_run_manifest(result.manifest)
    assert result.manifest["readout"]["basis_mode"] == "reduced"
    assert result.manifest["readout"]["basis_bitstrings"] == ["00", "10", "01"]
    assert result.manifest["readout"]["forbidden_bitstrings_excluded"] is True
    assert result.manifest["readout"]["forbidden_bitstring_count"] == 1
    assert result.final_bitstring_distribution() == {"00": 0.0, "10": 1.0, "01": 0.0}
    assert result.sample(8, seed=99)["counts"] == {"10": 8}
