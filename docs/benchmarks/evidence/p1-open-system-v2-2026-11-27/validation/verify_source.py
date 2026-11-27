"""Check source/runtime/package identity across all retained manifest outputs."""
import hashlib
import json
from pathlib import Path
root=Path('/tmp/open-system-v2-final-2026-11-27')
repo=Path('/home/oyxw/Sagittarius')
campaign=json.loads((root/'campaign.json').read_text())
rows=json.loads((root/'open_system_performance.json').read_text())['timings']
for name,digest in campaign['source_sha256'].items():
    assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==digest,name
signature=campaign['source']['build']['source']
packages=campaign['source']['python']['packages']
runtime=set(); versions=set(); count=0
for row in rows:
    state=row['metrics']['state']
    if row['status']=='skipped': continue
    runtime.add(tuple(sorted(state['runtime_files'].items())))
    for provider in state['runtime_context']['python_blas']['providers']:
        assert provider['effective_threads']==1,provider
    links=[r['artifacts']['run_manifest'] for r in state['records'] if r['artifacts'].get('run_manifest')]
    if state.get('sensitivity'): links.append(state['sensitivity']['run_manifest'])
    for link in links:
        data=json.loads(Path(link).read_text())
        assert data['versions']['build']['source']==signature,link
        assert data['versions']['python']['packages']==packages,link
        versions.add(data['versions']['julia_version']);count+=1
assert len(runtime)==1,runtime
assert len(versions)==1,versions
print(json.dumps({'source_identity_passed':True,'frozen_source_files':len(campaign['source_sha256']),
    'checked_manifests':count,'runtime_project_manifest_identities':len(runtime),'julia_versions':sorted(versions),
    'git_source':signature,'python_packages':packages},indent=2,sort_keys=True))
