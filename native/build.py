#!/usr/bin/env python3
"""Build the reviewed native source profile; no firmware acquisition or VM launch."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent
RAMSES19_SHA='1e87e852dde8b70aa86f3c928bd482454e83e6824a7f27ab7496c515a6726479'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def confined(root,name):
 if not isinstance(name,str)or not name or Path(name).is_absolute():raise ValueError('Expected relative input path')
 p=(root/name).resolve()
 if not p.is_relative_to(root.resolve())or not p.is_file():raise ValueError('Input path escapes its pack or is absent: '+name)
 return p
def validate_data(root):
 m=json.loads((root/'manifest.json').read_text())
 if m.get('schema')!='kombikraft-native-visual-inputs-v1'or(m.get('wireCompositionVersion'),m.get('layoutRevision'))!=(10,12):raise ValueError('Unsupported native visual profile')
 seen=set()
 for row in m['files']:
  if set(row)!={'file','sha256','bytes','kind'}or row['file']in seen:raise ValueError('Duplicate or malformed visual input')
  seen.add(row['file']);p=confined(root,row['file'])
  if p.stat().st_size!=row['bytes']or digest(p)!=row['sha256']:raise ValueError('Visual input hash mismatch: '+row['file'])
  if p.suffix not in ['.inc','.rgba','.txt']:raise ValueError('Unexpected native data type')
 return m
def import_runtime(manifest,stage):
 m=json.loads(manifest.read_text())
 if m.get('schema')!='kombikraft-native-runtime-import-v1':raise ValueError('Unsupported runtime import schema')
 copied=[]
 for key,name in [('ramses19','libramses-shared-lib-wayland-ivi-egl-es-3-0.so.19.0'),('glesTransport','libGLESv2.so.2')]:
  row=m['files'][key]
  if set(row)!={'file','sha256'}:raise ValueError('Malformed local runtime entry')
  p=Path(row['file']);p=p if p.is_absolute()else manifest.parent/p
  if not p.is_file()or digest(p)!=row['sha256']:raise ValueError('Local runtime hash mismatch: '+key)
  if key=='ramses19'and row['sha256']!=RAMSES19_SHA:raise ValueError('This profile requires the exact reviewed Ramses19.0.14 capture')
  with p.open('rb')as f:
   if f.read(6)!=b'\x7fELF\x02\x01':raise ValueError('Expected Linux ELF64 little-endian library')
  target=stage/'lib'/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target);copied.append({'role':key,'output':str(target),'sha256':digest(target)})
 return copied

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,default=HERE/'data/v13');p.add_argument('--output',type=Path,default=HERE/'build/v13');p.add_argument('--zig',default='zig');p.add_argument('--runtime-import',type=Path);p.add_argument('--make-disk',action='store_true');p.add_argument('--mke2fs',default='mke2fs');p.add_argument('--validate-only',action='store_true');a=p.parse_args(argv)
 try:
  root=a.data.resolve();m=validate_data(root)
  if a.validate_only:print(json.dumps({'passed':True,'visualInputs':len(m['files']),'wireCompositionVersion':10,'layoutRevision':12,'dataManifestSha256':digest(root/'manifest.json')}));return 0
  out=a.output.resolve()
  if out.is_relative_to(root)or root.is_relative_to(out)or out.is_relative_to(HERE/'source'):raise ValueError('Build output must be separate from source and visual data')
  out.mkdir(parents=True,exist_ok=True);stage=out/'stage';stage.mkdir(exist_ok=True)
  if(stage/'native-f97').exists():raise ValueError('Choose a fresh build output; existing binary is not overwritten')
  for row in m['files']:
   if row['file'].startswith('stage/'):
    target=stage/Path(row['file']).relative_to('stage');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/row['file'],target)
  zig=shutil.which(a.zig)
  if not zig:raise ValueError('Zig0.13.0 executable not found; supply --zig')
  version=subprocess.run([zig,'version'],capture_output=True,text=True,check=True).stdout.strip()
  if version!='0.13.0':raise ValueError('Reviewed compiler version is Zig0.13.0, got '+version)
  args=[zig,'cc','-target','x86_64-linux-gnu.2.27','-std=c11','-O1','-g','-Wall','-Wextra','-Wno-unused-function','-Wno-unused-variable','-Wl,--dynamic-linker=/lib/ld-linux-x86-64.so.2','-I',str(HERE/'source'),'-I',str(root/'generated'),str(HERE/'source/main.c'),'-ldl','-lm','-o',str(stage/'native-f97')]
  subprocess.run(args,check=True);runtime=import_runtime(a.runtime_import.resolve(),stage)if a.runtime_import else[]
  disk=None
  if a.make_disk:
   if not runtime:raise ValueError('--make-disk requires a verified local --runtime-import')
   tool=shutil.which(a.mke2fs)
   if not tool:raise ValueError('mke2fs missing; install e2fsprogs and supply its executable')
   disk=out/'scene-lab.img';subprocess.run([tool,'-q','-F','-t','ext4','-d',str(stage),str(disk),'65536'],check=True)
  sources={str(x.relative_to(HERE)):digest(x)for x in sorted((HERE/'source').rglob('*'))if x.is_file()and'__pycache__'not in x.parts}
  receipt={'schema':'kombikraft-public-native-build-v1','passed':True,'profile':m['profile'],'visualRevision':m.get('visualRevision',12),'wireCompositionVersion':10,'layoutRevision':12,'sourceSha256':sources,'visualManifestSha256':digest(root/'manifest.json'),'compiler':{'version':version,'arguments':args},'binarySha256':digest(stage/'native-f97'),'runtimeImports':runtime,'assetDiskSha256':digest(disk)if disk else None,'vmLaunched':False,'freshNativeRenderingVerified':False,'fullFactoryControllerInitialization':False,'vehicleIntegrationAvailable':False,'installationAllowed':False}
  (out/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'passed':True,'binary':str(stage/'native-f97'),'binarySha256':receipt['binarySha256'],'runtimeImported':bool(runtime),'vmLaunched':False,'installationAllowed':False}));return 0
 except (OSError,ValueError,KeyError,subprocess.CalledProcessError)as exc:print('Native build denied: '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
