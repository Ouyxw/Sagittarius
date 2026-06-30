# Julia User Projects

Julia users should keep long-running experiments outside the Sagittarius repository and give each experiment its own Julia project.

## Recommended Layout

```text
~/workspace/
|-- Sagittarius/
`-- my_julia_experiment/
    |-- Project.toml
    |-- Manifest.toml
    |-- scripts/
    |   `-- rabi_simulation.jl
    |-- results/
    `-- notebooks/
```

## Initialize the Project

This workflow needs a Julia executable in the current shell. Setting `PYTHON_JULIACALL_EXE` for Python/JuliaCall, or exporting `PATH` only inside `Sagittarius/sagittarius_py`, does not make `julia` available in a separate experiment shell.

Either install Julia on `PATH`, or carry the absolute executable path reported by JuliaPkg into the experiment shell:

```bash
mkdir -p ~/workspace/my_julia_experiment/scripts
cd ~/workspace/my_julia_experiment

JULIA_EXE=$(cd ../Sagittarius/sagittarius_py && uv run python -c 'import juliapkg, shutil; exe = juliapkg.executable(); print(shutil.which(exe) or exe)')
"$JULIA_EXE" --version

"$JULIA_EXE" --project=. -e '
using Pkg
Pkg.develop(path="../Sagittarius/Sagittarius.jl")
Pkg.instantiate()
Pkg.precompile()
using Sagittarius
println("Sagittarius loaded successfully")
'
```

`Pkg.develop` records Sagittarius in the experiment's `Project.toml` and `Manifest.toml` while continuing to load source code from the local checkout. It is not necessary to modify `JULIA_LOAD_PATH` or copy `Sagittarius.jl` into the experiment.

Because `--project=.` already activates the current directory, an additional `Pkg.activate(".")` call is unnecessary.

## Minimal Julia Script

A minimal `scripts/rabi_simulation.jl` can use the package directly:

```julia
using Sagittarius

reg = chain_register(3; spacing=0.5, C6=100.0)
context = reduced_basis_context(reg; blockade_radius=0.6)

H = hamiltonian(
    reg,
    fill(1.0, 3),
    zeros(3);
    basis_context=context,
)

println("Reduced basis size: ", length(context.basis))
```

Run scripts from the experiment root with its project activated:

```bash
cd ~/workspace/my_julia_experiment
JULIA_EXE=$(cd ../Sagittarius/sagittarius_py && uv run python -c 'import juliapkg, shutil; exe = juliapkg.executable(); print(shutil.which(exe) or exe)')
"$JULIA_EXE" --project=. scripts/rabi_simulation.jl
```

Always using `--project=.` prevents dependencies from being taken accidentally from the global Julia environment. Keep experiment scripts in the experiment `scripts/` directory; `Sagittarius/scripts/` remains reserved for repository maintenance and debugging.

If the Sagittarius checkout moves, update its path with `Pkg.develop(path="...")` from the experiment environment and run `Pkg.instantiate()` again.

## Nested Script Directories

If you are already inside a nested script directory, keep using the resolved executable and point `--project` back to the experiment root. For example, from `my_julia_experiment/scripts/dual_sdk`:

```bash
"$JULIA_EXE" --project=../.. algo_prototyping.jl
```

See [Backend setup](backend-setup.md) for details on JuliaPkg runtimes and making `julia` available on `PATH`.
