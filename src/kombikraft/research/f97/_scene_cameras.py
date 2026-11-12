"""Original Camera APIs over explicit serialized fields/world handoffs.

Property APIs receive the exact field words selected by the original reader.
The full Camera record reader/provider is not executed. Fresh unit statics,
architectural caller state and heap adapters are explicit; native fields and
callee results are not patched. Analysis aliases are not a hardware map.
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
def observe(bank,data,scene,graph,strings,models,fill):
 full=True;witness=False
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
 for at,b,flags in [(BASE,bank,UC_PROT_READ|UC_PROT_EXEC),(DATA,data,UC_PROT_READ|UC_PROT_WRITE)]:
  n=(len(b)+4095)&~4095;u.mem_map(at,n);u.mem_write(at,b);u.mem_protect(at,n,flags)
 groups=[]
 for at in range(0,len(scene)-16,4):
  n,kind,name=struct.unpack_from('<3I',scene,at)
  if kind==0x945 and str(name)in strings and 12<=n<=len(scene)-at:groups.append(dict(headerOffset=at,recordBytes=n,name=strings[str(name)],className='Camera'))
 classes={}
 for at in range(0x9bd244,0x9bd3d4,8):
  ptr,kind=struct.unpack_from('<2I',bank,at);off=ptr-BASE;classes[kind]=bank[off:bank.index(0,off)].decode('ascii')
 assert classes[0x945]=='Camera'and len(groups)==5
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
 def call(entry,name,r0=0,r1=0,r2=0,stopAt=None,floatWord=None):
  nonlocal phase,stop
  phase=name;stop=stopAt
  for i,r in enumerate(REGS):u.reg_write(r,0x44440000+i)
  for i,r in enumerate(range(UC_ARM_REG_D8,UC_ARM_REG_D15+1)):u.reg_write(r,0x3ff0000000000000+i)
  for r,v in((UC_ARM_REG_R0,r0),(UC_ARM_REG_R1,r1),(UC_ARM_REG_R2,r2),(UC_ARM_REG_SP,STACK+0x3f00),(UC_ARM_REG_LR,RET)):u.reg_write(r,v)
  if floatWord is not None:u.reg_write(UC_ARM_REG_S0,floatWord)
  error=None
  try:u.emu_start(BASE+entry,RET+4,count=100000)
  except unicorn.UcError as e:error=str(e)
  pc=u.reg_read(UC_ARM_REG_PC);returned=pc==RET
  if returned:
   assert u.reg_read(UC_ARM_REG_SP)==STACK+0x3f00 and all(u.reg_read(r)==0x44440000+i for i,r in enumerate(REGS)),name
   assert all(u.reg_read(r)==0x3ff0000000000000+i for i,r in enumerate(range(UC_ARM_REG_D8,UC_ARM_REG_D15+1))),('AAPCS-VFP callee save',name)
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
 assert len(models)==376
 cameras=[]
 for node in groups:
  result.append(call(0x1128b8,'construct-camera-'+node['name']));obj=result[-1]['r0']
  if not result[-1]['returned']:break
  assert next(a['bytes']for a in alloc if a['pointer']==obj)==0x2f0
  assert struct.unpack('<I',bytes(u.mem_read(obj+4,4)))[0]==0x51a970
  u.mem_write(0x30000000,struct.pack('<5I',0x30001000,0,0x40000000+node['headerOffset'],0,0))
  result.append(call(0x3f02a4,'read-camera-common-'+node['name'],obj,0x30000000))
  if not result[-1]['returned']:break
  result.append(call(0x115e70,'camera-world-'+node['name'],obj))
  if not result[-1]['returned']:break
  matrix=list(struct.unpack('<16f',bytes(u.mem_read(result[-1]['r0'],64))));want=local_oracle(scene,node['headerOffset']);assert max(abs(a-b)for a,b in zip(matrix,want))<1e-3
  result.append(call(0x10ce3c,'set-current-original-camera-'+node['name'],obj));assert result[-1]['returned']
  result.append(call(0x10ce4c,'get-current-original-camera-'+node['name']));assert result[-1]['returned']and result[-1]['r0']==obj
  branch=struct.unpack_from('<I',scene,node['headerOffset']+0x130)[0];assert branch in(0,1)
  holder=0x30002000;u.mem_write(holder,bytes(4))
  result.append(call(0x11f468 if branch==0 else 0x44fb30,'projection-factory-'+node['name'],holder))
  if not result[-1]['returned']:break
  projection=struct.unpack('<I',bytes(u.mem_read(holder,4)))[0];assert next(a['bytes']for a in alloc if a['pointer']==projection)==0x68
  bindings=[(0x140,0x11f56c,0x64),(0x134,0x11f51c,0x58),(0x138,0x11f534,0x5c),(0x13c,0x11f554,0x60)]if branch==0 else[(0x134,0x44fbe4,0x58),(0x138,0x44fbfc,0x5c),(0x144,0x44fc1c,0x60),(0x148,0x44fc2c,0x64)]
  for field,method,target in bindings:
   raw=struct.unpack_from('<I',scene,node['headerOffset']+field)[0]
   result.append(call(method,'projection-field-'+node['name']+'-'+hex(field),projection,floatWord=raw))
   if not result[-1]['returned']:break
   assert bytes(u.mem_read(projection+target,4))==struct.pack('<I',raw)
  if not result[-1]['returned']:break
  vt=struct.unpack('<I',bytes(u.mem_read(projection+0x50,4)))[0];assert vt==(0x51dac0 if branch==0 else 0x9f72a4)
  update=struct.unpack('<I',bytes(u.mem_read(vt+0x24,4)))[0];assert update==(0x12f584 if branch==0 else 0x45fc3c)
  result.append(call(update-BASE,'original-projection-update-'+node['name'],projection))
  if not result[-1]['returned']:break
  projectionMatrix=list(struct.unpack('<16f',bytes(u.mem_read(projection,64))));assert all(math.isfinite(v)for v in projectionMatrix)
  result.append(call(0x112a5c,'attach-projection-original-api-'+node['name'],obj,holder))
  if not result[-1]['returned']:break
  assert struct.unpack('<I',bytes(u.mem_read(obj+0x204,4)))[0]==projection
  assert struct.unpack('<I',bytes(u.mem_read(projection+0x40,4)))[0]==2
  u.mem_write(holder+4,bytes(4));result.append(call(0x113410,'release-local-projection-holder-'+node['name'],holder,holder+4));assert result[-1]['returned']and bytes(u.mem_read(holder,4))==bytes(4)and struct.unpack('<I',bytes(u.mem_read(projection+0x40,4)))[0]==1
  result.append(call(update-BASE,'repeat-projection-update-'+node['name'],projection))
  if not result[-1]['returned']:break
  assert list(struct.unpack('<16f',bytes(u.mem_read(projection,64))))==projectionMatrix
  a=0x30002100;b=0x30002110;u.mem_write(a,scene[node['headerOffset']+0xd0:node['headerOffset']+0xdc]);u.mem_write(b,scene[node['headerOffset']+0xc4:node['headerOffset']+0xd0])
  result.append(call(0x112efc,'source-camera-basis-api-'+node['name'],obj,a,b))
  if not result[-1]['returned']:break
  assert result[-1]['r0']==1
  result.append(call(0x112fc8,'original-camera-view-'+node['name'],obj))
  if not result[-1]['returned']:break
  assert result[-1]['r0']==obj+0x1c4
  viewMatrix=list(struct.unpack('<16f',bytes(u.mem_read(result[-1]['r0'],64))))
  result.append(call(0x112b2c,'original-camera-combined-'+node['name'],obj))
  if not result[-1]['returned']:break
  assert result[-1]['r0']==obj+0x208
  combinedMatrix=list(struct.unpack('<16f',bytes(u.mem_read(result[-1]['r0'],64))));combinedOracle=product(viewMatrix,projectionMatrix);combinedDelta=max(abs(a-b)for a,b in zip(combinedMatrix,combinedOracle));assert combinedDelta<1e-3
  for method,label,want in[(0x112fc8,'view',viewMatrix),(0x112b2c,'combined',combinedMatrix)]:
   result.append(call(method,'repeat-camera-'+label+'-'+node['name'],obj));assert result[-1]['returned']and list(struct.unpack('<16f',bytes(u.mem_read(result[-1]['r0'],64))))==want
  basisControls=[]
  for label,va,vb in[('zero-basis',0x30002140,b),('parallel-basis',a,a)]:
   u.mem_write(0x30002140,bytes(12));before=bytes(u.mem_read(obj,0x2f0));result.append(call(0x112efc,label+'-'+node['name'],obj,va,vb));assert result[-1]['returned']and result[-1]['r0']==0 and bytes(u.mem_read(obj,0x2f0))==before;basisControls.append(label)
  sourceField,method,_=bindings[0 if branch==0 else 2];raw=struct.unpack_from('<I',scene,node['headerOffset']+sourceField)[0];value=struct.unpack('<f',struct.pack('<I',raw))[0];fixtureWord=struct.unpack('<I',struct.pack('<f',value*1.25))[0]
  result.append(call(method,'projection-mutation-api-'+node['name'],projection,floatWord=fixtureWord));assert result[-1]['returned']
  dirtyAfterMutation=bytes(u.mem_read(obj+0x17a,1))[0]
  result.append(call(0x112b2c,'mutated-original-combined-'+node['name'],obj));assert result[-1]['returned']
  changed=list(struct.unpack('<16f',bytes(u.mem_read(result[-1]['r0'],64))));assert changed!=combinedMatrix
  result.append(call(method,'restore-source-projection-api-'+node['name'],projection,floatWord=raw));assert result[-1]['returned']
  result.append(call(0x112b2c,'restored-original-combined-'+node['name'],obj));assert result[-1]['returned']and list(struct.unpack('<16f',bytes(u.mem_read(result[-1]['r0'],64))))==combinedMatrix
  mutation=dict(callerFixtureOnly=True,sourceField=sourceField,originalWord=raw,fixtureWord=fixtureWord,originalSetter=method,sourceCameraDirtyAfterMutation=dirtyAfterMutation,changedCombined=changed,restoredSourceCombinedBitIdentical=True)
  modelProducts=[]
  for model in models:
   modelBuffer=0x30002200;outBuffer=0x30002240;u.mem_write(modelBuffer,struct.pack('<16f',*model['world']))
   result.append(call(0x127628,'original-model-camera-product-'+node['name']+'-'+str(model['owner']['meshHeaderOffset']),modelBuffer,outBuffer,obj+0x208));assert result[-1]['returned']
   nativeMvp=list(struct.unpack('<16f',bytes(u.mem_read(outBuffer,64))));oracleMvp=product(model['world'],combinedMatrix);delta=max(abs(a-b)for a,b in zip(nativeMvp,oracleMvp));assert delta<1e-3
   modelProducts.append(dict(sourceOwner=model['owner'],sourceModelWorld=model['world'],nativeModelViewProjection=nativeMvp,nativeMvpBytes=bytes(u.mem_read(outBuffer,64)).hex(),oracleMaximumDelta=delta))
  cameras.append(dict(modelProducts=modelProducts,basisRejectionControls=basisControls,projectionMutation=mutation,sourceBasisA=list(struct.unpack('<3f',bytes(u.mem_read(a,12)))),sourceBasisB=list(struct.unpack('<3f',bytes(u.mem_read(b,12)))),viewMatrix=viewMatrix,combinedMatrix=combinedMatrix,combinedOracle=combinedOracle,combinedOracleMaximumDelta=combinedDelta,projection=projection,projectionMatrix=projectionMatrix,projectionBindings=[dict(recordField=f,originalMethod=m,ownerField=t)for f,m,t in bindings],projectionReferenceCount=struct.unpack('<I',bytes(u.mem_read(projection+0x40,4)))[0],localFactoryHolderReleasedByOriginalSharedPtr=True,projectionStateHex=bytes(u.mem_read(projection,0x68)).hex(),record=node,object=obj,world=matrix,ownerBytes=bytes(u.mem_read(obj,0x2f0)).hex(),sourceProjectionBranchRaw=struct.unpack_from('<I',scene,node['headerOffset']+0x130)[0],actualSpecificReaderExecuted=False))
 assert len(cameras)==5 and not denials,(len(cameras),denials,result[-1])
 result.append(call(0x10ce3c,'clear-current-camera-after-actual-objects',0));assert result[-1]['returned']
 provider=None
 return dict(executedOriginalSourceRanges=source_ranges(bank,spans),stopPC=u.reg_read(UC_ARM_REG_PC),stopRegisters={name:u.reg_read(r)for name,r in[('r0',UC_ARM_REG_R0),('r1',UC_ARM_REG_R1),('r2',UC_ARM_REG_R2),('r3',UC_ARM_REG_R3),('sp',UC_ARM_REG_SP),('lr',UC_ARM_REG_LR),('cpsr',UC_ARM_REG_CPSR)]},lastSourceVisits=visits[-32:],stopOriginalBytes=bank[u.reg_read(UC_ARM_REG_PC)-BASE-8:u.reg_read(UC_ARM_REG_PC)-BASE+8].hex(),cameras=cameras,calls=result,providerConstructor=provider,allocations=alloc,globalWrites=writes,denials=denials,originalInstructionsByPhase=dict(Counter(p for p,_ in visits)),originalTraceSha256=trace.hexdigest(),freshStaticStorage=globals_,fullCameraRecordReaderExecuted=False,projectionFactoryExecuted=True,hostSourceFieldOrReturnPatches=False,heapAllocationOnlyAdapter=True,carContact=False)