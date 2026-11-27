# Main/dev merge integration — 2026-11-27

Status: Conflict resolution and local verification complete; merge commit pending
Merge policy: Retain as development record; formal behavior belongs in specs.

## Baseline and authorization

- Target: `main`, `78b5f5eb3a19d1283905aaba71639d0a10557041`.
- Incoming: `dev`, `ff7cf441a70b6332ba9b64272cb2a20f3fdad87a`.
- Existing merge: 25 unmerged paths, 595 other staged paths, no separate
  unstaged changes. The user authorized resolution following the conflict review.
- Preserve the pending merge and existing staged work. Do not publish, push,
  change release tags, or rebuild historical evidence. No commit is created by
  this resolution session.

## Scope and acceptance

Integrate Phase 15/16/19 work with the 1.0.11 release baseline. Retain main's
package versions, subpackage discovery, CUDA module cache and explicit-module
solve entry. Retain dev's single-host-transfer diagonal observables, MWIS exact
batch helper, sweep artifact visualization, recipes, benchmarks and tests.
Keep canonical and embedded Julia sources identical. No physics definitions,
schema versions, solver options or published artifact identities change.

Restore development/reference/governance dependencies required by the incoming
docs and restore the existing MWIS batch regression tests. Retain branch records
and historical release handoffs as development history, separate from public
user navigation and package contents. Retain every incoming benchmark evidence
file unchanged; its source/runtime hashes describe the historical campaign,
not this merged tree or a new release candidate.

Acceptance: no unmerged index entries or conflict markers; documentation
validation passes; affected Python/MWIS/sweep and backend regressions pass;
fresh-process real CUDA parity passes with initialized diagnostics; historical
evidence is unchanged. Clean-wheel, cross-platform, TestPyPI, production and
recurring benchmark release gates remain separate.

## Resolution and validation

- Kept 21 delete/modify files from dev and restored 11 document/test dependencies.
- Kept main's GPU solve entry and changed dev's diagonal CUDA-vector check to
  `_is_cuda_vector`, preserving one transfer per diagonal expectation and the
  original accumulation order (composite observables call multiple expectations).
- Adopted the sweep artifact contract and wheel recipe installation link.
- Marked source documentation as unreleased beyond the published 1.0.11 package.
- Normalized whitespace in the restored workflow template and the incoming
  documentation validator/test; historical evidence files were not reformatted.
- Document validator: passed after restoration (34 missing links resolved).
- Initial targeted MWIS/sweep/docs tests: 64 passed, 2 backend-dependent skips.

| Validation | Result |
| :--- | :--- |
| `python3 scripts/validate_documentation.py` | Passed. |
| `uv run --no-sync python -m pytest tests -q` in the CPU environment | 761 passed, 10 skipped, 13 packaging-fixture setup errors. All 13 errors share the sandbox network denial while fetching `setuptools>=61.0`; original failures retained. |
| `uv run --no-sync python -m pytest tests/test_packaging_artifacts.py -q -rs` outside the sandbox | 14 passed, 4 opt-in release smokes skipped. Covers every initial setup error; metadata, embedded backend/subpackages, forbidden contents, candidate manifest and twine checks passed. |
| Fresh-process `tests/test_gpu_acceleration.py::test_gpu_diagonal_observables_match_cpu_at_shared_times` | 1 passed, no skips. |
| `tests/test_gpu_acceleration.py tests/test_cross_language_golden.py` on real CUDA hardware | 8 passed, no skips. |
| Final per-test reconciliation across the full run and targeted reruns | 774 passed, 10 conditional skips across 784 distinct tests; no unresolved error/failure. This combines separate CPU, packaging and GPU contexts, not a single all-pass full-suite invocation. |
| Source/embedded solver comparison and conflict-marker/index scan | Identical solver copies; no conflict markers or unmerged entries. |
| Historical benchmark evidence verification | All 474 incoming files, 666269296 bytes, match their original Git blob hashes. |
| Main release metadata/lock comparison | Python, canonical/embedded Julia versions, package discovery and `uv.lock` retained from main. |
| `git diff --cached --check -- . ':!docs/benchmarks/evidence/**'` | Passed. Raw archived CSV/log whitespace is retained unchanged. |

Validation used Python 3.11.15 and the existing Julia 1.13.4 CPU/CUDA projects
under `sagittarius_py/.venv/`, with Julia/BLAS/OpenMP/MKL thread counts set to one.
CUDA opt-in was explicit (`SAGITTARIUS_ENABLE_GPU_TESTS=1`); host diagnostics
identified an RTX 5070 Ti, driver 610.88 and 16303 MiB device memory. A separate
writable Julia depot and uv cache under `/tmp` kept tracked dependency locks
unchanged. Test logs/JUnit XML, source/runtime hashes, original index backup,
evidence verification and per-test reconciliation are retained locally under
`/tmp/sagittarius-merge-78b5f5e-ff7cf44/`. This temporary directory is a local
handoff aid, not a durable release-evidence artifact.

The resolved files are staged; `HEAD` and `MERGE_HEAD` retain the baseline
identities above. Creating the merge commit and any push remain separate steps.

## Limits

Software and bounded CPU/CUDA numerical verification do not establish scientific
validation, performance improvements, release readiness or cross-platform
support. CUDA remains experimental. The restored 1.0.11 release records do not
validate these new sources or authorize publication.
