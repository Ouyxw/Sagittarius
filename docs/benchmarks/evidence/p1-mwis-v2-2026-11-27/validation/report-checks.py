"""Additional report-field and phase/memory checks for this retained campaign."""
import json
import math
from pathlib import Path
import sys

root = Path(sys.argv[1])
artifact = json.loads((root / 'mwis_aqc_performance.json').read_text())
rows = artifact['timings']
maximum_norm = maximum_error = 0.
measured = {'aqc': 0, 'ilp': 0}
runtime_hashes = set()
cbc_hashes = set()
proven_ilp_calls = 0
for row in rows:
    problem, metrics = row['problem'], row['metrics']
    for key in ('N', 'basis_size', 'average_degree', 'edge_density'):
        assert row[key] == problem[key], (row['scenario_id'], key)
    n, edges = problem['N'], problem['edges']
    assert row['average_degree'] == 2 * len(edges) / n
    assert row['edge_density'] == (2 * len(edges) / (n * (n - 1)) if n > 1 else 0.)
    assert row['raw_records'] == f"[paths]({row['scenario_id']}/paths.json)"
    errors = []
    for path, evidence in metrics['paths'].items():
        state = evidence['state']
        if path == 'aqc' and state.get('runtime_files'):
            runtime_hashes.add(tuple(sorted(state['runtime_files'].items())))
        if path == 'ilp' and state.get('solver'):
            cbc_hashes.add(state['solver']['binary_sha256'])
        for record in state.get('records', []):
            for key in ('runtime_seconds', 'model_construction_seconds', 'postprocessing_seconds', 'serialization_seconds'):
                if key in record:
                    assert math.isfinite(record[key]) and record[key] >= 0
            if record['phase'] == 'measured' and record['eligible']:
                measured[path] += 1
            if path == 'ilp' and record.get('reference', {}).get('proven_optimal'):
                proven_ilp_calls += 1
            gate = record.get('gate') or {}
            if gate.get('numerical_max_abs_error') is not None:
                errors.append(gate['numerical_max_abs_error'])
            if gate.get('raw_state_norm_error') is not None:
                maximum_norm = max(maximum_norm, gate['raw_state_norm_error'])
        if row['status'] == 'passed':
            assert state['memory']['source_unit'] == 'kB (1024 bytes)'
            assert state['memory']['peak_bytes'] > 0
            assert state['memory_baseline']['rss_bytes'] > 0
            assert evidence['supervision']['sampled_peak_bytes'] > 0
            if path == 'aqc':
                for key in ('initialization_seconds', 'setup_seconds', 'reference_seconds'):
                    assert math.isfinite(state[key]) and state[key] >= 0
            else:
                assert state['solver']['threads'] == 1 and state['solver']['warm_start'] is False
                assert len(state['solver']['binary_sha256']) == 64
    assert row['numerical_max_abs_error'] == (max(errors) if errors else None)
    maximum_error = max(maximum_error, max(errors) if errors else 0.)
assert len(runtime_hashes) <= 1 and len(cbc_hashes) <= 1
print(json.dumps({'proven_ilp_calls': proven_ilp_calls, 'runtime_identity_count': len(runtime_hashes), 'cbc_binary_identity_count': len(cbc_hashes), 'all_report_fields_verified': True, 'scenario_count': len(rows),
                  'eligible_measured_calls': measured, 'maximum_numerical_error': maximum_error,
                  'maximum_raw_state_norm_error': maximum_norm}, indent=2))
