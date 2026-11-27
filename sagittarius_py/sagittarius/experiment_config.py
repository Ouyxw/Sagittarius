"""Validated JSON experiment configuration and execution workflow."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Union

import numpy as np

from .api import (
    Atom, PulseSequence, Register, Simulation, SimulationResult, SolverConfig,
    _normalize_bitstring, _normalize_observable_declarations, _normalize_saveat,
    _normalize_solver_config,
)
from .pulse import dict_to_pulse_node
from .runtime import SagittariusSerializationError, SagittariusValidationError, make_issue

EXPERIMENT_CONFIG_SCHEMA_VERSION = "experiment-config/v1"
EXPERIMENT_CONFIG_ARTIFACT_TYPE = "sagittarius.experiment_config"
_REQUIRED = {"schema_version", "register", "pulse", "solver", "time_span", "initial_state", "outputs"}
_ALLOWED = _REQUIRED | {"observables", "readout"}


def _error(code: str, message: str, remediation: str) -> SagittariusValidationError:
    return SagittariusValidationError(make_issue(code, message, remediation))


def _serror(code: str, message: str, remediation: str) -> SagittariusSerializationError:
    return SagittariusSerializationError(make_issue(code, message, remediation))


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise _error("VALIDATION_EXPERIMENT_CONFIG_FIELD_TYPE", f"{name} must be a JSON object.", "Use the experiment-config/v1 object shape.")
    return dict(value)


def _fields(value: Mapping[str, Any], name: str, required: set[str], allowed: set[str]) -> None:
    missing, unknown = sorted(required - set(value)), sorted(set(value) - allowed)
    if missing:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_REQUIRED_FIELD", f"{name} is missing: {', '.join(missing)}.", "Add the documented required fields.")
    if unknown:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_UNKNOWN_FIELD", f"{name} has unsupported fields: {', '.join(unknown)}.", "Remove unsupported fields or use a newer schema.")


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise _error("VALIDATION_EXPERIMENT_CONFIG_NUMBER", f"{name} must be a finite number.", "Use a finite JSON number.")
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_NUMBER", f"{name} must be a finite number.", "Use a finite JSON number.") from exc
    if not np.isfinite(value):
        raise _error("VALIDATION_EXPERIMENT_CONFIG_NUMBER", f"{name} must be finite.", "Replace NaN or infinity with a finite JSON number.")
    return value


def _pulse(value: Any, name: str) -> Any:
    if isinstance(value, bool) or value is None:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_PULSE", f"{name} is not a replayable JSON pulse.", "Use a scalar, pulse AST, local vector, or local index map.")
    if isinstance(value, (int, float)):
        return _number(value, name)
    if isinstance(value, list):
        return [_pulse(item, f"{name}[{index}]") for index, item in enumerate(value)]
    if not isinstance(value, Mapping):
        raise _error("VALIDATION_EXPERIMENT_CONFIG_PULSE", f"{name} is not a replayable JSON pulse.", "Use a scalar, pulse AST, local vector, or local index map.")
    raw = dict(value)
    if "type" in raw:
        try:
            return dict_to_pulse_node(raw)
        except (TypeError, ValueError) as exc:
            raise _error("VALIDATION_EXPERIMENT_CONFIG_PULSE_AST", f"{name} is not a valid pulse AST: {exc}", "Use a documented pulse AST with required fields.") from exc
    decoded = {}
    for key, item in raw.items():
        try:
            index = int(key)
        except (TypeError, ValueError) as exc:
            raise _error("VALIDATION_EXPERIMENT_CONFIG_PULSE_INDEX", f"{name} key {key!r} is not an atom index.", "Use zero-based integer JSON keys.") from exc
        if index < 0 or str(index) != str(key):
            raise _error("VALIDATION_EXPERIMENT_CONFIG_PULSE_INDEX", f"{name} key {key!r} is not a non-negative atom index.", "Use canonical zero-based integer JSON keys.")
        decoded[index] = _pulse(item, f"{name}[{index}]")
    return decoded


def _register(document: Mapping[str, Any]) -> Register:
    value = _object(document, "register")
    _fields(value, "register", {"atoms"}, {"atoms", "C6", "topology"})
    if not isinstance(value["atoms"], list) or not value["atoms"]:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_REGISTER_ATOMS", "register.atoms must be a non-empty coordinate list.", "Provide [x, y] or [x, y, z] coordinates in atom order.")
    atoms = []
    for index, coordinate in enumerate(value["atoms"]):
        if not isinstance(coordinate, list) or len(coordinate) not in {2, 3}:
            raise _error("VALIDATION_EXPERIMENT_CONFIG_REGISTER_COORDINATE", f"register.atoms[{index}] must have two or three values.", "Use [x, y] or [x, y, z].")
        xyz = [_number(item, f"register.atoms[{index}]") for item in coordinate]
        atoms.append(Atom(*(xyz if len(xyz) == 3 else [*xyz, 0.0])))
    topology = value.get("topology", {})
    if not isinstance(topology, Mapping):
        raise _error("VALIDATION_EXPERIMENT_CONFIG_REGISTER_TOPOLOGY", "register.topology must be a JSON object.", "Use an object or omit topology.")
    return Register(atoms, C6=_number(value.get("C6", 1.0), "register.C6"), topology=dict(topology))


def _solver(document: Mapping[str, Any], start: float, end: float) -> SolverConfig:
    value = _object(document, "solver")
    unknown = sorted(set(value) - set(SolverConfig.__dataclass_fields__))
    if unknown:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_SOLVER_FIELD", f"solver has unsupported fields: {', '.join(unknown)}.", "Use public SolverConfig field names only.")
    try:
        result = SolverConfig(**value)
        _normalize_solver_config(result)
        _normalize_saveat(result.saveat, t_start=start, t_end=end)
        return result
    except SagittariusValidationError:
        raise
    except (TypeError, ValueError) as exc:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_SOLVER", f"solver is invalid: {exc}", "Use valid public SolverConfig values.") from exc


@dataclass(frozen=True)
class ExperimentConfig:
    document: dict[str, Any]
    source_path: Optional[Path] = None

    @property
    def sha256(self) -> str:
        return hashlib.sha256(json.dumps(self.document, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(self.document))


def validate_experiment_config(document: Mapping[str, Any]) -> ExperimentConfig:
    try:
        canonical = json.loads(json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_JSON", "The config must contain finite JSON-compatible values.", "Use JSON values only.") from exc
    if not isinstance(canonical, dict):
        raise _error("VALIDATION_EXPERIMENT_CONFIG_ROOT_TYPE", "The config root must be a JSON object.", "Store one JSON object.")
    _fields(canonical, "root", _REQUIRED, _ALLOWED)
    if canonical["schema_version"] != EXPERIMENT_CONFIG_SCHEMA_VERSION:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_SCHEMA_VERSION", f"Unsupported schema {canonical['schema_version']!r}.", f"Use {EXPERIMENT_CONFIG_SCHEMA_VERSION!r}.")
    register = _register(canonical["register"])
    pulse = _object(canonical["pulse"], "pulse")
    _fields(pulse, "pulse", {"omega", "delta"}, {"omega", "delta"})
    _pulse(pulse["omega"], "pulse.omega")
    _pulse(pulse["delta"], "pulse.delta")
    if not isinstance(canonical["time_span"], list) or len(canonical["time_span"]) != 2:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_TIME_SPAN", "time_span must be [t_start, t_end].", "Provide two finite increasing times.")
    start, end = (_number(item, f"time_span[{index}]") for index, item in enumerate(canonical["time_span"]))
    if end <= start:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_TIME_SPAN", "time_span must have t_end > t_start.", "Provide an increasing interval.")
    _solver(canonical["solver"], start, end)
    initial_state = _object(canonical["initial_state"], "initial_state")
    _fields(initial_state, "initial_state", {"bitstring"}, {"bitstring"})
    _normalize_bitstring(initial_state["bitstring"], len(register.atoms), context="initial_state")
    observables = canonical.get("observables", {})
    if not isinstance(observables, Mapping):
        raise _error("VALIDATION_EXPERIMENT_CONFIG_OBSERVABLES", "observables must be a JSON object.", "Use {} or public observable declarations.")
    _normalize_observable_declarations(dict(observables), len(register.atoms))
    if not observables:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_OBSERVABLES_REQUIRED", "experiment-config/v1 requires at least one observable for a persistent result artifact.", "Declare at least one named observable.")
    readout = canonical.get("readout")
    if readout is not None:
        readout = _object(readout, "readout")
        _fields(readout, "readout", {"shots"}, {"shots", "seed"})
        if isinstance(readout["shots"], bool) or not isinstance(readout["shots"], int) or readout["shots"] <= 0:
            raise _error("VALIDATION_EXPERIMENT_CONFIG_READOUT_SHOTS", "readout.shots must be a positive integer.", "Use a positive shot count.")
        if "seed" in readout and (isinstance(readout["seed"], bool) or not isinstance(readout["seed"], int) or readout["seed"] < 0):
            raise _error("VALIDATION_EXPERIMENT_CONFIG_READOUT_SEED", "readout.seed must be a non-negative integer.", "Use a non-negative integer or omit seed.")
    outputs = _object(canonical["outputs"], "outputs")
    _fields(outputs, "outputs", {"result"}, {"result", "manifest", "samples"})
    if any(not isinstance(path, str) or not path.strip() for path in outputs.values()):
        raise _error("VALIDATION_EXPERIMENT_CONFIG_OUTPUT_PATH", "Every output path must be a non-empty string.", "Use relative or absolute JSON file paths.")
    if "samples" in outputs and readout is None:
        raise _error("VALIDATION_EXPERIMENT_CONFIG_SAMPLES_WITHOUT_READOUT", "outputs.samples requires readout.", "Add readout.shots or remove outputs.samples.")
    return ExperimentConfig(canonical)


def load_experiment_config(filepath: Union[str, Path]) -> ExperimentConfig:
    path = Path(filepath)
    try:
        with path.open(encoding="utf-8") as handle:
            document = json.load(handle)
    except json.JSONDecodeError as exc:
        raise _serror("SERIALIZATION_EXPERIMENT_CONFIG_INVALID_JSON", f"Could not parse {str(path)!r}.", "Repair the JSON or save a valid config.") from exc
    except OSError as exc:
        raise _serror("SERIALIZATION_EXPERIMENT_CONFIG_READ_FAILED", f"Could not read {str(path)!r}.", "Check the file path and permissions.") from exc
    if not isinstance(document, Mapping):
        raise _error("VALIDATION_EXPERIMENT_CONFIG_ROOT_TYPE", "The config root must be a JSON object.", "Store one JSON object.")
    config = validate_experiment_config(document)
    return ExperimentConfig(config.document, path.resolve())


def save_experiment_config(config: Union[ExperimentConfig, Mapping[str, Any]], filepath: Union[str, Path]) -> ExperimentConfig:
    config = config if isinstance(config, ExperimentConfig) else validate_experiment_config(config)
    path = Path(filepath)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(config.document, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
    except OSError as exc:
        raise _serror("SERIALIZATION_EXPERIMENT_CONFIG_WRITE_FAILED", f"Could not write {str(path)!r}.", "Check the output path and permissions.") from exc
    return ExperimentConfig(config.document, path.resolve())


def _path(config: ExperimentConfig, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (config.source_path.parent if config.source_path else Path.cwd()) / path


def _basis_state(simulation: Simulation, bitstring: Any) -> np.ndarray:
    value = _normalize_bitstring(bitstring, len(simulation.register.atoms), context="initial_state")
    state = np.zeros(simulation.validate(), dtype=complex)
    if simulation.config.blockade_radius > 0:
        basis = [int(item) for item in simulation._basis]
        if value not in basis:
            raise _error("VALIDATION_EXPERIMENT_CONFIG_INITIAL_STATE_FORBIDDEN", f"initial_state {bitstring!r} is forbidden by the reduced basis.", "Use a represented bitstring or blockade_radius=0.0.")
        state[basis.index(value)] = 1.0
    else:
        state[value] = 1.0
    return state


def run_experiment_config(config: Union[ExperimentConfig, Mapping[str, Any], str, Path]) -> SimulationResult:
    config = load_experiment_config(config) if isinstance(config, (str, Path)) else (config if isinstance(config, ExperimentConfig) else validate_experiment_config(config))
    document = config.document
    register = _register(document["register"])
    sequence = PulseSequence(_pulse(document["pulse"]["omega"], "pulse.omega"), _pulse(document["pulse"]["delta"], "pulse.delta"))
    start, end = map(float, document["time_span"])
    simulation = Simulation(register, sequence, _solver(document["solver"], start, end))
    result = simulation.run(_basis_state(simulation, document["initial_state"]["bitstring"]), start, end, dict(document.get("observables", {})))
    if not isinstance(result, SimulationResult):
        raise _error("VALIDATION_EXPERIMENT_CONFIG_RESULT_TYPE", "The config must declare observables to persist a SimulationResult.", "Add at least one observable.")
    result.manifest["source_config"] = {"schema_version": EXPERIMENT_CONFIG_SCHEMA_VERSION, "sha256": config.sha256, "source_kind": "file" if config.source_path else "mapping", "source_path": str(config.source_path) if config.source_path else None}
    outputs = document["outputs"]
    result_path = _path(config, outputs["result"])
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(str(result_path))
    if "manifest" in outputs:
        path = _path(config, outputs["manifest"]); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    if document.get("readout") is not None and "samples" in outputs:
        path = _path(config, outputs["samples"]); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.sample(document["readout"]["shots"], seed=document["readout"].get("seed")), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return result
