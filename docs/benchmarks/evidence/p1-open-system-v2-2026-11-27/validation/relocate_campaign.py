"""Reassemble, verify, relocate and accept evidence with the original tree hidden."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

repo=Path('/home/oyxw/Sagittarius')
evidence=repo/'docs/benchmarks/evidence/p1-open-system-v2-2026-11-27'
original=Path('/tmp/open-system-v2-final-2026-11-27')
identity_path=evidence/'archive-identity.json'
assembled=Path('/tmp/open-system-reassembled-2026-11-27.tar.xz')
if identity_path.exists():
    identity=json.loads(identity_path.read_text())
    total=hashlib.sha256();size=0
    with assembled.open('xb') as output:
        for part in identity['parts']:
            h=hashlib.sha256();part_size=0
            with (evidence/part['filename']).open('rb') as stream:
                while block:=stream.read(1024*1024):
                    h.update(block);total.update(block);size+=len(block);part_size+=len(block);output.write(block)
            assert h.hexdigest()==part['sha256'] and part_size==part['size_bytes'],part
    assert total.hexdigest()==identity['sha256'] and size==identity['size_bytes']
    archive=assembled;archive_hash=total.hexdigest()
else:
    archive=evidence/'campaign.tar.xz'
    with archive.open('rb') as stream:
        h=hashlib.file_digest(stream,'sha256')
    archive_hash=h.hexdigest()
relocation=Path('/tmp/open-system-relocated-2026-11-27')
relocation.mkdir(exist_ok=False)
subprocess.run(['tar','-xJf',str(archive),'-C',str(relocation)],check=True)
relocated=relocation/original.name
with Path('/tmp/open-system-internal-checksums.log').open('w') as log:
    subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=relocated,stdout=log,stderr=subprocess.STDOUT,check=True)
hidden=Path('/tmp/open-system-original-hidden-2026-11-27')
if hidden.exists():raise FileExistsError(hidden)
original.rename(hidden)
try:
    env={**os.environ,'UV_CACHE_DIR':'/tmp/sagittarius-open-uv','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    with Path('/tmp/open-system-relocated-acceptance.log').open('w') as log:
        subprocess.run(['uv','run','python','../scripts/accept_open_system_campaign.py',str(relocated)],cwd=repo/'sagittarius_py',env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
finally:
    hidden.rename(original)
old=json.loads((original/'acceptance.json').read_text());new=json.loads((relocated/'acceptance.json').read_text())
assert old['accepted'] and new['accepted']
assert old==new,'Original and relocated reports differ'
report={'relocated_acceptance_passed':True,'full_reports_identical':True,'original_tree_hidden_during_audit':True,
    'internal_checksum_count':len((relocated/'SHA256SUMS').read_text().splitlines()),'archive_sha256':archive_hash}
Path('/tmp/open-system-relocation-comparison.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2,sort_keys=True))
