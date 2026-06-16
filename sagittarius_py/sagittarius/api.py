from __future__ import annotations

import json
import numbers
from datetime import datetime, timezone
from collections.abc import Sequence as ABCSequence
from dataclasses import dataclass, field
from typing import Optional, Dict, Union, Any, List, Tuple

import numpy as np
RESULT_ARTIFACT_SCHEMA_VERSION = "result-artifact/v1"
RESULT_ARTIFACT_TYPE = "sagittarius.simulation_result"
RUN_MANIFEST_SCHEMA_VERSION = "run-manifest/v1"
RUN_MANIFEST_SCHEMA = {
    "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
    "artifact_type": "sagittarius.run_manifest",
    "required": [
        "schema_version",
        "created_at",
        "result_type",
        "register",
        "pulse",
        "solver",
        "initial_state",
        "backend_diagnostics",
        "versions",
        "event_taxonomy_schema",
        "event_ids",
        "random",
    ],
    "sections": {
        "register": ["atom_count", "C6", "atoms", "geometry"],
        "pulse": ["omega", "delta"],
        "solver": [
            "method",
            "t_span",
            "reltol",
            "abstol",
            "blockade_radius",
            "gamma",
            "gamma_phi",
            "use_mc",
            "n_trajectories",
            "use_gpu",
            "gpu_backend",
            "observables",
        ],
        "initial_state": ["basis_size", "norm"],
        "backend_diagnostics": [
            "requested_backend",
            "available",
            "issues",
            "issue_details",
            "backend_probe_schema",
            "backend_probe_available",
            "versions",
            "devices",
        ],
        "random": ["seed", "n_trajectories"],
    },
}

from .events import EVENT_CATALOG, EVENT_TAXONOMY_SCHEMA_VERSION, get_event_spec
from .runtime import (
    SagittariusError,
    SagittariusSerializationError,
    SagittariusSolverError,
    SagittariusValidationError,
    doctor,
    emit_failure_diagnostic,
    get_julia,
    get_modules,
    log_event,
    make_issue,
    version_info,
)

def _constructor_error(code: str, message: str, remediation: str) -> SagittariusValidationError:
    return SagittariusValidationError(make_issue(code, message, remediation))


def _coerce_xyz(value: Any, *, field_name: str) -> Tuple[float, float, float]:
    if isinstance(value, np.ndarray):
        raw = value.tolist()
    elif isinstance(value, ABCSequence) and not isinstance(value, (str, bytes, bytearray)):
        raw = list(value)
    else:
        raise _constructor_error(
            "VALIDATION_REGISTER_COORDINATE_TYPE",
            f"{field_name} must be a 2D or 3D coordinate sequence, got {type(value).__name__}",
            "Provide coordinates as (x, y) or (x, y, z) numeric sequences.",
        )

    if len(raw) == 2:
        raw.append(0.0)
    if len(raw) != 3:
        raise _constructor_error(
            "VALIDATION_REGISTER_COORDINATE_DIMENSION",
            f"{field_name} must contain 2 or 3 values, got {len(raw)}",
            "Provide coordinates as (x, y) or (x, y, z) numeric sequences.",
        )
    try:
        return (float(raw[0]), float(raw[1]), float(raw[2]))
    except (TypeError, ValueError) as exc:
        raise _constructor_error(
            "VALIDATION_REGISTER_COORDINATE_VALUE",
            f"{field_name} must contain numeric coordinate values.",
            "Convert coordinate values to real numbers before constructing the register.",
        ) from exc


def _positive_int(value: Any, *, field_name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise _constructor_error(
            "VALIDATION_REGISTER_SIZE_TYPE",
            f"{field_name} must be a positive integer, got {value!r}",
            "Use a positive integer atom count or lattice dimension.",
        )
    value = int(value)
    if value <= 0:
        raise _constructor_error(
            "VALIDATION_REGISTER_SIZE_VALUE",
            f"{field_name} must be positive, got {value}",
            "Use at least one atom in specialized register constructors.",
        )
    return value


def _positive_float(value: Any, *, field_name: str) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise _constructor_error(
            "VALIDATION_REGISTER_SPACING_TYPE",
            f"{field_name} must be a positive numeric value.",
            "Use a positive numeric spacing or blockade radius.",
        ) from exc
    if value <= 0.0:
        raise _constructor_error(
            "VALIDATION_REGISTER_SPACING_VALUE",
            f"{field_name} must be positive, got {value}",
            "Use a positive numeric spacing or blockade radius.",
        )
    return value


@dataclass
class Atom:
    x: float
    y: float
    z: float = 0.0

    @property
    def jl_obj(self):
        jl, _, phys, _ = get_modules()
        return phys.Atom(jl.SVector(float(self.x), float(self.y), float(self.z)))

@dataclass
class Register:
    atoms: List[Atom]
    C6: float = 1.0
    topology: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def chain(
        cls,
        n: int,
        *,
        spacing: float = 1.0,
        C6: float = 1.0,
        origin: Any = (0.0, 0.0, 0.0),
        axis: str = "x",
    ) -> "Register":
        n = _positive_int(n, field_name="n")
        spacing = _positive_float(spacing, field_name="spacing")
        ox, oy, oz = _coerce_xyz(origin, field_name="origin")
        axes = {"x": (spacing, 0.0, 0.0), "y": (0.0, spacing, 0.0), "z": (0.0, 0.0, spacing)}
        if axis not in axes:
            raise _constructor_error(
                "VALIDATION_REGISTER_AXIS",
                f"axis must be one of 'x', 'y', or 'z', got {axis!r}",
                "Choose an axis from {'x', 'y', 'z'} for Register.chain().",
            )
        dx, dy, dz = axes[axis]
        atoms = [Atom(ox + i * dx, oy + i * dy, oz + i * dz) for i in range(n)]
        return cls(atoms, C6=C6, topology={"kind": "chain", "n": n, "spacing": spacing, "axis": axis, "origin": [ox, oy, oz]})

    @classmethod
    def square_lattice(
        cls,
        rows: int,
        cols: int,
        *,
        spacing: float = 1.0,
        C6: float = 1.0,
        origin: Any = (0.0, 0.0, 0.0),
        plane: str = "xy",
    ) -> "Register":
        rows = _positive_int(rows, field_name="rows")
        cols = _positive_int(cols, field_name="cols")
        spacing = _positive_float(spacing, field_name="spacing")
        ox, oy, oz = _coerce_xyz(origin, field_name="origin")
        planes = {
            "xy": ((spacing, 0.0, 0.0), (0.0, spacing, 0.0)),
            "xz": ((spacing, 0.0, 0.0), (0.0, 0.0, spacing)),
            "yz": ((0.0, spacing, 0.0), (0.0, 0.0, spacing)),
        }
        if plane not in planes:
            raise _constructor_error(
                "VALIDATION_REGISTER_PLANE",
                f"plane must be one of 'xy', 'xz', or 'yz', got {plane!r}",
                "Choose a plane from {'xy', 'xz', 'yz'} for Register.square_lattice().",
            )
        row_step, col_step = planes[plane]
        atoms = []
        for r in range(rows):
            for c in range(cols):
                atoms.append(Atom(
                    ox + r * row_step[0] + c * col_step[0],
                    oy + r * row_step[1] + c * col_step[1],
                    oz + r * row_step[2] + c * col_step[2],
                ))
        return cls(
            atoms,
            C6=C6,
            topology={"kind": "square_lattice", "rows": rows, "cols": cols, "spacing": spacing, "plane": plane, "origin": [ox, oy, oz]},
        )

    @classmethod
    def udg(
        cls,
        points: Optional[Any] = None,
        *,
        graph: Optional[Any] = None,
        position_attr: str = "pos",
        C6: float = 1.0,
        blockade_radius: Optional[float] = None,
    ) -> "Register":
        if graph is not None and points is not None:
            raise _constructor_error(
                "VALIDATION_REGISTER_UDG_SOURCE",
                "Register.udg() accepts either points or graph, not both.",
                "Pass coordinate points directly or pass a graph with node position attributes.",
            )
        node_order = None
        if graph is not None:
            node_order = list(graph.nodes())
            raw_points = [graph.nodes[node].get(position_attr, (0.0, 0.0)) for node in node_order]
        elif points is not None:
            raw_points = list(points)
        else:
            raise _constructor_error(
                "VALIDATION_REGISTER_UDG_SOURCE",
                "Register.udg() requires points or graph.",
                "Pass coordinate points directly or pass a graph with node position attributes.",
            )
        coords = [_coerce_xyz(point, field_name=f"points[{i}]") for i, point in enumerate(raw_points)]
        if not coords:
            raise _constructor_error(
                "VALIDATION_REGISTER_SIZE_VALUE",
                "Register.udg() requires at least one point.",
                "Pass at least one 2D or 3D coordinate.",
            )
        topology: Dict[str, Any] = {"kind": "udg", "n": len(coords)}
        if node_order is not None:
            topology["node_order"] = [str(node) for node in node_order]
            topology["position_attr"] = position_attr
        if blockade_radius is not None:
            topology["blockade_radius"] = _positive_float(blockade_radius, field_name="blockade_radius")
        return cls([Atom(x, y, z) for x, y, z in coords], C6=C6, topology=topology)

    @classmethod
    def from_udg_graph(cls, graph: Any, *, position_attr: str = "pos", C6: float = 1.0, blockade_radius: Optional[float] = None) -> "Register":
        return cls.udg(graph=graph, position_attr=position_attr, C6=C6, blockade_radius=blockade_radius)

    def geometry_summary(self, *, blockade_radius: Optional[float] = None, include_edges: bool = True) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            "atom_count": len(self.atoms),
            "topology": dict(self.topology),
        }
        if blockade_radius is not None and blockade_radius > 0:
            edges = []
            coords = np.array([[atom.x, atom.y, atom.z] for atom in self.atoms], dtype=float)
            for i in range(len(self.atoms)):
                for j in range(i + 1, len(self.atoms)):
                    if float(np.linalg.norm(coords[i] - coords[j])) < float(blockade_radius):
                        edges.append([i, j])
            summary["blockade_radius"] = float(blockade_radius)
            summary["blockade_edge_count"] = len(edges)
            if include_edges:
                summary["blockade_edges"] = edges
        return summary

    @property
    def jl_obj(self):
        jl, _, phys, _ = get_modules()
        jl_atoms = jl.Vector[phys.Atom]([a.jl_obj for a in self.atoms])
        return phys.Register(jl_atoms, float(self.C6))

@dataclass
class SolverConfig:
    reltol: float = 1e-8
    abstol: float = 1e-8
    blockade_radius: float = 0.0
    method: str = "Tsit5"
    gamma: Union[float, List[float]] = 0.0      # T1 decay rate
    gamma_phi: Union[float, List[float]] = 0.0  # T2 dephasing rate
    use_mc: bool = False                        # Use Monte Carlo Trajectories instead of Lindblad
    n_trajectories: int = 100                   # Number of trajectories for Monte Carlo
    use_gpu: bool = False                       # Use GPU acceleration
    gpu_backend: str = "CUDA"                   # GPU backend: "CUDA", "AMDGPU", or "Metal"

@dataclass
class PulseSequence:
    omega: Any = 1.0
    delta: Any = 0.0


def _is_bool(value: Any) -> bool:
    return isinstance(value, (bool, np.bool_))


def _is_numeric_scalar(value: Any) -> bool:
    return isinstance(value, numbers.Real) and not _is_bool(value)


def _validation_error(code: str, message: str, remediation: str) -> SagittariusValidationError:
    return SagittariusValidationError(make_issue(code, message, remediation))


def _serialization_error(code: str, message: str, remediation: str) -> SagittariusSerializationError:
    return SagittariusSerializationError(make_issue(code, message, remediation))


def _manifest_schema_error(message: str, remediation: str) -> SagittariusSerializationError:
    return _serialization_error("SERIALIZATION_RUN_MANIFEST_SCHEMA_INVALID", message, remediation)


def validate_run_manifest(manifest: Dict[str, Any]) -> None:
    """Validate the stable run-manifest/v1 structure produced by Sagittarius."""
    if not isinstance(manifest, dict):
        raise _manifest_schema_error(
            "Run manifest must be a JSON object.",
            "Pass the manifest dictionary produced by Simulation.run() or load_result().",
        )
    if manifest.get("schema_version") != RUN_MANIFEST_SCHEMA_VERSION:
        raise _manifest_schema_error(
            f"Run manifest has unsupported schema_version: {manifest.get('schema_version')!r}.",
            f"Use a manifest with schema_version {RUN_MANIFEST_SCHEMA_VERSION!r}.",
        )

    missing = [field for field in RUN_MANIFEST_SCHEMA["required"] if field not in manifest]
    if missing:
        raise _manifest_schema_error(
            f"Run manifest is missing required fields: {', '.join(missing)}.",
            "Regenerate the result with Simulation.run() and SimulationResult.save().",
        )

    for section, fields in RUN_MANIFEST_SCHEMA["sections"].items():
        value = manifest.get(section)
        if not isinstance(value, dict):
            raise _manifest_schema_error(
                f"Run manifest field {section!r} must be a JSON object.",
                "Regenerate the result with Simulation.run() and SimulationResult.save().",
            )
        section_missing = [field for field in fields if field not in value]
        if section_missing:
            raise _manifest_schema_error(
                f"Run manifest section {section!r} is missing fields: {', '.join(section_missing)}.",
                "Regenerate the result with Simulation.run() and SimulationResult.save().",
            )

    register = manifest["register"]
    atoms = register.get("atoms")
    if not isinstance(register.get("atom_count"), int) or register["atom_count"] < 0:
        raise _manifest_schema_error("Run manifest register.atom_count must be a non-negative integer.", "Regenerate the manifest from a valid Register.")
    if not isinstance(atoms, list) or len(atoms) != register["atom_count"]:
        raise _manifest_schema_error("Run manifest register.atoms length must match register.atom_count.", "Regenerate the manifest from a valid Register.")

    solver = manifest["solver"]
    if not (isinstance(solver.get("t_span"), list) and len(solver["t_span"]) == 2):
        raise _manifest_schema_error("Run manifest solver.t_span must contain exactly [t_start, t_end].", "Regenerate the manifest from Simulation.run().")

    if manifest.get("event_taxonomy_schema") != EVENT_TAXONOMY_SCHEMA_VERSION:
        raise _manifest_schema_error(
            f"Run manifest has unsupported event_taxonomy_schema: {manifest.get('event_taxonomy_schema')!r}.",
            f"Use event_taxonomy_schema {EVENT_TAXONOMY_SCHEMA_VERSION!r} for {RUN_MANIFEST_SCHEMA_VERSION} manifests.",
        )

    event_ids = manifest.get("event_ids")
    known_event_ids = {spec.event_id for spec in EVENT_CATALOG.values()}
    if not isinstance(event_ids, list) or not all(isinstance(event_id, str) and event_id in known_event_ids for event_id in event_ids):
        raise _manifest_schema_error(
            "Run manifest event_ids must be known Sagittarius event taxonomy IDs.",
            "Use cataloged event IDs from event_taxonomy() when constructing manifests.",
        )


def _json_compatible(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _json_compatible(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(v) for v in value]
    return value


def _explicit_pulse_kind(value: Any) -> Optional[str]:
    from .pulse import CallablePulse, GlobalPulse, LocalPulseVector

    if isinstance(value, GlobalPulse):
        return "global"
    if isinstance(value, LocalPulseVector):
        return "local"
    if isinstance(value, CallablePulse):
        return "callable"
    return None


def _explicit_pulse_payload(value: Any) -> Any:
    from .pulse import CallablePulse, GlobalPulse, LocalPulseVector

    if isinstance(value, GlobalPulse):
        return value.value
    if isinstance(value, LocalPulseVector):
        return value.values
    if isinstance(value, CallablePulse):
        return value.func
    return value


def _pulse_manifest(value: Any) -> Dict[str, Any]:
    from .pulse import is_pulse

    explicit_kind = _explicit_pulse_kind(value)
    if explicit_kind is not None:
        return {"kind": explicit_kind, "payload": _pulse_manifest(_explicit_pulse_payload(value))}

    if _is_numeric_scalar(value):
        return {"kind": "scalar", "value": float(value)}
    if isinstance(value, np.ndarray):
        return _pulse_manifest(value.tolist())
    if isinstance(value, list):
        return {"kind": "local_vector", "values": [_pulse_manifest(item) for item in value]}
    if isinstance(value, dict):
        return {
            "kind": "local_dict",
            "values": [
                {"atom_index": int(key), "value": _pulse_manifest(item)}
                for key, item in sorted(value.items(), key=lambda pair: int(pair[0]))
            ],
        }
    if callable(value):
        return {
            "kind": "callable",
            "name": getattr(value, "__name__", type(value).__name__),
            "module": getattr(value, "__module__", None),
            "reproducible": False,
        }
    if is_pulse(value):
        params = {
            key: _pulse_manifest(item) if is_pulse(item) else _json_compatible(item)
            for key, item in vars(value).items()
        }
        return {"kind": "pulse_ast", "type": type(value).__name__, "parameters": params}
    return {"kind": "unsupported", "type": type(value).__name__, "repr": repr(value)}


def _config_manifest(config: SolverConfig, *, t_start: float, t_end: float, observables: Optional[Dict[str, int]]) -> Dict[str, Any]:
    return {
        "method": config.method,
        "t_span": [float(t_start), float(t_end)],
        "reltol": float(config.reltol),
        "abstol": float(config.abstol),
        "blockade_radius": float(config.blockade_radius),
        "gamma": _json_compatible(config.gamma),
        "gamma_phi": _json_compatible(config.gamma_phi),
        "use_mc": bool(config.use_mc),
        "n_trajectories": int(config.n_trajectories),
        "use_gpu": bool(config.use_gpu),
        "gpu_backend": str(config.gpu_backend).upper(),
        "observables": dict(observables or {}),
    }


def _backend_manifest(diagnostics: Dict[str, Any]) -> Dict[str, Any]:
    probe = diagnostics.get("backend_probe") or {}
    return {
        "requested_backend": diagnostics.get("requested_backend"),
        "available": diagnostics.get("available"),
        "issues": diagnostics.get("issues", []),
        "issue_details": diagnostics.get("issue_details", []),
        "backend_probe_schema": probe.get("schema_version"),
        "backend_probe_available": probe.get("available"),
        "versions": probe.get("versions", {}),
        "devices": probe.get("devices", []),
    }


def _event_ids_for_run(result_event: str) -> List[str]:
    names = ["doctor_report", "solver_start", result_event]
    return [get_event_spec(name).event_id for name in names]


def _build_run_manifest(
    *,
    register: Register,
    sequence: PulseSequence,
    config: SolverConfig,
    t_start: float,
    t_end: float,
    observables: Optional[Dict[str, int]],
    psi0: np.ndarray,
    diagnostics: Dict[str, Any],
    metadata: Dict[str, Any],
    result_type: str,
) -> Dict[str, Any]:
    n_atoms = len(register.atoms)
    return {
        "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result_type": result_type,
        "register": {
            "atom_count": n_atoms,
            "C6": float(register.C6),
            "atoms": [[float(atom.x), float(atom.y), float(atom.z)] for atom in register.atoms],
            "geometry": register.geometry_summary(blockade_radius=config.blockade_radius, include_edges=False),
        },
        "pulse": {
            "omega": _pulse_manifest(sequence.omega),
            "delta": _pulse_manifest(sequence.delta),
        },
        "solver": _config_manifest(config, t_start=t_start, t_end=t_end, observables=observables),
        "initial_state": {
            "basis_size": int(len(psi0)),
            "norm": float(np.linalg.norm(psi0)),
        },
        "backend_diagnostics": _backend_manifest(diagnostics),
        "versions": metadata,
        "event_taxonomy_schema": EVENT_TAXONOMY_SCHEMA_VERSION,
        "event_ids": _event_ids_for_run("solver_finish"),
        "random": {
            "seed": None,
            "n_trajectories": int(config.n_trajectories) if config.use_mc else None,
        },
    }


def _validate_atom_index(index: Any, N: int, *, context: str) -> int:
    if _is_bool(index) or not isinstance(index, (int, np.integer)):
        raise _validation_error(
            "VALIDATION_ATOM_INDEX_TYPE",
            f"{context} atom index must be an integer in [0, {N - 1}], got {index!r}",
            "Use zero-based integer atom indices matching Register.atoms order.",
        )
    idx = int(index)
    if idx < 0 or idx >= N:
        raise _validation_error(
            "VALIDATION_ATOM_INDEX_OUT_OF_RANGE",
            f"{context} atom index {idx} is out of range for {N} atoms",
            "Use an atom index in the inclusive range [0, atom_count - 1].",
        )
    return idx


def _validate_pulse_value(value: Any, *, field_name: str, atom_index: Optional[int] = None) -> None:
    from .pulse import is_pulse

    if is_pulse(value) or _is_numeric_scalar(value):
        return

    suffix = "" if atom_index is None else f" for atom {atom_index}"
    raise _validation_error(
        "VALIDATION_PULSE_VALUE_TYPE",
        f"PulseSequence.{field_name}{suffix} must be a numeric scalar or Pulse node, got {type(value).__name__}",
        "Use a real numeric scalar or a sagittarius Pulse node for local pulse values.",
    )


def _coerce_callable_vector(values: Any, N: int, *, field_name: str) -> List[float]:
    if isinstance(values, np.ndarray):
        raw_values = values.tolist()
    elif isinstance(values, ABCSequence) and not isinstance(values, (str, bytes, bytearray)):
        raw_values = list(values)
    else:
        raise _validation_error(
            "VALIDATION_CALLABLE_PULSE_RETURN_TYPE",
            f"Callable PulseSequence.{field_name} must return a sequence of {N} numeric values, "
            f"got {type(values).__name__}",
            "Return a list, tuple, or numpy array with one numeric value per atom.",
        )

    if len(raw_values) != N:
        raise _validation_error(
            "VALIDATION_CALLABLE_PULSE_LENGTH",
            f"Callable PulseSequence.{field_name} returned {len(raw_values)} values for {N} atoms",
            "Return exactly one pulse value for each atom in Register.atoms order.",
        )

    coerced = []
    for i, value in enumerate(raw_values):
        if not _is_numeric_scalar(value):
            raise _validation_error(
                "VALIDATION_CALLABLE_PULSE_VALUE_TYPE",
                f"Callable PulseSequence.{field_name} value for atom {i} must be numeric, got {type(value).__name__}",
                "Return only real numeric scalar values from callable pulse functions.",
            )
        coerced.append(float(value))
    return coerced


def _validate_pulse_config(p_config: Any, N: int, *, field_name: str, sample_time: Optional[float] = None) -> None:
    from .pulse import CallablePulse, GlobalPulse, LocalPulseVector, is_pulse

    if isinstance(p_config, GlobalPulse):
        _validate_pulse_value(p_config.value, field_name=field_name)
        return

    if isinstance(p_config, LocalPulseVector):
        _validate_pulse_config(p_config.values, N, field_name=field_name, sample_time=sample_time)
        return

    if isinstance(p_config, CallablePulse):
        p_config = p_config.func

    if callable(p_config):
        if sample_time is not None:
            try:
                values = p_config(float(sample_time))
            except Exception as exc:
                raise _validation_error(
                    "VALIDATION_CALLABLE_PULSE_FAILED",
                    f"Callable PulseSequence.{field_name} failed during validation: {exc}",
                    "Make callable pulse functions total for the sampled time range and return one numeric value per atom.",
                ) from exc
            _coerce_callable_vector(values, N, field_name=field_name)
        return

    if isinstance(p_config, dict):
        for key, value in p_config.items():
            idx = _validate_atom_index(key, N, context=f"PulseSequence.{field_name}")
            _validate_pulse_value(value, field_name=field_name, atom_index=idx)
        return

    if isinstance(p_config, list):
        if len(p_config) != N:
            raise _validation_error(
                "VALIDATION_PULSE_LIST_LENGTH",
                f"PulseSequence.{field_name} list length {len(p_config)} does not match {N} atoms",
                "Provide one pulse value per atom, or use a dict for sparse local addressing.",
            )
        for idx, value in enumerate(p_config):
            _validate_pulse_value(value, field_name=field_name, atom_index=idx)
        return

    if is_pulse(p_config) or _is_numeric_scalar(p_config):
        return

    raise _validation_error(
        "VALIDATION_PULSE_CONFIG_TYPE",
        f"PulseSequence.{field_name} must be a scalar, Pulse node, list, dict, or callable; "
        f"got {type(p_config).__name__}",
        "Use a supported pulse input shape documented in docs/PULSE_CONTRACT.md.",
    )


def _local_pulse_values_in_register_order(p_config: Union[Dict[int, Any], List[Any]], N: int) -> List[Any]:
    from .pulse import LocalPulseVector

    if isinstance(p_config, LocalPulseVector):
        p_config = p_config.values
    if isinstance(p_config, dict):
        return [p_config.get(i, 0.0) for i in range(N)]
    return list(p_config)

def _constant_vector(value: Any, N: int, *, field_name: str) -> List[float]:
    from .pulse import CallablePulse, GlobalPulse, LocalPulseVector, is_pulse

    if isinstance(value, GlobalPulse):
        value = value.value
    elif isinstance(value, LocalPulseVector):
        value = value.values
    elif isinstance(value, CallablePulse):
        value = value.func

    if callable(value) or is_pulse(value):
        raise _validation_error(
            "VALIDATION_DENSE_REDUCED_PULSE_UNSUPPORTED",
            f"dense-vs-reduced validation currently requires time-independent numeric PulseSequence.{field_name} values.",
            "Use numeric scalar, list, or dict pulse values for dense_vs_reduced_validation().",
        )
    if isinstance(value, dict):
        return [float(v) for v in _local_pulse_values_in_register_order(value, N)]
    if isinstance(value, list):
        if len(value) != N:
            raise _validation_error(
                "VALIDATION_PULSE_LIST_LENGTH",
                f"PulseSequence.{field_name} list length {len(value)} does not match {N} atoms",
                "Provide one pulse value per atom for dense-vs-reduced validation.",
            )
        return [float(v) for v in value]
    if _is_numeric_scalar(value):
        return [float(value) for _ in range(N)]
    raise _validation_error(
        "VALIDATION_DENSE_REDUCED_PULSE_UNSUPPORTED",
        f"dense-vs-reduced validation does not support PulseSequence.{field_name} value of type {type(value).__name__}.",
        "Use numeric scalar, list, or dict pulse values for dense_vs_reduced_validation().",
    )


def _interaction_matrix_python(register: Register) -> np.ndarray:
    n_atoms = len(register.atoms)
    matrix = np.zeros((n_atoms, n_atoms), dtype=float)
    for i in range(n_atoms):
        ci = np.array([register.atoms[i].x, register.atoms[i].y, register.atoms[i].z], dtype=float)
        for j in range(i + 1, n_atoms):
            cj = np.array([register.atoms[j].x, register.atoms[j].y, register.atoms[j].z], dtype=float)
            distance = float(np.linalg.norm(ci - cj))
            value = 0.0 if distance == 0.0 else float(register.C6) / distance**6
            matrix[i, j] = value
            matrix[j, i] = value
    return matrix


def _dense_hamiltonian_matrix(register: Register, omega: List[float], delta: List[float]) -> np.ndarray:
    n_atoms = len(register.atoms)
    dim = 2**n_atoms
    interactions = _interaction_matrix_python(register)
    matrix = np.zeros((dim, dim), dtype=np.complex128)
    for state in range(dim):
        diagonal = 0.0
        for j in range(n_atoms):
            if state & (1 << j):
                diagonal -= delta[j]
                for k in range(j + 1, n_atoms):
                    if state & (1 << k):
                        diagonal += interactions[j, k]
        matrix[state, state] = diagonal
        for j in range(n_atoms):
            target = state ^ (1 << j)
            matrix[target, state] += omega[j] / 2.0
    return matrix


def _reduced_hamiltonian_matrix(register: Register, omega: List[float], delta: List[float], basis: List[int]) -> np.ndarray:
    n_atoms = len(register.atoms)
    interactions = _interaction_matrix_python(register)
    mapping = {state: idx for idx, state in enumerate(basis)}
    matrix = np.zeros((len(basis), len(basis)), dtype=np.complex128)
    for idx, state in enumerate(basis):
        diagonal = 0.0
        for j in range(n_atoms):
            if state & (1 << j):
                diagonal -= delta[j]
                for k in range(j + 1, n_atoms):
                    if state & (1 << k):
                        diagonal += interactions[j, k]
        matrix[idx, idx] = diagonal
        for j in range(n_atoms):
            target = state ^ (1 << j)
            target_idx = mapping.get(target)
            if target_idx is not None:
                matrix[target_idx, idx] += omega[j] / 2.0
    return matrix


def _reduced_basis_python(register: Register, blockade_radius: float) -> List[int]:
    n_atoms = len(register.atoms)
    coords = np.array([[atom.x, atom.y, atom.z] for atom in register.atoms], dtype=float)
    adjacency = [[] for _ in range(n_atoms)]
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            if float(np.linalg.norm(coords[i] - coords[j])) < blockade_radius:
                adjacency[i].append(j)
                adjacency[j].append(i)

    basis: List[int] = []

    def visit(atom_idx: int, state: int) -> None:
        if atom_idx >= n_atoms:
            basis.append(state)
            return
        visit(atom_idx + 1, state)
        if all(neighbor >= atom_idx or not (state & (1 << neighbor)) for neighbor in adjacency[atom_idx]):
            visit(atom_idx + 1, state | (1 << atom_idx))

    visit(0, 0)
    return sorted(basis)


def dense_vs_reduced_validation(
    register: Register,
    sequence: PulseSequence,
    *,
    blockade_radius: float,
    duration: float = 1.0,
    psi0: Optional[np.ndarray] = None,
    atol: float = 1e-10,
) -> Dict[str, Any]:
    """Compare projected full dense evolution with reduced-basis evolution for a small static system."""
    from scipy.linalg import expm

    n_atoms = len(register.atoms)
    if n_atoms > 10:
        raise _validation_error(
            "VALIDATION_DENSE_REDUCED_SYSTEM_TOO_LARGE",
            f"dense-vs-reduced validation is limited to <= 10 atoms, got {n_atoms}.",
            "Use this validation on small systems because the full dense Hilbert space scales as 2**N.",
        )
    blockade_radius = _positive_float(blockade_radius, field_name="blockade_radius")
    duration = float(duration)
    omega = _constant_vector(sequence.omega, n_atoms, field_name="omega")
    delta = _constant_vector(sequence.delta, n_atoms, field_name="delta")
    full_h = _dense_hamiltonian_matrix(register, omega, delta)
    basis = _reduced_basis_python(register, blockade_radius)
    reduced_h = _reduced_hamiltonian_matrix(register, omega, delta, basis)

    if psi0 is None:
        psi0_reduced = np.zeros(len(basis), dtype=np.complex128)
        psi0_reduced[0] = 1.0
    else:
        psi0_reduced = np.asarray(psi0, dtype=np.complex128)
        if psi0_reduced.shape != (len(basis),):
            raise _validation_error(
                "VALIDATION_INITIAL_STATE_SIZE",
                f"Initial state psi0 must have size {len(basis)} (current reduced basis size)",
                "Provide a reduced-basis initial state for dense_vs_reduced_validation().",
            )

    projected_h = full_h[np.ix_(basis, basis)]
    projected_state = expm(-1j * projected_h * duration) @ psi0_reduced
    reduced_state = expm(-1j * reduced_h * duration) @ psi0_reduced
    hamiltonian_error = float(np.max(np.abs(projected_h - reduced_h))) if reduced_h.size else 0.0
    state_error = float(np.max(np.abs(projected_state - reduced_state))) if reduced_state.size else 0.0
    full_dim = 2**n_atoms
    return {
        "schema_version": "dense-vs-reduced-validation/v1",
        "ok": bool(hamiltonian_error <= atol and state_error <= atol),
        "atol": float(atol),
        "atom_count": n_atoms,
        "blockade_radius": blockade_radius,
        "full_basis_size": full_dim,
        "reduced_basis_size": len(basis),
        "reduced_basis_pruning_ratio": 1.0 - (len(basis) / full_dim),
        "basis": basis,
        "max_hamiltonian_error": hamiltonian_error,
        "max_state_error": state_error,
        "duration": duration,
    }


def _copy_solver_config(config: SolverConfig, **overrides: Any) -> SolverConfig:
    values = dict(config.__dict__)
    values.update(overrides)
    return SolverConfig(**values)


def _density_matrix_metrics(states: Any) -> Dict[str, Any]:
    trace_errors: List[float] = []
    min_eigenvalues: List[float] = []
    for rho in states:
        rho_arr = np.asarray(rho, dtype=np.complex128)
        trace = np.trace(rho_arr)
        trace_errors.append(float(abs(trace - 1.0)))
        hermitian_rho = 0.5 * (rho_arr + rho_arr.conj().T)
        min_eigenvalues.append(float(np.min(np.linalg.eigvalsh(hermitian_rho))))
    return {
        "max_trace_error": max(trace_errors) if trace_errors else 0.0,
        "min_density_eigenvalue": min(min_eigenvalues) if min_eigenvalues else 0.0,
        "sample_count": len(trace_errors),
    }


def _observable_series(result: "SimulationResult", observables: Dict[str, int]) -> Dict[str, np.ndarray]:
    return {name: np.asarray(result.data[name], dtype=float) for name in observables}


def open_system_sanity_checks(
    register: Register,
    sequence: PulseSequence,
    *,
    config: Optional[SolverConfig] = None,
    psi0: Optional[np.ndarray] = None,
    t_start: float = 0.0,
    t_end: float = 1.0,
    observables: Optional[Dict[str, int]] = None,
    n_trajectories: int = 300,
    trace_atol: float = 1e-6,
    positivity_atol: float = 1e-7,
    mc_mean_abs_atol: float = 0.08,
) -> Dict[str, Any]:
    """Run small-system open-system sanity checks for Lindblad and MCWF paths."""
    n_atoms = len(register.atoms)
    if n_atoms > 8:
        raise _validation_error(
            "VALIDATION_OPEN_SYSTEM_SYSTEM_TOO_LARGE",
            f"open-system sanity checks are limited to <= 8 atoms, got {n_atoms}.",
            "Use this validation on small systems because raw density matrices scale as 4**N.",
        )
    if config is None:
        config = SolverConfig(gamma=0.1)
    n_trajectories = _positive_int(n_trajectories, field_name="n_trajectories")
    has_gamma = bool(np.any(np.asarray(config.gamma, dtype=float) > 0))
    has_gamma_phi = bool(np.any(np.asarray(config.gamma_phi, dtype=float) > 0))
    if not has_gamma and not has_gamma_phi:
        raise _validation_error(
            "VALIDATION_OPEN_SYSTEM_NO_NOISE",
            "open-system sanity checks require gamma or gamma_phi to be positive.",
            "Provide a SolverConfig with nonzero gamma and/or gamma_phi.",
        )
    if psi0 is None:
        dim = Simulation(register, sequence, config).validate()
        psi0 = np.zeros(dim, dtype=np.complex128)
        psi0[0] = 1.0
    else:
        psi0 = np.asarray(psi0, dtype=np.complex128)
    if observables is None:
        observables = {f"atom_{idx}": idx for idx in range(n_atoms)}
    Simulation(register, sequence, config).validate_inputs(sample_time=float(t_start), observables=observables)

    lindblad_config = _copy_solver_config(config, use_mc=False, use_gpu=False)
    lindblad_sim = Simulation(register, sequence, lindblad_config)
    lindblad_raw = lindblad_sim.run(psi0, float(t_start), float(t_end))
    metrics = _density_matrix_metrics(lindblad_raw.u)

    lindblad_obs = Simulation(register, sequence, lindblad_config).run(
        psi0,
        float(t_start),
        float(t_end),
        observables=observables,
    )
    mc_config = _copy_solver_config(
        config, use_mc=True, use_gpu=False, n_trajectories=n_trajectories
    )
    mc_obs = Simulation(register, sequence, mc_config).run(
        psi0,
        float(t_start),
        float(t_end),
        observables=observables,
    )

    lindblad_t = np.asarray(lindblad_obs.data["t"], dtype=float)
    mc_t = np.asarray(mc_obs.data["t"], dtype=float)
    lindblad_series = _observable_series(lindblad_obs, observables)
    mc_series = _observable_series(mc_obs, observables)
    observable_reports: Dict[str, Dict[str, float]] = {}
    max_mean_abs_error = 0.0
    max_abs_error = 0.0
    for name in observables:
        interpolated = np.interp(mc_t, lindblad_t, lindblad_series[name])
        diff = np.abs(interpolated - mc_series[name])
        mean_abs_error = float(np.mean(diff)) if diff.size else 0.0
        obs_max_abs_error = float(np.max(diff)) if diff.size else 0.0
        observable_reports[name] = {
            "mean_abs_error": mean_abs_error,
            "max_abs_error": obs_max_abs_error,
        }
        max_mean_abs_error = max(max_mean_abs_error, mean_abs_error)
        max_abs_error = max(max_abs_error, obs_max_abs_error)

    trace_ok = metrics["max_trace_error"] <= float(trace_atol)
    positivity_ok = metrics["min_density_eigenvalue"] >= -float(positivity_atol)
    mc_lindblad_ok = max_mean_abs_error <= float(mc_mean_abs_atol)
    return {
        "schema_version": "open-system-sanity-checks/v1",
        "ok": bool(trace_ok and positivity_ok and mc_lindblad_ok),
        "atom_count": n_atoms,
        "basis_size": int(len(psi0)),
        "t_start": float(t_start),
        "t_end": float(t_end),
        "n_trajectories": n_trajectories,
        "trace_atol": float(trace_atol),
        "positivity_atol": float(positivity_atol),
        "mc_mean_abs_atol": float(mc_mean_abs_atol),
        "lindblad_trace": {
            "ok": bool(trace_ok),
            "max_error": metrics["max_trace_error"],
        },
        "lindblad_positivity": {
            "ok": bool(positivity_ok),
            "min_eigenvalue": metrics["min_density_eigenvalue"],
        },
        "mcwf_vs_lindblad": {
            "ok": bool(mc_lindblad_ok),
            "max_mean_abs_error": max_mean_abs_error,
            "max_abs_error": max_abs_error,
            "observables": observable_reports,
        },
        "lindblad_sample_count": metrics["sample_count"],
        "observable_names": list(observables.keys()),
    }


def _simulation_result_with_manifest(
    data: Dict[str, List[float]],
    *,
    metadata: Dict[str, Any],
    diagnostics: Dict[str, Any],
    register: Register,
    sequence: PulseSequence,
    config: SolverConfig,
    t_start: float,
    t_end: float,
    observables: Optional[Dict[str, int]],
    psi0: np.ndarray,
    result_type: str,
) -> "SimulationResult":
    manifest = _build_run_manifest(
        register=register,
        sequence=sequence,
        config=config,
        t_start=t_start,
        t_end=t_end,
        observables=observables,
        psi0=psi0,
        diagnostics=diagnostics,
        metadata=metadata,
        result_type=result_type,
    )
    validate_run_manifest(manifest)
    return SimulationResult(data, metadata=metadata, diagnostics=diagnostics, manifest=manifest)


class SimulationResult:
    def __init__(
        self,
        data: Dict[str, List[float]],
        metadata: Optional[Dict[str, Any]] = None,
        diagnostics: Optional[Dict[str, Any]] = None,
        manifest: Optional[Dict[str, Any]] = None,
    ):
        self.data = data
        self.metadata = metadata or {}
        self.diagnostics = diagnostics or {}
        self.manifest = manifest or {}
        self.t = np.array(data.get('t', []))

    def to_envelope(self) -> Dict[str, Any]:
        """Return the stable JSON artifact envelope for this result."""
        return {
            "schema_version": RESULT_ARTIFACT_SCHEMA_VERSION,
            "artifact_type": RESULT_ARTIFACT_TYPE,
            "data": _json_compatible(self.data),
            "metadata": _json_compatible(self.metadata),
            "diagnostics": _json_compatible(self.diagnostics),
            "manifest": _json_compatible(self.manifest),
        }
    
    def to_pandas(self):
        import pandas as pd

        return pd.DataFrame(self.data)
    
    def save(self, filepath: str):
        """Save results to a JSON artifact envelope."""
        try:
            serializable_data = self.to_envelope()
            with open(filepath, "w") as f:
                json.dump(serializable_data, f)
        except TypeError as exc:
            err = _serialization_error(
                "SERIALIZATION_NOT_JSON_COMPATIBLE",
                "SimulationResult contains values that cannot be encoded as JSON.",
                "Convert result data, metadata, and diagnostics to JSON-compatible scalars, lists, and dicts before saving.",
            )
            emit_failure_diagnostic(err.issue)
            raise err from exc
        except OSError as exc:
            err = _serialization_error(
                "SERIALIZATION_WRITE_FAILED",
                f"Could not write SimulationResult to {filepath!r}.",
                "Check that the parent directory exists and is writable, then retry save().",
            )
            emit_failure_diagnostic(err.issue)
            raise err from exc
    
    @classmethod
    def load(cls, filepath: str):
        """Load results from a JSON file."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            err = _serialization_error(
                "SERIALIZATION_INVALID_JSON",
                f"Could not parse SimulationResult JSON from {filepath!r}.",
                "Regenerate the result artifact or repair the JSON before calling load_result().",
            )
            emit_failure_diagnostic(err.issue)
            raise err from exc
        except OSError as exc:
            err = _serialization_error(
                "SERIALIZATION_READ_FAILED",
                f"Could not read SimulationResult from {filepath!r}.",
                "Check that the file exists and is readable, then retry load_result().",
            )
            emit_failure_diagnostic(err.issue)
            raise err from exc

        if isinstance(data, dict) and data.get("schema_version") == RESULT_ARTIFACT_SCHEMA_VERSION:
            if data.get("artifact_type") != RESULT_ARTIFACT_TYPE:
                err = _serialization_error(
                    "SERIALIZATION_SCHEMA_INVALID",
                    "Result artifact envelope has an unsupported artifact_type.",
                    f"Expected artifact_type {RESULT_ARTIFACT_TYPE!r} for SimulationResult.load().",
                )
                emit_failure_diagnostic(err.issue)
                raise err
            if not isinstance(data.get("data"), dict):
                err = _serialization_error(
                    "SERIALIZATION_SCHEMA_INVALID",
                    "SimulationResult envelope field 'data' must be a JSON object.",
                    "Regenerate the result artifact with SimulationResult.save().",
                )
                emit_failure_diagnostic(err.issue)
                raise err
            return cls(
                data["data"],
                metadata=data.get("metadata"),
                diagnostics=data.get("diagnostics"),
                manifest=data.get("manifest"),
            )

        if isinstance(data, dict) and "schema_version" in data:
            err = _serialization_error(
                "SERIALIZATION_SCHEMA_UNSUPPORTED",
                f"Unsupported SimulationResult artifact schema_version: {data.get('schema_version')!r}.",
                f"Use artifacts with schema_version {RESULT_ARTIFACT_SCHEMA_VERSION!r} or convert the file before loading.",
            )
            emit_failure_diagnostic(err.issue)
            raise err

        if isinstance(data, dict) and "data" in data:
            if not isinstance(data["data"], dict):
                err = _serialization_error(
                    "SERIALIZATION_SCHEMA_INVALID",
                    "SimulationResult envelope field 'data' must be a JSON object.",
                    "Regenerate the result artifact with SimulationResult.save().",
                )
                emit_failure_diagnostic(err.issue)
                raise err
            return cls(data["data"], metadata=data.get("metadata"), diagnostics=data.get("diagnostics"), manifest=data.get("manifest"))
        if not isinstance(data, dict):
            err = _serialization_error(
                "SERIALIZATION_SCHEMA_INVALID",
                "Legacy SimulationResult JSON must be a JSON object mapping series names to values.",
                "Load only artifacts produced by SimulationResult.save() or convert the file to the result envelope schema.",
            )
            emit_failure_diagnostic(err.issue)
            raise err
        return cls(data)

    def plot(self, show: bool = True):
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 6))
        for key, values in self.data.items():
            if key == 't':
                continue
            plt.plot(self.t, values, label=key)
        plt.xlabel("Time (μs)")
        plt.ylabel("Observable Value")
        plt.title("Simulation Results")
        plt.legend()
        plt.grid(True)
        if show:
            plt.show()

class Simulation:
    def __init__(self, register: Register, sequence: PulseSequence, config: SolverConfig = SolverConfig()):
        self.register = register
        self.sequence = sequence
        self.config = config
        self._basis = None
        self._mapping = None
        self._basis_context = None

    def validate_inputs(self, *, sample_time: Optional[float] = None, observables: Optional[Dict[str, int]] = None) -> None:
        N = len(self.register.atoms)
        _validate_pulse_config(self.sequence.omega, N, field_name="omega", sample_time=sample_time)
        _validate_pulse_config(self.sequence.delta, N, field_name="delta", sample_time=sample_time)
        if observables:
            for name, idx in observables.items():
                if not isinstance(name, str):
                    raise _validation_error(
                        "VALIDATION_OBSERVABLE_NAME_TYPE",
                        f"Observable names must be strings, got {type(name).__name__}",
                        "Use string keys for the observables mapping.",
                    )
                _validate_atom_index(idx, N, context=f"Observable {name!r}")

    def validate(self) -> int:
        """Returns the size of the Hilbert space after pruning."""
        if self.config.blockade_radius > 0:
            _, _, phys, _ = get_modules()
            self._basis_context = phys.reduced_basis_context(self.register.jl_obj, blockade_radius=float(self.config.blockade_radius))
            self._basis = self._basis_context.basis
            self._mapping = self._basis_context.mapping
            return len(self._basis)
        else:
            self._basis_context = None
            self._basis = None
            self._mapping = None
            return 2**len(self.register.atoms)

    def _get_compiled_func(self, p_config: Any, N: int) -> Any:
        """Compiles a pulse configuration into a Julia-side closure t -> Vector{Float64}."""
        from .pulse import CallablePulse, GlobalPulse, LocalPulseVector, is_pulse
        jl, sgr = get_julia()

        if isinstance(p_config, GlobalPulse):
            p_config = p_config.value
        elif isinstance(p_config, LocalPulseVector):
            p_config = p_config.values
        elif isinstance(p_config, CallablePulse):
            p_config = p_config.func

        if callable(p_config):
            # Callable pulses return one numeric value per Python atom index, in Register.atoms order.
            return jl.seval("""
                (f, n) -> (t -> begin
                    vals = [pyconvert(Float64, x) for x in f(t)]
                    length(vals) == n || throw(ArgumentError("callable pulse returned $(length(vals)) values for $n atoms"))
                    vals
                end)
            """)(p_config, int(N))

        if isinstance(p_config, (dict, list)):
            # Local addressing follows Python's 0-based Register.atoms order.
            compiled_funcs = []
            for i, p in enumerate(_local_pulse_values_in_register_order(p_config, N)):
                if is_pulse(p):
                    compiled_funcs.append(sgr.compile_pulse(p.jl_obj))
                else:
                    v = float(p)
                    compiled_funcs.append(sgr.compile_pulse(sgr.ConstantPulse(v, 1e12)))

            jl_vec = jl.Vector[jl.Any](compiled_funcs)
            return jl.seval("funcs -> (t -> Float64[f(t) for f in funcs])")(jl_vec)
        else:
            # Global addressing
            if is_pulse(p_config):
                f = sgr.compile_pulse(p_config.jl_obj)
                jl_vec = jl.Vector[jl.Any]([f for _ in range(N)])
                return jl.seval("funcs -> (t -> Float64[f(t) for f in funcs])")(jl_vec)
            else:
                v = float(p_config)
                return sgr.create_const_vec_func(v, N)

    def run(self, psi0: np.ndarray, t_start: float, t_end: float, observables: Optional[Dict[str, int]] = None) -> SimulationResult:
        try:
            return self._run_impl(psi0, t_start, t_end, observables)
        except SagittariusError as exc:
            emit_failure_diagnostic(exc.issue, backend=self.config.gpu_backend if self.config.use_gpu else "CPU")
            raise
        except Exception as exc:
            issue = make_issue(
                "SOLVER_EXECUTION_FAILED",
                "Simulation solver execution failed.",
                "Inspect the original exception, validate inputs with Simulation.validate_inputs(), and run doctor(initialize_backend=True) for backend details.",
            )
            emit_failure_diagnostic(issue, backend=self.config.gpu_backend if self.config.use_gpu else "CPU")
            raise SagittariusSolverError(issue) from exc

    def _run_impl(self, psi0: np.ndarray, t_start: float, t_end: float, observables: Optional[Dict[str, int]] = None) -> SimulationResult:
        self.validate_inputs(sample_time=float(t_start), observables=observables)
        jl, sgr, phys, solv = get_modules()
        backend_report = doctor(backend=self.config.gpu_backend if self.config.use_gpu else "CPU")
        log_event(
            "solver_start",
            backend=backend_report["requested_backend"],
            use_gpu=self.config.use_gpu,
            reltol=self.config.reltol,
            abstol=self.config.abstol,
            blockade_radius=self.config.blockade_radius,
        )
        N = len(self.register.jl_obj.atoms)
        basis_size = self.validate()
        diagnostics = dict(backend_report)
        diagnostics["simulation"] = {
            "solver_method": self.config.method,
            "reltol": self.config.reltol,
            "abstol": self.config.abstol,
            "basis_size": basis_size,
            "full_basis_size": 2**N,
            "reduced_basis_pruning_ratio": 1.0 - (basis_size / (2**N)),
            "use_gpu": self.config.use_gpu,
            "use_mc": self.config.use_mc,
        }
        diagnostics["register"] = self.register.geometry_summary(blockade_radius=self.config.blockade_radius, include_edges=False)
        
        if len(psi0) != basis_size:
            raise _validation_error(
                "VALIDATION_INITIAL_STATE_SIZE",
                f"Initial state psi0 must have size {basis_size} (current basis size)",
                "Resize psi0 to the current full or blockade-reduced basis size returned by validate().",
            )

        # 1. Compile pulses
        omega_func = self._get_compiled_func(self.sequence.omega, N)
        delta_func = self._get_compiled_func(self.sequence.delta, N)

        # 2. Build Hamiltonian
        H_func = phys.build_hamiltonian_func(
            self.register.jl_obj,
            omega_func,
            delta_func,
            blockade_radius=float(self.config.blockade_radius),
            basis_context=self._basis_context,
            use_gpu=bool(self.config.use_gpu),
        )

        # 3. Handle observables
        jl_obs = None
        observable_names = list(observables.keys()) if observables else []
        if observables:
            if self.config.blockade_radius > 0:
                jl_obs = jl.Vector[jl.Any]([
                    solv.RydbergPopulation(observables[name] + 1, N, basis_context=self._basis_context)
                    for name in observable_names
                ])
            else:
                jl_obs = jl.Vector[jl.Any]([
                    solv.RydbergPopulation(observables[name] + 1, N)
                    for name in observable_names
                ])

        # 4. Determine if we use Lindblad, MC, or Schrodinger
        is_noisy = (np.any(np.array(self.config.gamma) > 0) or 
                    np.any(np.array(self.config.gamma_phi) > 0))

        if is_noisy:
            # Get jump operators
            if self.config.blockade_radius > 0:
                j_ops = phys.get_jump_operators(
                    N,
                    self.config.gamma,
                    self.config.gamma_phi,
                    basis_context=self._basis_context,
                )
            else:
                j_ops = phys.get_jump_operators(N, self.config.gamma, self.config.gamma_phi)

            if self.config.use_mc:
                # Solve Monte Carlo Trajectories
                jl_psi0 = jl.Vector[jl.ComplexF64](psi0)
                result = solv.solve_mc_trajectories(
                    jl_psi0,
                    H_func,
                    j_ops,
                    jl.SVector(float(t_start), float(t_end)),
                    n_trajectories=int(self.config.n_trajectories),
                    observables=jl_obs,
                    reltol=float(self.config.reltol),
                    abstol=float(self.config.abstol)
                )
                
                if jl_obs:
                    t_vals, avg_res = result
                    times = list(t_vals)
                    data = {name: [avg_res[t_idx][i] for t_idx in range(len(times))]
                            for i, name in enumerate(observable_names)}
                    data['t'] = times
                    result_type = "mcwf_observables"
                    log_event("solver_finish", result_type=result_type, basis_size=basis_size)
                    metadata = version_info()
                    return _simulation_result_with_manifest(
                        data,
                        metadata=metadata,
                        diagnostics=diagnostics,
                        register=self.register,
                        sequence=self.sequence,
                        config=self.config,
                        t_start=t_start,
                        t_end=t_end,
                        observables=observables,
                        psi0=np.asarray(psi0),
                        result_type=result_type,
                    )
                log_event("solver_finish", result_type="raw_mcwf", basis_size=basis_size)
                return result

            else:
                # Solve Lindblad Master Equation
                rho0 = np.outer(psi0, psi0.conj())
                jl_rho0 = jl.convert(jl.Matrix[jl.ComplexF64], rho0)
                
                result = solv.solve_lindblad(
                    jl_rho0,
                    H_func,
                    j_ops,
                    jl.SVector(float(t_start), float(t_end)),
                    observables=jl_obs,
                    reltol=float(self.config.reltol),
                    abstol=float(self.config.abstol)
                )
        else:
            # Solve Schrodinger Equation
            if self.config.use_gpu:
                backend = self.config.gpu_backend.upper()
                if backend == "CUDA":
                    jl.seval("using CUDA")
                    jl_psi0 = jl.CUDA.CuVector[jl.ComplexF64](psi0)
                elif backend == "AMDGPU":
                    jl.seval("using AMDGPU")
                    jl_psi0 = jl.AMDGPU.ROCVector[jl.ComplexF64](psi0)
                elif backend == "METAL":
                    jl.seval("using Metal")
                    jl_psi0 = jl.Metal.MtlVector[jl.ComplexF64](psi0)
                else:
                    raise _validation_error(
                        "UNSUPPORTED_BACKEND",
                        f"Unsupported GPU backend: {backend}",
                        "Choose one of: CPU, CUDA, AMDGPU, METAL.",
                    )

                result = solv.solve_schrodinger_gpu(
                    jl_psi0,
                    H_func,
                    jl.SVector(float(t_start), float(t_end)),
                    observables=jl_obs,
                    reltol=float(self.config.reltol),
                    abstol=float(self.config.abstol)
                )
            else:
                jl_psi0 = jl.Vector[jl.ComplexF64](psi0)
                result = solv.solve_schrodinger(
                    jl_psi0, 
                    H_func, 
                    jl.SVector(float(t_start), float(t_end)), 
                    observables=jl_obs,
                    reltol=float(self.config.reltol),
                    abstol=float(self.config.abstol)
                )
        
        if jl_obs:
            sol, saved = result
            times = list(saved.t)
            data = {name: [v[i] for v in saved.saveval] for i, name in enumerate(observable_names)}
            data['t'] = times
            result_type = "observables"
            log_event("solver_finish", result_type=result_type, basis_size=basis_size)
            metadata = version_info()
            return _simulation_result_with_manifest(
                data,
                metadata=metadata,
                diagnostics=diagnostics,
                register=self.register,
                sequence=self.sequence,
                config=self.config,
                t_start=t_start,
                t_end=t_end,
                observables=observables,
                psi0=np.asarray(psi0),
                result_type=result_type,
            )
        
        log_event("solver_finish", result_type="raw", basis_size=basis_size)
        return result

def solve(register, sequence, config=SolverConfig(), psi0=None, t_start=0.0, t_end=1.0, observables=None):
    sim = Simulation(register, sequence, config)
    if psi0 is None:
        dim = sim.validate()
        psi0 = np.zeros(dim, dtype=complex)
        psi0[0] = 1.0
    
    res = sim.run(psi0, t_start, t_end, observables)
    
    if isinstance(res, SimulationResult):
        return res.data
    return res

def get_basis(register, blockade_radius):
    _, _, phys, _ = get_modules()
    res = phys.generate_reduced_basis(register.jl_obj, float(blockade_radius))
    return list(res[0])

def load_result(filepath: str) -> SimulationResult:
    """Load a SimulationResult from a file."""
    return SimulationResult.load(filepath)
