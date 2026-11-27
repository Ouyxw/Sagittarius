"""Versioned artifacts for resumable scientific parameter exploration."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Union

from .api import _json_compatible
from .runtime import SagittariusSerializationError, SagittariusValidationError, make_issue

SWEEP_ARTIFACT_SCHEMA_VERSION = "sweep-artifact/v1"
SWEEP_ARTIFACT_TYPE = "sagittarius.experiment_sweep"
SWEEP_PURPOSE = "scientific_exploration"
_ITEM_STATUSES = {"pending", "running", "succeeded", "failed"}


def _error(code: str, message: str, remediation: str) -> SagittariusValidationError:
    return SagittariusValidationError(make_issue(code, message, remediation))


def _serror(code: str, message: str, remediation: str) -> SagittariusSerializationError:
    return SagittariusSerializationError(make_issue(code, message, remediation))


def _canonical(value: Any) -> Any:
    try:
        return json.loads(json.dumps(_json_compatible(value), sort_keys=True, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise _error("VALIDATION_SWEEP_ARTIFACT_JSON", "Sweep artifacts must contain finite JSON-compatible values.", "Use finite JSON values for axes, parameters, paths, and failures.") from exc


def _validate_axes(axes: Any) -> list[dict[str, Any]]:
    if not isinstance(axes, list) or not axes:
        raise _error("VALIDATION_SWEEP_ARTIFACT_AXES", "axes must be a non-empty list.", "Provide one or more named parameter axes.")
    names = set()
    result = []
    for index, axis in enumerate(axes):
        if not isinstance(axis, Mapping) or set(axis) != {"name", "path", "values"}:
            raise _error("VALIDATION_SWEEP_ARTIFACT_AXIS", f"axes[{index}] must contain exactly name, path, and values.", "Use {'name': 'omega', 'path': 'pulse.omega', 'values': [...] }.")
        name, path, values = axis["name"], axis["path"], axis["values"]
        if not isinstance(name, str) or not name or name in names:
            raise _error("VALIDATION_SWEEP_ARTIFACT_AXIS_NAME", "Every axis name must be a unique non-empty string.", "Use distinct names such as omega and delta.")
        if not isinstance(path, str) or not path:
            raise _error("VALIDATION_SWEEP_ARTIFACT_AXIS_PATH", f"Axis {name!r} needs a non-empty config path.", "Use a dotted experiment-config path such as solver.blockade_radius.")
        if not isinstance(values, list) or not values:
            raise _error("VALIDATION_SWEEP_ARTIFACT_AXIS_VALUES", f"Axis {name!r} must have at least one value.", "Provide a non-empty JSON list of candidate values.")
        names.add(name); result.append(dict(axis))
    return result


def _validate_item(item: Any, axis_names: set[str]) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        raise _error("VALIDATION_SWEEP_ARTIFACT_ITEM", "Each sweep item must be a JSON object.", "Regenerate the artifact with make_sweep_artifact().")
    required = {"item_id", "parameters", "status", "attempts", "result_path", "manifest_path", "failure"}
    if set(item) != required:
        raise _error("VALIDATION_SWEEP_ARTIFACT_ITEM_FIELDS", "Each item must contain the documented status, paths, and failure fields.", "Regenerate the artifact with make_sweep_artifact().")
    if not isinstance(item["item_id"], str) or not item["item_id"]:
        raise _error("VALIDATION_SWEEP_ARTIFACT_ITEM_ID", "item_id must be a non-empty string.", "Use stable item IDs such as item-0001.")
    if not isinstance(item["parameters"], Mapping) or set(item["parameters"]) != axis_names:
        raise _error("VALIDATION_SWEEP_ARTIFACT_ITEM_PARAMETERS", "Each item parameters mapping must contain exactly the declared axis names.", "Record one value for every parameter axis.")
    if item["status"] not in _ITEM_STATUSES:
        raise _error("VALIDATION_SWEEP_ARTIFACT_ITEM_STATUS", "Item status must be pending, running, succeeded, or failed.", "Use a documented sweep item status.")
    if not isinstance(item["attempts"], int) or item["attempts"] < 0:
        raise _error("VALIDATION_SWEEP_ARTIFACT_ATTEMPTS", "Item attempts must be a non-negative integer.", "Increment attempts for each execution attempt.")
    for field in ("result_path", "manifest_path"):
        if item[field] is not None and (not isinstance(item[field], str) or not item[field]):
            raise _error("VALIDATION_SWEEP_ARTIFACT_PATH", f"{field} must be a non-empty path string or null.", "Record the result/manifest file path when available.")
    if item["status"] == "succeeded" and (item["result_path"] is None or item["manifest_path"] is None):
        raise _error("VALIDATION_SWEEP_ARTIFACT_SUCCESS_LINKS", "Succeeded items require both result_path and manifest_path.", "Link every completed result and its run manifest.")
    if item["status"] == "failed" and not isinstance(item["failure"], Mapping):
        raise _error("VALIDATION_SWEEP_ARTIFACT_FAILURE", "Failed items require a structured failure record.", "Record code, message, and remediation for the failure.")
    if item["status"] != "failed" and item["failure"] is not None:
        raise _error("VALIDATION_SWEEP_ARTIFACT_FAILURE", "Only failed items may contain a failure record.", "Set failure to null for pending, running, and succeeded items.")
    return dict(item)


def make_sweep_artifact(*, axes: Iterable[Mapping[str, Any]], items: Iterable[Mapping[str, Any]], base_config: Mapping[str, Any], artifact_path: str | None = None) -> dict[str, Any]:
    """Build a scientific-exploration artifact; it is not benchmark evidence."""
    axes_list = _validate_axes(_canonical(list(axes)))
    axis_names = {axis["name"] for axis in axes_list}
    item_list = [_validate_item(item, axis_names) for item in _canonical(list(items))]
    ids = [item["item_id"] for item in item_list]
    if len(ids) != len(set(ids)):
        raise _error("VALIDATION_SWEEP_ARTIFACT_ITEM_ID", "Sweep item IDs must be unique.", "Assign one stable ID per parameter combination.")
    pending = [item["item_id"] for item in item_list if item["status"] in {"pending", "running", "failed"}]
    artifact = {
        "schema_version": SWEEP_ARTIFACT_SCHEMA_VERSION,
        "artifact_type": SWEEP_ARTIFACT_TYPE,
        "purpose": SWEEP_PURPOSE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_config": _canonical(base_config),
        "axes": axes_list,
        "items": item_list,
        "resumability": {
            "schema_version": "sweep-resume/v1",
            "artifact_path": artifact_path,
            "resume_policy": "retry_pending_running_and_failed",
            "pending_item_ids": pending,
            "completed_item_ids": [item["item_id"] for item in item_list if item["status"] == "succeeded"],
        },
    }
    validate_sweep_artifact(artifact)
    return artifact


def validate_sweep_artifact(artifact: Mapping[str, Any]) -> None:
    required = {"schema_version", "artifact_type", "purpose", "created_at", "base_config", "axes", "items", "resumability"}
    if not isinstance(artifact, Mapping) or set(artifact) != required:
        raise _error("VALIDATION_SWEEP_ARTIFACT_SCHEMA", "Artifact fields do not match sweep-artifact/v1.", "Use make_sweep_artifact() or a compatible artifact writer.")
    if artifact["schema_version"] != SWEEP_ARTIFACT_SCHEMA_VERSION or artifact["artifact_type"] != SWEEP_ARTIFACT_TYPE:
        raise _error("VALIDATION_SWEEP_ARTIFACT_SCHEMA", "Artifact is not sweep-artifact/v1 / sagittarius.experiment_sweep.", "Do not pass benchmark-artifact/v1 to the sweep APIs.")
    if artifact["purpose"] != SWEEP_PURPOSE:
        raise _error("VALIDATION_SWEEP_ARTIFACT_PURPOSE", "Sweep artifacts are only for scientific exploration.", "Use benchmark-artifact/v1 and the benchmark workflow for governed evidence.")
    axes = _validate_axes(artifact["axes"]); names = {axis["name"] for axis in axes}
    items = [_validate_item(item, names) for item in artifact["items"]]
    resume = artifact["resumability"]
    if not isinstance(resume, Mapping) or resume.get("schema_version") != "sweep-resume/v1":
        raise _error("VALIDATION_SWEEP_ARTIFACT_RESUME", "resumability must use sweep-resume/v1.", "Regenerate the artifact with make_sweep_artifact().")
    expected_pending = [item["item_id"] for item in items if item["status"] in {"pending", "running", "failed"}]
    if resume.get("pending_item_ids") != expected_pending:
        raise _error("VALIDATION_SWEEP_ARTIFACT_RESUME", "resumability.pending_item_ids does not match item statuses.", "Refresh the artifact after updating item status.")


def resume_item_ids(artifact: Mapping[str, Any]) -> list[str]:
    """Return the stable IDs that must be retried to resume a sweep."""
    validate_sweep_artifact(artifact)
    return list(artifact["resumability"]["pending_item_ids"])


def save_sweep_artifact(artifact: Mapping[str, Any], filepath: Union[str, Path]) -> dict[str, Any]:
    artifact = _canonical(artifact); validate_sweep_artifact(artifact)
    path = Path(filepath)
    artifact["resumability"]["artifact_path"] = str(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    except OSError as exc:
        raise _serror("SERIALIZATION_SWEEP_ARTIFACT_WRITE_FAILED", f"Could not write {str(path)!r}.", "Check the output path and permissions.") from exc
    return artifact


def load_sweep_artifact(filepath: Union[str, Path]) -> dict[str, Any]:
    path = Path(filepath)
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _serror("SERIALIZATION_SWEEP_ARTIFACT_READ_FAILED", f"Could not load {str(path)!r}.", "Check that it is a readable sweep-artifact/v1 JSON file.") from exc
    validate_sweep_artifact(artifact)
    return artifact
