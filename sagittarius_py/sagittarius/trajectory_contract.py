"""Versioned MCWF trajectory payload validation for result artifacts."""

from typing import Any, Mapping

import numpy as np

TRAJECTORY_DATA_SCHEMA_VERSION = "trajectory-data/v1"
TRAJECTORY_DATA_TYPE = "sagittarius.mcwf_trajectories"
TRAJECTORY_AXIS_ORDER = ["trajectory", "time"]


def _observable_names(data: Mapping[str, Any]) -> list[str]:
    if not isinstance(data, Mapping) or "t" not in data:
        raise ValueError("Trajectory storage requires result data with a 't' time series.")
    names = [str(name) for name in data if name != "t"]
    if not names:
        raise ValueError("Trajectory storage requires at least one observable series.")
    return names


def _time_values(data: Mapping[str, Any]) -> np.ndarray:
    values = np.asarray(data["t"], dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("Trajectory storage requires a non-empty finite one-dimensional 't' series.")
    return values


def serialize_trajectories(
    trajectories: Mapping[str, Any] | None,
    data: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Validate in-memory trajectory arrays and produce ``trajectory-data/v1``."""
    if trajectories is None:
        return None
    if not isinstance(trajectories, Mapping):
        raise ValueError("Trajectories must be a mapping from observable name to a two-dimensional array.")

    observable_names = _observable_names(data)
    if list(trajectories) != observable_names:
        raise ValueError(
            "Trajectory observable order must exactly match result observable order: "
            + ", ".join(observable_names)
        )
    time_values = _time_values(data)
    series: dict[str, list[list[float]]] = {}
    trajectory_count: int | None = None
    for name in observable_names:
        values = np.asarray(trajectories[name], dtype=float)
        if values.ndim != 2:
            raise ValueError(f"Trajectory series {name!r} must have shape (trajectory, time).")
        if values.shape[1] != time_values.size:
            raise ValueError(
                f"Trajectory series {name!r} time axis has length {values.shape[1]}, "
                f"expected {time_values.size}."
            )
        if values.shape[0] < 1:
            raise ValueError(f"Trajectory series {name!r} must contain at least one trajectory.")
        if not np.all(np.isfinite(values)):
            raise ValueError(f"Trajectory series {name!r} contains non-finite values.")
        if trajectory_count is None:
            trajectory_count = int(values.shape[0])
        elif values.shape[0] != trajectory_count:
            raise ValueError("All trajectory series must have the same trajectory axis length.")
        series[name] = values.tolist()

    return {
        "schema_version": TRAJECTORY_DATA_SCHEMA_VERSION,
        "artifact_type": TRAJECTORY_DATA_TYPE,
        "axis_order": list(TRAJECTORY_AXIS_ORDER),
        "observable_names": observable_names,
        "time_values": time_values.tolist(),
        "shape": {
            "trajectory_count": trajectory_count,
            "time_count": int(time_values.size),
        },
        "series": series,
    }


def deserialize_trajectories(payload: Any, data: Mapping[str, Any]) -> dict[str, np.ndarray] | None:
    """Validate a trajectory payload and return ordered in-memory arrays.

    A legacy unversioned observable-to-array mapping remains readable for artifacts
    created before ``trajectory-data/v1`` was introduced.
    """
    if payload is None:
        return None
    if not isinstance(payload, Mapping):
        raise ValueError("Result artifact trajectories must be an object or null.")

    if "schema_version" not in payload:
        normalized = serialize_trajectories(payload, data)
        return {name: np.asarray(values, dtype=float) for name, values in normalized["series"].items()}

    required = {"schema_version", "artifact_type", "axis_order", "observable_names", "time_values", "shape", "series"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError("Trajectory payload is missing required fields: " + ", ".join(missing))
    if payload["schema_version"] != TRAJECTORY_DATA_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported trajectory schema_version: {payload['schema_version']!r}."
        )
    if payload["artifact_type"] != TRAJECTORY_DATA_TYPE:
        raise ValueError(f"Unsupported trajectory artifact_type: {payload['artifact_type']!r}.")
    if payload["axis_order"] != TRAJECTORY_AXIS_ORDER:
        raise ValueError("Trajectory axis_order must be ['trajectory', 'time'].")
    if not isinstance(payload["observable_names"], list) or not all(isinstance(name, str) for name in payload["observable_names"]):
        raise ValueError("Trajectory observable_names must be an ordered list of strings.")
    if not isinstance(payload["shape"], Mapping):
        raise ValueError("Trajectory shape must be an object.")
    expected_names = _observable_names(data)
    if payload["observable_names"] != expected_names:
        raise ValueError("Trajectory observable_names must exactly match result observable order.")
    if not np.array_equal(np.asarray(payload["time_values"], dtype=float), _time_values(data)):
        raise ValueError("Trajectory time_values must exactly match result data['t'].")
    normalized = serialize_trajectories(payload["series"], data)
    if normalized["shape"] != dict(payload["shape"]):
        raise ValueError("Trajectory shape metadata does not match trajectory series.")
    return {name: np.asarray(values, dtype=float) for name, values in normalized["series"].items()}


def trajectory_manifest(trajectories: Mapping[str, Any] | None, data: Mapping[str, Any], *, requested: bool) -> dict[str, Any]:
    """Return requested and effective trajectory-storage metadata for run-manifest/v1."""
    payload = serialize_trajectories(trajectories, data)
    if payload is None:
        return {
            "requested": bool(requested),
            "stored": False,
            "schema_version": TRAJECTORY_DATA_SCHEMA_VERSION,
            "axis_order": list(TRAJECTORY_AXIS_ORDER),
            "observable_names": [],
            "trajectory_count": 0,
            "time_count": 0,
        }
    return {
        "requested": bool(requested),
        "stored": True,
        "schema_version": payload["schema_version"],
        "axis_order": payload["axis_order"],
        "observable_names": payload["observable_names"],
        "trajectory_count": payload["shape"]["trajectory_count"],
        "time_count": payload["shape"]["time_count"],
    }


def validate_trajectory_manifest(storage: Any) -> None:
    """Validate effective trajectory-storage metadata in ``run-manifest/v1``."""
    if not isinstance(storage, Mapping):
        raise ValueError("solver.trajectory_storage must be an object.")
    required = {
        "requested", "stored", "schema_version", "axis_order", "observable_names",
        "trajectory_count", "time_count",
    }
    missing = sorted(required - set(storage))
    if missing:
        raise ValueError("solver.trajectory_storage is missing fields: " + ", ".join(missing))
    if not isinstance(storage["requested"], bool) or not isinstance(storage["stored"], bool):
        raise ValueError("solver.trajectory_storage requested and stored must be booleans.")
    if storage["schema_version"] != TRAJECTORY_DATA_SCHEMA_VERSION:
        raise ValueError("solver.trajectory_storage has an unsupported schema_version.")
    if storage["axis_order"] != TRAJECTORY_AXIS_ORDER:
        raise ValueError("solver.trajectory_storage axis_order must be ['trajectory', 'time'].")
    if not isinstance(storage["observable_names"], list) or not all(isinstance(name, str) for name in storage["observable_names"]):
        raise ValueError("solver.trajectory_storage observable_names must be a list of strings.")
    for field in ("trajectory_count", "time_count"):
        value = storage[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"solver.trajectory_storage {field} must be a non-negative integer.")
    if not storage["stored"] and (
        storage["observable_names"] or storage["trajectory_count"] != 0 or storage["time_count"] != 0
    ):
        raise ValueError("unstored trajectory metadata must have empty observable_names and zero counts.")
    if storage["stored"] and (
        not storage["observable_names"] or storage["trajectory_count"] < 1 or storage["time_count"] < 1
    ):
        raise ValueError("stored trajectory metadata requires observable names and positive shape counts.")
