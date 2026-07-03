# Shared Result Schema

Spec ID: `SPEC-DATA-001`
Status: `Current`
Roadmap: Phase 8
Version: `shared-result/v1`
Last reviewed: 2026-07-03


Sagittarius shared simulation outputs use `shared-result/v1` as the language-neutral result payload. The Python `result-artifact/v1` envelope now embeds this payload in `shared_result` while preserving legacy `data`, `metadata`, `diagnostics`, and `manifest` fields.

## Required Fields

| Field | Meaning |
| :--- | :--- |
| `schema_version` | Must be `shared-result/v1`. |
| `artifact_type` | Must be `sagittarius.shared_result`. |
| `result_type` | Logical result kind, for example `observables`, `mcwf_observables`, or `series`. |
| `series` | JSON object mapping series names to numeric/list data. Phase 15 readout-capable results may also include `final_bitstring_probabilities`, a JSON object mapping bitstring labels to probabilities. |
| `time_key` | Series key containing time samples, usually `t`, or `null` for timeless results. |
| `observable_names` | Ordered list of observable series names contained in `series`. |
| `basis_size` | Basis size used by the initial state when available, otherwise `null`. |
| `manifest_schema` | Linked run manifest schema version when available. |

## Compatibility

`SimulationResult.to_shared_result()` produces and validates this payload. `SimulationResult.save()` writes both the shared payload and the existing compatibility envelope fields. `load_result()` validates `shared_result` when present and still accepts older `result-artifact/v1` files without it, plus legacy raw result dictionaries.

Final-state readout distributions are compatibility series, not observable trajectories: they are present under `series.final_bitstring_probabilities` when available, while `observable_names` continues to list only named observable time series. The corresponding run manifest `readout` section records full versus reduced basis mode, represented bitstrings, whether forbidden reduced-basis bitstrings were excluded, and whether `SimulationResult.sample(shots, seed=...)` is supported.

Julia-native workflows should emit the same `shared-result/v1` shape when serializing solver outputs so Python and Julia artifacts can be consumed by the same downstream tools.
