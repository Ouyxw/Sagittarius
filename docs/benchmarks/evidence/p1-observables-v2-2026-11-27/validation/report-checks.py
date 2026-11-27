"""Additional source, phase, storage, order and environment checks; run from repo root."""
from pathlib import Path
import hashlib,json,math,subprocess
root=Path.cwd()
original=root/'sagittarius_py/benchmark-output/p1-observables-v2-2026-11-27'
evidence=root/'docs/benchmarks/evidence/p1-observables-v2-2026-11-27'
campaign=json.loads((original/'campaign.json').read_text())
rows=json.loads((original/'observable_performance_suite.json').read_text())['rows']
checks={'source_files':{name:hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in campaign['source_sha256'].items()}}
assert all(checks['source_files'].values())
identities={json.dumps(row['metrics']['state']['runtime_files'],sort_keys=True) for row in rows}
assert len(identities)==1
checks['runtime_dependency_identity_count']=len(identities)
checks['costs']=sum(r['kind']=='performance' for r in rows)
checks['correctness_fixtures']=sum(r['kind']=='correctness' for r in rows)
checks['records']=sum(len(r['metrics']['state']['records']) for r in rows)
checks['measured_eligible']=sum(r['eligible'] or 0 for r in rows)
assert (checks['costs'],checks['correctness_fixtures'],checks['records'],checks['measured_eligible'])==(52,12,476,260)
checks['empty_histories']=sum(bool(r['metrics']['state'].get('empty_observables',{}).get('arrays')) for r in rows)
assert checks['empty_histories']==2
checks['worker_peak_bytes']={r['scenario_id']:r['peak_bytes'] for r in rows}
for r in rows:
 assert r['status']=='passed' and r['value_gate'] and r['order_gate']
 st=r['metrics']['state']
 assert set(st['timing'])=={'initialized_doctor_seconds','setup_basis_seconds','reference_seconds'}
 assert all(math.isfinite(v) and v>=0 for v in st['timing'].values())
 for provider in st['runtime_context']['python_blas']['providers']:assert provider['effective_threads']==1
 for record in st['records']:
  assert all(math.isfinite(record[k]) and record[k]>=0 for k in ('runtime_seconds','serialization_seconds','validation_seconds'))
 if r['kind']=='correctness':assert r['metrics']['statistics'] is None
checks['v1_preserved']={}
for name in ('protocol','tiers','families','artifact-contracts'):
 path=f'docs/benchmarks/{name}.md';before=subprocess.check_output(['git','show',f'bb8725f:{path}'],text=True);after=(root/path).read_text()
 def chapter(t):return t.split('## Benchmarking V1',1)[1].split('## Benchmarking V2',1)[0]
 checks['v1_preserved'][name]=chapter(before)==chapter(after)
assert all(checks['v1_preserved'].values())
(evidence/'validation/report-checks.json').write_text(json.dumps(checks,indent=2,sort_keys=True)+'\n')
print({k:checks[k] for k in ('costs','correctness_fixtures','records','measured_eligible','empty_histories')})
