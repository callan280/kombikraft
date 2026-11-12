"""Original image construction, ownership and minification decision unit.

Runs the real BitmapTextureImage factory/constructor, Texture constructor and
SharedPtr assignment routines. The scene-reader fragment and parameter prefix
have explicit interior caller states; a bounded allocation adapter is the only
replaced function. Stops before the graphics call, without inventing its return.
This is not provider/cache startup or a full resource decoder.
"""
from pathlib import Path
import hashlib, json, struct
import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
    UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
    UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_SP, UC_ARM_REG_LR,
    UC_ARM_REG_PC, UC_ARM_REG_C1_C0_2, UC_ARM_REG_FPEXC)

BASE, OBJECT, DESC, STREAM, HOLDER = 0x10000, 0x30000000, 0x30001000, 0x30002000, 0x30003000
HEAP, SCENE, STACK, RETURN = 0x31000000, 0x40000000, 0x33000000, 0x70000000
CALLEE = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
          UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
sha = lambda b: hashlib.sha256(b).hexdigest()


def observe(bank, scene, texture, fill, witness=None):
    header = texture['record']['headerOffset']
    data = bytearray(scene)
    if witness is not None:
        min_filter, mip_filter, image_mips = witness
        struct.pack_into('<I', data, header + 0x7c, min_filter)
        struct.pack_into('<I', data, header + 0x80, mip_filter)
    else:
        image_mips = 0
    assert struct.unpack_from('<I', data, header + 0x84)[0] == 0
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    size = (len(bank) + 4095) & ~4095
    u.mem_map(BASE, size); u.mem_write(BASE, bank)
    u.mem_protect(BASE, size, UC_PROT_READ | UC_PROT_EXEC)
    u.mem_map(OBJECT, 0x4000, UC_PROT_READ | UC_PROT_WRITE)
    u.mem_write(OBJECT, bytes([fill]) * 0xd8)
    u.mem_map(SCENE, (len(data)+4095)&~4095, UC_PROT_READ); u.mem_write(SCENE, bytes(data))
    u.mem_map(HEAP, 0x10000, UC_PROT_READ | UC_PROT_WRITE)
    u.mem_map(STACK, 0x4000, UC_PROT_READ | UC_PROT_WRITE)
    u.mem_map(RETURN, 4096, UC_PROT_READ | UC_PROT_EXEC)
    u.mem_write(DESC, struct.pack('<4I', STREAM, 0, SCENE+header, 0))
    u.reg_write(UC_ARM_REG_C1_C0_2, 0xf00000)
    u.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    sp = STACK+0x3f00
    allocations, visits, boundary = [], [], {}
    trace = hashlib.sha256(); phase = ''; stop = None; next_at = HEAP

    def live(at, n):
        return any(a['pointer'] <= at and at+n <= a['pointer']+a['bytes'] for a in allocations)

    def code(uc, address, length, _):
        nonlocal next_at
        if address == RETURN or address == stop:
            if phase == 'minification':
                boundary['arguments'] = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
            uc.emu_stop(); return
        off = address-BASE
        assert 0 <= off and off+length <= len(bank), hex(address)
        if off == 0x128498:
            n = uc.reg_read(UC_ARM_REG_R0); assert n == 0x5c
            ptr = next_at; next_at = (ptr+n+15)&~15
            allocations.append({'pointer':ptr, 'bytes':n})
            uc.mem_write(ptr, bytes([fill])*n)
            uc.reg_write(UC_ARM_REG_R0,ptr); uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR)); return
        visits.append((phase,off)); trace.update(phase.encode()+struct.pack('<I',off)+bank[off:off+length])

    def access(uc, kind, address, n, value, _):
        writable = ((OBJECT <= address and address+n <= OBJECT+0x4000)
                    or (STACK <= address and address+n <= STACK+0x4000) or live(address,n))
        if kind == unicorn.UC_MEM_WRITE:
            assert writable, (hex(uc.reg_read(UC_ARM_REG_PC)-BASE),hex(address),n)
        else:
            assert writable or (BASE <= address and address+n <= BASE+len(bank)) or (SCENE <= address and address+n <= SCENE+len(data)), (hex(uc.reg_read(UC_ARM_REG_PC)-BASE),hex(address),n)

    u.hook_add(unicorn.UC_HOOK_CODE,code)
    u.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE,access)

    def call(entry, name, r0=0, r1=0):
        nonlocal phase, stop
        phase, stop = name, None
        for i,r in enumerate(CALLEE): u.reg_write(r,0x44440000+i)
        u.reg_write(UC_ARM_REG_R0,r0); u.reg_write(UC_ARM_REG_R1,r1)
        u.reg_write(UC_ARM_REG_SP,sp); u.reg_write(UC_ARM_REG_LR,RETURN)
        u.emu_start(BASE+entry, RETURN+4, count=30000)
        assert u.reg_read(UC_ARM_REG_PC)==RETURN, (name,hex(u.reg_read(UC_ARM_REG_PC)-BASE))
        assert u.reg_read(UC_ARM_REG_SP)==sp
        assert all(u.reg_read(r)==0x44440000+i for i,r in enumerate(CALLEE)), name
        return u.reg_read(UC_ARM_REG_R0)

    word = lambda at: struct.unpack('<I',bytes(u.mem_read(at,4)))[0]
    assert call(0x1195b8,'texture-constructor',OBJECT)==OBJECT
    assert word(OBJECT+0xb8)==0
    call(0x1124ac,'image-factory',HOLDER)
    image=word(HOLDER); assert live(image,0x5c)
    assert word(image+0x24)==0 and word(image+0x28)==1
    assert bytes(u.mem_read(image+0x30,1))==b'\0'
    vtable=word(image+4); assert vtable==0x51a7fc
    mip_getter,target_getter=word(vtable+0x44),word(vtable+0x5c)
    assert (mip_getter-BASE,target_getter-BASE)==(0x112378,0x112744)
    assert call(target_getter-BASE,'original-target-getter',image)==0
    assert call(mip_getter-BASE,'original-default-mip-getter',image)==0
    call(0x104318,'assign-image',OBJECT+0xb8,HOLDER)
    assert word(image+0x28)==2 and word(OBJECT+0xb8)==image
    call(0x104318,'release-local-holder',HOLDER,HOLDER+4)
    assert word(image+0x28)==1 and word(HOLDER)==0
    phase,stop='texture-fields',BASE+0x3efbc0
    u.reg_write(UC_ARM_REG_R7,DESC); u.reg_write(UC_ARM_REG_SP,sp)
    u.mem_write(sp+0x34,struct.pack('<I',OBJECT))
    u.emu_start(BASE+0x3efae8,stop+4,count=4096)
    assert u.reg_read(UC_ARM_REG_PC)==stop
    fields=list(struct.unpack('<5I',bytes(u.mem_read(OBJECT+0xc0,20))))
    assert fields==[struct.unpack_from('<I',data,header+o)[0] for o in (0x78,0x7c,0x80,0x88,0x8c)]
    if image_mips:
        # A declared property mutation tests the original virtual decision;
        # it does not claim a mip chain was generated or loaded.
        u.mem_write(image+0x30,b'\1')
    assert call(mip_getter-BASE,'original-selected-mip-getter',image)==image_mips
    phase,stop='minification',BASE+0x26e36
    u.reg_write(UC_ARM_REG_SP,sp)
    u.reg_write(UC_ARM_REG_R5,word(image+0x24))
    u.reg_write(UC_ARM_REG_R6,OBJECT)
    u.reg_write(UC_ARM_REG_R7,fields[2])
    u.reg_write(UC_ARM_REG_R8,0)  # original getter output above; explicit caller state
    u.reg_write(UC_ARM_REG_R9,fields[1])
    u.emu_start(BASE+0x10b4fc,stop+4,count=4096)
    assert u.reg_read(UC_ARM_REG_PC)==stop and word(image+0x28)==1
    want=0x2600+fields[1] if fields[2]==0 or image_mips==0 else 0x2700+fields[1]+2*(fields[2]-1)
    assert boundary['arguments']==[0xde1,0x2801,want]
    assert bytes(u.mem_read(SCENE,len(data)))==bytes(data)
    return {'label':texture['bitmapResourceName'],'recordHeaderOffset':header,'heapFill':fill,
        'variant':'genuine-record' if witness is None else 'declared-property-and-field-witness',
        'declaredWitness':list(witness) if witness is not None else None,
        'sourceMipmapGenerationField':0,'constructedImageDefaultMipmapFlag':0,
        'selectedImageMipmapFlag':image_mips,'decodedSamplingFields':fields,
        'originalVtable':vtable,'originalMipmapGetterBankOffset':mip_getter-BASE,
        'originalTargetGetterBankOffset':target_getter-BASE,'originalTargetGetterValue':0,
        'referenceCountSequence':[1,2,1],'referenceCountAtGraphicsBoundary':word(image+0x28),
        'originalMinificationArguments':boundary['arguments'],
        'originalMinificationGetterCalls':sum(p=='minification' and o==0x112378 for p,o in visits),
        'allocations':allocations,'originalInstructionsByPhase':{p:sum(x==p for x,_ in visits) for p in dict.fromkeys(x for x,_ in visits)},
        'originalTraceSha256':trace.hexdigest(),'sourceSceneUnchanged':True}
