#!/usr/bin/env python3
"""Structural/hash admission for local input manifests; not firmware compatibility."""
from pathlib import Path
import argparse,copy,hashlib,json,re


def zeros_hash(size):
    digest=hashlib.sha256();chunk=bytes(65536)
    while size:digest.update(chunk[:min(size,len(chunk))]);size-=min(size,len(chunk))
    return digest.hexdigest()


def validate(layout,root):
    root=Path(root).resolve();result=copy.deepcopy(layout);regions=result.get('regions');intervals=[]
    if not isinstance(regions,list)or not 1<=len(regions)<=32:raise ValueError('Expected1..32 regions')
    for row in regions:
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',row.get('name','')):raise ValueError('Invalid region name')
        size=row.get('bytes');readonly=row.get('readonly');address=int(row['address'],0)
        if type(size)is not int or not 0<size<=0x1000000:raise ValueError('Invalid region size')
        if type(readonly)is not bool or not 0<=address<2**64 or address+size>2**64:raise ValueError('Invalid bounds/permissions')
        if not re.fullmatch(r'[a-f0-9]{64}',row.get('sha256','')):raise ValueError('Invalid SHA256')
        for start,end in intervals:
            if address<end and start<address+size:raise ValueError('Overlapping regions')
        intervals.append((address,address+size))
        if 'file'in row:
            relative=Path(row['file'])
            if relative.is_absolute():raise ValueError('Input file paths must be relative to the supplied root')
            path=(root/relative).resolve()
            try:path.relative_to(root)
            except ValueError:raise ValueError('Input file escapes root')
            if path.stat().st_size!=size:raise ValueError('Input size mismatch')
            actual=hashlib.sha256(path.read_bytes()).hexdigest();row['file']=str(path)
        else:actual=zeros_hash(size)
        if actual!=row['sha256']:raise ValueError('Input hash mismatch')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--source-root',type=Path,required=True);p.add_argument('--emit-resolved',type=Path)
    a=p.parse_args();resolved=validate(json.loads(a.manifest.read_text()),a.source_root)
    if a.emit_resolved:
        with a.emit_resolved.open('x')as stream:stream.write(json.dumps(resolved,indent=2)+'\n')
    print(json.dumps({'result':'PASS','regions':len(resolved['regions']),
                      'sourceCompatibilityProved':False,'guestStarted':False}))


if __name__=='__main__':main()
