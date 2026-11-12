"""Original492-node tree and declared property suffix on admitted inputs.

Fresh static storage and descriptor/stack frames are explicit unit inputs.
Original constructors, attachment and suffix instructions write native fields;
heap allocation is the sole function adapter. This is not whole CRT/boot.
"""
from collections import Counter
import struct,json,hashlib,math,bisect
import unicorn
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_PROT_READ,UC_PROT_WRITE,UC_PROT_EXEC
from unicorn.arm_const import *
BASE,DATA,HEAP,STACK,RET=0x10000,0xf00000,0x31000000,0x33000000,0x70000000
REGS=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
sha=lambda b:hashlib.sha256(b).hexdigest()
def source_ranges(bank,spans):
 merged=[]
 for start,end in sorted(spans):
  if merged and start<=merged[-1][1]:merged[-1][1]=max(end,merged[-1][1])
  else:merged.append([start,end])
 return [dict(bankOffsetStart=a,endExclusive=b,bytes=b-a,sha256=sha(bank[a:b]))for a,b in merged]

def product(a,b):return [sum(a[i*4+k]*b[k*4+j]for k in range(4))for i in range(4)for j in range(4)]
def local_oracle(scene,h):
 p=struct.unpack_from('<3f',scene,h+0x4c);r=struct.unpack_from('<3f',scene,h+0x58);s=struct.unpack_from('<3f',scene,h+0x64);base=struct.unpack_from('<16f',scene,h+12)
 x,y,z=[v*0.017453292 for v in r];sx,cx,sy,cy,sz,cz=math.sin(x),math.cos(x),math.sin(y),math.cos(y),math.sin(z),math.cos(z)
 a=[cy*cz,cy*sz,-sy,0,cz*sx*sy-cx*sz,cx*cz+sx*sy*sz,cy*sx,0,cx*cz*sy+sx*sz,cx*sy*sz-cz*sx,cx*cy,0,*p,1]
 for i in range(3):
  for j in range(3):a[i*4+j]*=s[i]
 return product(a,base)
def observe(bank,data,scene,graph,fill):
 full=True;witness=False
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
 for at,b,flags in [(BASE,bank,UC_PROT_READ|UC_PROT_EXEC),(DATA,data,UC_PROT_READ|UC_PROT_WRITE)]:
  n=(len(b)+4095)&~4095;u.mem_map(at,n);u.mem_write(at,b);u.mem_protect(at,n,flags)
 groups=graph['nodes']
 u.mem_map(0x40000000,(len(scene)+4095)&~4095);u.mem_write(0x40000000,scene);u.mem_protect(0x40000000,(len(scene)+4095)&~4095,UC_PROT_READ);u.mem_map(0x30000000,0x3000,UC_PROT_READ|UC_PROT_WRITE)
 globals_=[(0x106267c,24)]
 if full:globals_=[(0x10625cc,0xc8),(0x102ec7c,0x54),(0x1062830,4),(0x103f53c,4),(0x1062418,0x28),(0x1062580,4)]
 for page in sorted({a&~4095 for a,n in globals_}):u.mem_map(page,4096,UC_PROT_READ|UC_PROT_WRITE)
 u.mem_write(0x106267c,bytes([fill])*24);u.mem_write(0x1062580,bytes([0xa5])*4)
 u.mem_map(HEAP,0x100000,UC_PROT_READ|UC_PROT_WRITE);u.mem_map(STACK,0x4000,UC_PROT_READ|UC_PROT_WRITE);u.mem_map(RET,4096,UC_PROT_READ|UC_PROT_EXEC)
 u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
 phase='';stop=None;alloc=[];starts=[];nextat=HEAP;visits=[];writes=[];denials=[];trace=hashlib.sha256();spans=set()
 def live(a,n):
  i=bisect.bisect_right(starts,a)-1
  return i>=0 and a+n<=starts[i]+alloc[i]['bytes']
 fresh=lambda a,n:any(g<=a and a+n<=g+s for g,s in globals_)
 def code(uc,a,n,_):
  nonlocal nextat
  if a in(RET,stop):uc.emu_stop();return
  off=a-BASE;assert 0<=off and off+n<=len(bank),hex(a)
  if off in(0x128498,0x184718):
   count=uc.reg_read(UC_ARM_REG_R0);assert 0<count<=0x1000
   ptr=nextat;nextat=(ptr+count+15)&~15;assert nextat<=HEAP+0x100000
   starts.append(ptr);alloc.append(dict(pointer=ptr,bytes=count,phase=phase));uc.mem_write(ptr,bytes([fill])*count);uc.reg_write(UC_ARM_REG_R0,ptr);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
  spans.add((off,off+n))
  visits.append((phase,off));trace.update(phase.encode()+struct.pack('<I',off)+bank[off:off+n])
 def access(uc,k,a,n,v,_):
  mutable=0xf1f22c<=a and a+n<=0xf1f230 or 0x30000000<=a and a+n<=0x30003000 or live(a,n)or STACK<=a and a+n<=STACK+0x4000 or fresh(a,n)
  allowed=mutable or k!=unicorn.UC_MEM_WRITE and(BASE<=a and a+n<=BASE+len(bank)or DATA<=a and a+n<=DATA+len(data)or 0x40000000<=a and a+n<=0x40000000+len(scene))
  if not allowed:denials.append(dict(phase=phase,address=a,bytes=n,sourceBankPC=uc.reg_read(UC_ARM_REG_PC)-BASE,kind=k));uc.emu_stop();return
  if k==unicorn.UC_MEM_WRITE and(fresh(a,n)or 0xf1f22c<=a and a+n<=0xf1f230):writes.append(dict(phase=phase,address=a,bytes=n,value=v,sourceBankPC=uc.reg_read(UC_ARM_REG_PC)-BASE))
 def invalid(uc,k,a,n,v,_):denials.append(dict(phase=phase,address=a,bytes=n,sourceBankPC=uc.reg_read(UC_ARM_REG_PC)-BASE,kind=k));return False
 u.hook_add(unicorn.UC_HOOK_CODE,code);u.hook_add(unicorn.UC_HOOK_MEM_READ|unicorn.UC_HOOK_MEM_WRITE,access);u.hook_add(unicorn.UC_HOOK_MEM_INVALID,invalid)
 def call(entry,name,r0=0,r1=0,stopAt=None,r6=None,r7=None):
  nonlocal phase,stop
  phase=name;stop=stopAt
  for i,r in enumerate(REGS):u.reg_write(r,0x44440000+i)
  for r,v in((UC_ARM_REG_R0,r0),(UC_ARM_REG_R1,r1),(UC_ARM_REG_SP,STACK+0x3f00),(UC_ARM_REG_LR,RET)):u.reg_write(r,v)
  if r6 is not None:u.reg_write(UC_ARM_REG_R6,r6)
  if r7 is not None:u.reg_write(UC_ARM_REG_R7,r7)
  error=None
  try:u.emu_start(BASE+entry,RET+4,count=100000)
  except unicorn.UcError as e:error=str(e)
  pc=u.reg_read(UC_ARM_REG_PC);returned=pc==RET
  if returned:assert u.reg_read(UC_ARM_REG_SP)==STACK+0x3f00 and all(u.reg_read(r)==0x44440000+i for i,r in enumerate(REGS)),name
  return dict(name=name,returned=returned,stoppedAtDeclaredBoundary=stopAt is not None and pc==stopAt,pc=pc,r0=u.reg_read(UC_ARM_REG_R0),error=error)
 assert struct.unpack_from('<I',bank,0xef60fc-BASE)[0]==0x125f20
 result=[call(0x115f20,'original-static-initializer',stopAt=None if full else BASE+0x115f54)]
 constants=list(struct.unpack('<6I',bytes(u.mem_read(0x106267c,24))))
 assert constants==[0xff7fffff]*3+[0x7f7fffff]*3
 if full:
  assert result[0]['returned'] and not denials
  before=[bytes(u.mem_read(a,n))for a,n in globals_]
  result.append(call(0x115f20,'original-static-initializer-repeat'))
  assert result[-1]['returned'] and before==[bytes(u.mem_read(a,n))for a,n in globals_]
 result.append(call(0x10ce3c,'explicit-clear-current-camera-api',0));assert result[-1]['returned']and bytes(u.mem_read(0x1062580,4))==bytes(4)
 u.mem_write(0x30002000+0xc,struct.pack('<I',0x40000000-12))
 objects={};hierarchy=[];expected={};suffixes=[]
 for node in groups:
  u.mem_write(0x30000000,struct.pack('<4I',0x30001000,0,0x40000000+node['headerOffset'],0))
  result.append(call({'Group':0x11e334,'Mesh':0x114110,'Billboard':0x4098f8}[node['className']],'construct-'+str(node['headerOffset']),0x30000000 if node['className']=='Billboard'else 0));obj=result[-1]['r0']
  if not result[-1]['returned']:break
  objects[node['headerOffset']]=obj
  u.mem_write(0x30000000,struct.pack('<4I',0x30001000,0,0x40000000+node['headerOffset'],0))
  result.append(call(0x3f02a4,'read-'+node['name'],obj,0x30000000))
  if not result[-1]['returned']:break
  if node['className']=='Billboard':
   result.append(call(0x4097e0,'billboard-specific-'+str(node['headerOffset']),obj,0x30000000))
   if not result[-1]['returned']:break
   assert result[-1]['r0']==1 and struct.unpack('<I',bytes(u.mem_read(obj+0x210,4)))[0]==struct.unpack_from('<I',scene,node['headerOffset']+0xc8)[0]
  # Declared interior original reader suffix, not a fake child/material return.
  u.mem_write(0x30000000,struct.pack('<5I',0x30001000,0,0x40000000+node['headerOffset'],0x30002000,0))
  fragment=call(0x3fa794,'original-property-suffix-'+str(node['headerOffset']),stopAt=BASE+0x3fa808,r6=0x30000000,r7=obj)
  result.append(fragment);assert fragment['stoppedAtDeclaredBoundary']and not denials,fragment
  assert u.reg_read(UC_ARM_REG_SP)==STACK+0x3f00
  source_gate=scene[node['headerOffset']+0x9c];source_factor=scene[node['headerOffset']+0xb0:node['headerOffset']+0xb4]
  native_gate=bytes(u.mem_read(obj+0xb8,1))[0];native_factor=bytes(u.mem_read(obj+0xc8,4))
  assert source_gate==native_gate and source_factor==native_factor
  suffixes.append(dict(headerOffset=node['headerOffset'],source9c=source_gate,nativeB8=native_gate,sourceB0Hex=source_factor.hex(),nativeC8Hex=native_factor.hex(),interiorStop=fragment))
  if node['parentHeaderOffset'] is not None:
   result.append(call(0x115764,'attach-'+node['name'],objects[node['parentHeaderOffset']],obj))
   if not result[-1]['returned']:break
   assert result[-1]['r0']==1
  fn=struct.unpack('<I',bytes(u.mem_read(struct.unpack('<I',bytes(u.mem_read(obj+4,4)))[0]+0x2c,4)))[0]
  result.append(call(fn-BASE,'world-'+node['name'],obj))
  if not result[-1]['returned']:break
  world_bytes=bytes(u.mem_read(result[-1]['r0'],64))
  world=list(struct.unpack('<16f',world_bytes))
  want=local_oracle(scene,node['headerOffset']);parent=node['parentHeaderOffset']
  if parent is not None:want=product(want,expected[parent])
  expected[node['headerOffset']]=want;delta=max(abs(a-b)for a,b in zip(want,world));assert delta<1e-3,(node['name'],delta)
  parentword=struct.unpack('<I',bytes(u.mem_read(obj+0xe4,4)))[0];assert parentword==(objects[parent]if parent is not None else 0)
  extent=next(a['bytes']for a in alloc if a['pointer']==obj);vt=struct.unpack('<I',bytes(u.mem_read(obj+4,4)))[0];assert vt=={'Group':0x51d850,'Mesh':0x51af24,'Billboard':0x9f6998}[node['className']]
  leaf=dict(originalAllocationBytes=extent,originalVtable=vt)
  if node['className']=='Mesh':
   leaf['pendingMeshResourcePointer']=struct.unpack('<I',bytes(u.mem_read(obj+0x178,4)))[0];assert leaf['pendingMeshResourcePointer']==0
  if node['className']=='Billboard':
   leaf.update(mode=struct.unpack('<I',bytes(u.mem_read(obj+0x210,4)))[0],originalVertexBytes=bytes(u.mem_read(obj+0x1c0,80)).hex(),serializedFactoryAndSpecificReaderInputHex=scene[node['headerOffset']+0xc0:node['headerOffset']+0xec].hex());assert leaf['mode']==3
  hierarchy.append(dict(node=node,object=obj,leafState=leaf,parentWord=parentword,world=world,worldBytesHex=world_bytes.hex(),oracleWorld=want,oracleMaximumDelta=delta))
 assert len(hierarchy)==492 and not denials,(len(hierarchy),denials,result[-1])
 word=lambda at:struct.unpack('<I',bytes(u.mem_read(at,4)))[0]
 sibling_checks=[]
 for node in groups:
  obj=objects[node['headerOffset']];children=[g for g in groups if g['parentHeaderOffset']==node['headerOffset']];actual=[];cursor=word(obj+0xe8)
  while cursor:
   assert cursor not in actual;actual.append(cursor);cursor=word(cursor+0x168)
  assert actual==[objects[g['headerOffset']]for g in children] and word(obj+0xc4)==len(children)
  sibling_checks.append(dict(headerOffset=node['headerOffset'],sourceGroupChildren=[g['headerOffset']for g in children],actualPointers=actual,actualCount=word(obj+0xc4)))
 policies=[];by_node={n['headerOffset']:n for n in groups}
 for node in groups:
  header=node['headerOffset'];obj=objects[header];chain=[];cursor=node
  while cursor is not None:
   chain.append(cursor['headerOffset']);cursor=by_node.get(cursor['parentHeaderOffset'])
  expected_gate=int(all(scene[h+0x9c]!=0 for h in chain))
  factors=[struct.unpack_from('<f',scene,h+0xb0)[0]for h in chain];factor=1.0
  for value in reversed(factors):factor=struct.unpack('<f',struct.pack('<f',factor*value))[0]
  gate_call=call(0x115078,'original-effective-gate-'+str(header),obj);result.append(gate_call);assert gate_call['returned']and gate_call['r0']==expected_gate
  factor_call=call(0x11510c,'original-inherited-factor-'+str(header),obj);result.append(factor_call);actual_factor=u.reg_read(UC_ARM_REG_S0);assert factor_call['returned']and actual_factor==struct.unpack('<I',struct.pack('<f',factor))[0]
  local_gate=scene[header+0x9c];local_factor=struct.unpack_from('<f',scene,header+0xb0)[0];skip=None
  if local_gate==0 or local_factor==0:
   skip=call(0x1172d8,'original-local-render-bin-skip-'+str(header),0,obj);result.append(skip);assert skip['returned']and skip['r0']==1 and not denials
  policies.append(dict(node=node,ancestorHeaders=chain,sourceLocalB8=local_gate,sourceLocalC8=local_factor,originalEffectiveB8=gate_call['r0'],originalInheritedC8Word=actual_factor,originalInheritedC8=factor,localRenderBinSkipExecuted=skip is not None,renderBinResult=skip,nonzeroFactorAppliedToShaders=False))
 controls=[];root=objects[groups[0]['headerOffset']];first=objects[groups[1]['headerOffset']]
 for label,parent,child in [('null-child',root,0),('self-child',root,root),('already-parented',root,first)]:
  before=[bytes(u.mem_read(a['pointer'],a['bytes']))for a in alloc]
  r=call(0x115764,'reject-'+label,parent,child);assert r['returned']and r['r0']==0
  assert before==[bytes(u.mem_read(a['pointer'],a['bytes']))for a in alloc];controls.append(r)
 cached=[]
 for row in hierarchy:
  if 'world'not in row:continue
  fn=word(word(row['object']+4)+0x2c)
  r=call(fn-BASE,'cached-world-'+str(row['node']['headerOffset']),row['object']);assert r['returned']
  assert list(struct.unpack('<16f',bytes(u.mem_read(r['r0'],64))))==row['world'];cached.append(r)

 assert bytes(u.mem_read(0x40000000,len(scene)))==scene
 orderWitness=None
 if witness:
  child=hierarchy[1];wrong=product(expected[groups[0]['headerOffset']],local_oracle(scene,groups[1]['headerOffset']));separation=max(abs(a-b)for a,b in zip(child['world'],wrong));assert separation>1
  orderWitness=dict(reversedCompositionMaximumDelta=separation,originalFlatComposition='child-local times parent-world',notGraphicsUploadConvention=True)
 assert bytes(u.mem_read(DATA,len(data)))==data
 return dict(executedOriginalSourceRanges=source_ranges(bank,spans),propertySuffixes=suffixes,nodePolicies=policies,explicitInteriorPropertySuffixRange=[0x3fa794,0x3fa808],wholeGroupReaderExecuted=False,allSourceNodesAttachedBeforeInheritedFactorGetters=True,explicitClearCurrentCameraCallerFixture=True,billboardModes=[struct.unpack('<I',bytes(u.mem_read(objects[n['headerOffset']]+0x210,4)))[0]for n in groups if n['className']=='Billboard'],orderWitness=orderWitness,variant="declared-two-node-transform-witness"if witness else"genuine-records",sceneFixtureSha256=sha(scene),hierarchy=hierarchy,siblingChecks=sibling_checks,negativeAttachments=controls,cachedReadbacks=cached,heapFill=fill,fullStaticInitializerAttempted=full,calls=result,constantsWords=constants,declaredFreshStaticStorage=globals_,finalStaticStorage=[dict(address=a,bytes=n,hex=bytes(u.mem_read(a,n)).hex())for a,n in globals_],allocations=alloc,globalWrites=writes,denials=denials,originalInstructionsByPhase=dict(Counter(p for p,_ in visits)),originalTraceSha256=trace.hexdigest(),sourceInstructionsPatched=False,heapAllocationOnlyAdapter=True,fullCRTExecuted=False,bootMappingProven=False)