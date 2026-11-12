"""Original resident bitmap -> real image attachment -> filtering unit.

Fresh-zero selected globals are explicit single-thread unit inputs. Original
thread-manager initialization and destructor registration execute using the
unaltered initialized-data bank. Only heap allocation is adapted. This does not
execute provider/cache startup, resource lookup, kernel, or the GPU implementation.
"""
from pathlib import Path
import hashlib,json,struct
import unicorn
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_PROT_READ,UC_PROT_WRITE,UC_PROT_EXEC
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,
    UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,
    UC_ARM_REG_C1_C0_2,UC_ARM_REG_FPEXC)

BASE,DATA,DESC,OWNER,HOLDER,OBJECT=0x10000,0xf00000,0x30000000,0x30001000,0x30002000,0x30003000
NODE,HEAP,STACK,RETURN=0x40000000,0x31000000,0x33000000,0x70000000
HEAD,THREAD,RECORD=0x103f53c,0x1062418,0xf1f22c
CALLEE=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
sha=lambda b:hashlib.sha256(b).hexdigest()


def observe(bank,initialized,raw,texture,fill):
    _,width,height,fmt,component,alignment,mips,flag,n=struct.unpack_from('<9I',raw)
    assert len(raw)==36+n and n==width*height*4 and (fmt,component,alignment,mips)==(1,0,1,0xffffffff)
    node=struct.pack('<3I',len(raw)+12,7,0)+raw
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    def mapped(at,data,perms):
        u.mem_map(at,(len(data)+4095)&~4095);u.mem_write(at,data);u.mem_protect(at,(len(data)+4095)&~4095,perms)
    mapped(BASE,bank,UC_PROT_READ|UC_PROT_EXEC)
    mapped(DATA,initialized,UC_PROT_READ|UC_PROT_WRITE)
    mapped(NODE,node,UC_PROT_READ)
    u.mem_map(DESC,0x4000,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_map(HEAP,0x200000,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_map(STACK,0x4000,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_map(RETURN,4096,UC_PROT_READ|UC_PROT_EXEC)
    u.mem_map(HEAD&~4095,4096,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_map(THREAD&~4095,4096,UC_PROT_READ|UC_PROT_WRITE)
    u.mem_write(DESC,struct.pack('<4I',OWNER+0x800,0,NODE,OWNER))
    u.mem_write(OWNER+0xc,struct.pack('<I',NODE));u.mem_write(OWNER+0x20,struct.pack('<I',1))
    u.mem_write(OBJECT,bytes([fill])*0xd8)
    assert initialized[RECORD-DATA:RECORD-DATA+12]==struct.pack('<3I',0,THREAD,0x10efe8)
    u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
    sp=STACK+0x3f00;phase='';stop=None;next_at=HEAP
    allocations,visits,memcpys,global_writes=[],[],[],[];trace=hashlib.sha256();boundary={}
    def live(at,count):return any(a['pointer']<=at and at+count<=a['pointer']+a['bytes'] for a in allocations)
    def fresh_global(at,count):return (HEAD<=at and at+count<=HEAD+4) or (THREAD<=at and at+count<=THREAD+0x28)
    def code(uc,address,length,_):
        nonlocal next_at
        if address==RETURN or address==stop:
            if phase=='minification':boundary['filter']=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
            if phase=='upload':
                boundary['upload']=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]+list(struct.unpack('<5I',bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_SP),20))))
            uc.emu_stop();return
        off=address-BASE;assert 0<=off and off+length<=len(bank),hex(address)
        if off==0x128498:
            count=uc.reg_read(UC_ARM_REG_R0);assert count in (n,52,0x5c)
            ptr=next_at;next_at=(ptr+count+15)&~15;assert next_at<=HEAP+0x200000
            allocations.append({'pointer':ptr,'bytes':count,'phase':phase});uc.mem_write(ptr,bytes([fill])*count)
            uc.reg_write(UC_ARM_REG_R0,ptr);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
        if off==0x195950:memcpys.append([uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)])
        visits.append((phase,off));trace.update(phase.encode()+struct.pack('<I',off)+bank[off:off+length])
    def access(uc,kind,at,count,value,_):
        caller=(DESC<=at and at+count<=DESC+0x4000) or (STACK<=at and at+count<=STACK+0x4000) or live(at,count)
        if kind==unicorn.UC_MEM_WRITE:
            assert caller or fresh_global(at,count) or (RECORD<=at and at+count<=RECORD+4),(phase,hex(uc.reg_read(UC_ARM_REG_PC)-BASE),hex(at),count)
            if fresh_global(at,count) or RECORD<=at<RECORD+4:global_writes.append({'phase':phase,'sourceBankOffset':uc.reg_read(UC_ARM_REG_PC)-BASE,'address':at,'bytes':count,'value':value})
        else:
            assert caller or fresh_global(at,count) or (BASE<=at and at+count<=BASE+len(bank)) or (DATA<=at and at+count<=DATA+len(initialized)) or (NODE<=at and at+count<=NODE+len(node)),(phase,hex(uc.reg_read(UC_ARM_REG_PC)-BASE),hex(at),count)
    u.hook_add(unicorn.UC_HOOK_CODE,code);u.hook_add(unicorn.UC_HOOK_MEM_READ|unicorn.UC_HOOK_MEM_WRITE,access)
    def call(entry,name,r0=0,r1=0,r2=0):
        nonlocal phase,stop
        phase,stop=name,None
        for i,r in enumerate(CALLEE):u.reg_write(r,0x44440000+i)
        for r,val in ((UC_ARM_REG_R0,r0),(UC_ARM_REG_R1,r1),(UC_ARM_REG_R2,r2),(UC_ARM_REG_SP,sp),(UC_ARM_REG_LR,RETURN)):u.reg_write(r,val)
        u.emu_start(BASE+entry,RETURN+4,count=250000)
        assert u.reg_read(UC_ARM_REG_PC)==RETURN and u.reg_read(UC_ARM_REG_SP)==sp,name
        assert all(u.reg_read(r)==0x44440000+i for i,r in enumerate(CALLEE)),name
        return u.reg_read(UC_ARM_REG_R0)
    word=lambda at:struct.unpack('<I',bytes(u.mem_read(at,4)))[0]
    bitmap=call(0x3dad6c,'resident-bitmap',DESC);pixels=word(bitmap+0x14)
    assert live(bitmap,52) and live(pixels,n) and bytes(u.mem_read(pixels,n))==raw[36:]
    assert memcpys==[[pixels,NODE+48,n]]
    call(0x1124ac,'image-factory',HOLDER);image=word(HOLDER)
    assert live(image,0x5c) and word(image+0x28)==1
    # Source callback3EA774h sets r2=0 before3EA778h calls this exact function.
    assert call(0x112610,'attach-original-bitmap',image,bitmap,0)==1
    assert word(image+0x34)==bitmap and word(image+0x38)==0
    assert word(THREAD)==0 and word(THREAD+0xc)==1 and word(THREAD+0x10)==1
    assert word(THREAD+0x14)==THREAD and word(THREAD+0x18)==THREAD
    assert word(HEAD)==RECORD and word(RECORD)==0
    call(0x11256c,'set-source-mip-flag',image,0)
    assert bytes(u.mem_read(image+0x30,1))==b'\0'
    assert call(0x1195b8,'texture-constructor',OBJECT)==OBJECT
    call(0x104318,'assign-image',OBJECT+0xb8,HOLDER)
    call(0x104318,'release-local-holder',HOLDER,HOLDER+4)
    assert word(image+0x28)==1 and word(OBJECT+0xb8)==image and word(HOLDER)==0
    vtable=word(image+4);assert vtable==0x51a7fc
    target=call(word(vtable+0x5c)-BASE,'original-target-getter',image)
    assert target==0 and call(word(vtable+0x44)-BASE,'original-loaded-mip-getter',image)==0
    # Explicit source-decoded filtering fields; original field reader is
    # separately pinned. Full Texture decoder/provider are not supplied here.
    source_fields=texture['samplingFields'];assert source_fields in ([1,1,0,1,1],[1,1,2,1,1])
    u.mem_write(OBJECT+0xc0,struct.pack('<5I',*source_fields))
    phase,stop='minification',BASE+0x26e36
    for r,val in ((UC_ARM_REG_SP,sp),(UC_ARM_REG_R5,word(image+0x24)),(UC_ARM_REG_R6,OBJECT),
                  (UC_ARM_REG_R7,source_fields[2]),(UC_ARM_REG_R8,target),(UC_ARM_REG_R9,source_fields[1])):u.reg_write(r,val)
    u.emu_start(BASE+0x10b4fc,stop+4,count=4096)
    assert u.reg_read(UC_ARM_REG_PC)==stop and boundary['filter']==[0xde1,0x2801,0x2601]
    assert word(image+0x28)==1 and word(image+0x34)==bitmap
    phase,stop='upload',BASE+0x2545c
    u.reg_write(UC_ARM_REG_R5,word(image+0x34));u.reg_write(UC_ARM_REG_SP,sp-0x40)
    u.emu_start(BASE+0x10aabc,stop+4,count=1024)
    assert u.reg_read(UC_ARM_REG_PC)==stop and boundary['upload']==[0xde1,0,0x1908,width,height,0,0x1908,0x1401,pixels]
    # Separate explicit active-count witness: original mutation methods must
    # reject changes while active, then allow the same request while inactive.
    assert word(image+0x10)==0
    u.mem_write(image+0x10,struct.pack('<I',1))
    assert call(0x112610,'active-attachment-rejection',image,0,0)==0
    assert word(image+0x34)==bitmap
    call(0x11256c,'active-mip-change-rejection',image,1)
    assert bytes(u.mem_read(image+0x30,1))==b'\0'
    u.mem_write(image+0x10,struct.pack('<I',0))
    call(0x11256c,'inactive-mip-change-acceptance',image,1)
    assert bytes(u.mem_read(image+0x30,1))==b'\1'
    call(0x11256c,'restore-source-mip-flag',image,0)
    assert bytes(u.mem_read(image+0x30,1))==b'\0' and word(image+0x34)==bitmap
    assert bytes(u.mem_read(NODE,len(node)))==node
    assert bytes(u.mem_read(DATA+0x1f22c+4,8))==initialized[0x1f230:0x1f238]
    return {'label':texture['bitmapResourceName'],'recordHeaderOffset':texture['record']['headerOffset'],
        'heapFill':fill,'sourcePayloadSha256':sha(raw),'samplingFields':source_fields,
        'pixelPointer':pixels,'bitmapPointer':bitmap,'imagePointer':image,'pixelBytes':n,
        'copiedPixelSha256':sha(bytes(u.mem_read(pixels,n))),'width':width,'height':height,
        'allocations':allocations,'originalMemcpyArguments':memcpys,'globalWrites':global_writes,
        'originalInstructionsByPhase':{p:sum(x==p for x,_ in visits) for p in dict.fromkeys(x for x,_ in visits)},
        'threadManagerIndex':word(THREAD),'threadManagerPointer':THREAD,'registrationHead':word(HEAD),
        'loadedBitmapAttached':word(image+0x34)==bitmap,'deleterPointer':word(image+0x38),
        'mipmapFlag':0,'referenceCountAtGraphicsBoundary':word(image+0x28),
        'activeStateWitness':{'explicitActiveCountMutation':True,'attachmentRejected':True,
            'activeMipmapChangeRejected':True,'inactiveMipmapChangeAccepted':True,'sourceStateRestored':True},
        'nativeFilterArguments':boundary['filter'],'nativeUploadArguments':boundary['upload'],
        'originalTraceSha256':trace.hexdigest(),'sourcePixelsUnchanged':True}
