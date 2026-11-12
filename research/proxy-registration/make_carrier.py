"""Exact original SOME/IP proxy code/data slices; relocation semantics remain separate."""
from pathlib import Path
import struct,json,hashlib,re
from source_profile import admit_firmware,output_directory,make_parser
args=make_parser(__doc__).parse_args();P,b=admit_firmware(args.firmware);H=output_directory(args.output,P);digest=hashlib.sha256(b).hexdigest();so=struct.unpack_from('<Q',b,40)[0];se,sn,ni=struct.unpack_from('<HHH',b,58);ss=[struct.unpack_from('<IIQQQQIIQQ',b,so+i*se)for i in range(sn)];s=ss[ni];ns=b[s[4]:s[4]+s[5]];sections={ns[s[0]:ns.index(0,s[0])].decode():s for s in ss};po=struct.unpack_from('<Q',b,32)[0];pe,pn=struct.unpack_from('<HH',b,54);loads=[struct.unpack_from('<IIQQQQQQ',b,po+i*pe)for i in range(pn)]
def source(va,n):
 p=next(s for s in loads if s[0]==1 and s[3]<=va and va+n<=s[3]+s[5]);o=p[2]+va-p[3];return o,b[o:o+n]
code=[('loaderInit',0xc3340,0x80),('registerKombiProxy',0x28fd80,0x1d0),('creator',0x299cd0,0x120)]
regions=list(code);pages={0x765000,0x77c000,0x77d000,0x488000,0x48a000,0x42f000}
for _,va,n in code:
 raw=source(va,n)[1]
 for m in re.finditer(rb'[\x40-\x4f][\x8d\x8b][\x05\x0d\x15\x1d\x25\x2d\x35\x3d](....)',raw,re.S):
  target=va+m.start()+7+struct.unpack('<i',m.group(1))[0]
  if target<sections['.rodata'][3]:continue
  try:source(target&~4095,4096)
  except StopIteration:continue
  pages.add(target&~4095)
for name in ['.plt','.plt.got']:
 if name in sections:
  s=sections[name];regions.append((name[1:],s[3],s[5]))
for i,p in enumerate(sorted(pages)):regions.append(('data'+str(i),p,4096))
offset=0x1000;parts=[]
for name,va,n in regions:
 off,raw=source(va,n);parts.append((name,va,offset,raw,off));offset+=n
seeds=[('OriginalLibraryLoaderInitC3340',0xc3340),('OriginalRegisteredKombiProxyCallback28FD80',0x28fd80),('OriginalRegisteredKombiProxyCreator',0x299cd0)]
strings=b'\0';symbols=[b'\0'*24]
for name,va in seeds:
 idx=next(i+1 for i,p in enumerate(parts)if p[1]<=va<p[1]+len(p[3]));symbols.append(struct.pack('<IBBHQQ',len(strings),0x12,0,idx,va,0));strings+=('analyst_'+name).encode()+b'\0'
# Original PLT import names label original, validated JUMP_SLOT references only.
labels=[]
if '.rela.plt'in sections:
 rel=sections['.rela.plt'];dyn=sections['.dynsym'];st=ss[dyn[6]];names=b[st[4]:st[4]+st[5]];plt=sections['.plt'];idx=next(i+1 for i,p in enumerate(parts)if p[0]=='plt')
 for i,at in enumerate(range(rel[4],rel[4]+rel[5],rel[9])):
  where,info,add=struct.unpack_from('<QQq',b,at);s=struct.unpack_from('<IBBHQQ',b,dyn[4]+(info>>32)*dyn[9]);name=names[s[0]:names.index(0,s[0])].decode();va=plt[3]+16*(i+1);raw=source(va,6)[1]
  assert raw[:2]==b'\xff\x25'and va+6+struct.unpack_from('<i',raw,2)[0]==where
  symbols.append(struct.pack('<IBBHQQ',len(strings),0x12,0,idx,va,16));strings+=(name+'@plt').encode()+b'\0';labels.append({'va':hex(va),'name':name,'originalGotVa':hex(where)})
symtab=b''.join(symbols);symoff=offset;stroff=symoff+len(symtab);shstroff=stroff+len(strings);shnames=b'\0'+b''.join(('.'+r[0]).encode()+b'\0'for r in parts)+b'.symtab\0.strtab\0.shstrtab\0';shoff=(shstroff+len(shnames)+7)&~7;num=len(parts)+4;out=bytearray(shoff+num*64)
assert 64+56*len(parts)<=0x1000
struct.pack_into('<16sHHIQQQIHHHHHH',out,0,b'\x7fELF\x02\x01\x01'+b'\0'*9,2,62,1,seeds[0][1],64,shoff,0,64,56,len(parts),64,num,num-1)
for i,(name,va,off,raw,src)in enumerate(parts):
 executable=not name.startswith('data');flags=5 if executable else 4;struct.pack_into('<IIQQQQQQ',out,64+i*56,1,flags,off,va,va,len(raw),len(raw),1);out[off:off+len(raw)]=raw;struct.pack_into('<IIQQQQIIQQ',out,shoff+(i+1)*64,shnames.index(('.'+name).encode()),1,6 if executable else 2,va,off,len(raw),0,0,1,0)
out[symoff:stroff]=symtab;out[stroff:shstroff]=strings;out[shstroff:shstroff+len(shnames)]=shnames
for index,name,typ,off,raw,link,info,align,entsz in [(len(parts)+1,b'.symtab',2,symoff,symtab,len(parts)+2,1,8,24),(len(parts)+2,b'.strtab',3,stroff,strings,0,0,1,0),(len(parts)+3,b'.shstrtab',3,shstroff,shnames,0,0,1,0)]:struct.pack_into('<IIQQQQIIQQ',out,shoff+index*64,shnames.index(name),typ,0,0,off,len(raw),link,info,align,entsz)
p=H/'mgu-proxy-registration-complete-analysis.elf';assert p.resolve()!=P,'output would overwrite input';p.write_bytes(out);m={'scope':__doc__,'source':P.name,'sourceSha256':digest,'file':p.name,'sha256':hashlib.sha256(out).hexdigest(),'originalRelocationsApplied':False,'ranges':[{'source':P.name,'sourceSha256':digest,'sourceByteOffset':src,'originalVa':hex(va),'length':len(raw),'sliceSha256':hashlib.sha256(raw).hexdigest()}for name,va,off,raw,src in parts],'pltLabels':labels};(H/'mgu-proxy-registration-complete-analysis-map.json').write_text(json.dumps(m,indent=2)+'\n');print(len(out),'bytes',len(parts),'source slices',len(labels),'validated PLT labels')
