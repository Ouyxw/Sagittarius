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
    assert taxonomy["events"]["basis_generated"]["status"] == "active"
    assert taxonomy["events"]["hamiltonian_built"]["status"] == "active"


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


def test_julia_physics_emitters_use_structured_event_taxonomy():
    from sagittarius.runtime import get_julia

    jl, _ = get_julia()
    report = jl.seval("""
    begin
        using Logging
        using Test
        using StaticArrays

        Sagittarius.Physics._clear_reduced_basis_cache!()
        logger = Test.TestLogger()
        reg = Sagittarius.Physics.Register([
            Sagittarius.Physics.Atom(SVector(0.0, 0.0, 0.0)),
            Sagittarius.Physics.Atom(SVector(0.5, 0.0, 0.0)),
        ], 10.0)

        with_logger(logger) do
            Sagittarius.Physics.RydbergHamiltonian(reg, [1.0, 1.0], [0.0, 0.0]; blockade_radius=0.75)
        end

        basis_record = logger.logs[1]
        hamiltonian_record = logger.logs[2]
        Dict(
            "basis_message" => basis_record.message,
            "basis_event_id" => basis_record.kwargs[:event_id],
            "basis_schema" => basis_record.kwargs[:event_schema],
            "basis_component" => basis_record.kwargs[:component],
            "basis_size" => basis_record.kwargs[:basis_size],
            "hamiltonian_message" => hamiltonian_record.message,
            "hamiltonian_event_id" => hamiltonian_record.kwargs[:event_id],
            "hamiltonian_schema" => hamiltonian_record.kwargs[:event_schema],
            "hamiltonian_component" => hamiltonian_record.kwargs[:component],
            "hamiltonian_basis_size" => hamiltonian_record.kwargs[:basis_size],
            "hamiltonian_use_gpu" => hamiltonian_record.kwargs[:use_gpu],
        )
    end
    """)

    assert report["basis_message"] == "basis_generated"
    assert report["basis_event_id"] == "SAG-EVT-0010"
    assert report["basis_schema"] == "event-taxonomy/v1"
    assert report["basis_component"] == "physics"
    assert report["basis_size"] == 3
    assert report["hamiltonian_message"] == "hamiltonian_built"
    assert report["hamiltonian_event_id"] == "SAG-EVT-0011"
    assert report["hamiltonian_schema"] == "event-taxonomy/v1"
    assert report["hamiltonian_component"] == "physics"
    assert report["hamiltonian_basis_size"] == 3
    assert report["hamiltonian_use_gpu"] is False


def test_julia_log_event_validates_required_payload_fields():
    from sagittarius.runtime import get_julia

    jl, _ = get_julia()
    message = jl.seval("""
    begin
        try
            Sagittarius.StructuredLogging.log_event("basis_generated"; atom_count=2, basis_size=3, full_basis_size=4)
            "missing validation"
        catch err
            sprint(showerror, err)
        end
    end
    """)

    assert "blockade_radius" in message
