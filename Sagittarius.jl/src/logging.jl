module StructuredLogging

using Logging

export log_event, event_spec

const EVENT_TAXONOMY_SCHEMA_VERSION = "event-taxonomy/v1"

const EVENT_CATALOG = Dict{String, NamedTuple}(
    "backend_init_start" => (
        event_id="SAG-EVT-0001",
        severity="info",
        component="runtime",
        required_fields=(:setup,),
    ),
    "backend_init_finish" => (
        event_id="SAG-EVT-0002",
        severity="info",
        component="runtime",
        required_fields=(:julia_version,),
    ),
    "backend_init_failed" => (
        event_id="SAG-EVT-0003",
        severity="error",
        component="runtime",
        required_fields=(:code, :message),
    ),
    "doctor_report" => (
        event_id="SAG-EVT-0004",
        severity="info",
        component="runtime",
        required_fields=(:backend, :available, :issues),
    ),
    "solver_start" => (
        event_id="SAG-EVT-0005",
        severity="info",
        component="solver",
        required_fields=(:backend, :use_gpu, :reltol, :abstol, :blockade_radius),
    ),
    "solver_finish" => (
        event_id="SAG-EVT-0006",
        severity="info",
        component="solver",
        required_fields=(:result_type, :basis_size),
    ),
    "cluster_setup_start" => (
        event_id="SAG-EVT-0007",
        severity="info",
        component="cluster",
        required_fields=(:n_workers,),
    ),
    "cluster_setup_finish" => (
        event_id="SAG-EVT-0008",
        severity="info",
        component="cluster",
        required_fields=(:n_workers,),
    ),
    "backend_selected" => (
        event_id="SAG-EVT-0009",
        severity="info",
        component="runtime",
        required_fields=(:backend, :use_gpu),
    ),
    "basis_generated" => (
        event_id="SAG-EVT-0010",
        severity="info",
        component="physics",
        required_fields=(:atom_count, :basis_size, :full_basis_size, :blockade_radius),
    ),
    "hamiltonian_built" => (
        event_id="SAG-EVT-0011",
        severity="info",
        component="physics",
        required_fields=(:atom_count, :basis_size, :use_gpu),
    ),
    "gpu_allocation" => (
        event_id="SAG-EVT-0012",
        severity="info",
        component="runtime",
        required_fields=(:backend, :ok),
    ),
    "failure_diagnostic" => (
        event_id="SAG-EVT-0013",
        severity="error",
        component="runtime",
        required_fields=(:code, :message, :remediation),
    ),
)

const SEVERITY_LEVELS = Dict(
    "debug" => Logging.Debug,
    "info" => Logging.Info,
    "warning" => Logging.Warn,
    "error" => Logging.Error,
)

event_spec(name::AbstractString) = get(EVENT_CATALOG, String(name), nothing)

function _validate_event_payload(event::String, spec, fields::NamedTuple)
    isnothing(spec) && return nothing
    missing = Symbol[]
    for field in spec.required_fields
        if !haskey(fields, field)
            push!(missing, field)
        end
    end
    if !isempty(missing)
        throw(ArgumentError("Event $(repr(event)) is missing required payload fields: $(join(string.(missing), ", "))"))
    end
    return nothing
end

function log_event(event::AbstractString; level=nothing, kwargs...)
    event_name = String(event)
    fields = (; kwargs...)
    spec = event_spec(event_name)
    _validate_event_payload(event_name, spec, fields)

    severity = isnothing(spec) ? "info" : spec.severity
    log_level = isnothing(level) ? get(SEVERITY_LEVELS, severity, Logging.Info) : level
    payload = isnothing(spec) ?
        (event=event_name, event_id=nothing, event_schema=nothing, severity=severity, fields...) :
        (event=event_name, event_id=spec.event_id, event_schema=EVENT_TAXONOMY_SCHEMA_VERSION,
         severity=severity, component=spec.component, fields...)

    @logmsg log_level event_name payload...
    return payload
end

end # module StructuredLogging
