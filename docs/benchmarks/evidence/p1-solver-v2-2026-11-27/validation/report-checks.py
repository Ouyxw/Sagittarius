from pathlib import Path
import hashlib
import json
import math
import subprocess
root=Path('/home/oyxw/Sagittarius')
output=root/'sagittarius_py/benchmark-output/p1-solver-v2-2026-11-27'
evidence=root/'docs/benchmarks/evidence/p1-solver-v2-2026-11-27'
campaign=json.loads((output/'campaign.json').read_text())
rows=json.loads((output/'solver_sensitivity_suite.json').read_text())['rows']
checks={'frozen_files_match_current':{name:hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in campaign['source_sha256'].items()}}
assert all(checks['frozen_files_match_current'].values())
runtime_sets={json.dumps(r['metrics']['state']['runtime_files'],sort_keys=True) for r in rows}
assert len(runtime_sets)==1
checks['runtime_identity_count']=len(runtime_sets)
checks['maximum_reference_stability_error']=max(r['metrics']['state']['reference']['stability_error'] for r in rows)
checks['peak_worker_bytes']={r['scenario_id']:r['peak_bytes'] for r in rows}
checks['timing_phases_present']=True
for row in rows:
 state=row['metrics']['state']
 assert set(state['timing'])=={'initialized_doctor_seconds','setup_basis_seconds','reference_seconds'}
 assert all(math.isfinite(v) and v>=0 for v in state['timing'].values())
 for record in state['records']:
  assert all(math.isfinite(record[k]) and record[k]>=0 for k in ('runtime_seconds','serialization_seconds','validation_seconds'))
  assert record['output_sample_count']==row['output_count']
 for provider in state['runtime_context']['python_blas']['providers']:
  assert provider['effective_threads']==1
 assert state['memory']['peak_bytes']>0 and state['memory_baseline']['rss_bytes']>0
checks['summary']={'configurations':len(rows),'total_records':sum(len(r['metrics']['state']['records']) for r in rows),'eligible_measured':sum(r['eligible'] for r in rows)}
checks['v1_preserved']={}
for name in ('protocol','tiers','families','artifact-contracts'):
 path=f'docs/benchmarks/{name}.md'
 before=subprocess.check_output(['git','show',f'781a09e:{path}'],cwd=root,text=True)
 after=(root/path).read_text()
 def chapter(t):return t.split('## Benchmarking V1',1)[1].split('## Benchmarking V2',1)[0]
 checks['v1_preserved'][name]=chapter(before)==chapter(after)
assert all(checks['v1_preserved'].values())
(evidence/'validation/report-checks.json').write_text(json.dumps(checks,indent=2,sort_keys=True)+'\n')
print(checks['summary'])
