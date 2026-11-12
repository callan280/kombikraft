#!/usr/bin/env python3
"""Extract one LZ4 NORboot bank from a locally supplied decoded flash image.

This reads the NORboot table, not an arbitrary SWFL/PSdZ archive. It never
executes a boot loader or treats table targets as proved runtime addresses.
"""
import argparse
import ctypes
import ctypes.util
import hashlib
import json
from pathlib import Path
import struct

MAX_IMAGE = 128*1024*1024
MAX_BANK = 64*1024*1024


def record(image, offset, index):
    if offset < 0 or offset+16 > len(image) or image[offset:offset+8] != b'NORboot\0':
        raise ValueError('No NORboot header at the supplied offset')
    version,count = struct.unpack_from('<2I',image,offset+8)
    if version != 0x14 or not 0 < count <= 64:
        raise ValueError('Unsupported NORboot table version/count')
    if not 0 <= index < count or offset+16+count*24 > len(image):
        raise ValueError('Bank index or table outside input')
    row = struct.unpack_from('<6I',image,offset+16+index*24)
    start,target,packed,decoded,memory,flags = row
    if flags != 4 or not 0 < packed <= MAX_BANK or not 0 < decoded <= memory <= MAX_BANK:
        raise ValueError('Unsupported bank flags or lengths')
    if start < 16+count*24 or offset+start+packed > len(image):
        raise ValueError('Compressed bank outside input')
    if target+decoded > 1<<32:
        raise ValueError('Table target range wraps')
    return {'index':index,'packedOffset':offset+start,'tableTarget':target,
            'packedBytes':packed,'decodedBytes':decoded,'word4':memory,'flags':flags}


def decode(image, row, library=None):
    name = library or ctypes.util.find_library('lz4')
    if not name:
        raise ValueError('Provide --lz4-library pointing to your installed liblz4')
    lib=ctypes.CDLL(str(name))
    fn=lib.LZ4_decompress_safe
    fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int]
    fn.restype=ctypes.c_int
    source=image[row['packedOffset']:row['packedOffset']+row['packedBytes']]
    output=ctypes.create_string_buffer(row['decodedBytes'])
    if fn(source,output,len(source),len(output)) != row['decodedBytes']:
        raise ValueError('LZ4 output length differs from table')
    return output.raw


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--offset',type=lambda v:int(v,0),default=0)
    p.add_argument('--bank',type=int,default=13)
    p.add_argument('--lz4-library',help='Local dynamic library path; otherwise use the system lookup')
    args=p.parse_args(argv)
    try:
        if args.output.exists():raise ValueError('Output exists; choose a new directory')
        if args.image.stat().st_size > MAX_IMAGE:raise ValueError('Input exceeds 128 MiB limit')
        image=args.image.read_bytes();row=record(image,args.offset,args.bank)
        data=decode(image,row,args.lz4_library)
        receipt={'schema':'kombikraft-norboot-bank-v1','sourceSha256':hashlib.sha256(image).hexdigest(),
            'headerOffset':args.offset,'record':row,'decodedSha256':hashlib.sha256(data).hexdigest(),
            'originalLoaderExecuted':False,'runtimeMappingProven':False,'word4ZeroFillProven':False,
            'vehicleCompatibilityVerified':False,'installationAllowed':False}
        args.output.mkdir(parents=True,exist_ok=False)
        name=f"bank-{args.bank:02d}.bin"
        (args.output/name).write_bytes(data)
        (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    except (OSError,ValueError) as exc:p.exit(1,f'NORboot extraction failed: {exc}\n')
    print(json.dumps({'bank':row['index'],'decodedBytes':len(data),
                      'sha256':receipt['decodedSha256'],'runtimeMappingProven':False}))
    return 0


if __name__=='__main__':raise SystemExit(main())
