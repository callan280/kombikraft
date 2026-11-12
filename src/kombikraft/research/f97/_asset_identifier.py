"""Run the original identifier parser on extracted M-ring bitmap paths.

Only allocation/free wrappers use a declared host heap. This does not register
or fetch a resource and does not construct a DefaultAssetProvider.
"""
from pathlib import Path
import hashlib,json,struct
import unicorn
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_PROT_READ,UC_PROT_WRITE,UC_PROT_EXEC
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC)

H=Path(__file__).resolve().parent
BASE,OBJECT,HEAP,STACK,SCENE,RETURN=0x10000,0x30000000,0x31000000,0x33000000,0x40000000,0x70000000
sha=lambda b:hashlib.sha256(b).hexdigest()


def observe(bank,scene,texture,fill):
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    size=(len(bank)+4095)&~4095
    u.mem_map(BASE,size);u.mem_write(BASE,bank);u.mem_protect(BASE,size,UC_PROT_READ|UC_PROT_EXEC)
    u.mem_map(OBJECT,4096,UC_PROT_READ|UC_PROT_WRITE);u.mem_write(OBJECT,bytes([0xa5])*20)
    u.mem_map(HEAP,0x10000,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_map(STACK,4096,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_map(SCENE,(len(scene)+4095)&~4095,UC_PROT_READ);u.mem_write(SCENE,scene)
    u.mem_map(RETURN,4096,UC_PROT_READ|UC_PROT_EXEC)
    input_at=texture['bitmapPathOffset'];end=scene.index(0,input_at)
    path=scene[input_at:end].decode();assert path=='/Bitmap:'+texture['bitmapResourceName']
    allocations,freed,visits=[],[],[];next_at=HEAP;trace=hashlib.sha256();phase='parse'
    def live(address,n):return any(a['pointer']<=address and address+n<=a['pointer']+a['bytes'] and a['pointer'] not in freed for a in allocations)
    def code(uc,address,length,_):
        nonlocal next_at
        if address==RETURN:uc.emu_stop();return
        off=address-BASE;assert 0<=off and off+length<=len(bank),hex(address)
        if off==0x128498:
            n=uc.reg_read(UC_ARM_REG_R0);assert 0<n<=4096,n
            ptr=next_at;next_at=(ptr+n+15)&~15;assert next_at<=HEAP+0x10000
            uc.mem_write(ptr,bytes([fill])*n);allocations.append({'pointer':ptr,'bytes':n})
            uc.reg_write(UC_ARM_REG_R0,ptr);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
        if off==0x1284c4 and uc.reg_read(UC_ARM_REG_R0):
            ptr=uc.reg_read(UC_ARM_REG_R0);assert any(a['pointer']==ptr for a in allocations) and ptr not in freed
            freed.append(ptr);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
        visits.append((phase,off));trace.update(phase.encode()+struct.pack('<I',off)+bank[off:off+length])
    def access(uc,kind,address,n,value,_):
        rw=(OBJECT<=address and address+n<=OBJECT+20) or (STACK<=address and address+n<=STACK+4096) or live(address,n)
        if kind==unicorn.UC_MEM_WRITE:assert rw,(hex(uc.reg_read(UC_ARM_REG_PC)-BASE),hex(address))
        else:assert rw or (BASE<=address and address+n<=BASE+len(bank)) or (SCENE<=address and address+n<=SCENE+len(scene)),(hex(uc.reg_read(UC_ARM_REG_PC)-BASE),hex(address))
    u.hook_add(unicorn.UC_HOOK_CODE,code);u.hook_add(unicorn.UC_HOOK_MEM_READ|unicorn.UC_HOOK_MEM_WRITE,access)
    def call(entry,r1):
        u.reg_write(UC_ARM_REG_R0,OBJECT);u.reg_write(UC_ARM_REG_R1,r1)
        u.reg_write(UC_ARM_REG_SP,STACK+4096);u.reg_write(UC_ARM_REG_LR,RETURN)
        try:u.emu_start(BASE+entry,RETURN+4,count=100000)
        except unicorn.UcError as e:raise AssertionError({'pc':hex(u.reg_read(UC_ARM_REG_PC)-BASE),'last':[hex(o) for _,o in visits[-8:]]}) from e
        assert u.reg_read(UC_ARM_REG_PC)==RETURN and u.reg_read(UC_ARM_REG_SP)==STACK+4096
        return u.reg_read(UC_ARM_REG_R0)
    assert call(0x3d7f68,SCENE+input_at)==OBJECT
    descriptor=bytes(u.mem_read(OBJECT,20));count=struct.unpack_from('<H',descriptor,2)[0]
    assert descriptor[0]==1 and count==1
    phase='type';typ=call(0x3d8084,0);assert typ==7,hex(typ)
    phase='name';nameptr=call(0x3d8014,0);assert live(nameptr,len(texture['bitmapResourceName'])+1)
    name=bytes(u.mem_read(nameptr,len(texture['bitmapResourceName'])+1));assert name==texture['bitmapResourceName'].encode()+b'\0'
    assert bytes(u.mem_read(SCENE,len(scene)))==scene
    phase='release';call(0x3d7f28,2)
    assert set(freed)=={a['pointer'] for a in allocations}
    return {'inputPath':path,'sourcePathOffset':input_at,'heapFill':fill,'componentCount':count,
        'originalResolvedType':typ,'originalResolvedName':name[:-1].decode(),'allocations':allocations,
        'allAllocationsFreed':True,'originalInstructions':len(visits),'traceSha256':trace.hexdigest(),
        'sourceSceneUnchanged':True}
