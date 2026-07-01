# Python Backend Setup

This guide covers Julia executable discovery, JuliaPkg resolution, Python/JuliaCall configuration, and the current CPU/GPU backend boundary for Python SDK users. For Julia-native projects, see [Julia backend setup](../julia/backend-setup.md).

## Julia Executable Overrides

If Julia is installed but cannot be found automatically, specify its executable before resolving Julia packages:

```bash
export PYTHON_JULIACALL_EXE=/absolute/path/to/julia
```

Windows PowerShell:

```powershell
$env:PYTHON_JULIACALL_EXE = "C:\absolute\path\to\julia.exe"
```

## Julia Backend Source Override

Python runtime backend discovery uses this order:

1. `SAGITTARIUS_JULIA_BACKEND_PATH`, when set, pointing at a `Sagittarius.jl` directory that contains `Project.toml` and `src/Sagittarius.jl`;
2. packaged Julia backend resources inside the installed Python package;
3. the adjacent repository checkout fallback used by current source installations.

Use the override only for development or local debugging:

```bash
export SAGITTARIUS_JULIA_BACKEND_PATH=/absolute/path/to/Sagittarius.jl
```

Windows PowerShell:

```powershell
$env:SAGITTARIUS_JULIA_BACKEND_PATH = "C:\absolute\path\to\Sagittarius.jl"
```

## JuliaPkg Runtime Is Not on PATH


If `uv run python -m juliapkg resolve` succeeds but the shell reports `julia: command not found`, do not install a second Julia runtime immediately. First query the executable selected by JuliaPkg:

```bash
cd Sagittarius/sagittarius_py
uv run python -c 'import juliapkg, shutil; exe = juliapkg.executable(); print(shutil.which(exe) or exe)'
```

Use the printed absolute path in Julia commands:

```bash
JULIA_EXE=/absolute/path/printed/above
"$JULIA_EXE" --version
```

If the command cannot query JuliaPkg, locate a downloaded executable directly:

```bash
find "$HOME/.julia" -type f -path '*/bin/julia'
```

JuliaPkg and Juliaup commonly place versioned runtimes below `~/.julia`. Avoid documenting or scripting a fixed version path because it changes after a Julia upgrade.

To make the selected executable available as `julia`, add its `bin` directory to `PATH`, then restart the shell or source its startup file:

```bash
export PATH="/absolute/path/to/julia/bin:$PATH"
```

A successful `"$JULIA_EXE" --version` does not mean the bare `julia` command is on `PATH`. These two commands use different lookup paths:

```bash
"$JULIA_EXE" --version   # uses the explicit executable path
julia --version          # requires a julia command on PATH
```

To make `julia` available in the current shell from a resolved executable:

```bash
export PATH="$(dirname "$JULIA_EXE"):$PATH"
julia --version
```

Add that `export PATH=...` line to your shell startup file, such as `~/.bashrc`, only if you want it to persist for future terminals.

## CPU Setup

CPU simulations do not require an NVIDIA GPU. The regular CPU test suite should run after source installation:

```bash
cd sagittarius_py
uv run python check_env.py
uv run python -m pytest tests/
```

The current dependency profile may still resolve CUDA.jl because `sagittarius/juliapkg.json` includes it. A CPU-first default profile with optional GPU setup is planned Phase 13 work.

## CUDA Setup

CUDA is the primary GPU development backend and is marked experimental. Before using it, run diagnostics:

```bash
cd sagittarius_py
uv run python - <<'PY'
from sagittarius import doctor
print(doctor(backend="CUDA", initialize_backend=True))
PY
```

GPU tests are opt-in:

```bash
SAGITTARIUS_ENABLE_GPU_TESTS=1 uv run python -m pytest tests/test_gpu_acceleration.py
```

CUDA requires a compatible host driver, device passthrough if containerized, CUDA runtime compatibility, Julia CUDA packages, and a visible GPU device. See [Backend maturity](../../reference/SPEC-BACKEND-001-backends.md) and [Containerized development](../containerization.md).

## Planned Backend Commands

Phase 13 plans a user-facing backend setup workflow such as:

```bash
sagittarius backend resolve
sagittarius backend install cuda
sagittarius doctor
```

Those commands are not documented as currently available here. Until they exist, use `uv run python -m juliapkg resolve` and `doctor()` as the explicit setup and diagnostics path.
