"""Original Texture constructor/reader prefix to its image-cache factory.

Original code, including lists, callback registration, name selection, type
classification and memcpy, runs unchanged. Only allocation and free wrappers
are replaced. The provider vtable is a declared caller input, with original source methods. The provider constructor and resource cache factory do not run. This is a resource-reader unit; it does not initialize the real
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


def observe(bank,scene,nor,pool,texture,fill,flag):
    record=texture['record'];header=record['headerOffset']
    data=bytearray(scene)
    assert struct.unpack_from('<I',data,header+4)[0]==0xa46
    assert data[header+0x84]==0
    data[header+0x84]=flag
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
    u.mem_write(HEADER+0x414,struct.pack('<I',NOR+pool))
    u.mem_write(HEADER+0x10c,struct.pack('<I',SCENE-12))  # encoded origin includes omitted 12-byte prefix
    u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
    u.mem_write(CONTEXT+0x1c,struct.pack('<I',0x9ccf48))  # explicit source-vtable caller fixture; provider constructor not run
    sp=STACK+0x4000
    for i,r in enumerate(CALLEE):u.reg_write(r,0x44440000+i)
    allocations,freed,visits,memcpys=[],[],[],[]
    trace=hashlib.sha256();phase='constructor';next_at=HEAP;boundary={}

    def live(address,n):
        return any(a['pointer'] <= address and address+n <= a['pointer']+a['backingBytes'] and a['pointer'] not in freed for a in allocations)

    def code(uc,address,length,_):
        nonlocal next_at
        if address==RETURN:uc.emu_stop();return
        if phase=='reader' and address==BASE+0x3d3db0:
            boundary['cacheObjectMatches']=uc.reg_read(UC_ARM_REG_R0)==CONTEXT+0x3ac
            ptr=uc.reg_read(UC_ARM_REG_R2);assert live(ptr,1)
            raw=bytearray()
            while True:
                assert live(ptr+len(raw),1)
                v=uc.mem_read(ptr+len(raw),1)[0]
                if not v:break
                raw.append(v)
            boundary['key']=raw.decode()
            uc.emu_stop();return
        off=address-BASE
        assert 0 <= off and off+length <= len(bank),hex(address)
        if off==0x128498:
            n=uc.reg_read(UC_ARM_REG_R0);assert 0<n<=4096,n
            ptr=next_at;next_at=(ptr+n+15)&~15;assert next_at<=HEAP+0x10000
            capacity=(n+3)&~3
            uc.mem_write(ptr,bytes([fill])*capacity)
            allocations.append({'phase':phase,'pointer':ptr,'bytes':n,'backingBytes':capacity,'callerOffset':(uc.reg_read(UC_ARM_REG_LR)&~1)-BASE-4})
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
    def call(entry):
        u.reg_write(UC_ARM_REG_R0,OBJECT);u.reg_write(UC_ARM_REG_R1,DESC)
        u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,RETURN)
        try:
            u.emu_start(BASE+entry,RETURN+4,count=100000)
        except unicorn.UcError as error:
            raise AssertionError({'phase':phase,'sourcePcOffset':hex(u.reg_read(UC_ARM_REG_PC)-BASE),
                'registers':[hex(u.reg_read(r)) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)],
                'lastOriginalOffsets':[hex(o) for _,o in visits[-8:]],'error':str(error)}) from error
        if phase=='constructor':
            assert u.reg_read(UC_ARM_REG_PC)==RETURN and u.reg_read(UC_ARM_REG_SP)==sp
            assert all(u.reg_read(r)==0x44440000+i for i,r in enumerate(CALLEE))
        else:assert u.reg_read(UC_ARM_REG_PC)==BASE+0x3d3db0
        return u.reg_read(UC_ARM_REG_R0)
    assert call(0x1195b8)==OBJECT
    phase='reader'
    call(0x3ef378)
    assert boundary=={'cacheObjectMatches':True,'key':texture['bitmapResourceName']+'/'+str(flag)}
    assert bytes(u.mem_read(SCENE,len(data)))==bytes(data)
    return {'bitmapResourceName':texture['bitmapResourceName'],'recordHeaderOffset':header,'heapFill':fill,
        'sourceFlagFixture':flag,'sourceFlagMutated':flag!=0,'originalCacheBoundary':boundary,
        'originalConstructorInstructions':sum(p=='constructor' for p,_ in visits),
        'originalReaderPrefixInstructions':sum(p=='reader' for p,_ in visits),
        'originalProviderPathResolverCalls':sum(off==0x3c2528 for _,off in visits),
        'allocations':allocations,'freed':freed,'originalMemcpyCalls':memcpys,'traceSha256':trace.hexdigest()}
