from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Dict, Tuple


EVENT_TAXONOMY_SCHEMA_VERSION = "event-taxonomy/v1"

SEVERITY_LEVELS: Dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


@dataclass(frozen=True)
class EventSpec:
    """Stable event catalog entry shared by logs, manifests, and diagnostics."""

    event_id: str
    name: str
    severity: str
    component: str
    description: str
    required_fields: Tuple[str, ...] = ()
    optional_fields: Tuple[str, ...] = ()
    status: str = "active"
    added_in: str = EVENT_TAXONOMY_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        data["required_fields"] = list(self.required_fields)
        data["optional_fields"] = list(self.optional_fields)
        return data


EVENT_CATALOG: Dict[str, EventSpec] = {
    "backend_init_start": EventSpec(
        event_id="SAG-EVT-0001",
        name="backend_init_start",
        severity="info",
        component="runtime",
        description="Julia backend initialization has started.",
        required_fields=("setup",),
    ),
    "backend_init_finish": EventSpec(
        event_id="SAG-EVT-0002",
        name="backend_init_finish",
        severity="info",
        component="runtime",
        description="Julia backend initialization completed successfully.",
        required_fields=("julia_version",),
    ),
    "backend_init_failed": EventSpec(
        event_id="SAG-EVT-0003",
        name="backend_init_failed",
        severity="error",
        component="runtime",
        description="Julia backend initialization failed with a classified diagnostic issue.",
        required_fields=("code", "message"),
    ),
    "doctor_report": EventSpec(
        event_id="SAG-EVT-0004",
        name="doctor_report",
        severity="info",
        component="runtime",
        description="Runtime capability diagnostics report was produced.",
        required_fields=("backend", "available", "issues"),
    ),
    "solver_start": EventSpec(
        event_id="SAG-EVT-0005",
        name="solver_start",
        severity="info",
        component="solver",
        description="Simulation solve has started after input validation and backend diagnostics.",
        required_fields=("backend", "use_gpu", "reltol", "abstol", "blockade_radius"),
        optional_fields=("method", "use_mc"),
    ),
    "solver_finish": EventSpec(
        event_id="SAG-EVT-0006",
        name="solver_finish",
        severity="info",
        component="solver",
        description="Simulation solve completed and produced a result.",
        required_fields=("result_type", "basis_size"),
        optional_fields=("backend",),
    ),
    "cluster_setup_start": EventSpec(
        event_id="SAG-EVT-0007",
        name="cluster_setup_start",
        severity="info",
        component="cluster",
        description="Distributed worker setup has started.",
        required_fields=("n_workers",),
    ),
    "cluster_setup_finish": EventSpec(
        event_id="SAG-EVT-0008",
        name="cluster_setup_finish",
        severity="info",
        component="cluster",
        description="Distributed worker setup completed.",
        required_fields=("n_workers",),
    ),
    "backend_selected": EventSpec(
        event_id="SAG-EVT-0009",
        name="backend_selected",
        severity="info",
        component="runtime",
        description="A solver backend was selected for execution.",
        required_fields=("backend", "use_gpu"),
        status="reserved",
    ),
    "basis_generated": EventSpec(
        event_id="SAG-EVT-0010",
        name="basis_generated",
        severity="info",
        component="physics",
        description="A full or blockade-reduced basis was generated.",
        required_fields=("atom_count", "basis_size", "full_basis_size", "blockade_radius"),
        optional_fields=("reduced_basis_pruning_ratio",),
        status="reserved",
    ),
    "hamiltonian_built": EventSpec(
        event_id="SAG-EVT-0011",
        name="hamiltonian_built",
        severity="info",
        component="physics",
        description="Hamiltonian construction completed for a register and pulse configuration.",
        required_fields=("atom_count", "basis_size", "use_gpu"),
        optional_fields=("backend", "nnz"),
        status="reserved",
    ),
    "gpu_allocation": EventSpec(
        event_id="SAG-EVT-0012",
        name="gpu_allocation",
        severity="info",
        component="runtime",
        description="A GPU allocation or transfer was attempted by a backend.",
        required_fields=("backend", "ok"),
        optional_fields=("bytes", "device", "code", "message"),
        status="reserved",
    ),
    "failure_diagnostic": EventSpec(
        event_id="SAG-EVT-0013",
        name="failure_diagnostic",
        severity="error",
        component="runtime",
        description="A normalized failure diagnostic was emitted.",
        required_fields=("code", "message", "remediation"),
        optional_fields=("backend", "severity"),
    ),
}


def event_taxonomy() -> Dict[str, object]:
    """Return the stable event taxonomy in a manifest-friendly shape."""
    return {
        "schema_version": EVENT_TAXONOMY_SCHEMA_VERSION,
        "severity_levels": dict(SEVERITY_LEVELS),
        "compatibility": {
            "event_id": "Stable once published; IDs are never reused for a different meaning.",
            "name": "Stable event names are snake_case and may be used as log filters.",
            "payload": "Required fields are additive only across compatible schema updates.",
            "severity": "Default severities may become more severe only for correctness or safety issues.",
            "status": "reserved entries document planned cross-language events before emitters exist.",
        },
        "events": {name: spec.to_dict() for name, spec in sorted(EVENT_CATALOG.items())},
    }


def get_event_spec(name: str) -> EventSpec:
    """Return a catalog entry by event name."""
    return EVENT_CATALOG[name]


def validate_event_payload(name: str, fields: Dict[str, object]) -> None:
    """Validate required payload fields for cataloged events."""
    spec = EVENT_CATALOG.get(name)
    if spec is None:
        return

    missing = [field for field in spec.required_fields if field not in fields]
    if missing:
        raise ValueError(f"Event {name!r} is missing required payload fields: {', '.join(missing)}")
