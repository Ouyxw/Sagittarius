import json
import logging

import numpy as np
import pytest

from sagittarius import (
    Atom,
    PulseSequence,
    Register,
    SagittariusSerializationError,
    SagittariusSolverError,
    SagittariusValidationError,
    Simulation,
    SimulationResult,
    SolverConfig,
    load_result,
)


def _sim(sequence=None, *, config=None):
    return Simulation(
        Register([Atom(0, 0, 0), Atom(1, 0, 0)], C6=0.0),
        sequence or PulseSequence(),
        config or SolverConfig(),
    )


def test_validation_errors_carry_normalized_issue_and_remain_value_errors():
    sim = _sim(PulseSequence(omega=[1.0]))

    with pytest.raises(ValueError) as excinfo:
        sim.validate_inputs(sample_time=0.0)

    exc = excinfo.value
    assert isinstance(exc, SagittariusValidationError)
    assert exc.issue.code == "VALIDATION_PULSE_LIST_LENGTH"
    assert "one pulse value per atom" in exc.issue.remediation
    assert "omega list length 1 does not match 2 atoms" in str(exc)


def test_run_emits_failure_diagnostic_for_validation_errors(caplog):
    import sagittarius.runtime as runtime

    runtime.configure_logging(logging.INFO, json_output=True)
    caplog.set_level(logging.ERROR, logger="sagittarius")

    sim = _sim(PulseSequence(omega=[1.0]))
    with pytest.raises(SagittariusValidationError):
        sim.run(np.array([1.0 + 0j, 0.0 + 0j, 0.0 + 0j, 0.0 + 0j]), 0.0, 1.0)

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "failure_diagnostic"
    assert payload["event_id"] == "SAG-EVT-0013"
    assert payload["code"] == "VALIDATION_PULSE_LIST_LENGTH"
    assert payload["remediation"]


def test_solver_errors_are_normalized(monkeypatch):
    sim = _sim()

    def fail_impl(*args, **kwargs):
        raise RuntimeError("low-level integrator failure")

    monkeypatch.setattr(sim, "_run_impl", fail_impl)

    with pytest.raises(SagittariusSolverError) as excinfo:
        sim.run(np.array([1.0 + 0j, 0.0 + 0j, 0.0 + 0j, 0.0 + 0j]), 0.0, 1.0)

    assert excinfo.value.issue.code == "SOLVER_EXECUTION_FAILED"
    assert "doctor(initialize_backend=True)" in excinfo.value.issue.remediation


def test_serialization_write_errors_are_normalized(tmp_path):
    res = SimulationResult({"t": [0.0], "bad": [object()]})

    with pytest.raises(SagittariusSerializationError) as excinfo:
        res.save(str(tmp_path / "bad.json"))

    assert excinfo.value.issue.code == "SERIALIZATION_NOT_JSON_COMPATIBLE"
    assert "JSON-compatible" in excinfo.value.issue.remediation


def test_serialization_read_errors_are_normalized(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not-json")

    with pytest.raises(SagittariusSerializationError) as excinfo:
        load_result(str(path))

    assert excinfo.value.issue.code == "SERIALIZATION_INVALID_JSON"
    assert "repair the JSON" in excinfo.value.issue.remediation
