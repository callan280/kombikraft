#!/usr/bin/env python3
"""Bounded observed CE51 tables and zlib resources; no source modification."""
from pathlib import Path
import argparse,collections,hashlib,json,re,struct,zlib
HERE=Path(__file__).resolve().parent

def sha(data):return hashlib.sha256(data).hexdigest()
def write_rgba_png(path,width,height,pixels):
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
 raw=b''.join(b'\0'+pixels[y*width*4:(y+1)*width*4] for y in range(height))
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
def extract(source,output):
 assert source.stat().st_size<=512*1024*1024,'Input exceeds observed CE51 bound'
 data=source.read_bytes();assert data[:4]==b'\xceQ\0\0'
 pool,section_count=struct.unpack_from('<I',data,0x58)[0],struct.unpack_from('<I',data,0x7c)[0]
 assert 0<pool<len(data) and 0<section_count<=128
 plen,count=struct.unpack_from('<II',data,pool);assert pool+plen<=len(data) and count<=100000
 strings={};pos=pool+8
 for _ in range(count):
  start=pos;n=struct.unpack_from('<H',data,pos)[0];assert n and pos+2+n<=pool+plen
  raw=data[pos+2:pos+2+n];assert raw[-1]==0
  strings[start-pool]=raw[:-1].decode('utf8');pos=(pos+2+n+3)&~3
 assert pos==pool+plen
 output.mkdir(parents=True,exist_ok=False);(output/'strings.json').write_text(json.dumps(strings,indent=2)+'\n')
 groups=[];rows=[];missing=[];formats=collections.Counter()
 payload_origin=min(struct.unpack_from('<4I',data,0x80+si*16)[2] for si in range(section_count))
 for si in range(section_count):
  kind,index,base,span=struct.unpack_from('<4I',data,0x80+si*16)
  index_size,n,unknown=struct.unpack_from('<3I',data,index)
  assert index_size==12+n*20 and index+index_size<=len(data)
  groups.append({'kind':hex(kind),'indexOffset':index,'count':n,'indexUnknownWord':unknown,'payloadBase':base,'payloadSpan':span})
  for i in range(n):
   name_ref,index_tag,ordinal_tag,relative,raw_size=struct.unpack_from('<5I',data,index+12+i*20)
   assert 0<=raw_size<=128*1024*1024
   name=strings.get(name_ref,f'unnamed_resource_{name_ref:08x}');offset=payload_origin+relative
   assert base<=offset<base+span
   row={'kind':hex(kind),'name':name,'nameStringOffset':name_ref,'nameStringReferenceVerified':name_ref in strings,'indexEntryOffset':index+12+i*20,'indexOffsetTag':index_tag,'ordinalTag':ordinal_tag,'recordOffset':offset,'declaredDecodedBytes':raw_size}
   if offset+12>len(data):missing.append(row);continue
   record_size,rkind,rname=struct.unpack_from('<3I',data,offset)
   if offset+record_size>len(data):missing.append(row);continue
   assert record_size>=12 and rkind==kind and rname==name_ref
   if raw_size:
    dec=zlib.decompressobj()
    try:decoded=dec.decompress(data[offset+12:offset+record_size],raw_size+1)
    except zlib.error as e:raise ValueError(f'Not zlib: {kind:x} {i} {name} at {offset:x}, decoded-size {raw_size}, prefix {data[offset+12:offset+28].hex()}') from e
    assert len(decoded)==raw_size and dec.eof and not dec.unconsumed_tail
    assert len(dec.unused_data)<=3 and not any(dec.unused_data)
    padding=len(dec.unused_data);encoding='zlib with exact declared output length'
   else:
    assert kind==0x2301
    decoded=data[offset+12:offset+record_size];padding=None;encoding='opaque font-pack bytes; zero decoded-length declaration, no zlib decoding'
   stem=f'{kind:04x}-{i:04d}-'+re.sub('[^A-Za-z0-9_.-]','_',name.split('#')[-1])[:150]
   folder=output/'payloads'/f'{kind:04x}';folder.mkdir(parents=True,exist_ok=True)
   dest=folder/(stem+'.bin');dest.write_bytes(decoded)
   row.update(recordBytes=record_size,decodedSha256=sha(decoded),decodedFile=str(dest),paddingAfterZlib=padding,resourceEncoding=encoding)
   if kind==7:
    h=struct.unpack_from('<9I',decoded);assert h[0]==44 and 0<h[1]<=16384 and 0<h[2]<=16384
    w,height,fmt,variant=h[1:5];pixels=decoded[36:];formats[(fmt,variant)]+=1
    row.update(width=w,height=height,bitmapFormat=fmt,bitmapVariant=variant,bitmapHeader=list(h),pixelDataBytes=len(pixels))
    selected=bool(re.search(r'ki_3d_kombi|ki_dzm_shiftlights|F97|Logo|logo|MSPORT|msport',name))
    if selected and fmt==1 and variant==0 and len(pixels)==w*height*4:
     pngdir=output/'bitmaps';pngdir.mkdir(exist_ok=True);png=pngdir/(stem+'.png')
     write_rgba_png(png,w,height,pixels)
     row.update(png=str(png),pngSha256=sha(png.read_bytes()),pixelInterpretation='Four stored byte channels as RGBA, original row order; shader/material interpretation not established')
    elif selected:row['bitmapDecodeLimitation']='Pixel variant/packing not yet interpreted'
   rows.append(row)
 manifest={'sourceFile':str(source),'sourceSha256':sha(data),'sourceBytes':len(data),'containerMagic':'CE51 little endian','engineIdentity':'not established','declaredContainerEnd':struct.unpack_from('<I',data,4)[0],'stringPoolOffset':pool,'stringCount':count,'sections':groups,'resourceCountDecoded':len(rows),'resourceCountUnavailableInThisSegment':len(missing),'missingResources':missing,'bitmapFormats':{str(k):v for k,v in formats.items()},'resources':rows,'limitations':['CE51 table interpretation established from bounded headers and matching zlib records; not original vendor documentation.','All emitted payloads match declared decoded lengths and zlib end-of-stream checks.','Static resources do not establish execution or F40 compatibility.','Some NOR logical resource offsets may extend outside this flash segment; they remain unextracted.']}
 (output/'ce51-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 return manifest

def main():
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();m=extract(a.source,a.output);print(json.dumps({'decoded':m['resourceCountDecoded'],'unavailable':m['resourceCountUnavailableInThisSegment'],'formats':m['bitmapFormats'],'pngs':sum('png'in r for r in m['resources'])},indent=2))
if __name__=='__main__':main()
