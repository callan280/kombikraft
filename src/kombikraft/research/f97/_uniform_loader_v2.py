"""Version2: original UniformSetter reader and actual C-string name lookup.

Original code, including lists, callback registration, name selection, type
classification and memcpy, runs unchanged. Only allocation and free wrappers
are replaced. This is a resource-reader unit; it does not initialize the real
heap, scene or graphics driver. The observed linked +10000h mapping permits
original absolute callback pointers and does not prove a physical memory map.
"""
from pathlib import Path
import hashlib
import json
import struct
import unicorn
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_PROT_READ,UC_PROT_WRITE,UC_PROT_EXEC
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,
    UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,
    UC_ARM_REG_C1_C0_2,UC_ARM_REG_FPEXC)

H=Path(__file__).resolve().parent
BASE=0x10000
OBJECT,DESC,STREAM,HEADER,HOLDER,CONTEXT=0x30000000,0x30001000,0x30002000,0x30003000,0x30004000,0x30005000
HEAP,STACK,SCENE,NOR,RETURN=0x31000000,0x33000000,0x40000000,0x50000000,0x70000000
sha=lambda b:hashlib.sha256(b).hexdigest()
CALLEE=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]


def observe(bank,scene,nor,pool,row,fill,value):
    record=row['parameterSetter'];header=record['headerOffset']
    assert struct.unpack_from('<3I',scene,header+0x50)==(16,0x73d80,0)
    assert struct.unpack_from('<f',scene,header+0x5c)[0]==1
    data=bytearray(scene)
    if value != 1:struct.pack_into('<f',data,header+0x5c,value)
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    size=(len(bank)+4095)&~4095
    u.mem_map(BASE,size);u.mem_write(BASE,bank);u.mem_protect(BASE,size,UC_PROT_READ|UC_PROT_EXEC)
    u.mem_map(OBJECT,0x6000,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_write(OBJECT,bytes([0xa5])*0x100)
    u.mem_map(HEAP,0x10000,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_map(STACK,0x4000,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_map(SCENE,(len(data)+4095)&~4095,UC_PROT_READ);u.mem_write(SCENE,bytes(data))
    u.mem_map(NOR,(len(nor)+4095)&~4095,UC_PROT_READ);u.mem_write(NOR,nor)
    u.mem_map(RETURN,4096,UC_PROT_READ|UC_PROT_EXEC)
    u.mem_write(DESC,struct.pack('<5I',STREAM,0,SCENE+header,HEADER+0x100,CONTEXT))
    u.mem_write(STREAM+0x10,struct.pack('<I',HOLDER));u.mem_write(HOLDER,struct.pack('<I',HEADER))
    u.mem_write(HEADER+0x414,struct.pack('<I',NOR+pool+8))
    u.mem_write(HEADER+0x10c,struct.pack('<I',SCENE-12))  # encoded origin includes omitted 12-byte prefix
    u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
    sp=STACK+0x4000
    for i,r in enumerate(CALLEE):u.reg_write(r,0x44440000+i)
    allocations,freed,visits,memcpys=[],[],[],[]
    trace=hashlib.sha256();phase='constructor';next_at=HEAP

    def live(address,n):
        return any(a['pointer'] <= address and address+n <= a['pointer']+a['bytes'] and a['pointer'] not in freed for a in allocations)

    def code(uc,address,length,_):
        nonlocal next_at
        if address==RETURN:uc.emu_stop();return
        off=address-BASE
        assert 0 <= off and off+length <= len(bank),hex(address)
        if off==0x128498:
            n=uc.reg_read(UC_ARM_REG_R0);assert 0<n<=4096,n
            ptr=next_at;next_at=(ptr+n+15)&~15;assert next_at<=HEAP+0x10000
            uc.mem_write(ptr,bytes([fill])*n)
            allocations.append({'phase':phase,'pointer':ptr,'bytes':n,'callerOffset':(uc.reg_read(UC_ARM_REG_LR)&~1)-BASE-4})
            uc.reg_write(UC_ARM_REG_R0,ptr);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
        if off==0x1284c4 and uc.reg_read(UC_ARM_REG_R0):
            ptr=uc.reg_read(UC_ARM_REG_R0);assert any(a['pointer']==ptr for a in allocations) and ptr not in freed,hex(ptr)
            freed.append(ptr);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
        if off==0x195950:
            memcpys.append({'destination':uc.reg_read(UC_ARM_REG_R0),'source':uc.reg_read(UC_ARM_REG_R1),'bytes':uc.reg_read(UC_ARM_REG_R2)})
        visits.append((phase,off));trace.update(phase.encode()+struct.pack('<I',off)+bank[off:off+length])

    def access(uc,kind,address,n,value,_):
        rw=(OBJECT<=address and address+n<=OBJECT+0x6000) or (STACK<=address and address+n<=STACK+0x4000) or live(address,n)
        if kind==unicorn.UC_MEM_WRITE:assert rw,(hex(uc.reg_read(UC_ARM_REG_PC)-BASE),hex(address),n)
        else:assert rw or (BASE<=address and address+n<=BASE+len(bank)) or (SCENE<=address and address+n<=SCENE+len(data)) or (NOR<=address and address+n<=NOR+len(nor)),(hex(uc.reg_read(UC_ARM_REG_PC)-BASE),hex(address),n)

    u.hook_add(unicorn.UC_HOOK_CODE,code);u.hook_add(unicorn.UC_HOOK_MEM_READ|unicorn.UC_HOOK_MEM_WRITE,access)
    def call(entry, argument=DESC):
        u.reg_write(UC_ARM_REG_R0,OBJECT);u.reg_write(UC_ARM_REG_R1,argument)
        u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,RETURN)
        try:
            u.emu_start(BASE+entry,RETURN+4,count=100000)
        except unicorn.UcError as error:
            raise AssertionError({'phase':phase,'sourcePcOffset':hex(u.reg_read(UC_ARM_REG_PC)-BASE),
                'registers':[hex(u.reg_read(r)) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)],
                'lastOriginalOffsets':[hex(o) for _,o in visits[-8:]],'error':str(error)}) from error
        assert u.reg_read(UC_ARM_REG_PC)==RETURN and u.reg_read(UC_ARM_REG_SP)==sp
        assert all(u.reg_read(r)==0x44440000+i for i,r in enumerate(CALLEE))
        return u.reg_read(UC_ARM_REG_R0)
    assert call(0x11c640)==OBJECT
    phase='reader'
    assert call(0x3ee5d8)==1
    count,node=struct.unpack('<2I',bytes(u.mem_read(OBJECT+0x14,8)))
    assert count==1 and live(node,20)
    link,num,typ,name,pixels=struct.unpack('<5I',bytes(u.mem_read(node,20)))
    assert link==0 and num==1 and typ==0 and name==NOR+pool+8+0x73d80-6
    assert live(pixels,4)
    got=bytes(u.mem_read(pixels,4));assert got==struct.pack('<f',value)
    assert bytes(u.mem_read(name,8))==b'oparam0\0'
    phase='native-name-lookup'
    query=OBJECT+0x5000;u.mem_write(query,b'oparam0\0')
    assert call(0x11dd24,query)==node
    assert bytes(u.mem_read(pixels,4))==got
    assert bytes(u.mem_read(SCENE,len(data)))==bytes(data)
    return {'appearance':row['appearance']['name'],'recordHeaderOffset':header,'heapFill':fill,
        'uniformValueFixture':value,'sourceValueMutated':value!=1,'name':'oparam0','typeTag':typ,'elementCount':num,
        'uniformBytesHex':got.hex(),'originalConstructorInstructions':sum(p=='constructor' for p,_ in visits),
        'originalReaderInstructions':sum(p=='reader' for p,_ in visits),'allocations':allocations,'freed':freed,
        'originalMemcpyCalls':memcpys,'traceSha256':trace.hexdigest(),
        'nativeCStringNameVerified':True,'sourcePoolOriginAdjustment':8,'originalNameLookupExecuted':True,
        'originalNameLookupInstructions':sum(p=='native-name-lookup'for p,_ in visits),
        'calleeRegistersPreserved':True,'stackPointerPreserved':True}


def _name_case(bank,scene,nor,pool,row,fill,origin):
    record=row['uniformSetter'];header=record['headerOffset']
    data=bytearray(scene)
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    size=(len(bank)+4095)&~4095
    u.mem_map(BASE,size);u.mem_write(BASE,bank);u.mem_protect(BASE,size,UC_PROT_READ|UC_PROT_EXEC)
    u.mem_map(OBJECT,0x6000,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_write(OBJECT,bytes([0xa5])*0x100)
    u.mem_map(HEAP,0x10000,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_map(STACK,0x4000,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_map(SCENE,(len(data)+4095)&~4095,UC_PROT_READ);u.mem_write(SCENE,bytes(data))
    u.mem_map(NOR,(len(nor)+4095)&~4095,UC_PROT_READ);u.mem_write(NOR,nor)
    u.mem_map(RETURN,4096,UC_PROT_READ|UC_PROT_EXEC)
    u.mem_write(DESC,struct.pack('<5I',STREAM,0,SCENE+header,HEADER+0x100,CONTEXT))
    u.mem_write(STREAM+0x10,struct.pack('<I',HOLDER));u.mem_write(HOLDER,struct.pack('<I',HEADER))
    u.mem_write(HEADER+0x414,struct.pack('<I',NOR+pool+origin))
    u.mem_write(HEADER+0x10c,struct.pack('<I',SCENE-12))  # encoded origin includes omitted 12-byte prefix
    u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
    sp=STACK+0x4000
    for i,r in enumerate(CALLEE):u.reg_write(r,0x44440000+i)
    allocations,freed,visits,memcpys=[],[],[],[]
    trace=hashlib.sha256();phase='constructor';next_at=HEAP

    def live(address,n):
        return any(a['pointer'] <= address and address+n <= a['pointer']+a['bytes'] and a['pointer'] not in freed for a in allocations)

    def code(uc,address,length,_):
        nonlocal next_at
        if address==RETURN:uc.emu_stop();return
        off=address-BASE
        assert 0 <= off and off+length <= len(bank),hex(address)
        if off==0x128498:
            n=uc.reg_read(UC_ARM_REG_R0);assert 0<n<=4096,n
            ptr=next_at;next_at=(ptr+n+15)&~15;assert next_at<=HEAP+0x10000
            uc.mem_write(ptr,bytes([fill])*n)
            allocations.append({'phase':phase,'pointer':ptr,'bytes':n,'callerOffset':(uc.reg_read(UC_ARM_REG_LR)&~1)-BASE-4})
            uc.reg_write(UC_ARM_REG_R0,ptr);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
        if off==0x1284c4 and uc.reg_read(UC_ARM_REG_R0):
            ptr=uc.reg_read(UC_ARM_REG_R0);assert any(a['pointer']==ptr for a in allocations) and ptr not in freed,hex(ptr)
            freed.append(ptr);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
        if off==0x195950:
            memcpys.append({'destination':uc.reg_read(UC_ARM_REG_R0),'source':uc.reg_read(UC_ARM_REG_R1),'bytes':uc.reg_read(UC_ARM_REG_R2)})
        visits.append((phase,off));trace.update(phase.encode()+struct.pack('<I',off)+bank[off:off+length])

    def access(uc,kind,address,n,value,_):
        rw=(OBJECT<=address and address+n<=OBJECT+0x6000) or (STACK<=address and address+n<=STACK+0x4000) or live(address,n)
        if kind==unicorn.UC_MEM_WRITE:assert rw,(hex(uc.reg_read(UC_ARM_REG_PC)-BASE),hex(address),n)
        else:assert rw or (BASE<=address and address+n<=BASE+len(bank)) or (SCENE<=address and address+n<=SCENE+len(data)) or (NOR<=address and address+n<=NOR+len(nor)),(hex(uc.reg_read(UC_ARM_REG_PC)-BASE),hex(address),n)

    u.hook_add(unicorn.UC_HOOK_CODE,code);u.hook_add(unicorn.UC_HOOK_MEM_READ|unicorn.UC_HOOK_MEM_WRITE,access)
    def call(entry, argument=DESC):
        u.reg_write(UC_ARM_REG_R0,OBJECT);u.reg_write(UC_ARM_REG_R1,argument)
        u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,RETURN)
        try:
            u.emu_start(BASE+entry,RETURN+4,count=100000)
        except unicorn.UcError as error:
            raise AssertionError({'phase':phase,'sourcePcOffset':hex(u.reg_read(UC_ARM_REG_PC)-BASE),
                'registers':[hex(u.reg_read(r)) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)],
                'lastOriginalOffsets':[hex(o) for _,o in visits[-8:]],'error':str(error)}) from error
        assert u.reg_read(UC_ARM_REG_PC)==RETURN and u.reg_read(UC_ARM_REG_SP)==sp
        assert all(u.reg_read(r)==0x44440000+i for i,r in enumerate(CALLEE))
        return u.reg_read(UC_ARM_REG_R0)
    assert call(0x11c640)==OBJECT
    phase='reader'
    assert call(0x3ee5d8)==1
    count,node=struct.unpack('<2I',bytes(u.mem_read(OBJECT+0x14,8)))
    source_count=struct.unpack_from('<I',scene,header+0x48)[0]
    assert source_count==4
    expected={};source_entries=[]
    for i in range(source_count):
        at=struct.unpack_from('<I',scene,header+0x4c+i*4)[0]-12
        n,name_ref,tag=struct.unpack_from('<3I',scene,at)
        assert tag==0 and n==16
        ptr=NOR+pool+name_ref+2
        text=bytes(u.mem_read(ptr,256)).split(b'\0',1)[0].decode('ascii')
        expected[text]=scene[at+12:at+n].hex()
    assert set(expected)=={'u_eco','oparam0','u_SLDLimit','u_SLDActive'}
    assert expected['u_SLDLimit']=='0000803f' and expected['u_SLDActive']=='00000000'
    phase='native-name-lookup';lookups=[]
    for text in ('u_SLDActive','u_SLDLimit'):
        query=OBJECT+0x5100;u.mem_write(query,text.encode()+b'\0')
        found=call(0x11dd24,query)
        result=None
        if found:
            assert live(found,20)
            _,num,typ,name,pixels=struct.unpack('<5I',bytes(u.mem_read(found,20)))
            assert num==1 and typ==0 and live(pixels,4)
            result=bytes(u.mem_read(pixels,4)).hex()
            assert bytes(u.mem_read(name,len(text)+1))==text.encode()+b'\0'
        lookups.append(dict(name=text,found=bool(found),valueHex=result,expectedValueHex=expected[text]))
    if origin==8:
        assert count==4 and all(r['found']and r['valueHex']==r['expectedValueHex']for r in lookups)
    else:
        assert origin==0 and count==3 and not any(r['found']for r in lookups)
    assert bytes(u.mem_read(SCENE,len(data)))==bytes(data)
    assert bytes(u.mem_read(NOR,len(nor)))==nor
    return dict(recordHeaderOffset=header,heapFill=fill,callerPoolOriginAdjustment=origin,
        acceptedCallerFixture=origin==8,rejectedRawOriginWitness=origin==0,
        sourceEntryCount=source_count,nativeEntryCount=count,originalNameLookupResults=lookups,
        originalInstructionsByPhase={p:sum(q==p for q,_ in visits)for p in ('constructor','reader','native-name-lookup')},
        originalTraceSha256=trace.hexdigest(),calleeRegistersPreserved=True,stackPointerPreserved=True,
        kernelOrProviderResultsAdapted=False,sourceInstructionsModified=False)


def name_regressions(bank,scene,nor,pool):
    """Two fills × correct/raw caller origin; all four runs execute originals.

    The one genuine ECO source record has four scalar entries. Actual original
    list lookup with a separately allocated query string must distinguish
    u_SLDActive0 from u_SLDLimit1. The raw-origin negative remains rejected.
    """
    from . import PROFILE
    for role,data in (('bank',bank),('scene',scene),('nor',nor)):
        if sha(data)!=PROFILE[role]:raise ValueError(role+': unsupported source hash')
    header=142732
    size,kind,_=struct.unpack_from('<3I',scene,header)
    assert kind==0xa44 and size==156 and struct.unpack_from('<I',scene,header+0x48)[0]==4
    row={'uniformSetter':{'headerOffset':header},'appearance':{'name':'source-ECO-uniform-name-regression'}}
    return [_name_case(bank,scene,nor,pool,row,fill,origin)for fill in (0,0xa5)for origin in (8,0)]
