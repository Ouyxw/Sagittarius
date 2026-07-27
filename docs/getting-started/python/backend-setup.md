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

If you set JuliaCall overrides directly, set the executable and project together. JuliaCall rejects a partial configuration where only one of `PYTHON_JULIACALL_EXE` or `PYTHON_JULIACALL_PROJECT` is present:

```bash
export PYTHON_JULIACALL_EXE=/absolute/path/to/julia
export PYTHON_JULIACALL_PROJECT=/absolute/path/to/juliapkg/project
export PYTHON_JULIACALL_BINDIR="$("$PYTHON_JULIACALL_EXE" --startup-file=no -e 'print(Sys.BINDIR)')"
```

`PYTHON_JULIAPKG_PROJECT` is used by JuliaPkg and is not a substitute for `PYTHON_JULIACALL_PROJECT`. In the VS Code devcontainer, `.devcontainer/setup-juliacall-env.sh` derives the JuliaCall variables dynamically and writes them to `/etc/profile.d/sagittarius-juliacall.sh`; rebuild the container or run that script manually if an older container only has a partial JuliaCall environment.

## Julia Backend Source Override

Python runtime backend discovery uses this order:

1. `SAGITTARIUS_JULIA_BACKEND_PATH`, when set, pointing at a `Sagittarius.jl` directory that contains `Project.toml` and `src/Sagittarius.jl`;
2. the adjacent editable/source checkout backend, so Julia source edits take effect immediately during development;
3. packaged Julia backend resources inside an installed wheel or source distribution.

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

When Julia was installed through Juliaup, `command -v julia` may return a shim such as `$HOME/.juliaup/bin/julia`. Do not use `dirname "$PYTHON_JULIACALL_EXE"` as `PYTHON_JULIACALL_BINDIR` in that case. Query `Sys.BINDIR` through Julia so JuliaCall receives the real runtime directory:

```bash
export PYTHON_JULIACALL_BINDIR="$("$PYTHON_JULIACALL_EXE" --startup-file=no -e 'print(Sys.BINDIR)')"
```

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
uv run sagittarius doctor
uv run python -m pytest tests/
```

The default `sagittarius/juliapkg.json` profile is CPU-first and does not install CUDA.jl. CUDA remains opt-in through the packaged `sagittarius/juliapkg-cuda.json` profile and the `sagittarius backend install cuda` command.

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

CUDA requires a compatible host driver, device passthrough if containerized, CUDA runtime compatibility, Julia CUDA packages, and a visible GPU device. Use `sagittarius doctor --backend CUDA --initialize-backend` before enabling the opt-in GPU tests.

## Backend Commands

The Python package provides a user-facing backend setup workflow:

```bash
sagittarius backend resolve
sagittarius doctor
```

`backend resolve` resolves the default CPU-first JuliaPkg environment. It is the preferred command for installed wheels and source checkouts; `uv run python -m juliapkg resolve` remains the lower-level equivalent for debugging.

CUDA setup is explicit and experimental:

```bash
sagittarius backend profiles
sagittarius backend install cuda --dry-run
sagittarius backend install cuda
sagittarius doctor --backend CUDA --initialize-backend
```

`backend profiles` lists the packaged optional backend profiles and `backend install cuda --dry-run` prints the CUDA profile without changing the Julia environment. `backend install cuda` uses the packaged `juliapkg-cuda.json` profile and may download Julia CUDA packages. CUDA still requires compatible NVIDIA driver, runtime, device visibility, and parity validation before using CUDA results for claims.

Hardware-backed wheel validation is available as an opt-in smoke test:

```bash
cd sagittarius_py
SAGITTARIUS_RUN_CUDA_WHEEL_SMOKE=1 SAGITTARIUS_ENABLE_GPU_TESTS=1 \
  uv run python -m pytest tests/test_packaging_artifacts.py::test_clean_venv_installed_wheel_cuda_smoke_and_parity
```

The smoke installs the built wheel into a clean virtual environment outside the repository, runs `sagittarius backend install cuda`, checks `sagittarius doctor --backend CUDA --initialize-backend`, executes a small CPU/CUDA parity simulation, and validates result artifact and manifest metadata.
