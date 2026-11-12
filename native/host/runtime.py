"""Strict local dependency import for the reviewed offline native profile."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from build import digest
KERNEL_SHA='6a0ffde4cde7c91b4e5ead26e9a0747964b94c37d1263638248fe61f8b78273a'
def load(manifest):
 manifest=manifest.resolve();m=json.loads(manifest.read_text())
 if m.get('schema')!='kombikraft-native-runtime-import-v1':raise ValueError('Unsupported runtime import')
 result={}
 for role in ['kernel','qemu','glHost']:
  row=m['files'][role]
  if set(row)!={'file','sha256'}:raise ValueError('Malformed local dependency '+role)
  p=Path(row['file']);p=(p if p.is_absolute()else manifest.parent/p).resolve()
  if not p.is_file()or digest(p)!=row['sha256']:raise ValueError('Local dependency hash mismatch: '+role)
  if role=='kernel'and row['sha256']!=KERNEL_SHA:raise ValueError('The clock adapter requires the exact reviewed kernel capture')
  result[role]=p
 share=m['qemuShare'];root=Path(share['directory']);root=(root if root.is_absolute()else manifest.parent/root).resolve()
 if not share['sha256']:raise ValueError('Pin the local QEMU share directory files')
 for name,want in share['sha256'].items():
  p=(root/name).resolve()
  if Path(name).is_absolute()or not p.is_relative_to(root)or not p.is_file()or digest(p)!=want:raise ValueError('QEMU share file mismatch: '+name)
 result['qemuShare']=root;return result

def wrapper(metadata):
 m=json.loads(metadata.read_text())
 if not isinstance(m.get('wrapperFile'),str)or Path(m['wrapperFile']).name!=m['wrapperFile']:raise ValueError('Wrapper filename must stay beside its metadata')
 disk=(metadata.parent/m['wrapperFile']).resolve()
 if m.get('schema')!='kombikraft-native-root-wrapper-v1'or m.get('partUuid')!='4f344d47-01'or m.get('partitionPayloadSha256')!='aa2e052b7ce1770e8d38ad3191a067bd6185e91b6ed09ccb72a628fe27f5bdab'or m.get('partitionStartBytes')!=1048576 or m.get('partitionBytes')!=4294967296:raise ValueError('Wrong local wrapper profile')
 if disk.stat().st_size!=m['wrapperBytes']or disk.stat().st_mtime_ns!=m['wrapperMtimeNs']or disk.stat().st_mode&0o222:raise ValueError('Local immutable wrapper identity changed')
 with disk.open('rb')as f:
  if hashlib.sha256(f.read(512)).hexdigest()!=m['mbrSha256']:raise ValueError('Wrapper MBR changed')
 return disk
