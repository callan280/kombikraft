#!/usr/bin/env python3
"""Export a verified viewer pack, sanitizing provenance but preserving visual bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO/'src'))
from kombikraft.assets import AssetPack

PRIVATE_PATH = re.compile(r'/(?:Users|Volumes|var/folders)/[^\s"<>]+')
VIN = re.compile(r'\bWB[ASY][A-HJ-NPR-Z0-9]{14}\b')


def sanitize(value):
    if isinstance(value, dict):
        result={}
        for key,item in value.items():
            clean=sanitize(key);candidate=clean;ordinal=1
            while candidate in result:
                ordinal+=1;candidate=clean+'#'+str(ordinal)
            result[candidate]=sanitize(item)
        return result
    if isinstance(value, list):return [sanitize(v)for v in value]
    if isinstance(value, str):
        value=PRIVATE_PATH.sub(lambda m:'source/'+Path(m.group()).name,value)
        return VIN.sub('[vehicle-identifier-redacted]',value)
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    pack=AssetPack(args.source)
    assert pack.status()['layoutAvailable'],'Source viewer pack is incomplete'
    assert not args.destination.exists(),'Refusing to overwrite a published asset pack'
    output=[];provenance=[]
    for route,entry in sorted(pack.entries.items()):
        data=pack.read(route);original=hashlib.sha256(data).hexdigest()
        if Path(entry.file).suffix=='.json':
            data=(json.dumps(sanitize(json.loads(data)),ensure_ascii=False,separators=(',',':'))+'\n').encode()
        elif Path(entry.file).suffix=='.js':
            text=data.decode();clean=sanitize(text);assert clean==text,'Executable source needs separate privacy review'
        assert Path(entry.file).suffix in ('.json','.js','.png','.pixels','.ttf')
        target=args.destination/entry.file
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        digest=hashlib.sha256(data).hexdigest();assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
        output.append({'route':route,'file':entry.file,'sha256':digest})
        provenance.append({'route':route,'sourceSha256':original,'publishedSha256':digest,
                           'metadataSanitized':original!=digest})
    (args.destination/'manifest.json').write_text(json.dumps({'schema':'kombikraft-local-assets-v1','entries':output},indent=2)+'\n')
    (args.destination/'provenance.json').write_text(json.dumps({'schema':'kombikraft-published-visual-pack-v1',
        'permissionBasis':'Maintainer confirmed redistribution permission; original rights retained.',
        'license':'See ../../ASSET-NOTICE.md; the project MIT grant does not cover these visual resources.',
        'firmwareImagesIncluded':False,'vehicleTested':False,'entries':provenance},indent=2)+'\n')
    checked=AssetPack(args.destination);assert checked.status()['layoutAvailable']
    print(json.dumps(checked.status(),indent=2))


if __name__=='__main__':main()
