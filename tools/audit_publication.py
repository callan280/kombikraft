#!/usr/bin/env python3
"""Read back the expanded public tree; report exact files and publication limits."""
from pathlib import Path
import argparse,hashlib,json,re,tarfile

ROOT=Path(__file__).resolve().parents[1]
SKIP={'.git','.venv','__pycache__','build','dist','private','local'}
TEXT={'.py','.js','.json','.html','.css','.md','.txt','.toml','.yml','.yaml','.c','.h','.inc','.sh','.patch','.xml','.svg','.cjs','.tsv'}
MACHINE=re.compile(rb'/(?:Users|Volumes|var/folders)/[A-Za-z0-9_.@-][A-Za-z0-9_.@ -]{0,127}/',re.I)
SECRET=re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9_]{20,}|\bsk-[A-Za-z0-9_-]{24,}')
VIN=re.compile(rb'\bWB[ASY][A-HJ-NPR-Z0-9]{14}\b')
SYNTHETIC_VINS={b'WBA12345678901234',b'WBA00000000000000'}
sha=lambda b:hashlib.sha256(b).hexdigest()


def known_inputs():
    admitted={}
    manifest=ROOT/'assets/viewer-pack/manifest.json'
    for row in json.loads(manifest.read_text())['entries']:
        admitted['assets/viewer-pack/'+row['file']]=row['sha256']
    library=json.loads((ROOT/'assets/library/export-receipt.json').read_text())
    for file,row in library['objects'].items():admitted['assets/library/'+file]=row['sha256']
    for file,row in library['detailShards'].items():admitted['assets/library/details/'+file]=row['sha256']
    admitted['assets/library/catalog.js']=library['catalogSha256']
    for profile in ('v12','v13'):
        native=ROOT/'native/data'/profile/'manifest.json'
        if native.exists():
            for row in json.loads(native.read_text())['files']:
                admitted['native/data/'+profile+'/'+row['file']]=row['sha256']
    return admitted


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);args=p.parse_args()
    admitted=known_inputs();files=[];failures=[];seen=set()
    for file in sorted(ROOT.rglob('*')):
        rel=file.relative_to(ROOT)
        if any(part in SKIP or part.endswith('.egg-info')for part in rel.parts):continue
        if file.is_dir():continue
        name=rel.as_posix()
        if name=='publication-manifest.json':continue
        if file.is_symlink():failures.append((name,'symlink'));continue
        data=file.read_bytes();digest=sha(data)
        if name in admitted:
            seen.add(name)
            if digest!=admitted[name]:failures.append((name,'admitted input hash changed'))
        if len(data)>50*1024*1024:failures.append((name,'blob exceeds50MiB review limit'))
        if MACHINE.search(data):failures.append((name,'machine/account path marker'))
        if SECRET.search(data):failures.append((name,'credential marker'))
        if any(m[0]not in SYNTHETIC_VINS for m in VIN.finditer(data)):failures.append((name,'non-fixture vehicle identifier'))
        if data.startswith((b'\x7fELF',b'\xcf\xfa\xed\xfe',b'QFI\xfb',b'MZ')):failures.append((name,'executable/disk image'))
        if file.suffix in ('.img','.qcow2','.ramscene','.ramres','.ncd','.pem','.key'):
            failures.append((name,'unreviewed runtime/vehicle payload extension'))
        is_text=file.suffix in TEXT or file.name.startswith(('LICENSE','NOTICE','COPYING')) or file.name in ('.gitignore','.gitattributes')
        if is_text:
            try:data.decode('utf-8')
            except UnicodeError:failures.append((name,'invalid text encoding'))
        elif name not in admitted:
            if file.suffix=='.tgz' and name.startswith('mgu/packages/'):
                with tarfile.open(file,'r:gz') as archive:
                    for item in archive:
                        if item.issym()or item.islnk()or item.name.startswith('/')or '..'in Path(item.name).parts:
                            failures.append((name,'unconfined app archive member'))
                        if item.isfile():
                            payload=archive.extractfile(item).read()
                            if MACHINE.search(payload)or SECRET.search(payload):failures.append((name,'private archive content'))
                            if '/oap-sdk/'in '/'+item.name or item.name.endswith('oap-sdk.js'):
                                failures.append((name,'captured SDK bundled'))
            else:failures.append((name,'unclassified binary input'))
        files.append({'file':name,'bytes':len(data),'sha256':digest})
    for name in admitted.keys()-seen:failures.append((name,'manifest file missing'))
    assert not failures,json.dumps(failures[:30])
    result={'schema':'kombikraft-expanded-publication-v1','passed':True,'fileCount':len(files),
        'bytes':sum(f['bytes']for f in files),'manifestAdmittedInputs':len(admitted),
        'visualResourcesSeparatelyAttributed':True,'fullFirmwareOrRuntimeImagesIncluded':False,
        'vehicleValidatedRelease':False,'files':files,
        'scope':'Exact declared visual-input hashes, source/private-marker checks and SDK-free package inspection; not image OCR or a general legal/secret guarantee.'}
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='files'}))


if __name__=='__main__':main()
