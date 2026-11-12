#!/usr/bin/env python3
"""Build separately licensed graphics bridges from source; no downloads or VM launch."""
from pathlib import Path
import argparse,json,platform,shutil,subprocess,sys
from build import digest
H=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--astc-source',type=Path,required=True,help='Arm astc-encoder Source directory at pinned revision');p.add_argument('--zig',default='zig');p.add_argument('--output',type=Path,default=H/'build/bridges');a=p.parse_args()
 try:
  if platform.system()!='Darwin'or platform.machine()!='arm64':raise ValueError('Reviewed host bridge build requires Apple Silicon macOS')
  pin=json.loads((H/'bridges/astc-source-pin.json').read_text());source=a.astc_source.resolve()
  for name,want in pin['sha256'].items():
   if digest(source/name)!=want:raise ValueError('ASTC source differs from pinned revision: '+name)
  out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);idemu=H/'bridges/idemu';zig=shutil.which(a.zig)
  if not zig or subprocess.run([zig,'version'],capture_output=True,text=True,check=True).stdout.strip()!='0.13.0':raise ValueError('Zig0.13.0 required')
  dylib=out/'libastcdec-neon.dylib';glhost=out/'glhost-cluster';gles=out/'libGLESv2.so.2'
  if any(p.exists()for p in [dylib,glhost,gles]):raise ValueError('Use a fresh bridge output directory')
  commands=[['clang++','-std=c++20','-O2','-DNDEBUG','-DASTCENC_DYNAMIC_LIBRARY=1','-DASTCENC_DECOMPRESS_ONLY','-DASTCENC_NEON=1','-DASTCENC_SVE=0','-DASTCENC_SSE=0','-DASTCENC_AVX=0','-dynamiclib','-fPIC','-pthread','-I',str(source),*[str(source/x)for x in pin['cppFiles']],'-o',str(dylib)],[zig,'cc','-target','x86_64-linux-gnu.2.27','-ffreestanding','-fPIC','-shared','-O1','-fno-stack-protector','-Wno-incompatible-library-redeclaration','-Wno-builtin-requires-header','-Wno-implicit-function-declaration','-Wno-empty-body','-I',str(idemu),str(idemu/'gles-cluster.c'),'-ldl','-Wl,-soname,libGLESv2.so.2','-o',str(gles)],['clang','-O2','-Wno-deprecated-declarations','-I',str(idemu),'-I',str(source),str(idemu/'glhost-cluster.c'),str(dylib),'-framework','OpenGL','-o',str(glhost)]]
  for cmd in commands:subprocess.run(cmd,check=True)
  r={'schema':'kombikraft-native-bridge-build-v1','passed':True,'commands':commands,'astcSourceRevision':pin['revision'],'sourcesPinSha256':digest(H/'bridges/astc-source-pin.json'),'outputs':{p.name:digest(p)for p in[dylib,glhost,gles]},'licences':{'idemu':'PolyForm-Noncommercial-1.0.0','astcenc':'Apache-2.0'},'qemuBuilt':False,'vmLaunched':False}
  (out/'build-receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':True,'outputs':r['outputs'],'qemuBuilt':False,'vmLaunched':False}));return 0
 except(OSError,ValueError,KeyError,subprocess.CalledProcessError)as exc:print('Bridge build denied: '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
