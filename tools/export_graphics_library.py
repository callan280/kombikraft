#!/usr/bin/env python3
"""Export only catalogued visual resources to a portable content-addressed library.

Input is the private asset inventory, never a firmware image. No application
executable, scene container, archive, ledger, device backup or user state is
copied. The export is deterministic; public metadata uses an explicit allowlist.
"""
import argparse,collections,hashlib,json,re,shutil,struct
from pathlib import Path
VISUAL={'font','font-wrapper','opaque-font-pack','opaque-font-container','mesh','compiled-shader','ramses-vertex-reference','ramses-index-reference','ramses-effect-reference'}
PRIVATE=re.compile(r'(?i)(?:/Users/|/Volumes/|[a-z]:\\|\b(?:password|passwd|access_token|refresh_token|private.key)\b|[\w.+-]+@[\w.-]+\.[a-z]{2,})')
VIN=re.compile(r'\b[A-HJ-NPR-Z0-9]{17}\b')
PERSONAL_PATH=re.compile(r'(?i)(?:/(?:userdata|user-data|user_data|contacts|phonebook|recordings|camera|photos|screenshots|browser/cache|personal)/|Gorillaz|Demon Days)')
FIELDS={'sourceSha256','sourceContainerSha256','sourceRecordOffset','sourceName','resourceDecodedSha256','containerKind','resourceKind','sourceVariantIndex','sourceComponentIndex','sourcePlacementOffset','sourceVariantMeaningVerified','pixelInterpretation','interpretation','format','variant','orientation','sourceOrientation','outputByteInterpretation','internalFormat','compression','decodedBytes','width','height','mipSizes','container','kind','identifier','idsAliases','contentHash','name','tableVa','tableIndex','descriptorVa','descriptorSourceByteOffset','descriptorSourceSha256','sourceCCIDs','staticProducerPathVerified','liveNativeBindingVerified','CANIdentifierMappingVerified','exactF97ID6OrID7AttributionVerified','originalDecoderSource','fontSha256','codepoints','rasterizer','embeddedOffset','recordBytes','atlasCell','fullNodePath','transform','cropDerivation','bitmapHeader','tables','decoding'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def clean(v):
 if isinstance(v,str):
  # Paths are source labels only, never caller-owned machine/volume paths.
  if '/Users/'in v or '/Volumes/'in v or re.match(r'^[a-zA-Z]:\\',v):v=Path(v.replace('\\','/')).name
  v=VIN.sub('[vehicle-id-redacted]',v)
  return PRIVATE.sub('[private-redacted]',v)
 if isinstance(v,list):return[clean(x)for x in v]
 if isinstance(v,dict):return{k:clean(x)for k,x in v.items()if k in FIELDS or k in {'x','y','z','w','width','height','left','right','top','bottom','scale','rotation','translation'}}
 return v

def font_names(path):
 b=path.read_bytes();count=struct.unpack_from('>H',b,4)[0];table=None
 for i in range(count):
  tag,_,off,size=struct.unpack_from('>4sIII',b,12+16*i)
  if tag==b'name':table=(off,size);break
 if table is None:return {}
 off,size=table;_,count,storage=struct.unpack_from('>HHH',b,off);names={}
 for i in range(count):
  platform,encoding,language,nid,length,rel=struct.unpack_from('>6H',b,off+6+12*i)
  if nid not in [0,1,2,6,8,13,14]or nid in names:continue
  raw=b[off+storage+rel:off+storage+rel+length]
  try:names[nid]=raw.decode('utf-16-be'if platform in [0,3]else'mac_roman')
  except UnicodeDecodeError:continue
 return names

def checked_source(root,relative):
 p=(root/relative).resolve();p.relative_to((root/'objects').resolve());assert p.is_file()and not p.is_symlink();return p

def export(source,dest):
 dest.mkdir(parents=True,exist_ok=True);objects=dest/'objects';objects.mkdir(exist_ok=True)
 records=[];copies={};licenses={};excluded=collections.Counter();kinds=collections.Counter();families=collections.Counter();total=0
 def copy_object(p,digest,ext):
  actual=sha(p);assert actual==digest,(p,'source digest mismatch')
  relative='objects/'+digest[:2]+'/'+digest+ext;out=dest/relative
  if relative not in copies:
   out.parent.mkdir(exist_ok=True)
   if not out.exists():shutil.copyfile(p,out)
   assert sha(out)==digest,'export readback mismatch'
   # Block whole executable/program images even if inventory classification drifts.
   head=out.open('rb').read(8)
   assert not(head.startswith(b'\x7fELF')or head[:2]==b'MZ' or head[:4]in[b'PK\x03\x04',b'\xcf\xfa\xed\xfe',b'\xfe\xed\xfa\xcf']),('executable/archive rejected',relative)
   copies[relative]={'sha256':digest,'bytes':out.stat().st_size}
  return relative
 for line in (source/'assets.jsonl').open():
  total+=1;x=json.loads(line);kind=x['kind'];m=x['metadata'];preview=x.get('png')
  if not preview and kind not in VISUAL:excluded[kind]+=1;continue
  aliases=[]
  for a in x.get('aliases',[]):
   if PERSONAL_PATH.search(a.get('source','')+' '+a.get('name','')):continue
   r={'sourceLabel':clean(Path(a.get('source','')).name),'name':clean(a.get('name','')),'offset':a.get('offset')}
   # Capture provenance from every alias, not only the first merged row.
   d=a.get('derivation',{});r.update({k:clean(d[k])for k in['sourceContainerSha256','sourceRecordOffset','sourceName','resourceDecodedSha256','descriptorSourceSha256','tableVa','tableIndex','descriptorVa','sourceCCIDs']if k in d})
   if r not in aliases:aliases.append(r)
  if not aliases:excluded['personal-or-unattributed-'+kind]+=1;continue
  row={'id':x['sha256'],'kind':kind,'families':sorted(set(clean(m.get('sourceFamilies',[])))),'names':sorted(set(a['name']for a in aliases if a['name'])),'source':aliases,'nativeControllerBindingVerified':False}
  row['metadata']={k:clean(m[k])for k in FIELDS if k in m}
  if kind=='font':
   original_names=font_names(checked_source(source,x['file']));licenses[x['sha256']]=original_names
   row['names']=sorted(set(row['names']+[clean(original_names[n])for n in [1,2,6]if n in original_names]))
   row['metadata']['fontNames']={str(n):clean(original_names[n])for n in [1,2,6,8]if n in original_names}

  if preview:
   p=checked_source(source,preview);head=p.open('rb').read(24);assert head[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',head[16:24]);assert(w,h)==(x['width'],x['height'])
   row.update(image=copy_object(p,m['previewSha256'],'.png'),width=w,height=h,imageSha256=m['previewSha256'])
  if kind in VISUAL:
   p=checked_source(source,x['file']);ext='.ttf'if kind=='font'else'.bin';row['resource']=copy_object(p,x['sha256'],ext);row['resourceSha256']=x['sha256'];row['resourceBytes']=p.stat().st_size
  records.append(row);kinds[kind]+=1;families.update(row['families'])
 notices=['# Original embedded font notices','', 'These notices are transcribed from the unchanged font name tables. They do not relicense BMW assets; see NOTICE.md. Public upstream license contact details below are retained as part of those notices.','']
 for digest,names in sorted(licenses.items()):
  notices.extend(['## '+names.get(1,digest),'', 'Object SHA-256: `'+digest+'`',''])
  for nid in [0,13,14]:
   if nid in names:notices.extend([names[nid].replace('\r\n','\n'),''])
 (dest/'FONT-LICENSES.md').write_text('\n'.join(notices))
 # Keep provenance complete in small on-demand JSONP shards, supporting file://.
 details=collections.defaultdict(dict);index=[]
 for row in records:
  details[row['id'][:2]][row['id']]=row
  brief={k:row[k]for k in ['id','kind','families','names','imageSha256','width','height','resourceSha256','resourceBytes']if k in row}
  index.append(brief)
 detail_dir=dest/'details';detail_dir.mkdir(exist_ok=True)
 for key,values in details.items():
  payload=json.dumps(values,ensure_ascii=False,separators=(',',':'),sort_keys=True)
  assert not PRIVATE.search(payload)
  (detail_dir/(key+'.js')).write_text('window.KOMBIKRAFT_LIBRARY_DETAILS=window.KOMBIKRAFT_LIBRARY_DETAILS||{};window.KOMBIKRAFT_LIBRARY_DETAILS["'+key+'"]='+payload.replace('</','<\\/')+';\n')
 catalog={'schema':'kombikraft-visual-library-v1','attribution':'BMW AG and respective original asset/font/renderer owners. Not covered by KombiKraft source-code license.','nativeControllerBindingVerified':False,'records':index}
 data=json.dumps(catalog,ensure_ascii=False,separators=(',',':'),sort_keys=True)
 assert not PRIVATE.search(data),'private metadata escaped sanitization'
 (dest/'catalog.js').write_text('window.KOMBIKRAFT_LIBRARY='+data.replace('</','<\\/')+';\n')
 receipt={'schema':'kombikraft-visual-library-export-v1','sourceInventorySha256':sha(source/'assets.jsonl'),'sourceRecordsChecked':total,'exportedRecords':len(records),'recordKinds':dict(kinds),'sourceFamilies':dict(families),'excludedKinds':dict(excluded),'uniqueObjects':len(copies),'objectBytes':sum(r['bytes']for r in copies.values()),'fontNoticesSha256':sha(dest/'FONT-LICENSES.md'),'catalogBytes':(dest/'catalog.js').stat().st_size,'detailShards':{f.name:{'sha256':sha(f),'bytes':f.stat().st_size}for f in sorted(detail_dir.glob('*.js'))},'catalogSha256':sha(dest/'catalog.js'),'objects':copies,'allObjectReadbacksVerified':True,'privateMetadataPatternCheckPassed':True,'sourceMachinePathsExported':False,'vehicleDataExported':False,'nativeControllerBindingVerified':False,'firmwareOrExecutableImagesExported':False}
 (dest/'export-receipt.json').write_text(json.dumps(receipt,separators=(',',':'),sort_keys=True)+'\n')
 print(json.dumps({k:v for k,v in receipt.items()if k not in ['objects','detailShards']},indent=2))

def verify(dest):
 r=json.loads((dest/'export-receipt.json').read_text());assert sha(dest/'catalog.js')==r['catalogSha256'];assert sha(dest/'FONT-LICENSES.md')==r['fontNoticesSha256']
 for p,row in r.get('detailShards',{}).items():
  f=dest/'details'/p;assert f.stat().st_size==row['bytes']and sha(f)==row['sha256'];assert not PRIVATE.search(f.read_text())
 for p,row in r['objects'].items():
  f=(dest/p).resolve();f.relative_to(dest.resolve());assert f.stat().st_size==row['bytes']and sha(f)==row['sha256']
 assert not PRIVATE.search((dest/'catalog.js').read_text())
 print(json.dumps({'result':'PASS','records':r['exportedRecords'],'objectReadbacks':len(r['objects']),'bytes':r['objectBytes'],'privateMetadataPatternCheckPassed':True}))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path);p.add_argument('--dest',type=Path,default=Path(__file__).resolve().parents[1]/'assets/library');p.add_argument('--verify',action='store_true');a=p.parse_args()
 if a.verify:verify(a.dest)
 else:
  if not a.source:p.error('--source private library directory is required for export')
  export(a.source.resolve(),a.dest.resolve())
