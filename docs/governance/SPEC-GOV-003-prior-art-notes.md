# Prior-Art-Aware Technical Notes

Spec ID: `SPEC-GOV-003`
Status: `Policy`
Roadmap: Phase 10
Version: `prior-art-notes/v1`
Last reviewed: 2026-06-30


This internal note separates Sagittarius implementation work from known Rydberg neutral-atom, MWIS, and simulator prior art. It is an engineering review aid, not legal advice or a patentability opinion. Before public technical disclosures, update this note with the exact release date, artifact references, and any newly reviewed sources.

## Review Scope

Sagittarius is a classical emulator and SDK for Rydberg neutral-atom analog dynamics. The project includes Python and Julia APIs, reduced-basis simulation, open-system solvers, CUDA-oriented execution paths, benchmark artifacts, result schemas, and an MWIS-on-unit-disk-graphs example.

The following should be treated as known background unless a future legal review says otherwise:

- Rydberg blockade physics and the Rydberg Hamiltonian model for neutral-atom arrays.
- Mapping unit-disk graph MWIS/MIS instances to Rydberg atom arrangements.
- Adiabatic or variational schedules for finding independent sets with Rydberg arrays.
- Benchmarking quantum optimization against exact, heuristic, or simulated annealing classical baselines.
- Pulse-level programming frameworks and analog Hamiltonian simulation workflows for neutral-atom devices.

## Representative Prior Art

| Area | Representative sources | Prior-art boundary for Sagittarius |
| :--- | :--- | :--- |
| Rydberg blockade and neutral-atom quantum simulation | Rydberg blockade and neutral-atom computing are established foundations; see, for example, Saffman/Walker/Molmer reviews and Aquila-style analog Hamiltonian simulation descriptions. | Do not frame the blockade Hamiltonian, atom-array analog simulation, or blockade-constrained Hilbert space as Sagittarius-specific inventions. |
| MIS/MWIS on unit-disk graphs with Rydberg arrays | Ebadi et al., "Quantum Optimization of Maximum Independent Set using Rydberg Atom Arrays"; Nguyen et al., "Quantum optimization with arbitrary connectivity using Rydberg atom arrays"; Farouk et al., "Generation of quantum phases of matter and finding a maximum-weight independent set of unit-disk graphs using Rydberg atoms". | Do not claim the UDG/MWIS-to-Rydberg mapping, weight-to-detuning idea, or adiabatic independent-set search as novel Sagittarius contributions. |
| Hardness and benchmark methodology | Andrist et al., "Hardness of the maximum-independent-set problem on unit-disk graphs and prospects for quantum speedups". | Hardness metrics such as solution degeneracy, local minima, and classical baseline comparisons are prior benchmark methodology. Sagittarius may implement reproducible checks, but should not present those metrics as new. |
| Neutral-atom pulse/device software | Pulser is an open-source Python package for pulse sequence design in programmable neutral-atom arrays. Aquila is documented as an analog Hamiltonian simulator exposed through AWS Braket. Bloqade/Bloqade-style tooling is part of the neutral-atom software ecosystem. | Do not claim pulse-level neutral-atom programming, analog Hamiltonian device workflows, or Python/Julia neutral-atom SDK concepts broadly. |
| General numerical solvers and sparse/GPU techniques | SciML/OrdinaryDiffEq, sparse matrix formats, CUDA sparse kernels, and matrix-free operator patterns are established numerical infrastructure. | Sagittarius-specific discussion should focus on local integration choices, schemas, tests, and code paths, not ownership of generic sparse/GPU numerical techniques. |

## Sagittarius-Specific Engineering Scope

The project-specific technical work is best described as an integration and reproducibility layer around the Rydberg simulation problem:

- Python SDK objects (`Atom`, `Register`, `PulseSequence`, `SolverConfig`, `Simulation`, `SimulationResult`) paired with Julia-native constructors and solver facades.
- Cross-language parity contracts for atom ordering, bitstring ordering, local addressing, pulse semantics, Hamiltonian construction, solver settings, result schemas, and manifests.
- `run-manifest/v1`, `result-artifact/v1`, `shared-result/v1`, `benchmark-artifact/v1`, and `version-info/v1` schemas that make runs and benchmark claims auditable.
- Structured event taxonomy and diagnostics for backend initialization, validation, solver execution, serialization failures, and benchmark metadata.
- Implementation choices such as reduced-basis cache keys, dense bitstring-to-index lookup fallback rules, sparse pattern reuse, CUDA value-buffer reuse, and shared `BasisContext` plumbing across Hamiltonians, observables, jump operators, and MCWF trajectories.
- Backend-free scientific validation helpers (`dense_vs_reduced_validation`, open-system sanity checks) and seeded MWIS batch verification against exact PuLP/CBC ILP solutions.

When writing public material, prefer phrases like "Sagittarius implements", "Sagittarius validates", "Sagittarius records", or "Sagittarius integrates" instead of "Sagittarius introduces" for concepts with known prior art.

## Claims to Avoid

Avoid these claims unless a separate review and artifact-backed evidence explicitly supports them:

- Sagittarius invented Rydberg blockade simulation or the Rydberg Hamiltonian model.
- Sagittarius invented the UDG/MWIS-to-Rydberg mapping or weight-to-detuning encoding.
- Sagittarius demonstrates quantum speedup or solves NP-hard MWIS instances generally.
- Sagittarius is a calibrated hardware control stack or replaces Pulser, Bloqade, Braket/Aquila tooling, or vendor calibration layers.
- Sagittarius GPU behavior is production-ready or generally faster without benchmark artifact references.
- Reduced-basis pruning, sparse matrices, matrix-free operators, or CUDA sparse kernels are novel as standalone concepts.

## Safer Public Wording

Use bounded wording that identifies the implementation and evidence:

- "Sagittarius implements a Rydberg blockade emulator with Python and Julia APIs and validates cross-language Hamiltonian semantics on small golden fixtures."
- "The MWIS example maps UDG instances into a Rydberg-style simulation following established literature; Sagittarius adds seeded batch verification against exact ILP baselines."
- "The benchmark scripts emit `benchmark-artifact/v1` files with hardware, version, backend, and solver metadata; performance statements should cite those artifacts."
- "The CUDA path is experimental and should be enabled only after `doctor(backend="CUDA", initialize_backend=True)` passes in the target environment."

## Disclosure Checklist

Before publishing a README section, benchmark report, release note, blog post, paper draft, or demo script:

- Identify whether the text is about known physics/mapping background, Sagittarius implementation, measured performance, or patent-sensitive strategy.
- Cite representative prior art when discussing Rydberg/MWIS mappings, hardware speedups, or neutral-atom software workflows.
- Replace broad performance language with artifact-backed wording from [`SPEC-GOV-001-performance-claims.md`](SPEC-GOV-001-performance-claims.md).
- Attach run manifests, shared result schemas, benchmark artifacts, and version metadata where measurements are discussed.
- Record planned and actual public disclosure dates in [`SPEC-GOV-002-disclosure-control.md`](SPEC-GOV-002-disclosure-control.md).

## Source Pointers

Use primary sources where possible:

- Ebadi et al., "Quantum Optimization of Maximum Independent Set using Rydberg Atom Arrays", [arXiv:2202.09372](https://arxiv.org/abs/2202.09372) / Science 2022.
- Nguyen et al., "Quantum optimization with arbitrary connectivity using Rydberg atom arrays", [arXiv:2209.03965](https://arxiv.org/abs/2209.03965) / PRX Quantum 2023.
- Andrist et al., "Hardness of the maximum-independent-set problem on unit-disk graphs and prospects for quantum speedups", [arXiv:2307.09442](https://arxiv.org/abs/2307.09442) / Physical Review Research 2023.
- Farouk et al., "Generation of quantum phases of matter and finding a maximum-weight independent set of unit-disk graphs using Rydberg atoms", [arXiv:2405.09803](https://arxiv.org/abs/2405.09803).
- Silverio et al., "Pulser: An open-source package for the design of pulse sequences in programmable neutral-atom arrays", [arXiv:2104.15044](https://arxiv.org/abs/2104.15044).
- Wurtz et al., "Aquila: QuEra's 256-qubit neutral-atom quantum computer", [arXiv:2306.11727](https://arxiv.org/abs/2306.11727).
