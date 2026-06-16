# Verifiable Performance Claims

Sagittarius performance statements must be tied to reproducible benchmark artifacts. Use this page as the review checklist before publishing README text, reports, plots, release notes, or hardware-facing summaries.

For claims involving Rydberg/MWIS mappings or neutral-atom simulator positioning, also check [`prior-art-notes.md`](prior-art-notes.md). For public releases or external reports, create or update a row in [`disclosure-control.md`](disclosure-control.md).

## Claim Requirements

A performance claim is verifiable only when it names all of the following:

- the benchmark artifact path or generated report stem;
- hardware model, accelerator backend, and whether the run was inside a container;
- `version-info/v1` metadata, including Python, Julia, Sagittarius.jl, and git source/build fields when available;
- solver configuration, tolerances, pulse schedule, blockade radius, and problem size;
- measured metric names exactly as written in the `benchmark-artifact/v1` rows;
- date or commit associated with the artifact.

Avoid unqualified claims such as "production ready", "linear scaling", "efficiently solves NP-hard instances", "GPU is faster", or "N=20 is sub-second" unless the same sentence or adjacent paragraph points to the exact artifact and configuration that produced the number.

## Approved Wording Patterns

Use bounded wording:

- "In artifact `<path>`, benchmark `<name>` measured `<metric>` on `<hardware>` for `<problem/config>`."
- "For this artifact only, CUDA was faster than CPU for rows where `<condition>` held."
- "The benchmark script emits `benchmark-artifact/v1` JSON plus CSV and Markdown companions; rerun it on the target machine before comparing results."

Use capability wording for unmeasured paths:

- "The CUDA path exists and is experimental."
- "AMDGPU and Metal are planned API names and require backend-specific validation before performance claims."
- "MWIS examples are research scaffolding; exact correctness should be checked with `batch_verify.py` or another exact baseline."

## Current Artifact Sources

The repository scripts that produce claim-ready artifacts are:

| Script | Artifact stem | Scope |
| :--- | :--- | :--- |
| `sagittarius_py/tests/test_performance/benchmark_scaling.py` | `scaling_results` | Reduced-basis CPU scaling rows. |
| `sagittarius_py/tests/test_performance/benchmark_gpu.py` | `gpu_results` | CPU vs CUDA timing with observable evaluation. |
| `sagittarius_py/tests/test_performance/benchmark_cluster.py` | `cluster_results` | Parallel parameter-sweep timing. |
| `sagittarius_py/tests/test_performance/benchmark_ablation.py` | `ablation_results` | Hamiltonian execution path timings, with optional CUDA cached sparse timing. |
| `sagittarius_py/projects/mwis_udg/batch_verify.py` | `mwis-batch-verification/v1` in-memory report | Seeded UDG/MWIS AQC-vs-ILP verification metrics. |

Generated benchmark JSON files carry `benchmark-artifact/v1`, companion CSV/Markdown tables, runtime/build/backend metadata, process memory usage, and linked run manifests when simulations produce `SimulationResult` objects.

## Historical Notes

Older Markdown summaries in `sagittarius_py/tests/test_performance/` or `sagittarius_py/projects/mwis_udg/` may record one-off local measurements. Treat them as historical notes unless they reference a current `benchmark-artifact/v1` file and include the exact environment and configuration. Prefer regenerating artifacts with the current scripts before using any number externally.
