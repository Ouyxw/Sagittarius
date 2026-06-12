import json

import pytest


def test_event_taxonomy_exposes_stable_catalog():
    from sagittarius import event_taxonomy, get_event_spec

    taxonomy = event_taxonomy()

    assert taxonomy["schema_version"] == "event-taxonomy/v1"
    assert taxonomy["events"]["solver_start"]["event_id"] == "SAG-EVT-0005"
    assert taxonomy["events"]["solver_start"]["required_fields"] == [
        "backend",
        "use_gpu",
        "reltol",
        "abstol",
        "blockade_radius",
    ]
    assert get_event_spec("backend_init_failed").severity == "error"


def test_event_ids_are_unique_and_severities_are_declared():
    from sagittarius import event_taxonomy

    taxonomy = event_taxonomy()
    event_ids = [entry["event_id"] for entry in taxonomy["events"].values()]

    assert len(event_ids) == len(set(event_ids))
    assert {entry["severity"] for entry in taxonomy["events"].values()} <= set(taxonomy["severity_levels"])


def test_log_event_enriches_json_payload(caplog):
    import logging
    import sagittarius.runtime as runtime

    runtime.configure_logging(logging.INFO, json_output=True)
    caplog.set_level(logging.INFO, logger="sagittarius")

    try:
        runtime.log_event(
            "solver_start",
            backend="CPU",
            use_gpu=False,
            reltol=1e-8,
            abstol=1e-8,
            blockade_radius=0.0,
        )
    finally:
        runtime.configure_logging(logging.INFO, json_output=False)

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "solver_start"
    assert payload["event_id"] == "SAG-EVT-0005"
    assert payload["event_schema"] == "event-taxonomy/v1"
    assert payload["severity"] == "info"


def test_log_event_validates_required_payload_fields():
    import sagittarius.runtime as runtime

    with pytest.raises(ValueError, match="blockade_radius"):
        runtime.log_event("solver_start", backend="CPU", use_gpu=False, reltol=1e-8, abstol=1e-8)
