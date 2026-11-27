"""Small measurement/retention helpers for supervised benchmark campaigns."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time

import numpy as np


def write_json(path, value):
    """Atomically checkpoint progress so a killed child leaves readable evidence."""
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def runtime_summary(repeats, requested):
    eligible = [row for row in repeats if row["eligible"]]
    values = [row["runtime_seconds"] for row in eligible]
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Eligible timings must be finite and nonnegative.")
    statistics = dict.fromkeys(("median", "min", "max", "p25", "p75"))
    if values:
        statistics.update(zip(statistics, map(float, (
            np.median(values), np.min(values), np.max(values),
            np.quantile(values, .25, method="linear"), np.quantile(values, .75, method="linear"),
        ))))
    return {
        "requested": requested, "completed": len(repeats), "eligible": len(eligible),
        "input_row_ids": [row["row_id"] for row in eligible],
        "quantile_convention": "numpy linear (Hyndman-Fan type 7)",
        "runtime_seconds": statistics,
        "unavailable_reason": None if values else "No eligible measured repeats.",
    }


def linux_process_memory(pid):
    """RSS/HWM in bytes; unavailable platforms retain a reason instead of zero."""
    try:
        fields = {}
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith(("VmRSS:", "VmHWM:")):
                key, value, unit = line.split()
                if unit != "kB":
                    raise ValueError(f"Unexpected /proc memory unit: {unit}")
                fields[key.rstrip(":")] = int(value) * 1024
        return {"rss_bytes": fields.get("VmRSS"), "peak_bytes": fields.get("VmHWM"),
                "source_unit": "kB (1024 bytes)", "method": "/proc/PID/status", "reason": None}
    except (OSError, ValueError) as exc:
        return {"rss_bytes": None, "peak_bytes": None, "source_unit": None,
                "method": "/proc/PID/status", "reason": str(exc)}


def supervise(command, *, cwd, env, log_path, timeout_seconds, memory_limit_bytes):
    """Supervise one scenario process; enforce sampled RSS and wall-time limits.

    RSS polling is not an address-space limit. A short transient can exceed the
    budget between polls; the child also reports its kernel lifetime high-water
    mark. Terminating a child never removes its previously checkpointed work.
    """
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0 or memory_limit_bytes <= 0:
        raise ValueError("Resource limits must be finite and positive.")
    if not Path("/proc/self/status").exists():
        raise RuntimeError("RSS-supervised campaigns currently require Linux /proc.")
    started = time.monotonic()
    peak = None
    reason = None
    with Path(log_path).open("w") as log:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            while process.poll() is None:
                memory = linux_process_memory(process.pid)
                sample = memory["peak_bytes"]
                if sample is not None:
                    peak = max(peak or 0, sample)
                if memory["rss_bytes"] is not None and memory["rss_bytes"] > memory_limit_bytes:
                    reason = "memory"
                elif time.monotonic() - started > timeout_seconds:
                    reason = "timeout"
                if reason:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    break
                time.sleep(.05)
        except BaseException:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait()
            raise
        returncode = process.wait()
    return {"returncode": returncode, "reason": reason,
            "wall_seconds": time.monotonic() - started, "sampled_peak_bytes": peak,
            "memory_limit_bytes": memory_limit_bytes, "timeout_seconds": timeout_seconds,
            "method": "/proc/PID/status VmHWM, sampled every 50 ms",
            "scope": "one scenario process including initialization, references and serialization"}
