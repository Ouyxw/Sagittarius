"""Backend-free coverage for experiment-config/v1 validation and persistence."""
import json

import pytest

from sagittarius import (
    EXPERIMENT_CONFIG_SCHEMA_VERSION,
    SagittariusValidationError,
    load_experiment_config,
    save_experiment_config,
    validate_experiment_config,
)


def _config():
    return {
        "schema_version": EXPERIMENT_CONFIG_SCHEMA_VERSION,
        "register": {"atoms": [[0.0, 0.0]], "C6": 0.0},
        "pulse": {"omega": 1.0, "delta": {"type": "ramp", "start_val": 0.0, "end_val": 1.0, "duration": 1.0}},
        "solver": {"seed": 12, "saveat": [0.0, 0.5, 1.0]},
        "time_span": [0.0, 1.0],
        "initial_state": {"bitstring": "0"},
        "observables": {"population": 0},
        "readout": {"shots": 20, "seed": 8},
        "outputs": {"result": "artifacts/result.json", "manifest": "artifacts/manifest.json", "samples": "artifacts/samples.json"},
    }


def test_experiment_config_round_trips_with_stable_digest(tmp_path):
    path = tmp_path / "experiment.json"
    saved = save_experiment_config(_config(), path)
    loaded = load_experiment_config(path)

    assert loaded.document == saved.document
    assert loaded.sha256 == saved.sha256
    assert loaded.source_path == path.resolve()
    assert json.loads(path.read_text())["schema_version"] == EXPERIMENT_CONFIG_SCHEMA_VERSION


def test_experiment_config_rejects_nonreproducible_or_incomplete_shapes():
    missing = _config()
    del missing["initial_state"]
    with pytest.raises(SagittariusValidationError) as excinfo:
        validate_experiment_config(missing)
    assert excinfo.value.issue.code == "VALIDATION_EXPERIMENT_CONFIG_REQUIRED_FIELD"

    samples_without_readout = _config()
    del samples_without_readout["readout"]
    with pytest.raises(SagittariusValidationError) as excinfo:
        validate_experiment_config(samples_without_readout)
    assert excinfo.value.issue.code == "VALIDATION_EXPERIMENT_CONFIG_SAMPLES_WITHOUT_READOUT"
