# Julia Backend Setup

This guide is for Julia-native users who run `Sagittarius.jl` directly through Julia projects. Python/JuliaCall and JuliaPkg setup is documented separately in [Python backend setup](../python/backend-setup.md).

## Julia Executable

Julia-native workflows need a `julia` executable available in the shell, or an explicit absolute executable path used in commands.

```bash
julia --version
```

If you installed Julia through JuliaPkg while setting up the Python SDK, that executable may not be on `PATH`. You can query it from the Python environment and reuse the absolute path:

```bash
JULIA_EXE=$(cd ../Sagittarius/sagittarius_py && uv run python -c 'import juliapkg, shutil; exe = juliapkg.executable(); print(shutil.which(exe) or exe)')
"$JULIA_EXE" --version
```

To make that executable available as `julia` in the current shell:

```bash
export PATH="$(dirname "$JULIA_EXE"):$PATH"
julia --version
```

## Project Activation

Use a project-local environment instead of modifying `JULIA_LOAD_PATH`:

```bash
mkdir -p ~/workspace/my_julia_experiment
cd ~/workspace/my_julia_experiment
julia --project=. -e 'using Pkg; Pkg.develop(path="../Sagittarius/Sagittarius.jl"); Pkg.instantiate(); Pkg.precompile()'
```

`Pkg.develop` records the local Sagittarius checkout in the experiment environment and continues to load source code from that checkout.

## CPU Checks

A minimal native Julia check should load the package and construct a small reduced basis:

```bash
julia --project=. -e 'using Sagittarius; reg = chain_register(3; spacing=0.5, C6=10.0); ctx = reduced_basis_context(reg; blockade_radius=0.6); println(length(ctx.basis))'
```

Expected output:

```text
5
```

## CUDA Notes

CUDA support is experimental. Julia-native GPU use should be treated as a backend-specific workflow and should be paired with the backend maturity policy in [Backend maturity](../../reference/SPEC-BACKEND-001-backends.md). Python `doctor()` diagnostics are useful for Python SDK runs, but Julia-native users should also verify the Julia CUDA environment directly when using GPU entry points.
