#!/usr/bin/env python3
"""Regenerate the F97 base mesh/pixels using the public viewer-pack route manifest."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,struct,sys
from build import confined,digest
ROUTE='/f97-reference/render-package/f97-gauges-package.json'
class RoutePack:
 def __init__(self,root):
  self.root=root.resolve();m=json.loads((self.root/'manifest.json').read_text())
  if m.get('schema')!='kombikraft-local-assets-v1':raise ValueError('Unsupported public viewer pack')
  self.rows={}
  for row in m['entries']:
   if set(row)!={'route','file','sha256'}or row['route']in self.rows:raise ValueError('Malformed/duplicate public route')
   self.rows[row['route']]=row
 def read(self,route):
  if route not in self.rows:raise ValueError('Public asset route absent: '+route)
  r=self.rows[route];p=confined(self.root,r['file'])
  if digest(p)!=r['sha256']:raise ValueError('Public route hash mismatch: '+route)
  return p.read_bytes()
def number(x):
 s=format(float(x),'.9g');return s+('f'if'.'in s or'e'in s else'.0f')
def generate(pack,out):
 d=json.loads(pack.read(ROUTE));out.mkdir(parents=True,exist_ok=True);lines=['/* Generated BMW-derived visual data; excluded from MIT. */'];textures=[]
 for key,m in d['meshes'].items():
  if not key.replace('_','').isalnum()or m['vertexCount']!=len(m['originalPosition'])or m['vertexCount']!=len(m['originalUv0'])or m['vertexCount']%3:raise ValueError('Malformed original mesh')
  for name,values in [('positions',[v for row in m['originalPosition']for v in row]),('uv',[v for row in m['originalUv0']for v in row[:2]])]:lines.append('static float '+key+'_'+name+'[]={'+','.join(number(v)for v in values)+'};')
 for key,t in d['textures'].items():
  rel=PurePosixPath(t['file'])
  if rel.is_absolute()or'..'in rel.parts:raise ValueError('Texture route must be relative')
  raw=pack.read(str(PurePosixPath(ROUTE).parent/rel))
  if hashlib.sha256(raw).hexdigest()!=t['sha256']:raise ValueError('Original texture digest mismatch')
  if t['storedBytesPerPixel']==2:raw=b''.join(bytes((raw[i],raw[i],raw[i],raw[i+1]))for i in range(0,len(raw),2))
  if len(raw)!=t['width']*t['height']*4:raise ValueError('Texture dimensions mismatch')
  filename=key+'.rgba';(out/filename).write_bytes(raw);textures.append((key,filename,t['width'],t['height']))
 lines.append('typedef struct{const char *key,*file;unsigned width,height;} F97Texture;');lines.append('static const F97Texture f97_textures[]={'+','.join('{'+json.dumps(k)+','+json.dumps(f)+','+str(w)+','+str(h)+'}'for k,f,w,h in textures)+'};');(out/'f97_arrays.inc').write_text('\n'.join(lines)+'\n')
 return{'meshes':len(d['meshes']),'textures':len(textures),'sourceRoute':ROUTE,'generatedArraySha256':digest(out/'f97_arrays.inc'),'physicalCalibrationVerified':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--asset-pack',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:print(json.dumps(generate(RoutePack(a.asset_pack),a.output.resolve())));return 0
 except (OSError,ValueError,KeyError)as exc:print('Generation denied: '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
