"""Retain complete frozen measurements; run only after the accepted original audit."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

repo=Path('/home/oyxw/Sagittarius')
raw=Path('/tmp/open-system-v2-final-2026-11-27')
evidence=repo/'docs/benchmarks/evidence/p1-open-system-v2-2026-11-27'
report=json.loads((raw/'audit.json').read_text())
assert report['bounded_campaign_accepted'],report
acceptance=json.loads((raw/'acceptance.json').read_text())
assert acceptance['accepted'],acceptance
for name,digest_value in acceptance['review_source_sha256'].items():
    source=repo/name
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest_value,name
    target=raw/'review-source'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
(raw/'review-source-index.json').write_text(json.dumps(acceptance['review_source_sha256'],indent=2,sort_keys=True)+'\n')
(evidence/'source-index.json').write_text(json.dumps(json.loads((raw/'campaign.json').read_text())['source_sha256'],indent=2,sort_keys=True)+'\n')
for path in raw.iterdir():
    if path.is_file() and (path.name in ('campaign.json','coverage.json','convergence.json','audit.json','acceptance.json','lindblad_mcwf.json','review-source-index.json','open_system_repeats.json') or path.name.startswith('open_system_performance')):
        shutil.copyfile(path,evidence/path.name)
shutil.copyfile('/tmp/open-system-v2-final.log',evidence/'validation/campaign.log')
shutil.copytree(evidence/'validation',raw/'validation')
# Incremental file hashing avoids retaining large JSON files in the packer.
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while data:=stream.read(1024*1024): h.update(data)
    return h.hexdigest()
files=sorted(p for p in raw.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(raw/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(raw)}\n' for p in files))
print('internal files',len(files),flush=True)
env={**os.environ,'XZ_OPT':'-T1 -9'}
subprocess.run(['tar','-cJf',str(evidence/'campaign.tar.xz'),'-C',str(raw.parent),raw.name],env=env,check=True)
subprocess.run(['tar','-cJf',str(evidence/'pilots.tar.xz'),'-C','/tmp',*[f'open-system-pilot-{i:02d}' for i in range(1,6)]],env=env,check=True)
archive=evidence/'campaign.tar.xz'
if archive.stat().st_size > 95*1024**2:
    whole_name='open-system-v2-2026-11-27-campaign.tar.xz'
    relocated_archive=Path('/tmp')/whole_name
    if relocated_archive.exists(): raise FileExistsError(relocated_archive)
    identity={'assembled_filename':whole_name,'sha256':digest(archive),'size_bytes':archive.stat().st_size,'parts':[]}
    with archive.open('rb') as stream:
        index=0
        while block:=stream.read(90*1024**2):
            part=evidence/f'campaign.tar.xz.part-{index:02d}'
            part.write_bytes(block)
            identity['parts'].append({'filename':part.name,'sha256':hashlib.sha256(block).hexdigest(),'size_bytes':len(block)})
            index+=1
    shutil.move(archive,relocated_archive)
    (evidence/'archive-identity.json').write_text(json.dumps(identity,indent=2,sort_keys=True)+'\n')
print('retained compressed bytes',{p.name:p.stat().st_size for p in evidence.glob('*.xz*')},flush=True)
