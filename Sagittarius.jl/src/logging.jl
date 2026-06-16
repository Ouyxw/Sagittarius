module StructuredLogging

using Logging

export log_event, event_spec

const EVENT_TAXONOMY_SCHEMA_VERSION = "event-taxonomy/v1"

const EVENT_CATALOG = Dict{String, NamedTuple}(
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
