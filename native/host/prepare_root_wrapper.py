#!/usr/bin/env python3
"""Wrap the reviewed local root filesystem in a disposable PARTUUID disk; never edit it."""
from pathlib import Path
import argparse,hashlib,json,os,struct,sys
SOURCE_SHA='aa2e052b7ce1770e8d38ad3191a067bd6185e91b6ed09ccb72a628fe27f5bdab';SIZE=4*1024**3;START=1024**2
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-filesystem',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:
  src=a.root_filesystem.resolve();out=a.output.resolve()
  if src==out or out.exists()or out.with_suffix('.json').exists()or src.stat().st_size!=SIZE:raise ValueError('A matching4GiB source and fresh distinct output are required')
  h=hashlib.sha256()
  with src.open('rb')as f:
   for b in iter(lambda:f.read(16*1024*1024),b''):h.update(b)
  if h.hexdigest()!=SOURCE_SHA:raise ValueError('Root filesystem differs from the reviewed native profile')
  out.parent.mkdir(parents=True,exist_ok=True);mbr=bytearray(512);struct.pack_into('<I',mbr,440,0x4f344d47);mbr[446:462]=struct.pack('<B3sB3sII',0,b'\xfe\xff\xff',0x83,b'\xfe\xff\xff',START//512,SIZE//512);mbr[510:512]=b'\x55\xaa';readback=hashlib.sha256()
  with out.open('xb')as target,src.open('rb')as f:
   target.truncate(8*1024**3);target.write(mbr);target.seek(START)
   for b in iter(lambda:f.read(16*1024*1024),b''):target.write(b)
   target.flush();os.fsync(target.fileno())
  with out.open('rb')as f:
   f.seek(START);left=SIZE
   while left:
    b=f.read(min(left,16*1024*1024));assert b;readback.update(b);left-=len(b)
  if readback.hexdigest()!=SOURCE_SHA:raise ValueError('Root payload readback differs')
  out.chmod(0o444);m={'schema':'kombikraft-native-root-wrapper-v1','wrapperFile':out.name,'wrapperBytes':out.stat().st_size,'wrapperMtimeNs':out.stat().st_mtime_ns,'partitionStartBytes':START,'partitionBytes':SIZE,'partitionPayloadSha256':SOURCE_SHA,'mbrSha256':hashlib.sha256(mbr).hexdigest(),'partUuid':'4f344d47-01','sourceModified':False,'snapshotRequired':True,'installationAllowed':False};out.with_suffix('.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({'passed':True,'metadata':str(out.with_suffix('.json')),'sourceModified':False,'installationAllowed':False}));return 0
 except(OSError,ValueError)as exc:print('Root wrapper denied: '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
