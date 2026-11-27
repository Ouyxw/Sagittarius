"""Backend-free validation of saved matched CPU/CUDA solve evidence."""
from __future__ import annotations

import numpy as np
from .api import validate_run_manifest

CUDA_WORKLOAD_VERSION = "matched-cpu-cuda-ode/v2"

MATCHED_SOLVER_FIELDS = (
    "method", "effective_method", "adaptive", "effective_adaptive", "dt", "effective_dt",
    "reltol", "abstol", "saveat", "effective_saveat", "blockade_radius", "observables", "t_span",
    "gamma", "gamma_phi", "use_mc",
)


def json_native(value):
    """Preserve Julia DictValue device fields as structured JSON, like CUDA protocol."""
    if hasattr(value, "items"):
        return {str(key): json_native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_native(item) for item in value]
    return value


def solve_pair_gate(cpu, cuda, times, atol, observable_names=("pop0",)):
    """Check full trajectories and executed settings, rejecting GPU fallback.

    CPU parity verifies implementation agreement, not independent scientific
    model validity. No runtime ratio is derived by this helper.
    """
    trajectories = []
    for result, backend in ((cpu, "CPU"), (cuda, "CUDA")):
        manifest = result.manifest
        validate_run_manifest(manifest)
        solver = manifest["solver"]
        if solver["use_gpu"] != (backend == "CUDA") or manifest["backend_diagnostics"]["requested_backend"] != backend or (backend == "CUDA" and solver.get("gpu_backend") != "CUDA"):
            raise AssertionError("Executed backend mismatch or CPU fallback")
        if solver["effective_method"] != "Tsit5" or not solver["effective_adaptive"] or solver["effective_dt"] is not None:
            raise AssertionError("Executed solver differs from adaptive Tsit5 anchor")
        if solver["effective_saveat"] != list(times):
            raise AssertionError("Effective output grid differs from frozen grid")
        t = np.asarray(result.data["t"])
        values = np.asarray([result.data[name] for name in observable_names])
        if t.shape != (len(times),) or values.shape != (len(observable_names), len(times)) or not np.allclose(t, times, rtol=0, atol=1e-14):
            raise AssertionError("Trajectory shape/output grid mismatch")
        trajectories.append(values)
    if any(cpu.manifest["solver"][key] != cuda.manifest["solver"][key] for key in MATCHED_SOLVER_FIELDS):
        raise AssertionError("CPU/CUDA effective solver configuration mismatch")
    if any(cpu.manifest[key] != cuda.manifest[key] for key in ("register", "pulse", "initial_state")):
        raise AssertionError("CPU/CUDA register/pulse/basis/initial-state mismatch")
    finite = bool(all(np.all(np.isfinite(values)) for values in trajectories))
    error = float(np.max(np.abs(trajectories[0] - trajectories[1]))) if finite else None
    return {"finite": finite, "parity_max_abs_error": error, "parity_atol": atol,
            "passed": finite and error <= atol, "output_sample_count": len(times)}
