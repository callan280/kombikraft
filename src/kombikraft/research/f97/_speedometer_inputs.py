"""Original F97 speedometer input callbacks -> parameter calculation unit.

Datastore IDs remain internal source IDs, not CAN identifiers or named driving
modes. Owner state/payloads are explicit fixtures; no widget lifecycle, scene
property application, event scheduler, kernel or display driver is simulated.
"""
from pathlib import Path
import hashlib,json,struct
import unicorn
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_PROT_READ,UC_PROT_WRITE,UC_PROT_EXEC
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R4,
    UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,
    UC_ARM_REG_R11,UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_C1_C0_2,UC_ARM_REG_FPEXC)

BASE,OBJECT,PAYLOAD,STACK,RETURN=0x10000,0x30000000,0x31000000,0x33000000,0x70000000
CALLEE=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
sha=lambda b:hashlib.sha256(b).hexdigest()
f32=lambda n:struct.unpack('<f',struct.pack('<f',n))[0]


def observe(bank,variant,selector,raw,fill):
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM);size=(len(bank)+4095)&~4095
    u.mem_map(BASE,size);u.mem_write(BASE,bank);u.mem_protect(BASE,size,UC_PROT_READ|UC_PROT_EXEC)
    u.mem_map(OBJECT,4096,UC_PROT_READ|UC_PROT_WRITE);u.mem_write(OBJECT,bytes([fill])*0x8c)
    u.mem_write(OBJECT,struct.pack('<I',0x7d49d8));u.mem_write(OBJECT+0x18,b'\0\0')
    u.mem_map(PAYLOAD,4096,UC_PROT_READ);u.mem_map(STACK,4096,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_map(RETURN,4096,UC_PROT_READ|UC_PROT_EXEC)
    u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
    visits=[];writes=[];trace=hashlib.sha256();phase='';sp=STACK+0xe00
    def code(uc,at,n,_):
        if at==RETURN:uc.emu_stop();return
        off=at-BASE;assert 0<=off and off+n<=len(bank)
        visits.append((phase,off));trace.update(phase.encode()+struct.pack('<I',off)+bank[off:off+n])
    def access(uc,kind,at,n,val,_):
        writable=(OBJECT<=at and at+n<=OBJECT+0x8c) or (STACK<=at and at+n<=STACK+4096)
        if kind==unicorn.UC_MEM_WRITE:
            assert writable,(hex(uc.reg_read(UC_ARM_REG_PC)-BASE),hex(at))
            if OBJECT<=at<OBJECT+0x8c:writes.append({'phase':phase,'offset':at-OBJECT,'bytes':n,'value':val})
        else:assert writable or (BASE<=at and at+n<=BASE+len(bank)) or (PAYLOAD<=at and at+n<=PAYLOAD+2)
    u.hook_add(unicorn.UC_HOOK_CODE,code);u.hook_add(unicorn.UC_HOOK_MEM_READ|unicorn.UC_HOOK_MEM_WRITE,access)
    def call(entry,name,r1=0,r2=0):
        nonlocal phase
        phase=name
        for i,r in enumerate(CALLEE):u.reg_write(r,0x44440000+i)
        for r,v in ((UC_ARM_REG_R0,OBJECT),(UC_ARM_REG_R1,r1),(UC_ARM_REG_R2,r2),(UC_ARM_REG_SP,sp),(UC_ARM_REG_LR,RETURN)):u.reg_write(r,v)
        u.emu_start(BASE+entry,RETURN+4,count=4096)
        assert u.reg_read(UC_ARM_REG_PC)==RETURN and u.reg_read(UC_ARM_REG_SP)==sp
        assert all(u.reg_read(r)==0x44440000+i for i,r in enumerate(CALLEE))
    inputs=[(0x293,1,variant),(0x3a8,1,selector),(0x3a9,2,raw[0]),(0x3aa,2,raw[1]),(0x3ab,2,raw[2])]
    vtable_entry=struct.unpack_from('<I',bank,0x7c49d8+0x74)[0]
    assert vtable_entry==0x34b03d
    for key,width,value in inputs:
        u.mem_write(PAYLOAD,value.to_bytes(width,'little')+b'\xa5'*(2-width))
        call(vtable_entry-BASE,'input-'+hex(key),key,PAYLOAD)
    before=bytes(u.mem_read(OBJECT,0x8c))
    assert before[0x1a]==int(variant>=5) and before[0x22]==selector
    assert struct.unpack_from('<3H',before,0x1c)==tuple(raw)
    assert struct.unpack_from('<H',before,0x18)[0]==0x28
    call(0x33aa95,'parameter-calculation')
    after=bytes(u.mem_read(OBJECT,0x8c));out=list(struct.unpack_from('<6f',after,0x2c))
    if variant<5:want=[0,0,f32(1.2),0,1,0]
    else:
        r=[f32(x/41600) for x in raw]
        if selector in (1,3):want=[r[1],r[2],r[0],r[0],0.5,1]
        elif selector==2:want=[r[1],r[2],f32(1.2),r[0],1,0]
        else:want=[r[1],r[2],f32(1.2),f32(1.2),1,1]
    assert out==want,(variant,selector,raw,out,want)
    assert after[:0x2c]==before[:0x2c] and after[0x44:]==before[0x44:]
    return {'variantInput':variant,'selectorInput':selector,'rawU16Inputs':list(raw),'ownerFill':fill,
        'inputEvents':[{'internalDatastoreId':key,'payloadBytes':width,'value':v} for key,width,v in inputs],
        'activeThresholdResult':int(variant>=5),'dirtyMask':0x28,'outputOffsets':list(range(0x2c,0x44,4)),
        'outputFloat32':out,'originalOwnerWrites':writes,
        'originalInstructionCounts':{p:sum(x==p for x,_ in visits) for p in dict.fromkeys(x for x,_ in visits)},
        'originalTraceSha256':trace.hexdigest(),'calleeRegistersAndStackPreserved':True,
        'calculationOnlyChangesSixFloatFields':True}
