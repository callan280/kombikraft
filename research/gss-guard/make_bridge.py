#!/usr/bin/env python3
"""Compile an authored reset-to-flat32 bridge; NOT a recovered OEM loader."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess

HERE=Path(__file__).resolve().parent


def build(out,clang='clang',entry=0x100000):
    if not isinstance(entry,int)or not 0<=entry<=0xffffffff:raise ValueError('Entry must be a32-bit address')
    source=(HERE/'reset_bridge.S').read_text()
    assert source.count('.long 0x100000')==1
    source=source.replace('.long 0x100000','.long '+hex(entry))
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    asm=out/'reset_bridge.S';obj=out/'reset_bridge.o';asm.write_text(source)
    subprocess.run([clang,'-target','i386-unknown-none-elf','-c',str(asm),'-o',str(obj)],check=True)
    raw=obj.read_bytes()
    if raw[:7]!=b'\x7fELF\x01\x01\x01':raise ValueError('Expected a little-endian ELF32 assembler object')
    header=struct.unpack_from('<16sHHIIIIIHHHHHH',raw)
    sections=[struct.unpack_from('<IIIIIIIIII',raw,header[6]+i*header[11])for i in range(header[12])]
    names=sections[header[13]];strings=raw[names[4]:names[4]+names[5]];text=[]
    for row in sections:
        if row[1]in[4,9]and row[5]:raise ValueError('Bridge must have no unresolved relocations')
        if strings[row[0]:].split(b'\0')[0]==b'.text':text.append(raw[row[4]:row[4]+row[5]])
    if len(text)!=1:raise ValueError('Expected one text section')
    bridge=text[0];rom=bytearray(b'\xcc'*65536);rom[0xfff0:0xfff5]=bytes.fromhex('ea00800000')
    (out/'reset_bridge.bin').write_bytes(bridge);(out/'reset_rom.bin').write_bytes(rom)
    (out/'bridge-receipt.json').write_text(json.dumps({'schema':'authored-flat32-bridge-v1','entry':hex(entry),
        'bridgeAddress':'0x8000','bridgeSha256':hashlib.sha256(bridge).hexdigest(),
        'resetRomSha256':hashlib.sha256(rom).hexdigest(),'authenticOemBootloader':False,
        'firmwareBytesIncluded':False},indent=2)+'\n')
    return bridge,bytes(rom)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--clang',default='clang');p.add_argument('--entry',type=lambda v:int(v,0),default=0x100000)
    a=p.parse_args();build(a.output_dir,a.clang,a.entry)


if __name__=='__main__':main()
